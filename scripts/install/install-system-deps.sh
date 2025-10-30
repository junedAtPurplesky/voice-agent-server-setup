#!/bin/bash
################################################################################
# Install System Dependencies
################################################################################

echo "Installing system dependencies..."

sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    python3.11-dev \
    build-essential \
    ffmpeg \
    libsndfile1 \
    git \
    curl \
    wget \
    htop \
    nvtop \
    tmux \
    vim \
    netcat \
    jq \
    bc

echo "✓ System dependencies installed"
