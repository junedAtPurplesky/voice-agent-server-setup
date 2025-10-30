#!/usr/bin/env python3
"""
Test STT Model Loading (Debug)
Loads Faster Whisper model without starting the service
"""

import os
import sys
import time

# Add base directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

# Load config
from dotenv import load_dotenv
load_dotenv(f"{BASE_DIR}/config/stt.env")

print("="*70)
print("STT Model Loading Test (Faster Whisper)")
print("="*70)

MODEL_NAME = os.getenv("STT_MODEL_NAME", "large-v3-turbo")
DEVICE = os.getenv("STT_DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE", "int8")

print(f"\nModel: {MODEL_NAME}")
print(f"Device: {DEVICE}")
print(f"Compute Type: {COMPUTE_TYPE}")

print("\n[1/3] Importing faster_whisper...")
start = time.time()
from faster_whisper import WhisperModel
print(f"✓ Import successful ({time.time() - start:.2f}s)")

print("\n[2/3] Loading model (this may take 20-30 seconds)...")
start = time.time()
try:
    model = WhisperModel(
        MODEL_NAME,
        device=DEVICE,
        compute_type=COMPUTE_TYPE
    )
    load_time = time.time() - start
    print(f"✓ Model loaded successfully ({load_time:.2f}s)")
except Exception as e:
    print(f"✗ Model loading failed: {e}")
    sys.exit(1)

print("\n[3/3] Testing transcription...")
# Create test audio
import numpy as np
from scipy.io import wavfile

duration = 3
sample_rate = 16000
t = np.linspace(0, duration, int(sample_rate * duration))
audio = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)
test_file = "/tmp/test_stt_debug.wav"
wavfile.write(test_file, sample_rate, audio)

start = time.time()
segments, info = model.transcribe(test_file, language="hi")
transcribe_time = time.time() - start

text = ""
for segment in segments:
    text += segment.text

print(f"✓ Transcription complete ({transcribe_time:.2f}s)")
print(f"  Audio duration: {info.duration:.2f}s")
print(f"  Real-time factor: {info.duration / transcribe_time:.2f}x")
print(f"  Text: {text if text else '(no speech detected)'}")

os.remove(test_file)

print("\n" + "="*70)
print("✓ STT Model Test Passed!")
print("="*70)
