FROM nvidia/cuda:12.1-devel-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    python3.11 \\
    python3-pip \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install vLLM with AWQ support
# vLLM 0.4.0+ has better AWQ support
RUN pip install \\
    vllm==0.4.0 \\
    fastapi==0.104.1 \\
    uvicorn==0.24.0 \\
    websockets==12.0 \\
    pydantic==2.5.0 \\
    python-multipart==0.0.6 \\
    torch==2.1.0 \\
    transformers==4.36.0

# Copy application
COPY app/llm_main.py /app/main.py

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f <http://localhost:8002/health> || exit 1

# Run application
CMD ["python", "main.py"]
