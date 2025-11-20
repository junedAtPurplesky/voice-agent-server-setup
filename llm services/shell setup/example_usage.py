#!/usr/bin/env python3
"""
Example: Using LLM Test Clients as a Library

This script demonstrates how to use the test clients programmatically
for custom testing scenarios.
"""

import asyncio
import sys
import subprocess
from pathlib import Path


# Auto-setup virtual environment if needed
def ensure_venv():
    """Ensure we're running in a virtual environment with dependencies"""
    script_dir = Path(__file__).parent
    venv_dir = script_dir / ".test_venv"
    
    # If we're already in a venv or dependencies are available, continue
    try:
        import httpx
        # Dependencies available, continue
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

# Now import the test clients (after ensuring dependencies)
from test_client import LLMTestClient
from test_stream import StreamingTestClient
from load_test import LoadTester, LoadTestConfig


async def example_basic_testing():
    """Example 1: Basic health check and simple test"""
    print("\n" + "="*60)
    print("Example 1: Basic Testing")
    print("="*60)
    
    client = LLMTestClient(base_url="http://127.0.0.1:8000")
    
    # Check if service is available
    if not await client.test_health():
        print("❌ Service not available")
        return False
    
    # Run a simple completion test
    result = await client.test_completion(
        prompt="What is the capital of France?",
        max_tokens=30
    )
    
    if result.success:
        print(f"✅ Completion test successful!")
        print(f"   Response time: {result.response_time:.3f}s")
        print(f"   Tokens: {result.tokens_generated}")
    else:
        print(f"❌ Test failed: {result.error}")
        return False
    
    return True


async def example_streaming_test():
    """Example 2: Test streaming with detailed metrics"""
    print("\n" + "="*60)
    print("Example 2: Streaming Test")
    print("="*60)
    
    client = StreamingTestClient(base_url="http://127.0.0.1:8000")
    
    # Test streaming completion
    metrics = await client.test_stream_completion(
        prompt="Write a haiku about programming",
        max_tokens=100,
        verbose=True  # Show output in real-time
    )
    
    # Display metrics
    client.print_metrics(metrics, "Haiku Generation")
    
    return metrics.success


async def example_concurrent_testing():
    """Example 3: Test concurrent requests"""
    print("\n" + "="*60)
    print("Example 3: Concurrent Testing")
    print("="*60)
    
    client = LLMTestClient()
    
    # Test 10 concurrent requests
    results = await client.test_concurrent_requests(
        num_requests=10,
        prompt="Test concurrent request"
    )
    
    # Analyze results
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    print(f"\nResults:")
    print(f"  Successful: {successful}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")
    
    if successful > 0:
        avg_time = sum(r.response_time for r in results if r.success) / successful
        print(f"  Avg Response Time: {avg_time:.3f}s")
    
    return failed == 0


async def example_custom_prompts():
    """Example 4: Test with multiple custom prompts"""
    print("\n" + "="*60)
    print("Example 4: Multiple Custom Prompts")
    print("="*60)
    
    client = LLMTestClient()
    
    # Define test prompts
    test_cases = [
        ("Math", "What is 15 * 23?", 20),
        ("Science", "What causes rain?", 50),
        ("History", "Who was the first person on the moon?", 30),
        ("Programming", "What is a variable in programming?", 50),
    ]
    
    results = []
    for name, prompt, max_tokens in test_cases:
        result = await client.test_completion(prompt=prompt, max_tokens=max_tokens)
        results.append((name, result))
        
        status = "✅" if result.success else "❌"
        time_str = f"{result.response_time:.3f}s" if result.success else "N/A"
        print(f"{status} {name:15} - {time_str}")
    
    # Summary
    successful = sum(1 for _, r in results if r.success)
    print(f"\nTotal: {successful}/{len(results)} successful")
    
    return successful == len(results)


