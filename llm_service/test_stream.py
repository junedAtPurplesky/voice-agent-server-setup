#!/usr/bin/env python3
"""
LLM Service Streaming Test Client
Focused testing of streaming capabilities with detailed metrics
"""

import asyncio
import json
import time
import argparse
import sys
import subprocess
from pathlib import Path
from typing import List, Optional
import httpx
from dataclasses import dataclass, field


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
class StreamMetrics:
    """Metrics for a streaming session"""
    total_time: float = 0.0
    time_to_first_token: float = 0.0
    chunks_received: int = 0
    total_text_length: int = 0
    chunk_times: List[float] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None
    
    @property
    def avg_chunk_time(self) -> float:
        """Average time between chunks"""
        return sum(self.chunk_times) / len(self.chunk_times) if self.chunk_times else 0.0
    
    @property
    def tokens_per_second(self) -> float:
        """Estimated throughput"""
        return self.chunks_received / self.total_time if self.total_time > 0 else 0.0


class StreamingTestClient:
    """Test client focused on streaming capabilities"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 120.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    async def test_stream_completion(self, prompt: str, max_tokens: int = 200,
                                    temperature: float = 0.7,
                                    verbose: bool = False) -> StreamMetrics:
        """Test streaming completion with detailed metrics"""
        metrics = StreamMetrics()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": "default",
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True
                }
                
                start_time = time.time()
                last_chunk_time = start_time
                full_text = ""
                
                if verbose:
                    print(f"\n{'='*60}")
                    print(f"🎯 Prompt: {prompt[:50]}...")
                    print(f"{'='*60}\n")
                
                async with client.stream(
                    'POST',
                    f"{self.base_url}/v1/completions",
                    json=payload
                ) as response:
                    
                    if response.status_code != 200:
                        metrics.error = f"HTTP {response.status_code}"
                        return metrics
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        if line.startswith('data: '):
                            current_time = time.time()
                            chunk_time = current_time - last_chunk_time
                            
                            data = line[6:].strip()
                            
                            if data == '[DONE]':
                                break
                            
                            try:
                                chunk_data = json.loads(data)
                                
                                # Extract text from chunk
                                if 'choices' in chunk_data:
                                    choice = chunk_data['choices'][0]
                                    text = choice.get('text', '')
                                    
                                    if text:
                                        full_text += text
                                        metrics.chunks_received += 1
                                        
                                        # Record time to first token
                                        if metrics.chunks_received == 1:
                                            metrics.time_to_first_token = current_time - start_time
                                        
                                        # Record chunk timing
                                        if metrics.chunks_received > 1:
                                            metrics.chunk_times.append(chunk_time)
                                        
                                        if verbose:
                                            print(text, end='', flush=True)
                                
                                last_chunk_time = current_time
                                
                            except json.JSONDecodeError as e:
                                if verbose:
                                    print(f"\n⚠️  JSON decode error: {e}")
                                continue
                
                metrics.total_time = time.time() - start_time
                metrics.total_text_length = len(full_text)
                metrics.success = True
                
                if verbose:
                    print(f"\n\n{'='*60}")
                
        except Exception as e:
            metrics.error = str(e)
            metrics.success = False
        
        return metrics
    
    async def test_stream_chat(self, message: str, max_tokens: int = 200,
                              temperature: float = 0.7,
                              verbose: bool = False) -> StreamMetrics:
        """Test streaming chat completion"""
        metrics = StreamMetrics()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": "default",
                    "messages": [
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True
                }
                
                start_time = time.time()
                last_chunk_time = start_time
                full_text = ""
                
                if verbose:
                    print(f"\n{'='*60}")
                    print(f"💬 Message: {message[:50]}...")
                    print(f"{'='*60}\n")
                
                async with client.stream(
                    'POST',
                    f"{self.base_url}/v1/chat/completions",
                    json=payload
                ) as response:
                    
                    if response.status_code != 200:
                        metrics.error = f"HTTP {response.status_code}"
                        return metrics
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        if line.startswith('data: '):
                            current_time = time.time()
                            chunk_time = current_time - last_chunk_time
                            
                            data = line[6:].strip()
                            
                            if data == '[DONE]':
                                break
                            
                            try:
                                chunk_data = json.loads(data)
                                
                                if 'choices' in chunk_data:
                                    choice = chunk_data['choices'][0]
                                    delta = choice.get('delta', {})
                                    text = delta.get('content', '')
                                    
                                    if text:
                                        full_text += text
                                        metrics.chunks_received += 1
                                        
                                        if metrics.chunks_received == 1:
                                            metrics.time_to_first_token = current_time - start_time
                                        
                                        if metrics.chunks_received > 1:
                                            metrics.chunk_times.append(chunk_time)
                                        
                                        if verbose:
                                            print(text, end='', flush=True)
                                
                                last_chunk_time = current_time
                                
                            except json.JSONDecodeError:
                                continue
                
                metrics.total_time = time.time() - start_time
                metrics.total_text_length = len(full_text)
                metrics.success = True
                
                if verbose:
                    print(f"\n\n{'='*60}")
                
        except Exception as e:
            metrics.error = str(e)
            metrics.success = False
        
        return metrics
    
    def print_metrics(self, metrics: StreamMetrics, test_name: str = "Stream Test"):
        """Print detailed streaming metrics"""
        print(f"\n📊 {test_name} Results:")
        print(f"{'─'*60}")
        
        if metrics.success:
            print(f"✅ Status:                 Success")
            print(f"⏱️  Total Time:             {metrics.total_time:.3f}s")
            print(f"🚀 Time to First Token:    {metrics.time_to_first_token:.3f}s")
            print(f"📦 Chunks Received:        {metrics.chunks_received}")
            print(f"📝 Total Text Length:      {metrics.total_text_length} chars")
            print(f"⚡ Throughput:             {metrics.tokens_per_second:.2f} chunks/s")
            
            if metrics.chunk_times:
                print(f"⏲️  Avg Chunk Time:        {metrics.avg_chunk_time*1000:.1f}ms")
                print(f"⏲️  Min Chunk Time:        {min(metrics.chunk_times)*1000:.1f}ms")
                print(f"⏲️  Max Chunk Time:        {max(metrics.chunk_times)*1000:.1f}ms")
        else:
            print(f"❌ Status:                 Failed")
            print(f"🔴 Error:                  {metrics.error}")
        
        print(f"{'─'*60}")
    
    async def run_multiple_streams(self, prompts: List[str], 
                                  max_tokens: int = 200,
                                  verbose: bool = False) -> List[StreamMetrics]:
        """Test multiple streaming requests"""
        results = []
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n🔄 Testing stream {i}/{len(prompts)}...")
            metrics = await self.test_stream_completion(
                prompt=prompt,
                max_tokens=max_tokens,
                verbose=verbose
            )
            results.append(metrics)
            
            if not verbose:
                self.print_metrics(metrics, f"Stream {i}")
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        return results
    
    def print_summary(self, results: List[StreamMetrics]):
        """Print summary of multiple stream tests"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"\n{'='*60}")
        print("📈 STREAMING TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests:          {len(results)}")
        print(f"Successful:           {len(successful)}")
        print(f"Failed:               {len(failed)}")
        print(f"Success Rate:         {len(successful)/len(results)*100:.1f}%")
        
        if successful:
            avg_total_time = sum(r.total_time for r in successful) / len(successful)
            avg_first_token = sum(r.time_to_first_token for r in successful) / len(successful)
            avg_chunks = sum(r.chunks_received for r in successful) / len(successful)
            avg_throughput = sum(r.tokens_per_second for r in successful) / len(successful)
            
            print(f"\n⏱️  Averages:")
            print(f"  Total Time:         {avg_total_time:.3f}s")
            print(f"  Time to First:      {avg_first_token:.3f}s")
            print(f"  Chunks per Stream:  {avg_chunks:.1f}")
            print(f"  Throughput:         {avg_throughput:.2f} chunks/s")
        
        print(f"{'='*60}\n")


