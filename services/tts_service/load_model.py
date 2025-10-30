#!/usr/bin/env python3
"""Test TTS Model Loading"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

print("="*70)
print("TTS Model Loading Test - CosyVoice2")
print("="*70)

MODEL_NAME = "iic/CosyVoice2-0.5B"
DEVICE = "cuda"

print(f"\nConfiguration:")
print(f"  Model: {MODEL_NAME}")
print(f"  Device: {DEVICE}")

print("\n[1/2] Importing CosyVoice...")
try:
    sys.path.insert(0, f"{BASE_DIR}/cosyvoice")
    from cosyvoice.cosyvoice import CosyVoice
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

print("\n[2/2] Loading model (may take 20-30 seconds)...")
try:
    model = CosyVoice(MODEL_NAME, device=DEVICE)
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Model loading failed: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✓ TTS Model Test PASSED - Ready for production")
print("="*70)
