#!/usr/bin/env python3
"""
LLM Service Load Testing
High-volume testing to measure service capacity and performance under load
"""

import asyncio
import json
import time
import argparse
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import httpx
from statistics import mean, median, stdev, quantiles


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
class LoadTestResult:
    """Result from a single request in load test"""
    request_id: int
    success: bool
    response_time: float
    tokens: int = 0
    status_code: int = 0
    error: Optional[str] = None
    timestamp: float = 0.0


@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    total_requests: int = 100
    concurrent_users: int = 10
    ramp_up_time: float = 0.0  # Seconds to gradually increase load
    prompt: str = "Tell me about artificial intelligence."
    max_tokens: int = 100
    temperature: float = 0.7
    use_streaming: bool = False


class LoadTester:
    """Load testing client for LLM service"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 120.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results: List[LoadTestResult] = []
        self.start_time: float = 0.0
        self.end_time: float = 0.0
    
    async def send_request(self, request_id: int, prompt: str,
                          max_tokens: int, temperature: float,
                          use_streaming: bool = False) -> LoadTestResult:
        """Send a single request and measure performance"""
        result = LoadTestResult(
            request_id=request_id,
            success=False,
            response_time=0.0,
            timestamp=time.time()
        )
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": "default",
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": use_streaming
                }
                
                start = time.time()
                
                if use_streaming:
                    # Handle streaming response
                    chunks = 0
                    async with client.stream(
                        'POST',
                        f"{self.base_url}/v1/completions",
                        json=payload
                    ) as response:
                        result.status_code = response.status_code
                        
                        if response.status_code == 200:
                            async for line in response.aiter_lines():
                                if line.startswith('data: '):
                                    data = line[6:].strip()
                                    if data == '[DONE]':
                                        break
                                    try:
                                        json.loads(data)
                                        chunks += 1
                                    except json.JSONDecodeError:
                                        pass
                            result.tokens = chunks
                            result.success = True
                        else:
                            result.error = f"HTTP {response.status_code}"
                else:
                    # Handle non-streaming response
                    response = await client.post(
                        f"{self.base_url}/v1/completions",
                        json=payload
                    )
                    result.status_code = response.status_code
                    
                    if response.status_code == 200:
                        data = response.json()
                        result.tokens = len(data['choices'][0]['text'].split())
                        result.success = True
                    else:
                        result.error = f"HTTP {response.status_code}"
                
                result.response_time = time.time() - start
                
        except asyncio.TimeoutError:
            result.error = "Timeout"
        except Exception as e:
            result.error = str(e)
        
        return result
    
    async def run_concurrent_batch(self, start_id: int, batch_size: int,
                                   config: LoadTestConfig) -> List[LoadTestResult]:
        """Run a batch of concurrent requests"""
        tasks = []
        for i in range(batch_size):
            task = self.send_request(
                request_id=start_id + i,
                prompt=f"{config.prompt} (Request #{start_id + i})",
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                use_streaming=config.use_streaming
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def run_load_test(self, config: LoadTestConfig) -> Dict:
        """Execute full load test with given configuration"""
        print(f"\n{'='*70}")
        print(f"🚀 STARTING LOAD TEST")
        print(f"{'='*70}")
        print(f"Total Requests:       {config.total_requests}")
        print(f"Concurrent Users:     {config.concurrent_users}")
        print(f"Ramp-up Time:         {config.ramp_up_time}s")
        print(f"Max Tokens:           {config.max_tokens}")
        print(f"Streaming:            {config.use_streaming}")
        print(f"{'='*70}\n")
        
        self.results = []
        self.start_time = time.time()
        
        # Calculate batches
        num_batches = (config.total_requests + config.concurrent_users - 1) // config.concurrent_users
        ramp_delay = config.ramp_up_time / num_batches if num_batches > 1 else 0
        
        request_id = 0
        
        for batch_num in range(num_batches):
            batch_size = min(config.concurrent_users, 
                           config.total_requests - request_id)
            
            print(f"🔄 Batch {batch_num + 1}/{num_batches}: "
                  f"Sending {batch_size} requests...")
            
            batch_results = await self.run_concurrent_batch(
                start_id=request_id,
                batch_size=batch_size,
                config=config
            )
            
            self.results.extend(batch_results)
            request_id += batch_size
            
            # Progress update
            completed = len(self.results)
            successful = sum(1 for r in batch_results if r.success)
            print(f"   ✓ Completed {completed}/{config.total_requests} "
                  f"({successful}/{batch_size} successful)")
            
            # Ramp-up delay
            if batch_num < num_batches - 1 and ramp_delay > 0:
                await asyncio.sleep(ramp_delay)
        
        self.end_time = time.time()
        
        return self.analyze_results()
    
    def analyze_results(self) -> Dict:
        """Analyze load test results and generate metrics"""
        total_time = self.end_time - self.start_time
        
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        if not successful:
            return {
                "error": "All requests failed",
                "total_requests": len(self.results),
                "successful": 0,
                "failed": len(failed)
            }
        
        response_times = [r.response_time for r in successful]
        tokens = [r.tokens for r in successful if r.tokens > 0]
        
        # Calculate percentiles
        try:
            percentiles = quantiles(response_times, n=100)
            p50 = percentiles[49]  # 50th percentile (median)
            p95 = percentiles[94]  # 95th percentile
            p99 = percentiles[98]  # 99th percentile
        except:
            p50 = median(response_times)
            p95 = max(response_times)
            p99 = max(response_times)
        
        # Error breakdown
        error_types = {}
        for r in failed:
            error_types[r.error or "Unknown"] = error_types.get(r.error or "Unknown", 0) + 1
        
        # Status code breakdown
        status_codes = {}
        for r in self.results:
            code = r.status_code or 0
            status_codes[code] = status_codes.get(code, 0) + 1
        
        metrics = {
            "total_requests": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.results) * 100,
            "total_time": total_time,
            "requests_per_second": len(successful) / total_time,
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": mean(response_times),
                "median": median(response_times),
                "stdev": stdev(response_times) if len(response_times) > 1 else 0,
                "p50": p50,
                "p95": p95,
                "p99": p99
            },
            "tokens": {
                "total": sum(tokens),
                "mean": mean(tokens) if tokens else 0,
                "tokens_per_second": sum(tokens) / total_time if tokens else 0
            },
            "errors": error_types,
            "status_codes": status_codes
        }
        
        return metrics
    
    def print_report(self, metrics: Dict):
        """Print comprehensive load test report"""
        print(f"\n{'='*70}")
        print("📊 LOAD TEST REPORT")
        print(f"{'='*70}\n")
        
        if "error" in metrics:
            print(f"❌ Test Failed: {metrics['error']}")
            return
        
        # Summary
        print("📈 SUMMARY")
        print(f"{'─'*70}")
        print(f"Total Requests:        {metrics['total_requests']}")
        print(f"Successful:            {metrics['successful']}")
        print(f"Failed:                {metrics['failed']}")
        print(f"Success Rate:          {metrics['success_rate']:.2f}%")
        print(f"Total Time:            {metrics['total_time']:.2f}s")
        print(f"Throughput:            {metrics['requests_per_second']:.2f} req/s")
        
        # Response Times
        print(f"\n⏱️  RESPONSE TIMES (seconds)")
        print(f"{'─'*70}")
        rt = metrics['response_times']
        print(f"Min:                   {rt['min']:.3f}s")
        print(f"Max:                   {rt['max']:.3f}s")
        print(f"Mean:                  {rt['mean']:.3f}s")
        print(f"Median (P50):          {rt['median']:.3f}s")
        print(f"P95:                   {rt['p95']:.3f}s")
        print(f"P99:                   {rt['p99']:.3f}s")
        print(f"Std Dev:               {rt['stdev']:.3f}s")
        
        # Token Stats
        if metrics['tokens']['total'] > 0:
            print(f"\n🎯 TOKEN STATISTICS")
            print(f"{'─'*70}")
            t = metrics['tokens']
            print(f"Total Tokens:          {t['total']}")
            print(f"Avg per Request:       {t['mean']:.1f}")
            print(f"Throughput:            {t['tokens_per_second']:.2f} tokens/s")
        
        # Status Codes
        if metrics['status_codes']:
            print(f"\n📡 HTTP STATUS CODES")
            print(f"{'─'*70}")
            for code, count in sorted(metrics['status_codes'].items()):
                print(f"{code}:                      {count} requests")
        
        # Errors
        if metrics['errors']:
            print(f"\n❌ ERRORS")
            print(f"{'─'*70}")
            for error, count in sorted(metrics['errors'].items(), 
                                      key=lambda x: x[1], reverse=True):
                print(f"{error[:50]:<50} {count}")
        
        print(f"\n{'='*70}\n")


async def main():
    parser = argparse.ArgumentParser(
        description="Load test LLM service"
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="Base URL of LLM service"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Total number of requests (default: 100)"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Concurrent requests (default: 10)"
    )
    parser.add_argument(
        "--ramp-up",
        type=float,
        default=0.0,
        help="Ramp-up time in seconds (default: 0)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=100,
        help="Maximum tokens to generate (default: 100)"
    )
    parser.add_argument(
        "--prompt",
        default="Explain artificial intelligence.",
        help="Prompt to use for testing"
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Use streaming mode"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Request timeout in seconds (default: 120)"
    )
    
    args = parser.parse_args()
    
    config = LoadTestConfig(
        total_requests=args.requests,
        concurrent_users=args.concurrent,
        ramp_up_time=args.ramp_up,
        prompt=args.prompt,
        max_tokens=args.max_tokens,
        use_streaming=args.stream
    )
    
    tester = LoadTester(base_url=args.url, timeout=args.timeout)
    
    try:
        metrics = await tester.run_load_test(config)
        tester.print_report(metrics)
    except KeyboardInterrupt:
        print("\n\n⚠️  Load test interrupted by user")
        if tester.results:
            print("Analyzing partial results...")
            metrics = tester.analyze_results()
            tester.print_report(metrics)
    except Exception as e:
        print(f"\n❌ Load test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

