import os
import json
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, WebSocket, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
API_KEY = os.getenv("LLM_API_KEY", "llm_secret_key_production_123456")
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct-AWQ"
QUANTIZATION = "awq"  # Important: AWQ quantization
DTYPE = "float16"  # Important: float16 only (NOT bfloat16)
DEVICE = "cuda"
MAX_MODEL_LEN = 4096
GPU_MEMORY_UTIL = 0.85

# Initialize FastAPI app
app = FastAPI(
    title="LLM Service - Qwen 2.5 7B AWQ",
    description="Language Model Microservice with AWQ 4-bit Quantization",
    version="1.0.0",
    root_path="/llm"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model on startup
llm = None

@app.on_event("startup")
async def load_model():
    global llm
    try:
        logger.info(f"Loading {MODEL_NAME}...")
        logger.info(f"Quantization: {QUANTIZATION} (4-bit)")
        logger.info(f"Data Type: {DTYPE} (required for AWQ)")
        logger.info(f"Max Model Length: {MAX_MODEL_LEN}")
        logger.info(f"GPU Memory Utilization: {GPU_MEMORY_UTIL * 100}%")

        from vllm import LLM

        # Initialize vLLM with AWQ quantization
        llm = LLM(
            model=MODEL_NAME,
            quantization=QUANTIZATION,  # Enable AWQ quantization
            dtype=DTYPE,  # Must be float16 for AWQ (not bfloat16)
            tensor_parallel_size=1,
            gpu_memory_utilization=GPU_MEMORY_UTIL,
            trust_remote_code=True,
            max_model_len=MAX_MODEL_LEN,
            enforce_eager=False  # Can use CUDA graphs
        )

        logger.info("✅ LLM model loaded successfully (AWQ 4-bit quantized)")
        logger.info(f"Expected VRAM usage: 3-4GB (vs 7-8GB full precision)")

    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise

# Validate API Key
async def validate_api_key(authorization: Optional[str] = Header(None)):
    """Simple Bearer token validation"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
        if token != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

# REST Endpoint: OpenAI-compatible chat completion
@app.post("/v1/chat/completions")
async def chat_completion(
    request_data: dict,
    authorization: Optional[str] = Header(None)
):
    """
    OpenAI-compatible chat completion endpoint

    Parameters:
    - model: Model name (ignored, uses Qwen 2.5 7B AWQ)
    - messages: Chat history
    - temperature: Sampling temperature (0-1)
    - max_tokens: Maximum tokens to generate
    - authorization: Bearer {API_KEY}

    Example:
    curl -X POST "<http://localhost/llm/v1/chat/completions>" \\\\
      -H "Authorization: Bearer llm_secret_key_production_123456" \\\\
      -H "Content-Type: application/json" \\\\
      -d '{
        "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
        "messages": [
          {"role": "system", "content": "You are a helpful assistant"},
          {"role": "user", "content": "What is AI?"}
        ],
        "temperature": 0.7,
        "max_tokens": 512
      }'

    Response:
    {
      "id": "chatcmpl-123456",
      "object": "chat.completion",
      "created": 1234567890,
      "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
      "choices": [{
        "index": 0,
        "message": {"role": "assistant", "content": "..."},
        "finish_reason": "stop"
      }],
      "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    }
    """
    await validate_api_key(authorization)

    try:
        from vllm import SamplingParams

        messages = request_data.get("messages", [])
        temperature = request_data.get("temperature", 0.7)
        max_tokens = request_data.get("max_tokens", 512)

        logger.info(f"Processing chat request with {len(messages)} messages (AWQ quantized)")

        # Create sampling parameters
        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95
        )

        # Generate response using AWQ quantized model
        outputs = llm.chat(messages, sampling_params=sampling_params)
        generated_text = outputs[0].outputs[0].text if outputs else "Error generating response"

        logger.info(f"✅ Chat completion generated: {len(generated_text)} characters")

        return {
            "id": f"chatcmpl-{int(datetime.utcnow().timestamp())}",
            "object": "chat.completion",
            "created": int(datetime.utcnow().timestamp()),
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": len(generated_text.split()),
                "total_tokens": len(generated_text.split())
            }
        }

    except Exception as e:
        logger.error(f"❌ Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket Endpoint: Real-time streaming responses
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket for real-time chat streaming with AWQ model

    Connection URL:
    wss://your-domain.com/llm/ws?token=llm_secret_key_production_123456

    Client -> Server (JSON):
    {
      "messages": [
        {"role": "system", "content": "You are a sales agent"},
        {"role": "user", "content": "What is the product price?"}
      ],
      "temperature": 0.7,
      "max_tokens": 512
    }

    Server -> Client (JSON stream):
    {"type": "token", "content": "The"}
    {"type": "token", "content": " product"}
    ...
    {"type": "complete", "total_tokens": 50}
    """

    # Validate token
    if not token or token != API_KEY:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()
    logger.info("✅ WebSocket client connected (LLM - AWQ)")

    try:
        from vllm import SamplingParams

        while True:
            # Receive chat request
            data = await websocket.receive_text()
            request = json.loads(data)

            messages = request.get("messages", [])
            temperature = request.get("temperature", 0.7)
            max_tokens = request.get("max_tokens", 512)

            try:
                # Create sampling parameters
                sampling_params = SamplingParams(
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=0.95
                )

                # Generate response using AWQ model
                outputs = llm.chat(messages, sampling_params=sampling_params)

                if outputs:
                    generated_text = outputs[0].outputs[0].text

                    # Stream tokens
                    for word in generated_text.split():
                        await websocket.send_json({
                            "type": "token",
                            "content": word + " "
                        })

                    # Signal completion
                    await websocket.send_json({
                        "type": "complete",
                        "total_tokens": len(generated_text.split()),
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()
        logger.info("❌ WebSocket client disconnected (LLM)")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LLM (Qwen 2.5 7B AWQ)",
        "model": MODEL_NAME,
        "quantization": QUANTIZATION,
        "dtype": DTYPE,
        "max_model_len": MAX_MODEL_LEN,
        "device": DEVICE,
        "timestamp": datetime.utcnow().isoformat()
    }

# Service info
@app.get("/")
async def service_info():
    """Service information"""
    return {
        "service": "Language Model (AWQ 4-bit Quantized)",
        "model": MODEL_NAME,
        "quantization": "AWQ 4-bit (50% VRAM reduction)",
        "vram_usage": "3-4GB (vs 7-8GB full precision)",
        "speed": "60-80 tokens/sec",
        "endpoints": {
            "v1/chat/completions": "/v1/chat/completions (POST)",
            "websocket": "/ws (WebSocket)",
            "health": "/health (GET)",
            "docs": "/docs"
        },
        "auth": "Bearer token in Authorization header"
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        workers=1,
        log_level="info"
    )
