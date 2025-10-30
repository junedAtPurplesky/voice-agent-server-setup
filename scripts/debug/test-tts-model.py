#!/usr/bin/env python3
"""
Test TTS Model Loading (Debug)
Loads CosyVoice model without starting the service
"""

import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(f"{BASE_DIR}/config/tts.env")

print("="*70)
print("TTS Model Loading Test (CosyVoice2)")
print("="*70)

MODEL_NAME = os.getenv("TTS_MODEL_NAME", "iic/CosyVoice2-0.5B")
DEVICE = os.getenv("TTS_DEVICE", "cuda")

print(f"\nModel: {MODEL_NAME}")
print(f"Device: {DEVICE}")

print("\n[1/3] Importing CosyVoice...")
start = time.time()
try:
    sys.path.insert(0, f"{BASE_DIR}/cosyvoice")
    from cosyvoice.cosyvoice import CosyVoice
    print(f"✓ Import successful ({time.time() - start:.2f}s)")
except Exception as e:
    print(f"✗ Import failed: {e}")
    print("  Make sure CosyVoice is installed in the base directory")
    sys.exit(1)

print("\n[2/3] Loading model (this may take 20-30 seconds)...")
start = time.time()
try:
    model = CosyVoice(MODEL_NAME, device=DEVICE)
    load_time = time.time() - start
    print(f"✓ Model loaded successfully ({load_time:.2f}s)")
except Exception as e:
    print(f"✗ Model loading failed: {e}")
    sys.exit(1)

print("\n[3/3] Testing synthesis...")
test_text = "नमस्ते, यह एक परीक्षण है।"
print(f"  Text: {test_text}")

start = time.time()
try:
    audio_data = model.inference_sft(test_text, speaker="default", language="hi")
    synthesis_time = time.time() - start
    
    import numpy as np
    if isinstance(audio_data, dict):
        audio_array = audio_data['tts_speech']
    else:
        audio_array = audio_data
    
    audio_duration = len(audio_array) / 22050
    
    print(f"✓ Synthesis complete ({synthesis_time:.2f}s)")
    print(f"  Audio duration: {audio_duration:.2f}s")
    print(f"  Real-time factor: {audio_duration / synthesis_time:.2f}x")
    
except Exception as e:
    print(f"✗ Synthesis failed: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✓ TTS Model Test Passed!")
print("="*70)
