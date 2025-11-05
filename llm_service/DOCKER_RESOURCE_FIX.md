# Docker Container Resource Monitoring Fix

## Problem
When running inside a Docker container, the resource monitor was showing **host system** resources instead of **container allocated** resources:
- RAM: 1007 GB instead of actual container limit (~117 GB)
- CPU: 256 cores instead of actual container allocation

## Solution
Updated `resource_monitor.py` to:

1. **Detect Container Environment**
   - Checks for `/.dockerenv` file
   - Checks `/proc/1/cgroup` for Docker/LXC indicators

2. **Read Container Memory Limits from cgroups**
   - **cgroup v2**: `/sys/fs/cgroup/memory.max`, `/sys/fs/cgroup/memory.current`
   - **cgroup v1**: `/sys/fs/cgroup/memory/memory.limit_in_bytes`, `/sys/fs/cgroup/memory/memory.usage_in_bytes`
   - Falls back to host memory if cgroup limits not found

3. **Read Container CPU Limits from cgroups**
   - **cgroup v2**: `/sys/fs/cgroup/cpu.max`
   - **cgroup v1**: `/sys/fs/cgroup/cpu/cpu.cfs_quota_us` and `/sys/fs/cgroup/cpu/cpu.cfs_period_us`
   - Calculates effective CPU count from quota/period ratio
   - Falls back to host CPU count if cgroup limits not found

## Testing
Run inside your Docker container:
```bash
cd /workspace/apps/voice-agent-server-setup/llm_service
python3 resource_monitor.py
```

Expected output should now show:
- ✅ Correct container RAM allocation (not 1007 GB)
- ✅ Correct container CPU cores (not 256 cores)
- ✅ "Running in container: True"

## Usage
No changes needed to existing scripts. The fix is automatic:
```bash
./run_test.sh load    # Now shows correct container resources
./run_test.sh quick   # Now shows correct container resources
./run_test.sh stream  # Now shows correct container resources
```

## Technical Details
The monitor now prioritizes container cgroup limits when detected, falling back to:
1. Container cgroups (when `in_container == True`)
2. psutil library
3. System-specific commands (sysctl, vm_stat, /proc/meminfo)
4. Fallback defaults

This ensures accurate resource reporting in containers while maintaining compatibility with bare metal systems.

