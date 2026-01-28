#!/usr/bin/env python3
"""
Resource Manager - Dynamic Memory Management for OppNDA
Implements memory-aware worker optimization as described in the research paper.

Mathematical Models Implemented:
- Memory footprint: M(t) ≈ M_base + Σ(γ * size(r_i) + M_overhead)
- Optimal workers: P_opt = max{p ∈ Z+ | M(t)|P=p ≤ η * M_RAM}
"""

import os
import threading
from pathlib import Path
from typing import Optional, List, Tuple

# Try to import psutil, use fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not installed. Memory management will use fallback mode.")


class ResourceConfig:
    """Configuration for resource management parameters."""
    
    # Default values - can be overridden
    ETA = 0.90              # η: RAM utilization threshold (90%)
    GAMMA = 3.0             # γ: DataFrame expansion factor
    M_OVERHEAD_MB = 50      # Per-worker overhead in MB
    MIN_WORKERS = 1         # Minimum worker count
    MAX_WORKERS = 32        # Maximum worker count (hard cap)
    FALLBACK_WORKERS = 8    # Used when safety is disabled or psutil unavailable
    
    # Safety can be disabled if needed
    SAFETY_ENABLED = True


class MemoryEstimator:
    """
    Estimates memory consumption for batch processing.
    
    Implements: M(t) ≈ M_base + Σ(γ * size(r_i) + M_overhead)
    """
    
    def __init__(self, gamma: float = ResourceConfig.GAMMA, 
                 overhead_mb: float = ResourceConfig.M_OVERHEAD_MB):
        self.gamma = gamma
        self.overhead_bytes = overhead_mb * 1024 * 1024
    
    def estimate_file_memory(self, file_size_bytes: int) -> int:
        """
        Estimate memory needed to process a single file.
        Returns memory in bytes.
        """
        return int(self.gamma * file_size_bytes + self.overhead_bytes)
    
    def estimate_batch_memory(self, file_sizes: List[int], num_workers: int) -> int:
        """
        Estimate peak memory for a batch of files with given worker count.
        
        Args:
            file_sizes: List of file sizes in bytes
            num_workers: Number of concurrent workers
            
        Returns:
            Estimated peak memory in bytes
        """
        if not file_sizes:
            return 0
        
        # Sort files by size (largest first) for worst-case estimation
        sorted_sizes = sorted(file_sizes, reverse=True)
        
        # Peak memory = sum of largest N files being processed concurrently
        concurrent_files = sorted_sizes[:num_workers]
        peak_memory = sum(self.estimate_file_memory(size) for size in concurrent_files)
        
        return peak_memory
    
    def get_file_sizes(self, file_paths: List[str]) -> List[int]:
        """Get sizes of multiple files."""
        sizes = []
        for path in file_paths:
            try:
                sizes.append(os.path.getsize(path))
            except OSError:
                sizes.append(0)
        return sizes


class DynamicSemaphore:
    """
    A semaphore that dynamically adjusts based on available memory.
    
    Implements: P_opt = max{p ∈ Z+ | M(t)|P=p ≤ η * M_RAM}
    
    This prevents OS-level swap thrashing by capping concurrent workers
    when memory pressure is detected.
    """
    
    def __init__(self, initial_permits: int, 
                 eta: float = ResourceConfig.ETA,
                 safety_enabled: bool = True):
        self._lock = threading.Lock()
        self._current_permits = initial_permits
        self._max_permits = initial_permits
        self._eta = eta
        self._safety_enabled = safety_enabled
        self._active_workers = 0
    
    def acquire(self, blocking: bool = True) -> bool:
        """Acquire a permit, potentially waiting if none available."""
        with self._lock:
            if self._safety_enabled:
                self._adjust_permits()
            
            if self._active_workers < self._current_permits:
                self._active_workers += 1
                return True
            elif not blocking:
                return False
        
        # Blocking wait (simple spin with sleep)
        import time
        while True:
            time.sleep(0.01)
            with self._lock:
                if self._safety_enabled:
                    self._adjust_permits()
                if self._active_workers < self._current_permits:
                    self._active_workers += 1
                    return True
    
    def release(self):
        """Release a permit."""
        with self._lock:
            self._active_workers = max(0, self._active_workers - 1)
    
    def _adjust_permits(self):
        """Dynamically adjust permits based on memory pressure."""
        if not PSUTIL_AVAILABLE:
            return
        
        memory = psutil.virtual_memory()
        available_ratio = memory.available / memory.total
        
        # If we're using more than η of RAM, reduce permits
        if available_ratio < (1 - self._eta):
            # Scale down permits based on memory pressure
            pressure = (1 - self._eta - available_ratio) / (1 - self._eta)
            new_permits = max(1, int(self._max_permits * (1 - pressure)))
            self._current_permits = new_permits
        else:
            # Memory is fine, allow up to max
            self._current_permits = self._max_permits
    
    @property
    def current_permits(self) -> int:
        return self._current_permits
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, *args):
        self.release()


