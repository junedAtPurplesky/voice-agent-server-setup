# Resource Monitoring

All test clients now display system resource usage including VRAM, RAM, CPU, and GPU metrics.

## Features

### Monitored Resources

#### 🎮 GPU (VRAM)
- **VRAM Usage**: Memory used vs total (MB and %)
- **GPU Utilization**: Percentage of GPU being used
- **Temperature**: GPU temperature in Celsius
- **Multiple GPUs**: Shows all available NVIDIA GPUs

#### 💾 RAM (System Memory)
- **Memory Usage**: Used vs total (GB and %)
- **Works on**: Linux, macOS, Windows (with psutil)

#### ⚙️ CPU
- **CPU Usage**: Current CPU utilization percentage
- **Core Count**: Number of CPU cores available

## Usage

### Python Test Clients

Resource monitoring is **automatic** - no additional flags needed!

```bash
# Just run any test client
python3 test_client.py
python3 test_stream.py
python3 load_test.py
```

**Example Output:**
```
📊 Initial System Resources:
  ============================================================
  📊 SYSTEM RESOURCES
  ============================================================
  💾 RAM: 12.45 GB / 32.00 GB (38.9%)
  ⚙️  CPU: 15.3% (16 cores)
  🎮 GPU:
     GPU 0 (NVIDIA GeForce RTX 3090):
       VRAM: 4532 MB / 24576 MB (18.4%)
       Utilization: 45%, 62°C
  ============================================================

🏥 Testing Service Health...
✅ Service is healthy (Response time: 0.123s)
...

📊 Resources before load test:
💾 RAM: 39% | ⚙️  CPU: 18% | GPU: 19% VRAM, 47% Util

[Load test runs...]

📊 Final System Resources:
  ============================================================
  📊 SYSTEM RESOURCES
  ============================================================
  💾 RAM: 15.23 GB / 32.00 GB (47.6%)
  ⚙️  CPU: 45.8% (16 cores)
  🎮 GPU:
     GPU 0 (NVIDIA GeForce RTX 3090):
       VRAM: 18234 MB / 24576 MB (74.2%)
       Utilization: 92%, 75°C
  ============================================================
```

### Shell Script

```bash
# Resource monitoring included in all tests
./test_llm.sh quick
./test_llm.sh completion
./test_llm.sh health
```

**Shows resources at:**
- Start of test suite
- End of test suite

## Requirements

### Automatic (Included)
- `nvidia-smi` - For GPU monitoring (if you have NVIDIA GPU)
- System tools (built-in):
  - Linux: `/proc/meminfo`, `nproc`, `mpstat`
  - macOS: `sysctl`, `vm_stat`, `top`
  - Windows: via `psutil`

### Optional (Better Metrics)
```bash
# For enhanced monitoring (auto-installed)
pip install psutil
```

**With psutil**, you get:
- More accurate RAM measurements
- Better CPU utilization metrics
- Cross-platform consistency

**Without psutil**, you still get:
- GPU monitoring (via nvidia-smi)
- Basic RAM and CPU info (via system commands)

## Implementation Details

### Python Clients

#### Auto-Detection
```python
try:
    from resource_monitor import ResourceMonitor
    HAS_RESOURCE_MONITOR = True
except ImportError:
    HAS_RESOURCE_MONITOR = False

# Use if available
if HAS_RESOURCE_MONITOR:
    monitor = ResourceMonitor()
    resources = monitor.get_snapshot()
    monitor.print_resources(resources)
```

#### ResourceMonitor Class
```python
# Get current snapshot
resources = monitor.get_snapshot()

# Full display
monitor.print_resources(resources)

# Compact one-line display
monitor.print_compact(resources)
```

#### Data Structure
```python
@dataclass
class SystemResources:
    timestamp: float
    ram_used: float       # GB
    ram_total: float      # GB
    ram_percent: float
    cpu_percent: float
    cpu_count: int
    gpus: List[GPUInfo]   # List of GPU info

@dataclass
class GPUInfo:
    index: int
    name: str
    memory_used: float    # MB
    memory_total: float   # MB
    memory_percent: float
    utilization: float    # Percentage
    temperature: float    # Celsius (optional)
```

### Shell Script

Uses native commands:
```bash
# GPU info
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu

# RAM info (Linux)
cat /proc/meminfo | grep -E "MemTotal|MemAvailable"

# RAM info (macOS)
sysctl -n hw.memsize
vm_stat

# CPU info
top -l 1 | grep "CPU usage"  # macOS
mpstat 1 1                    # Linux
```

## Viewing Resources Standalone

### Python Module
```bash
# Run resource monitor directly
python3 resource_monitor.py
```

