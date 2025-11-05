# Feature: System Resource Monitoring

## Overview

All LLM test clients now include automatic system resource monitoring, displaying VRAM, RAM, CPU, and GPU metrics during test execution.

## What's New

### Monitored Metrics

#### GPU (VRAM)
- Memory usage (MB and %)
- GPU utilization (%)
- Temperature (°C)
- Multi-GPU support

#### RAM
- Used vs total memory (GB)
- Memory percentage
- Cross-platform (Linux, macOS, Windows)

#### CPU
- Current utilization (%)
- Core count

### When Displayed

**test_client.py:**
- Initial resources before tests
- Compact view before load test
- Final resources after completion

**test_stream.py:**
- Initial and final resources

**load_test.py:**
- Before, during (compact), and after load test

**test_llm.sh:**
- Beginning and end of test suite

## Example Output

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
```

## Usage

### No Configuration Needed!

```bash
# Just run any test - resource monitoring is automatic
python3 test_client.py
python3 test_stream.py
python3 load_test.py
./test_llm.sh quick
```

### Standalone Resource Monitor

```bash
# View current system resources
python3 resource_monitor.py
```

## Implementation

### New File: `resource_monitor.py`

Provides:
- `ResourceMonitor` class
- GPU detection via nvidia-smi
- RAM/CPU monitoring (psutil or system commands)
- Pretty-print formatting

### Updated Files

1. **test_client.py** - Shows resources at start, before load test, and end
2. **test_stream.py** - Shows resources at start and end
3. **load_test.py** - Shows resources before, during, and after
4. **test_llm.sh** - Added `print_resources()` function
5. **requirements.txt** - Added psutil (optional)

## Dependencies

### Automatic (Built-in)
- nvidia-smi (for GPU, if available)
- System tools (sysctl, vm_stat, /proc/meminfo, etc.)

### Optional (Enhanced)
- psutil - Better cross-platform metrics (auto-installed)

## Benefits

### Performance Tracking
- Monitor VRAM during load tests
- Identify memory leaks
- Track GPU utilization
- Verify resource availability

### Capacity Planning
- See peak resource usage
- Determine optimal concurrent requests
- Identify bottlenecks

### Debugging
- Confirm GPU is being used
- Check for OOM conditions
- Monitor thermal throttling

## Files Added

1. `resource_monitor.py` - Core monitoring module
2. `RESOURCE_MONITORING.md` - Comprehensive documentation
3. `FEATURE_RESOURCE_MONITORING.md` - This summary

## Files Modified

1. `test_client.py` - Added resource displays
2. `test_stream.py` - Added resource displays
3. `load_test.py` - Added resource displays
4. `test_llm.sh` - Added print_resources() function
5. `requirements.txt` - Added psutil
6. `README.md` - Updated feature list

## Version

**Version**: 1.2.0  
**Date**: November 5, 2025  
**Status**: ✅ Complete and Tested
