"""Performance tests for DataBus — publish/subscribe latency measurement."""

import time
import statistics
from param_id_gui.core.data_bus import DataBus, Signal


def measure_publish_performance(n: int = 10000) -> dict:
    """Measure publish performance for n signals."""
    bus = DataBus(max_history=n + 100)
    times = []
    
    for i in range(n):
        sig = Signal(
            source="sensor://perf_test",
            signal_type="current",
            timestamp_ns=i * 1_000_000,
            value=float(i),
            unit="A",
        )
        start = time.perf_counter_ns()
        bus.publish("perf_topic", sig)
        end = time.perf_counter_ns()
        times.append(end - start)
    
    return {
        "operation": "publish",
        "count": n,
        "total_ns": sum(times),
        "total_ms": sum(times) / 1_000_000,
        "mean_ns": statistics.mean(times),
        "mean_ms": statistics.mean(times) / 1_000_000,
        "median_ns": statistics.median(times),
        "median_ms": statistics.median(times) / 1_000_000,
        "min_ns": min(times),
        "min_ms": min(times) / 1_000_000,
        "max_ns": max(times),
        "max_ms": max(times) / 1_000_000,
        "stdev_ns": statistics.stdev(times) if len(times) > 1 else 0,
        "stdev_ms": statistics.stdev(times) / 1_000_000 if len(times) > 1 else 0,
    }


def measure_subscribe_performance(n: int = 10000) -> dict:
    """Measure subscribe callback performance for n signals."""
    bus = DataBus(max_history=n + 100)
    received = []
    
    def callback(sig):
        received.append(sig)
    
    bus.subscribe("perf_topic", callback)
    times = []
    
    for i in range(n):
        sig = Signal(
            source="sensor://perf_test",
            signal_type="current",
            timestamp_ns=i * 1_000_000,
            value=float(i),
            unit="A",
        )
        start = time.perf_counter_ns()
        bus.publish("perf_topic", sig)
        end = time.perf_counter_ns()
        times.append(end - start)
    
    assert len(received) == n
    
    return {
        "operation": "subscribe",
        "count": n,
        "total_ns": sum(times),
        "total_ms": sum(times) / 1_000_000,
        "mean_ns": statistics.mean(times),
        "mean_ms": statistics.mean(times) / 1_000_000,
        "median_ns": statistics.median(times),
        "median_ms": statistics.median(times) / 1_000_000,
        "min_ns": min(times),
        "min_ms": min(times) / 1_000_000,
        "max_ns": max(times),
        "max_ms": max(times) / 1_000_000,
        "stdev_ns": statistics.stdev(times) if len(times) > 1 else 0,
        "stdev_ms": statistics.stdev(times) / 1_000_000 if len(times) > 1 else 0,
    }


def measure_history_read_performance(n: int = 10000) -> dict:
    """Measure history read performance."""
    bus = DataBus(max_history=n + 100)
    
    # First populate history
    for i in range(n):
        sig = Signal(
            source="sensor://perf_test",
            signal_type="current",
            timestamp_ns=i * 1_000_000,
            value=float(i),
            unit="A",
        )
        bus.publish("perf_topic", sig)
    
    # Measure read performance
    times = []
    for _ in range(1000):
        start = time.perf_counter_ns()
        history = bus.read_history("perf_topic", max_count=1000)
        end = time.perf_counter_ns()
        times.append(end - start)
    
    return {
        "operation": "history_read",
        "count": 1000,
        "history_size": n,
        "read_size": 1000,
        "total_ns": sum(times),
        "total_ms": sum(times) / 1_000_000,
        "mean_ns": statistics.mean(times),
        "mean_ms": statistics.mean(times) / 1_000_000,
        "median_ns": statistics.median(times),
        "median_ms": statistics.median(times) / 1_000_000,
        "min_ns": min(times),
        "min_ms": min(times) / 1_000_000,
        "max_ns": max(times),
        "max_ms": max(times) / 1_000_000,
    }


if __name__ == "__main__":
    print("DataBus Performance Tests")
    print("=" * 50)
    
    print("\n1. Publish Performance (10,000 signals):")
    pub_results = measure_publish_performance(10000)
    for key, value in pub_results.items():
        if "ms" in key:
            print(f"  {key}: {value:.3f} ms")
        elif "ns" in key:
            print(f"  {key}: {value:.0f} ns")
        else:
            print(f"  {key}: {value}")
    
    print("\n2. Subscribe Performance (10,000 signals with callback):")
    sub_results = measure_subscribe_performance(10000)
    for key, value in sub_results.items():
        if "ms" in key:
            print(f"  {key}: {value:.3f} ms")
        elif "ns" in key:
            print(f"  {key}: {value:.0f} ns")
        else:
            print(f"  {key}: {value}")
    
    print("\n3. History Read Performance (1000 reads of 1000 signals):")
    hist_results = measure_history_read_performance(10000)
    for key, value in hist_results.items():
        if "ms" in key:
            print(f"  {key}: {value:.3f} ms")
        elif "ns" in key:
            print(f"  {key}: {value:.0f} ns")
        else:
            print(f"  {key}: {value}")
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"  Publish mean latency: {pub_results['mean_ms']:.3f} ms")
    print(f"  Subscribe mean latency: {sub_results['mean_ms']:.3f} ms")
    print(f"  History read mean latency: {hist_results['mean_ms']:.3f} ms")
    
    # Check if meets requirement (< 1ms)
    if pub_results['mean_ms'] < 1.0 and sub_results['mean_ms'] < 1.0:
        print("\nPASS: Publish/Subscribe latency < 1ms requirement met")
    else:
        print("\nFAIL: Publish/Subscribe latency >= 1ms requirement not met")