#!/usr/bin/env python3
"""
System Resource Monitor
Tracks GPU, RAM, CPU, and other system resources
"""

import subprocess
import platform
import time
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class GPUInfo:
    """GPU information"""
    index: int
    name: str
    memory_used: float  # MB
    memory_total: float  # MB
    memory_percent: float
    utilization: float  # Percentage
    temperature: Optional[float] = None  # Celsius


@dataclass
class SystemResources:
    """System resource snapshot"""
    timestamp: float
    
    # RAM
    ram_used: float  # GB
    ram_total: float  # GB
    ram_percent: float
    
    # CPU
    cpu_percent: float
    cpu_count: int
    
    # GPU
    gpus: List[GPUInfo]
    
    # Disk
    disk_read_mb: Optional[float] = None
    disk_write_mb: Optional[float] = None


class ResourceMonitor:
    """Monitor system resources"""
    
    def __init__(self):
        self.has_nvidia_smi = self._check_nvidia_smi()
        self.has_psutil = self._check_psutil()
        self.in_container = self._check_container()
    
    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available"""
        try:
            subprocess.run(['nvidia-smi'], stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL, timeout=2)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False
    
    def _check_psutil(self) -> bool:
        """Check if psutil is available"""
        try:
            import psutil
            return True
        except ImportError:
            return False
    
    def _check_container(self) -> bool:
        """Check if running inside a container"""
        import os
        # Check for Docker
        if os.path.exists('/.dockerenv'):
            return True
        # Check for cgroup indicators
        try:
            with open('/proc/1/cgroup', 'r') as f:
                return 'docker' in f.read() or 'lxc' in f.read()
        except:
            pass
        return False
    
    def get_gpu_info(self) -> List[GPUInfo]:
        """Get GPU information using nvidia-smi"""
        if not self.has_nvidia_smi:
            return []
        
        try:
            # Query nvidia-smi for GPU info
            result = subprocess.run([
                'nvidia-smi',
                '--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return []
            
            gpus = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 5:
                    try:
                        memory_used = float(parts[2])
                        memory_total = float(parts[3])
                        memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0
                        
                        gpu = GPUInfo(
                            index=int(parts[0]),
                            name=parts[1],
                            memory_used=memory_used,
                            memory_total=memory_total,
                            memory_percent=memory_percent,
                            utilization=float(parts[4]),
                            temperature=float(parts[5]) if len(parts) > 5 and parts[5] else None
                        )
                        gpus.append(gpu)
                    except (ValueError, IndexError):
                        continue
            
            return gpus
        except Exception:
            return []
    
    def _get_container_memory_limit(self) -> Optional[int]:
        """Get container memory limit in bytes from cgroups"""
        # Try cgroup v2 first
        cgroup_v2_paths = [
            '/sys/fs/cgroup/memory.max',
            '/sys/fs/cgroup/memory/memory.max'
        ]
        for path in cgroup_v2_paths:
            try:
                with open(path, 'r') as f:
                    limit = f.read().strip()
                    if limit != 'max':
                        return int(limit)
            except:
                continue
        
        # Try cgroup v1
        cgroup_v1_paths = [
            '/sys/fs/cgroup/memory/memory.limit_in_bytes',
            '/sys/fs/cgroup/memory.limit_in_bytes'
        ]
        for path in cgroup_v1_paths:
            try:
                with open(path, 'r') as f:
                    limit = int(f.read().strip())
                    # Filter out "unlimited" values (usually very large numbers)
                    if limit < (1 << 62):  # Reasonable upper bound
                        return limit
            except:
                continue
        
        return None
    
    def _get_container_memory_usage(self) -> Optional[int]:
        """Get container current memory usage in bytes from cgroups"""
        # Try cgroup v2
        cgroup_v2_paths = [
            '/sys/fs/cgroup/memory.current',
            '/sys/fs/cgroup/memory/memory.current'
        ]
        for path in cgroup_v2_paths:
            try:
                with open(path, 'r') as f:
                    return int(f.read().strip())
            except:
                continue
        
        # Try cgroup v1
        cgroup_v1_paths = [
            '/sys/fs/cgroup/memory/memory.usage_in_bytes',
            '/sys/fs/cgroup/memory.usage_in_bytes'
        ]
        for path in cgroup_v1_paths:
            try:
                with open(path, 'r') as f:
                    return int(f.read().strip())
            except:
                continue
        
        return None
    
    def get_ram_info(self) -> tuple:
        """Get RAM information"""
        # If in container, try to get container limits first
        if self.in_container:
            try:
                mem_limit = self._get_container_memory_limit()
                mem_usage = self._get_container_memory_usage()
                
                if mem_limit and mem_usage:
                    total_gb = mem_limit / (1024**3)
                    used_gb = mem_usage / (1024**3)
                    percent = (used_gb / total_gb * 100) if total_gb > 0 else 0
                    return (used_gb, total_gb, percent)
            except Exception:
                pass
        
        if self.has_psutil:
            try:
                import psutil
                mem = psutil.virtual_memory()
                return (
                    mem.used / (1024**3),  # GB
                    mem.total / (1024**3),  # GB
                    mem.percent
                )
            except Exception:
                pass
        
        # Fallback for systems without psutil
        system = platform.system()
        
        if system == "Darwin":  # macOS
            try:
                # Get total memory
                result = subprocess.run(['sysctl', 'hw.memsize'], 
                                      capture_output=True, text=True, timeout=2)
                total_bytes = int(result.stdout.split(':')[1].strip())
                total_gb = total_bytes / (1024**3)
                
                # Get used memory (approximate)
                result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=2)
                lines = result.stdout.split('\n')
                page_size = 4096  # Default page size
                
                pages_active = 0
                pages_wired = 0
                for line in lines:
                    if 'Pages active:' in line:
                        pages_active = int(line.split(':')[1].strip().rstrip('.'))
                    elif 'Pages wired down:' in line:
                        pages_wired = int(line.split(':')[1].strip().rstrip('.'))
                
                used_bytes = (pages_active + pages_wired) * page_size
                used_gb = used_bytes / (1024**3)
                percent = (used_gb / total_gb * 100) if total_gb > 0 else 0
                
                return (used_gb, total_gb, percent)
            except Exception:
                pass
        
        elif system == "Linux":
            try:
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                
                mem_total = 0
                mem_available = 0
                for line in lines:
                    if line.startswith('MemTotal:'):
                        mem_total = int(line.split()[1]) / (1024**2)  # GB
                    elif line.startswith('MemAvailable:'):
                        mem_available = int(line.split()[1]) / (1024**2)  # GB
                
                used_gb = mem_total - mem_available
                percent = (used_gb / mem_total * 100) if mem_total > 0 else 0
                
                return (used_gb, mem_total, percent)
            except Exception:
                pass
        
        # Ultimate fallback
        return (0.0, 0.0, 0.0)
    
    def _get_container_cpu_quota(self) -> Optional[float]:
        """Get container CPU quota (number of CPUs allocated)"""
        quota = None
        period = None
        
        # Try cgroup v2
        try:
            with open('/sys/fs/cgroup/cpu.max', 'r') as f:
                parts = f.read().strip().split()
                if parts[0] != 'max':
                    quota = int(parts[0])
                    period = int(parts[1]) if len(parts) > 1 else 100000
        except:
            pass
        
        # Try cgroup v1
        if quota is None:
            try:
                with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us', 'r') as f:
                    quota = int(f.read().strip())
            except:
                pass
        
        if period is None:
            try:
                with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us', 'r') as f:
                    period = int(f.read().strip())
            except:
                period = 100000  # Default
        
        if quota and quota > 0 and period > 0:
            # Calculate number of CPUs
            return quota / period
        
        return None
    
    def get_cpu_info(self) -> tuple:
        """Get CPU information"""
        cpu_count = None
        
        # If in container, try to get container CPU limit first
        if self.in_container:
            try:
                container_cpus = self._get_container_cpu_quota()
                if container_cpus:
                    # Round to nearest integer, minimum 1
                    cpu_count = max(1, round(container_cpus))
            except Exception:
                pass
        
        if self.has_psutil:
            try:
                import psutil
                percent = psutil.cpu_percent(interval=0.1)
                if cpu_count is None:
                    cpu_count = psutil.cpu_count()
                return (percent, cpu_count)
            except Exception:
                pass
        
        # Fallback
        import os
        if cpu_count is None:
            cpu_count = os.cpu_count() or 1
        return (0.0, cpu_count)
    
    def get_snapshot(self) -> SystemResources:
        """Get current system resource snapshot"""
        gpus = self.get_gpu_info()
        ram_used, ram_total, ram_percent = self.get_ram_info()
        cpu_percent, cpu_count = self.get_cpu_info()
        
        return SystemResources(
            timestamp=time.time(),
            ram_used=ram_used,
            ram_total=ram_total,
            ram_percent=ram_percent,
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            gpus=gpus
        )
    
    def print_resources(self, resources: SystemResources, prefix: str = ""):
        """Pretty print resource information"""
        print(f"\n{prefix}{'='*60}")
        print(f"{prefix}📊 SYSTEM RESOURCES")
        print(f"{prefix}{'='*60}")
        
        # RAM
        print(f"{prefix}💾 RAM: {resources.ram_used:.2f} GB / {resources.ram_total:.2f} GB "
              f"({resources.ram_percent:.1f}%)")
        
        # CPU
        print(f"{prefix}⚙️  CPU: {resources.cpu_percent:.1f}% ({resources.cpu_count} cores)")
        
        # GPU
        if resources.gpus:
            print(f"{prefix}🎮 GPU:")
            for gpu in resources.gpus:
                temp_str = f", {gpu.temperature:.0f}°C" if gpu.temperature else ""
                print(f"{prefix}   GPU {gpu.index} ({gpu.name}):")
                print(f"{prefix}     VRAM: {gpu.memory_used:.0f} MB / {gpu.memory_total:.0f} MB "
                      f"({gpu.memory_percent:.1f}%)")
                print(f"{prefix}     Utilization: {gpu.utilization:.0f}%{temp_str}")
        else:
            print(f"{prefix}🎮 GPU: Not available (nvidia-smi not found)")
        
        print(f"{prefix}{'='*60}\n")
    
    def print_compact(self, resources: SystemResources):
        """Print compact one-line resource info"""
        gpu_str = ""
        if resources.gpus:
            gpu = resources.gpus[0]  # Show first GPU
            gpu_str = f" | GPU: {gpu.memory_percent:.0f}% VRAM, {gpu.utilization:.0f}% Util"
        
        print(f"💾 RAM: {resources.ram_percent:.0f}% | "
              f"⚙️  CPU: {resources.cpu_percent:.0f}%{gpu_str}")


def print_resource_summary(monitor: ResourceMonitor):
    """Print current resource summary"""
    resources = monitor.get_snapshot()
    monitor.print_resources(resources)


if __name__ == "__main__":
    # Test the monitor
    print("System Resource Monitor Test\n")
    
    monitor = ResourceMonitor()
    
    print(f"nvidia-smi available: {monitor.has_nvidia_smi}")
    print(f"psutil available: {monitor.has_psutil}")
    print(f"Running in container: {monitor.in_container}")
    print()
    
    resources = monitor.get_snapshot()
    monitor.print_resources(resources)
    
    print("\nCompact format:")
    monitor.print_compact(resources)

