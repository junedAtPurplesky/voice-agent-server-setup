#!/bin/bash
# Apply CUDA optimizations

echo "Applying CUDA optimizations..."

# Set environment variables for optimal GPU performance
export CUDA_VISIBLE_DEVICES=0
export CUDA_LAUNCH_BLOCKING=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export CUDA_MODULE_LOADING=LAZY

# Performance settings
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

echo "✓ CUDA optimizations applied"
echo "  CUDA_VISIBLE_DEVICES=0"
echo "  PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512"
echo "  CUDA_MODULE_LOADING=LAZY"
