#!/usr/bin/env python3
"""
LLM Service Test Client
Tests direct VLLM service endpoints with comprehensive metrics
"""

import asyncio
import json
import time
import argparse
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import httpx
from dataclasses import dataclass
from statistics import mean, median, stdev


# Auto-setup virtual environment if needed
def ensure_venv():
    """Ensure we're running in a virtual environment with dependencies"""
    script_dir = Path(__file__).parent
    venv_dir = script_dir / ".test_venv"
    
    # If we're already in a venv or dependencies are available, continue
    try:
        import httpx
        return
    except ImportError:
        pass
    
    # If venv doesn't exist, create it
    if not venv_dir.exists():
        print("📦 Setting up test environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        
        print("⬆️  Installing dependencies...")
        pip_path = venv_dir / "bin" / "pip"
        subprocess.run([str(pip_path), "install", "-q", "--upgrade", "pip"], check=True)
        subprocess.run([str(pip_path), "install", "-q", "-r", str(script_dir / "requirements.txt")], check=True)
        
        print("✅ Test environment ready\n")
    
    # Re-run script in venv
    python_path = venv_dir / "bin" / "python3"
    subprocess.run([str(python_path), __file__] + sys.argv[1:], check=True)
    sys.exit(0)


# Ensure dependencies are available
ensure_venv()


@dataclass
class TestResult:
    """Store test result metrics"""
    success: bool
    response_time: float
    tokens_generated: int = 0
    error: Optional[str] = None
    status_code: Optional[int] = None


class LLMTestClient:
    """Comprehensive test client for LLM service"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 60.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results: List[TestResult] = []
        
    async def test_health(self) -> bool:
        """Test service health and availability"""
        print("\n🏥 Testing Service Health...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = time.time()
                response = await client.get(f"{self.base_url}/v1/models")
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    models = response.json()
                    print(f"✅ Service is healthy (Response time: {elapsed:.3f}s)")
                    print(f"📋 Available models: {json.dumps(models, indent=2)}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def test_completion(self, prompt: str = "Hello, how are you?", 
                             max_tokens: int = 50) -> TestResult:
        """Test basic completion endpoint"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": "default",
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False
                }
                
                start = time.time()
                response = await client.post(
                    f"{self.base_url}/v1/completions",
                    json=payload
                )
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    data = response.json()
                    tokens = len(data['choices'][0]['text'].split())
                    return TestResult(
                        success=True,
                        response_time=elapsed,
                        tokens_generated=tokens,
                        status_code=200
                    )
                else:
                    return TestResult(
                        success=False,
                        response_time=elapsed,
                        error=f"Status {response.status_code}",
                        status_code=response.status_code
                    )
        except Exception as e:
            return TestResult(
                success=False,
                response_time=0,
                error=str(e)
            )
    
    async def test_chat_completion(self, message: str = "What is AI?",
                                   max_tokens: int = 100) -> TestResult:
        """Test chat completion endpoint"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": "default",
                    "messages": [
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False
                }
                
                start = time.time()
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload
                )
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    data = response.json()
                    tokens = data['usage']['completion_tokens']
                    return TestResult(
                        success=True,
                        response_time=elapsed,
                        tokens_generated=tokens,
                        status_code=200
                    )
                else:
                    return TestResult(
                        success=False,
                        response_time=elapsed,
                        error=f"Status {response.status_code}",
                        status_code=response.status_code
                    )
        except Exception as e:
            return TestResult(
                success=False,
                response_time=0,
                error=str(e)
            )
    
    async def test_streaming(self, prompt: str = "Write a short story about AI.",
                            max_tokens: int = 200) -> TestResult:
        """Test streaming completion"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": "default",
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": True
                }
                
                start = time.time()
                chunks_received = 0
                first_token_time = None
                
                async with client.stream(
                    'POST',
                    f"{self.base_url}/v1/completions",
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        return TestResult(
                            success=False,
                            response_time=0,
                            error=f"Status {response.status_code}",
                            status_code=response.status_code
                        )
                    
                    async for line in response.aiter_lines():
                        if line.startswith('data: '):
                            if first_token_time is None:
                                first_token_time = time.time() - start
                            
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                json.loads(data)
                                chunks_received += 1
                            except json.JSONDecodeError:
                                pass
                
                elapsed = time.time() - start
                
                return TestResult(
                    success=True,
                    response_time=elapsed,
                    tokens_generated=chunks_received,
                    status_code=200
                )
        except Exception as e:
            return TestResult(
                success=False,
                response_time=0,
                error=str(e)
            )
    
    async def test_concurrent_requests(self, num_requests: int = 10,
                                      prompt: str = "Test prompt") -> List[TestResult]:
        """Test concurrent request handling"""
        print(f"\n🔄 Testing {num_requests} concurrent requests...")
        
        tasks = [
            self.test_completion(prompt=f"{prompt} #{i}", max_tokens=50)
            for i in range(num_requests)
        ]
        
        results = await asyncio.gather(*tasks)
        self.results.extend(results)
        return results
    
    async def run_performance_test(self, num_requests: int = 20,
                                   concurrent: int = 5) -> Dict:
        """Run comprehensive performance test"""
        print(f"\n🏃 Running Performance Test...")
        print(f"Total requests: {num_requests}")
        print(f"Concurrent: {concurrent}")
        
        all_results = []
        
        # Run in batches of concurrent requests
        for batch_start in range(0, num_requests, concurrent):
            batch_end = min(batch_start + concurrent, num_requests)
            batch_size = batch_end - batch_start
            
            print(f"  Batch {batch_start // concurrent + 1}: "
                  f"Requests {batch_start + 1}-{batch_end}...")
            
            batch_results = await self.test_concurrent_requests(
                num_requests=batch_size,
                prompt=f"Performance test batch {batch_start // concurrent + 1}"
            )
            all_results.extend(batch_results)
            
            # Small delay between batches
            if batch_end < num_requests:
                await asyncio.sleep(1)
        
        return self.calculate_metrics(all_results)
    
    def calculate_metrics(self, results: List[TestResult]) -> Dict:
        """Calculate performance metrics from results"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if not successful:
            return {
                "total_requests": len(results),
                "successful": 0,
                "failed": len(failed),
                "success_rate": 0.0,
                "error": "All requests failed"
            }
        
        response_times = [r.response_time for r in successful]
        tokens = [r.tokens_generated for r in successful if r.tokens_generated > 0]
        
        metrics = {
            "total_requests": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) * 100,
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": mean(response_times),
                "median": median(response_times),
                "stdev": stdev(response_times) if len(response_times) > 1 else 0
            },
            "tokens": {
                "total": sum(tokens),
                "mean": mean(tokens) if tokens else 0,
                "tokens_per_second": sum(tokens) / sum(response_times) if tokens else 0
            }
        }
        
        return metrics
    
    def print_metrics(self, metrics: Dict):
        """Pretty print metrics"""
        print("\n" + "="*60)
        print("📊 PERFORMANCE METRICS")
        print("="*60)
        print(f"\n📈 Request Statistics:")
        print(f"  Total Requests:    {metrics['total_requests']}")
        print(f"  Successful:        {metrics['successful']}")
        print(f"  Failed:            {metrics['failed']}")
        print(f"  Success Rate:      {metrics['success_rate']:.2f}%")
        
        if 'response_times' in metrics:
            print(f"\n⏱️  Response Times (seconds):")
            rt = metrics['response_times']
            print(f"  Min:               {rt['min']:.3f}s")
            print(f"  Max:               {rt['max']:.3f}s")
            print(f"  Mean:              {rt['mean']:.3f}s")
            print(f"  Median:            {rt['median']:.3f}s")
            print(f"  Std Dev:           {rt['stdev']:.3f}s")
        
        if 'tokens' in metrics and metrics['tokens']['total'] > 0:
            print(f"\n🎯 Token Statistics:")
            t = metrics['tokens']
            print(f"  Total Tokens:      {t['total']}")
            print(f"  Avg per Request:   {t['mean']:.1f}")
            print(f"  Throughput:        {t['tokens_per_second']:.2f} tokens/s")
        
        print("\n" + "="*60)


async def run_all_tests(base_url: str, num_requests: int, concurrent: int):
    """Run all test suites"""
    client = LLMTestClient(base_url=base_url)
    
    # Health check
    if not await client.test_health():
        print("\n❌ Service is not available. Exiting.")
        return
    
    print("\n" + "="*60)
    print("🧪 RUNNING LLM SERVICE TESTS")
    print("="*60)
    
    # Test basic completion
    print("\n1️⃣  Testing Basic Completion...")
    result = await client.test_completion(
        prompt="What is the capital of France?",
        max_tokens=50
    )
    if result.success:
        print(f"✅ Completion test passed ({result.response_time:.3f}s, "
              f"{result.tokens_generated} tokens)")
    else:
        print(f"❌ Completion test failed: {result.error}")
    
    # Test chat completion
    print("\n2️⃣  Testing Chat Completion...")
    result = await client.test_chat_completion(
        message="Explain machine learning in one sentence.",
        max_tokens=100
    )
    if result.success:
        print(f"✅ Chat completion test passed ({result.response_time:.3f}s, "
              f"{result.tokens_generated} tokens)")
    else:
        print(f"❌ Chat completion test failed: {result.error}")
    
    # Test streaming
    print("\n3️⃣  Testing Streaming...")
    result = await client.test_streaming(
        prompt="Write a haiku about technology.",
        max_tokens=100
    )
    if result.success:
        print(f"✅ Streaming test passed ({result.response_time:.3f}s, "
              f"{result.tokens_generated} chunks)")
    else:
        print(f"❌ Streaming test failed: {result.error}")
    
    # Performance test
    print("\n4️⃣  Running Performance Test...")
    metrics = await client.run_performance_test(
        num_requests=num_requests,
        concurrent=concurrent
    )
    client.print_metrics(metrics)


def main():
    parser = argparse.ArgumentParser(
        description="Test LLM service with comprehensive metrics"
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="Base URL of LLM service (default: http://127.0.0.1:8000)"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=20,
        help="Number of requests for performance test (default: 20)"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=5,
        help="Number of concurrent requests (default: 5)"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_all_tests(args.url, args.requests, args.concurrent))
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")


if __name__ == "__main__":
    main()

