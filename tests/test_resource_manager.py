#!/usr/bin/env python3
"""
Tests for the Resource Manager module.
Verifies memory estimation, dynamic worker calculation, and semaphore control.
"""

import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.resource_manager import (
    ResourceManager, 
    ResourceConfig,
    MemoryEstimator,
    DynamicSemaphore,
    get_optimal_workers,
    PSUTIL_AVAILABLE
)


class TestResourceConfig:
    """Tests for ResourceConfig defaults"""
    
    def test_default_eta(self):
        """Verify default RAM threshold is 75%"""
        assert ResourceConfig.ETA == 0.75
    
    def test_default_gamma(self):
        """Verify default expansion factor is 3.0"""
        assert ResourceConfig.GAMMA == 3.0
    
    def test_default_overhead(self):
        """Verify default per-worker overhead is 50MB"""
        assert ResourceConfig.M_OVERHEAD_MB == 50
    
    def test_safety_enabled_by_default(self):
        """Verify safety is enabled by default"""
        assert ResourceConfig.SAFETY_ENABLED is True


class TestMemoryEstimator:
    """Tests for MemoryEstimator class"""
    
    def test_file_memory_estimate(self):
        """Test memory estimation for a single file"""
        estimator = MemoryEstimator(gamma=3.0, overhead_mb=50)
        
        # 10MB file should need ~80MB (3*10 + 50)
        file_size = 10 * 1024 * 1024  # 10MB
        estimated = estimator.estimate_file_memory(file_size)
        
        expected = int(3.0 * file_size + 50 * 1024 * 1024)
        assert estimated == expected
    
    def test_batch_memory_estimate(self):
        """Test peak memory estimation for batch processing"""
        estimator = MemoryEstimator(gamma=2.0, overhead_mb=10)
        
        # 3 files of different sizes, 2 workers
        file_sizes = [5 * 1024 * 1024, 10 * 1024 * 1024, 3 * 1024 * 1024]
        workers = 2
        
        peak = estimator.estimate_batch_memory(file_sizes, workers)
        
        # Should use 2 largest files (10MB and 5MB)
        overhead_bytes = 10 * 1024 * 1024
        expected = (2.0 * 10 * 1024 * 1024 + overhead_bytes) + \
                   (2.0 * 5 * 1024 * 1024 + overhead_bytes)
        
        assert peak == int(expected)
    
    def test_empty_batch(self):
        """Test empty file list returns 0"""
        estimator = MemoryEstimator()
        assert estimator.estimate_batch_memory([], 4) == 0


class TestResourceManager:
    """Tests for ResourceManager class"""
    
    def test_initialization(self):
        """Test ResourceManager initializes correctly"""
        rm = ResourceManager()
        assert rm.eta == 0.75
        assert rm.gamma == 3.0
        assert rm.safety_enabled is True
    
    def test_custom_parameters(self):
        """Test ResourceManager with custom parameters"""
        rm = ResourceManager(eta=0.85, gamma=2.0, safety_enabled=False)
        assert rm.eta == 0.85
        assert rm.gamma == 2.0
        assert rm.safety_enabled is False
    
    def test_optimal_workers_returns_positive(self):
        """Test that optimal workers is always positive"""
        rm = ResourceManager()
        workers = rm.get_optimal_workers()
        assert workers >= 1
    
    def test_optimal_workers_respects_max(self):
        """Test that optimal workers doesn't exceed MAX_WORKERS"""
        rm = ResourceManager()
        workers = rm.get_optimal_workers()
        assert workers <= ResourceConfig.MAX_WORKERS
    
    def test_safety_disabled_uses_fallback(self):
        """Test that disabling safety uses fallback worker count"""
        rm = ResourceManager(safety_enabled=False)
        workers = rm.get_optimal_workers()
        expected = min(ResourceConfig.FALLBACK_WORKERS, rm._cpu_count)
        assert workers == expected
    
    def test_memory_status_returns_dict(self):
        """Test memory status returns a dictionary"""
        rm = ResourceManager()
        status = rm.get_memory_status()
        assert isinstance(status, dict)
        assert 'safety_enabled' in status


class TestDynamicSemaphore:
    """Tests for DynamicSemaphore class"""
    
    def test_basic_acquire_release(self):
        """Test basic acquire and release functionality"""
        sem = DynamicSemaphore(initial_permits=3, safety_enabled=False)
        
        assert sem.acquire() is True
        assert sem._active_workers == 1
        
        sem.release()
        assert sem._active_workers == 0
    
    def test_context_manager(self):
        """Test semaphore as context manager"""
        sem = DynamicSemaphore(initial_permits=2, safety_enabled=False)
        
        with sem:
            assert sem._active_workers == 1
        
        assert sem._active_workers == 0
    
    def test_respects_permits(self):
        """Test non-blocking acquire respects permit limit"""
        sem = DynamicSemaphore(initial_permits=1, safety_enabled=False)
        
        assert sem.acquire(blocking=False) is True
        assert sem.acquire(blocking=False) is False  # Should fail
        
        sem.release()
        assert sem.acquire(blocking=False) is True


class TestConvenienceFunction:
    """Tests for get_optimal_workers convenience function"""
    
    def test_returns_positive_integer(self):
        """Test convenience function returns positive integer"""
        workers = get_optimal_workers()
        assert isinstance(workers, int)
        assert workers >= 1
    
    def test_safety_toggle_works(self):
        """Test safety_enabled parameter works"""
        workers_safe = get_optimal_workers(safety_enabled=True)
        workers_unsafe = get_optimal_workers(safety_enabled=False)
        
        # Both should be valid
        assert workers_safe >= 1
        assert workers_unsafe >= 1


class TestFileBasedEstimation:
    """Tests for file-based memory estimation"""
    
    def test_with_temp_files(self):
        """Test estimation with actual temporary files"""
        rm = ResourceManager()
        
        # Create temp files of known sizes
        with tempfile.TemporaryDirectory() as tmpdir:
            files = []
            for i, size in enumerate([1024, 2048, 4096]):  # 1KB, 2KB, 4KB
                path = os.path.join(tmpdir, f"test_{i}.txt")
                with open(path, 'w') as f:
                    f.write('x' * size)
                files.append(path)
            
            workers = rm.get_optimal_workers(file_paths=files)
            assert workers >= 1


# Pytest-compatible test runner
def test_psutil_availability():
    """Test psutil import detection"""
    # Just check the flag is boolean
    assert isinstance(PSUTIL_AVAILABLE, bool)


if __name__ == "__main__":
    # Run tests standalone
    print("="*60)
    print("RESOURCE MANAGER TESTS")
    print("="*60)
    
    test_classes = [
        TestResourceConfig,
        TestMemoryEstimator,
        TestResourceManager,
        TestDynamicSemaphore,
        TestConvenienceFunction,
        TestFileBasedEstimation,
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    getattr(instance, method_name)()
                    print(f"[PASS] {test_class.__name__}.{method_name}")
                    passed += 1
                except Exception as e:
                    print(f"[FAIL] {test_class.__name__}.{method_name}: {e}")
                    failed += 1
    
    # Run standalone function tests
    try:
        test_psutil_availability()
        print(f"[PASS] test_psutil_availability")
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_psutil_availability: {e}")
        failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
