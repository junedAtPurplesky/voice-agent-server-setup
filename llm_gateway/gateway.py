# gateway.py
import os
import json
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_KEYS = os.getenv("ALLOWED_API_KEYS", "").split(",")
VLLM_BASE = os.getenv("VLLM_BASE", "http://127.0.0.1:8000")
if VLLM_BASE.endswith("/"):
    VLLM_BASE = VLLM_BASE[:-1]

# --- FastAPI setup ---
app = FastAPI(title="vLLM Gateway", description="Proxies all vLLM endpoints with API key auth")


# --- Auth ---
def check_auth(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    token = authorization.split(None, 1)[1].strip()
    if token not in API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return token


# --- Helper: Stream Proxy ---
async def proxy_stream(resp: httpx.Response):
    async def event_stream():
        async for chunk in resp.aiter_bytes():
            if chunk:
                yield chunk
    return StreamingResponse(event_stream(), media_type=resp.headers.get("content-type", "text/event-stream"))


# --- Universal Proxy Handler ---
async def forward_request(
    request: Request,
    method: str,
    path: str,
    authorization: Optional[str]
):
    check_auth(authorization)

    body = await request.body()
    query_string = request.url.query
    url = f"{VLLM_BASE}/{path}"
    if query_string:
        url += f"?{query_string}"

    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    headers["Content-Type"] = "application/json"

    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.request(method, url, content=body or None, headers=headers, stream=True)

        if resp.headers.get("content-type", "").startswith("text/event-stream"):
            return await proxy_stream(resp)

        if resp.headers.get("content-type", "").startswith("application/json"):
            data = await resp.aread()
            return JSONResponse(status_code=resp.status_code, content=json.loads(data))

        return StreamingResponse(resp.aiter_bytes(), media_type=resp.headers.get("content-type", "application/octet-stream"))


# --- vLLM-compatible routes (OpenAI-style) ---
@app.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "v1/chat/completions", authorization)

@app.post("/v1/completions")
async def completions(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "v1/completions", authorization)

@app.post("/v1/embeddings")
async def embeddings(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "v1/embeddings", authorization)

@app.get("/v1/models")
async def models(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "GET", "v1/models", authorization)

@app.post("/v1/responses")
async def responses(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "v1/responses", authorization)

@app.get("/v1/responses/{response_id}")
async def get_response(response_id: str, request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "GET", f"v1/responses/{response_id}", authorization)

@app.post("/v1/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", f"v1/responses/{response_id}/cancel", authorization)

@app.post("/v1/audio/transcriptions")
async def transcriptions(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "v1/audio/transcriptions", authorization)

@app.post("/v1/audio/translations")
async def translations(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "v1/audio/translations", authorization)

@app.post("/v1/rerank")
async def rerank(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "v1/rerank", authorization)


# --- vLLM internal & utility routes ---
@app.get("/health")
async def health(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "GET", "health", authorization)

@app.get("/load")
async def load(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "GET", "load", authorization)

@app.post("/ping")
@app.get("/ping")
async def ping(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, request.method, "ping", authorization)

@app.post("/tokenize")
async def tokenize(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "tokenize", authorization)

@app.post("/detokenize")
async def detokenize(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "detokenize", authorization)

@app.post("/classify")
async def classify(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "classify", authorization)

@app.post("/score")
@app.post("/v1/score")
async def score(request: Request, authorization: Optional[str] = Header(None)):
    path = request.url.path.lstrip("/")
    return await forward_request(request, "POST", path, authorization)

@app.post("/pooling")
async def pooling(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "pooling", authorization)

@app.post("/scale_elastic_ep")
async def scale_elastic_ep(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "scale_elastic_ep", authorization)

@app.post("/is_scaling_elastic_ep")
async def is_scaling_elastic_ep(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "is_scaling_elastic_ep", authorization)

@app.post("/invocations")
async def invocations(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "POST", "invocations", authorization)

@app.get("/metrics")
async def metrics(request: Request, authorization: Optional[str] = Header(None)):
    return await forward_request(request, "GET", "metrics", authorization)


# --- Combined Health Check (Gateway + vLLM) ---
@app.get("/healthz")
async def healthz():
    """Reports both gateway and vLLM health status."""
    gateway_status = {"gateway": "ok"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{VLLM_BASE}/health")
            if resp.status_code == 200:
                vllm_status = resp.json()
                return {"gateway": gateway_status, "vllm": vllm_status, "vllm_status": "ok"}
            else:
                return {"gateway": gateway_status, "vllm_status": f"unhealthy ({resp.status_code})"}
    except Exception as e:
        return {"gateway": gateway_status, "vllm_status": f"unreachable: {e.__class__.__name__}"}
