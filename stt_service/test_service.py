#!/usr/bin/env python3
"""Test script for STT Service"""

import sys
import requests
import json
import time

API_KEY = "stt_secret_key_production_123456"
BASE_URL = "http://localhost:8000/stt"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_service_info():
    """Test service info endpoint"""
    print("🔍 Testing service info...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service: {data['service']} v{data['version']}")
            return True
        else:
            print(f"❌ Service info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Service info error: {e}")
        return False

def test_config():
    """Test configuration endpoint"""
    print("🔍 Testing configuration...")
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/config", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Config retrieved: {data['config']['model']['name']}")
            return True
        else:
            print(f"❌ Config failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("STT Service Test Suite")
    print("=" * 50)
    
    tests = [
        test_health,
        test_service_info,
        test_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
        print()
        time.sleep(1)
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

