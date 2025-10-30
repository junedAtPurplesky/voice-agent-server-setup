#!/usr/bin/env python3
"""
Test LLM Model Loading (Debug)
Loads vLLM Qwen model without starting the service
"""

import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(f"{BASE_DIR}/config/llm.env")

print("="*70)
print("LLM Model Loading Test (Qwen 2.5 7B AWQ)")
print("="*70)

MODEL_NAME = os.getenv("LLM_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct-AWQ")
QUANTIZATION = os.getenv("LLM_QUANTIZATION", "awq")
DTYPE = os.getenv("LLM_DTYPE", "float16")
MAX_MODEL_LEN = int(os.getenv("LLM_MAX_MODEL_LEN", "4096"))
GPU_MEMORY_UTIL = float(os.getenv("LLM_GPU_MEMORY_UTILIZATION", "0.85"))

print(f"\nModel: {MODEL_NAME}")
print(f"Quantization: {QUANTIZATION} (4-bit)")
print(f"Data Type: {DTYPE}")
print(f"Max Length: {MAX_MODEL_LEN}")
print(f"GPU Memory: {GPU_MEMORY_UTIL}")

print("\n[1/3] Importing vLLM...")
start = time.time()
try:
    from vllm import LLM, SamplingParams
    print(f"✓ Import successful ({time.time() - start:.2f}s)")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

print("\n[2/3] Loading model (this may take 60-90 seconds)...")
print("  Downloading/loading AWQ quantized weights...")
start = time.time()
try:
    llm = LLM(
        model=MODEL_NAME,
        quantization=QUANTIZATION,
        dtype=DTYPE,
        tensor_parallel_size=1,
        gpu_memory_utilization=GPU_MEMORY_UTIL,
        trust_remote_code=True,
        max_model_len=MAX_MODEL_LEN,
        enforce_eager=False
    )
    load_time = time.time() - start
    print(f"✓ Model loaded successfully ({load_time:.2f}s)")
except Exception as e:
    print(f"✗ Model loading failed: {e}")
    sys.exit(1)

print("\n[3/3] Testing inference...")
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Say hello in one sentence."}
]

sampling_params = SamplingParams(temperature=0.7, max_tokens=50, top_p=0.95)

start = time.time()
try:
    outputs = llm.chat(messages, sampling_params=sampling_params)
    inference_time = time.time() - start
    
    if outputs:
        generated_text = outputs[0].outputs[0].text
        num_tokens = len(generated_text.split())
        tokens_per_sec = num_tokens / inference_time
        
        print(f"✓ Inference complete ({inference_time:.2f}s)")
        print(f"  Tokens generated: {num_tokens}")
        print(f"  Throughput: {tokens_per_sec:.1f} tokens/sec")
        print(f"  Response: {generated_text[:100]}...")
        
except Exception as e:
    print(f"✗ Inference failed: {e}")
    sys.exit(1)

# Check VRAM usage
print("\n[GPU Memory]")
import subprocess
result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'], 
                       capture_output=True, text=True)
mem_used, mem_total = map(int, result.stdout.strip().split(','))
print(f"  VRAM: {mem_used}MB / {mem_total}MB ({mem_used*100//mem_total}%)")
if mem_used < 5000:
    print(f"  ✓ Excellent! AWQ quantization is working (using <5GB)")

print("\n" + "="*70)
print("✓ LLM Model Test Passed!")
print("="*70)
