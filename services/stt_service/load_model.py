#!/usr/bin/env python3
"""
Test STT Model Loading (Standalone Debug Script)
Run this to test if Faster Whisper model loads correctly
"""

import os
import sys

# Add base directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

print("="*70)
print("STT Model Loading Test - Faster Whisper")
print("="*70)

MODEL_NAME = "large-v3-turbo"
DEVICE = "cuda"
COMPUTE_TYPE = "int8"

print(f"\nConfiguration:")
print(f"  Model: {MODEL_NAME}")
print(f"  Device: {DEVICE}")
print(f"  Compute Type: {COMPUTE_TYPE}")

print("\n[1/2] Importing faster_whisper...")
try:
    from faster_whisper import WhisperModel
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

print("\n[2/2] Loading model (may take 20-30 seconds)...")
try:
    model = WhisperModel(MODEL_NAME, device=DEVICE, compute_type=COMPUTE_TYPE)
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Model loading failed: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✓ STT Model Test PASSED - Ready for production")
print("="*70)
