# --- Stage 1: Builder (Heavy) ---
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04 AS builder

WORKDIR /app

# Install Python and build dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip and build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies
# vllm is the core engine. We include common extras.
# We don't pin versions to allow the latest compatible ones, but for production, pinning is usually recommended.
# Here we follow the user's request for "any LLM" compatibility which implies flexibility.
RUN pip install --no-cache-dir \
    "vllm" \
    "fastapi" \
    "uvicorn[standard]" \
    "httpx[http2]" \
    "python-multipart" \
    "python-dotenv" \
    "hf_transfer" \
    "autoawq" \
    "huggingface_hub" \
    "bitsandbytes" \
    "accelerate"

# --- Stage 2: Runtime (Lightweight) ---
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

LABEL maintainer="User"
LABEL description="Generic Lightweight vLLM Docker Image"

WORKDIR /app

# Install Python runtime only
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Environment variables
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# RunPod specific optimizations (can be overridden)
ENV NCCL_P2P_DISABLE=1
ENV CUDA_HOME=/usr/local/cuda

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose port
EXPOSE 8000

ENTRYPOINT ["/app/start.sh"]