class ResourceManager:
    """
    Central resource manager for OppNDA's multiprocessing.
    
    Provides:
    - Dynamic worker count calculation based on available RAM
    - Memory estimation for batch processing
    - Configurable safety measures (can be disabled)
    
    Usage:
        rm = ResourceManager()
        workers = rm.get_optimal_workers()
        
        # Or with safety disabled:
        rm = ResourceManager(safety_enabled=False)
    """
    
    def __init__(self, 
                 eta: float = ResourceConfig.ETA,
                 gamma: float = ResourceConfig.GAMMA,
                 overhead_mb: float = ResourceConfig.M_OVERHEAD_MB,
                 safety_enabled: bool = ResourceConfig.SAFETY_ENABLED):
        """
        Initialize the resource manager.
        
        Args:
            eta: RAM utilization threshold (0.0-1.0). Default 0.75
            gamma: DataFrame expansion factor. Default 3.0
            overhead_mb: Per-worker overhead in MB. Default 50
            safety_enabled: If False, disables memory checks and uses static workers
        """
        self.eta = eta
        self.gamma = gamma
        self.overhead_mb = overhead_mb
        self.safety_enabled = safety_enabled
        
        self._estimator = MemoryEstimator(gamma, overhead_mb)
        
        # Cache system info
        self._cpu_count = os.cpu_count() or 1
        self._total_ram = self._get_total_ram()
    
    def _get_total_ram(self) -> int:
        """Get total system RAM in bytes."""
        if PSUTIL_AVAILABLE:
            return psutil.virtual_memory().total
        # Fallback: assume 8GB
        return 8 * 1024 * 1024 * 1024
    
    def _get_available_ram(self) -> int:
        """Get available system RAM in bytes."""
        if PSUTIL_AVAILABLE:
            return psutil.virtual_memory().available
        # Fallback: assume 4GB available
        return 4 * 1024 * 1024 * 1024
    
    def _get_baseline_memory(self) -> int:
        """Get baseline memory usage of current process."""
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            return process.memory_info().rss
        # Fallback: assume 100MB baseline
        return 100 * 1024 * 1024
    
    def get_optimal_workers(self, file_paths: Optional[List[str]] = None) -> int:
        """
        Calculate optimal worker count based on available resources.
        
        Implements: P_opt = max{p ∈ Z+ | M(t)|P=p ≤ η * M_RAM}
        
        Args:
            file_paths: Optional list of file paths to process.
                       If provided, uses actual file sizes for estimation.
                       
        Returns:
            Optimal number of worker processes
        """
        # If safety is disabled, return fallback value
        if not self.safety_enabled:
            return min(ResourceConfig.FALLBACK_WORKERS, self._cpu_count)
        
        # Get memory constraints
        available_ram = self._get_available_ram()
        memory_budget = int(self.eta * available_ram)
        
        # If no file paths provided, use simple estimation
        if not file_paths:
            # Assume 10MB average file size
            avg_file_memory = self._estimator.estimate_file_memory(10 * 1024 * 1024)
            max_workers_by_memory = max(1, memory_budget // avg_file_memory)
        else:
            # Use actual file sizes
            file_sizes = self._estimator.get_file_sizes(file_paths)
            
            # Binary search for optimal P
            max_workers_by_memory = 1
            for p in range(1, ResourceConfig.MAX_WORKERS + 1):
                estimated_memory = self._estimator.estimate_batch_memory(file_sizes, p)
                if estimated_memory <= memory_budget:
                    max_workers_by_memory = p
                else:
                    break
        
        # Constrain by CPU count and hard limits
        optimal = min(
            max_workers_by_memory,
            self._cpu_count,
            ResourceConfig.MAX_WORKERS
        )
        
        return max(ResourceConfig.MIN_WORKERS, optimal)
    
    def create_semaphore(self, initial_permits: Optional[int] = None) -> DynamicSemaphore:
        """
        Create a dynamic semaphore for worker pool management.
        
        Args:
            initial_permits: Starting permit count. If None, uses optimal workers.
            
        Returns:
            DynamicSemaphore instance
        """
        if initial_permits is None:
            initial_permits = self.get_optimal_workers()
        
        return DynamicSemaphore(
            initial_permits=initial_permits,
            eta=self.eta,
            safety_enabled=self.safety_enabled
        )
    
    def get_memory_status(self) -> dict:
        """
        Get current memory status for monitoring/logging.
        
        Returns:
            Dictionary with memory statistics
        """
        if not PSUTIL_AVAILABLE:
            return {
                'psutil_available': False,
                'safety_enabled': self.safety_enabled,
                'fallback_workers': ResourceConfig.FALLBACK_WORKERS
            }
        
        mem = psutil.virtual_memory()
        return {
            'psutil_available': True,
            'safety_enabled': self.safety_enabled,
            'total_ram_gb': mem.total / (1024**3),
            'available_ram_gb': mem.available / (1024**3),
            'used_percent': mem.percent,
            'eta_threshold': self.eta,
            'memory_budget_gb': (self.eta * mem.available) / (1024**3),
            'optimal_workers': self.get_optimal_workers(),
            'cpu_count': self._cpu_count
        }
    
    def log_status(self):
        """Print current memory status to console."""
        status = self.get_memory_status()
        
        if not status['psutil_available']:
            print(f"Memory Management: FALLBACK MODE (psutil not available)")
            print(f"  Workers: {status['fallback_workers']}")
            return
        
        if not status['safety_enabled']:
            print(f"Memory Management: DISABLED (using static workers)")
            print(f"  Workers: {ResourceConfig.FALLBACK_WORKERS}")
            return
        
        print(f"Memory Management: ACTIVE")
        print(f"  Total RAM: {status['total_ram_gb']:.1f} GB")
        print(f"  Available: {status['available_ram_gb']:.1f} GB ({100 - status['used_percent']:.0f}%)")
        print(f"  Budget (eta={status['eta_threshold']}): {status['memory_budget_gb']:.1f} GB")
        print(f"  Optimal Workers: {status['optimal_workers']} (CPU: {status['cpu_count']})")


# Convenience function for simple usage
def get_optimal_workers(safety_enabled: bool = True, 
                        file_paths: Optional[List[str]] = None) -> int:
    """
    Quick function to get optimal worker count.
    
    Args:
        safety_enabled: If False, returns static fallback count
        file_paths: Optional file paths for size-based estimation
        
    Returns:
        Optimal worker count
    """
    rm = ResourceManager(safety_enabled=safety_enabled)
    return rm.get_optimal_workers(file_paths)


if __name__ == "__main__":
    # Demo/test the resource manager
    print("=" * 60)
    print("OppNDA Resource Manager - Status Check")
    print("=" * 60)
    
    # Test with safety enabled
    print("\n[Safety ENABLED]")
    rm_safe = ResourceManager(safety_enabled=True)
    rm_safe.log_status()
    
    # Test with safety disabled
    print("\n[Safety DISABLED]")
    rm_unsafe = ResourceManager(safety_enabled=False)
    rm_unsafe.log_status()
    
    print("\n" + "=" * 60)