async def main():
    parser = argparse.ArgumentParser(
        description="Test LLM service streaming capabilities"
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="Base URL of LLM service"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=200,
        help="Maximum tokens to generate"
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=5,
        help="Number of streaming tests to run"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print streaming output in real-time"
    )
    parser.add_argument(
        "--custom-prompt",
        help="Use a custom prompt instead of test prompts"
    )
    
    args = parser.parse_args()
    
    client = StreamingTestClient(base_url=args.url)
    
    print("="*60)
    print("🌊 LLM STREAMING TEST CLIENT")
    print("="*60)
    
    if args.custom_prompt:
        # Single custom test
        metrics = await client.test_stream_completion(
            prompt=args.custom_prompt,
            max_tokens=args.max_tokens,
            verbose=True
        )
        client.print_metrics(metrics, "Custom Prompt")
    else:
        # Multiple test prompts
        test_prompts = [
            "Write a short poem about technology.",
            "Explain quantum computing in simple terms.",
            "Tell me a story about a robot learning to paint.",
            "What are the benefits of renewable energy?",
            "Describe the process of photosynthesis.",
        ]
        
        prompts = test_prompts[:args.num_tests]
        results = await client.run_multiple_streams(
            prompts=prompts,
            max_tokens=args.max_tokens,
            verbose=args.verbose
        )
        
        client.print_summary(results)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

