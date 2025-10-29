FROM nvidia/cuda:12.1-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    git \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    websockets==12.0 \
    torch==2.1.0 \
    torchaudio==2.1.0 \
    pydantic==2.5.0 \
    pyjwt==2.8.1 \
    python-multipart==0.0.6 \
    scipy==1.11.0 \
    numpy==1.24.0

# Clone and install CosyVoice
RUN git clone https://github.com/FunAudioLLM/CosyVoice.git /cosyvoice && \
    cd /cosyvoice && \
    pip install -e .

# Copy application
COPY app/tts_main.py /app/main.py

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
