import os
import json
from typing import Optional
import httpx
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
API_KEYS = [k.strip() for k in os.getenv("ALLOWED_API_KEYS", "").split(",") if k.strip()]
VLLM_BASE = os.getenv("VLLM_BASE", "http://127.0.0.1:8000").rstrip("/")

# --- FastAPI setup ---
app = FastAPI(
    title="vLLM Gateway",
    description="Secure proxy for vLLM-compatible endpoints with API key validation",
    version="1.3.1",
)


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


# --- Stream Handler ---
async def proxy_stream(resp: httpx.Response):
    """
    Properly stream SSE responses line by line to the client.
    """
    async def event_stream():
        try:
            async for line in resp.aiter_lines():
                # Send each line immediately with newline
                yield f"{line}\n"
        except httpx.StreamClosed:
            pass
        except Exception as e:
            print(f"[Stream error] {e}")
        finally:
            await resp.aclose()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


# --- Universal Proxy ---
async def forward_request(
    request: Request,
    method: str,
    path: str,
    authorization: Optional[str],
):
    # Validate API key
    check_auth(authorization)

    # Construct target URL
    query_string = request.url.query
    url = f"{VLLM_BASE}/{path}"
    if query_string:
        url += f"?{query_string}"

    # Copy headers except host/length
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = authorization

    # Read request body
    body = await request.body()

    async with httpx.AsyncClient(timeout=None, http2=True, follow_redirects=True) as client:
        async with client.stream(method, url, content=body or None, headers=headers) as resp:
            content_type = resp.headers.get("content-type", "")
            status = resp.status_code

            # --- Streamed Response (SSE) ---
            if content_type.startswith("text/event-stream"):
                return await proxy_stream(resp)

            # --- Normal Response ---
            data = await resp.aread()
            await resp.aclose()

            if content_type.startswith("application/json"):
                try:
                    parsed = json.loads(data.decode("utf-8"))
                    return JSONResponse(status_code=status, content=parsed)
                except json.JSONDecodeError:
                    return JSONResponse(status_code=status, content={"error": "Invalid JSON response"})
            else:
                return StreamingResponse(
                    iter([data]),
                    status_code=status,
                    media_type=content_type or "application/octet-stream",
                )


# --- OpenAI-compatible routes ---
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


# --- Internal + Utility Routes ---
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


# --- Health Check (Gateway + vLLM) ---
@app.get("/healthz")
async def healthz():
    """Combined gateway + vLLM health check."""
    gateway_status = {"gateway": "ok"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{VLLM_BASE}/health")
            if resp.status_code == 200:
                try:
                    vllm_status = resp.json()
                except Exception:
                    vllm_status = {"raw": await resp.aread()}
                return {"gateway": gateway_status, "vllm": vllm_status, "vllm_status": "ok"}
            else:
                return {"gateway": gateway_status, "vllm_status": f"unhealthy ({resp.status_code})"}
    except Exception as e:
        return {"gateway": gateway_status, "vllm_status": f"unreachable: {e.__class__.__name__}"}


# --- Run (optional) ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gateway:app", host="0.0.0.0", port=int(os.getenv("GATEWAY_PORT", 8080)), reload=False)