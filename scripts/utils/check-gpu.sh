#!/bin/bash
# Check GPU availability and status

echo "Checking GPU availability..."

if ! nvidia-smi &> /dev/null; then
    echo "✗ NVIDIA GPU not detected"
    exit 1
fi

echo "✓ GPU Information:"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

echo ""
echo "✓ CUDA Version:"
nvcc --version | grep "release" || echo "nvcc not in PATH"

echo ""
echo "✓ Current GPU Status:"
nvidia-smi
