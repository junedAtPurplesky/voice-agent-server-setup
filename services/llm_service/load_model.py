#!/usr/bin/env python3
"""Test LLM Model Loading"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

print("="*70)
print("LLM Model Loading Test - Qwen 2.5 7B AWQ")
print("="*70)

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct-AWQ"
QUANTIZATION = "awq"
DTYPE = "float16"

print(f"\nConfiguration:")
print(f"  Model: {MODEL_NAME}")
print(f"  Quantization: {QUANTIZATION} (4-bit)")
print(f"  Data Type: {DTYPE}")

print("\n[1/2] Importing vLLM...")
try:
    from vllm import LLM
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

print("\n[2/2] Loading model (may take 60-90 seconds)...")
try:
    llm = LLM(
        model=MODEL_NAME,
        quantization=QUANTIZATION,
        dtype=DTYPE,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.85,
        trust_remote_code=True,
        max_model_len=4096
    )
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Model loading failed: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✓ LLM Model Test PASSED - Ready for production")
print("="*70)