**Output:**
```
System Resource Monitor Test

nvidia-smi available: True
psutil available: True

============================================================
📊 SYSTEM RESOURCES
============================================================
💾 RAM: 12.45 GB / 32.00 GB (38.9%)
⚙️  CPU: 15.3% (16 cores)
🎮 GPU:
   GPU 0 (NVIDIA GeForce RTX 3090):
     VRAM: 4532 MB / 24576 MB (18.4%)
     Utilization: 45%, 62°C
============================================================

Compact format:
💾 RAM: 39% | ⚙️  CPU: 15% | GPU: 18% VRAM, 45% Util
```

### In Your Own Code
```python
from resource_monitor import ResourceMonitor

monitor = ResourceMonitor()

# Get snapshot
resources = monitor.get_snapshot()

# Access data
print(f"RAM: {resources.ram_percent:.1f}%")
print(f"CPU: {resources.cpu_percent:.1f}%")

for gpu in resources.gpus:
    print(f"GPU {gpu.index}: {gpu.memory_percent:.1f}% VRAM")
    print(f"  Utilization: {gpu.utilization:.0f}%")
    print(f"  Temperature: {gpu.temperature}°C")
```

## Display Formats

### Full Format
Detailed breakdown with all metrics:
```
============================================================
📊 SYSTEM RESOURCES
============================================================
💾 RAM: 12.45 GB / 32.00 GB (38.9%)
⚙️  CPU: 15.3% (16 cores)
🎮 GPU:
   GPU 0 (NVIDIA GeForce RTX 3090):
     VRAM: 4532 MB / 24576 MB (18.4%)
     Utilization: 45%, 62°C
============================================================
```

### Compact Format
One-line summary:
```
💾 RAM: 39% | ⚙️  CPU: 15% | GPU: 18% VRAM, 45% Util
```

## When Resources Are Displayed

### test_client.py (Comprehensive Tests)
- **Initial**: Before any tests
- **Before Load Test**: Just before performance test
- **Final**: After all tests complete

### test_stream.py (Streaming Tests)
- **Initial**: Before streaming tests
- **Final**: After all tests complete

### load_test.py (Load Testing)
- **Initial**: Before load test starts
- **During**: After each major batch (compact format)
- **Final**: After load test completes

### test_llm.sh (Shell Script)
- **Initial**: At start of test suite
- **Final**: After all tests complete

## Troubleshooting

### "GPU: Not available"
**Cause**: `nvidia-smi` not found

**Solutions:**
1. Install NVIDIA drivers
2. Ensure `nvidia-smi` is in PATH
3. If you don't have NVIDIA GPU, this is normal

### Missing psutil
**Effect**: Falls back to system commands

**Solution** (optional):
```bash
pip install psutil
# Or let auto-venv install it
python3 test_client.py  # Will install psutil automatically
```

### Inaccurate Metrics
**On macOS without psutil:**
- RAM metrics are approximate
- CPU usage may be 0%

**Solution**: Install psutil
```bash
pip install psutil
```

## Benefits

### Performance Monitoring
- Track VRAM usage during tests
- Identify memory leaks
- Monitor GPU utilization
- Check if system is under stress

### Capacity Planning
- See resource usage at different loads
- Determine optimal concurrent requests
- Identify bottlenecks (GPU, RAM, CPU)

### Debugging
- Verify GPU is being used
- Check if running out of memory
- Monitor temperature issues
- Track resource trends

## Examples

### Monitor GPU During Load Test
```bash
python3 load_test.py --requests 100 --concurrent 10
```

Watch VRAM increase as load increases.

### Compare Resource Usage
```bash
# Light load
python3 test_client.py --requests 10 --concurrent 2
# Note: VRAM usage

# Heavy load
python3 test_client.py --requests 100 --concurrent 20
# Note: VRAM usage (should be higher)
```

### Continuous Monitoring
```bash
# Run tests in loop and monitor resources
while true; do
    python3 test_client.py --requests 20
    sleep 60
done
```

## Advanced: Custom Monitoring

```python
from resource_monitor import ResourceMonitor
import asyncio

async def monitor_during_test():
    monitor = ResourceMonitor()
    
    # Monitor every second
    for i in range(10):
        resources = monitor.get_snapshot()
        print(f"[{i}s] VRAM: {resources.gpus[0].memory_percent:.1f}%")
        await asyncio.sleep(1)

asyncio.run(monitor_during_test())
```

## Summary

✅ **Automatic** - No configuration needed  
✅ **Comprehensive** - GPU, RAM, CPU metrics  
✅ **Cross-platform** - Linux, macOS, Windows  
✅ **Optional psutil** - Works without it  
✅ **Real-time** - Shows current usage  
✅ **Integrated** - Built into all test clients  

Track your system resources effortlessly while testing! 📊