async def example_performance_test():
    """Example 5: Run a performance/load test"""
    print("\n" + "="*60)
    print("Example 5: Performance Testing")
    print("="*60)
    
    # Configure load test
    config = LoadTestConfig(
        total_requests=20,
        concurrent_users=5,
        ramp_up_time=0.0,
        prompt="Performance test prompt",
        max_tokens=50,
        use_streaming=False
    )
    
    # Run load test
    tester = LoadTester(base_url="http://127.0.0.1:8000")
    metrics = await tester.run_load_test(config)
    
    # Print results
    tester.print_report(metrics)
    
    return metrics.get('success_rate', 0) > 90


async def example_streaming_multiple():
    """Example 6: Multiple streaming tests"""
    print("\n" + "="*60)
    print("Example 6: Multiple Streaming Tests")
    print("="*60)
    
    client = StreamingTestClient()
    
    prompts = [
        "Write a haiku about AI",
        "Explain recursion simply",
        "Tell a short joke",
    ]
    
    results = await client.run_multiple_streams(
        prompts=prompts,
        max_tokens=100,
        verbose=False
    )
    
    # Print summary
    client.print_summary(results)
    
    successful = sum(1 for r in results if r.success)
    return successful == len(results)


async def example_error_handling():
    """Example 7: Handling errors gracefully"""
    print("\n" + "="*60)
    print("Example 7: Error Handling")
    print("="*60)
    
    # Try to connect to non-existent service
    client = LLMTestClient(base_url="http://127.0.0.1:9999", timeout=5.0)
    
    print("Testing connection to non-existent service...")
    result = await client.test_completion(prompt="Test", max_tokens=10)
    
    if not result.success:
        print(f"✅ Error handled gracefully: {result.error}")
        return True
    else:
        print("❌ Expected error but got success")
        return False


async def example_chat_completion():
    """Example 8: Chat completion endpoint"""
    print("\n" + "="*60)
    print("Example 8: Chat Completion")
    print("="*60)
    
    client = LLMTestClient()
    
    # Test chat completion
    result = await client.test_chat_completion(
        message="Explain quantum computing in one sentence.",
        max_tokens=50
    )
    
    if result.success:
        print(f"✅ Chat completion successful!")
        print(f"   Response time: {result.response_time:.3f}s")
        print(f"   Tokens: {result.tokens_generated}")
    else:
        print(f"❌ Chat completion failed: {result.error}")
    
    return result.success


async def run_all_examples():
    """Run all examples"""
    print("\n" + "="*70)
    print("🧪 LLM TEST CLIENT USAGE EXAMPLES")
    print("="*70)
    
    examples = [
        ("Basic Testing", example_basic_testing),
        ("Streaming Test", example_streaming_test),
        ("Concurrent Testing", example_concurrent_testing),
        ("Custom Prompts", example_custom_prompts),
        ("Performance Test", example_performance_test),
        ("Multiple Streams", example_streaming_multiple),
        ("Error Handling", example_error_handling),
        ("Chat Completion", example_chat_completion),
    ]
    
    results = []
    
    for name, example_func in examples:
        try:
            success = await example_func()
            results.append((name, success))
            
            # Small delay between examples
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"\n❌ Example failed with exception: {e}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("📊 EXAMPLES SUMMARY")
    print("="*70)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    successful = sum(1 for _, s in results if s)
    print(f"\nTotal: {successful}/{len(results)} examples successful")
    print("="*70 + "\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Examples of using LLM test clients programmatically"
    )
    parser.add_argument(
        "--example",
        type=int,
        choices=range(1, 9),
        help="Run specific example (1-8), or omit to run all"
    )
    
    args = parser.parse_args()
    
    try:
        if args.example:
            # Run specific example
            examples = [
                example_basic_testing,
                example_streaming_test,
                example_concurrent_testing,
                example_custom_prompts,
                example_performance_test,
                example_streaming_multiple,
                example_error_handling,
                example_chat_completion,
            ]
            
            print(f"\nRunning Example {args.example}...")
            asyncio.run(examples[args.example - 1]())
        else:
            # Run all examples
            asyncio.run(run_all_examples())
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

