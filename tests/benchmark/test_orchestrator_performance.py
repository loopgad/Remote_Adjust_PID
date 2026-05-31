"""Performance benchmark: Orchestrator and DataBus throughput.

Measures:
  - Orchestrator.run() for 1000-step simulation
  - DataBus publish/subscribe throughput (10000 calls)
  - Memory usage during long simulation

Target: < 1s for 1000 steps, > 100k pub/sub calls/sec.
"""

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Dict, List

import pytest

from param_id_gui.core.orchestrator import Orchestrator, OrchestratorConfig, StepResult
from param_id_gui.core.data_bus import DataBus, Signal


# ── Benchmark Helpers ────────────────────────────────────────

def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback: use sys.getsizeof approximation
        return 0.0


# ── Orchestrator Benchmark ───────────────────────────────────

class TestOrchestratorPerformance:
    """Orchestrator performance benchmarks."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with default config."""
        cfg = OrchestratorConfig(
            dt_ns=50000,
            enable_energy_audit=False,  # Disable for pure performance
        )
        return Orchestrator(cfg=cfg)

    @pytest.mark.slow
    def test_orchestrator_1000_steps(self, orchestrator):
        """Benchmark orchestrator for 1000-step simulation."""
        n_steps = 1000
        step_ns = 50000  # 50μs

        # Register a simple stepper
        def simple_stepper(step_ns: int) -> StepResult:
            return StepResult(solver_id="test", converged=True)

        orchestrator.register_stepper("test", simple_stepper)

        # Run simulation
        start = time.perf_counter()
        orchestrator.run(step_ns=step_ns, duration_s=n_steps * step_ns / 1e9)
        end = time.perf_counter()

        elapsed = end - start
        steps_per_sec = n_steps / elapsed if elapsed > 0 else float('inf')

        print(f"\n{'='*60}")
        print(f"Orchestrator Performance (1000 steps)")
        print(f"{'='*60}")
        print(f"  Total time:    {elapsed*1000:.2f} ms")
        print(f"  Steps/sec:     {steps_per_sec:,.0f}")
        print(f"  Time per step: {elapsed/n_steps*1e6:.2f} μs")
        print(f"{'='*60}")

        # Target: < 1s for 1000 steps
        assert elapsed < 1.0, (
            f"Orchestrator too slow: {elapsed:.2f}s for {n_steps} steps"
        )

    @pytest.mark.slow
    def test_orchestrator_multiple_solvers(self, orchestrator):
        """Benchmark orchestrator with multiple registered solvers."""
        n_steps = 1000
        step_ns = 50000

        # Register multiple solvers
        for i in range(5):
            def stepper(step_ns: int, idx=i) -> StepResult:
                return StepResult(solver_id=f"solver_{idx}", converged=True)
            orchestrator.register_stepper(f"solver_{i}", stepper)

        start = time.perf_counter()
        orchestrator.run(step_ns=step_ns, duration_s=n_steps * step_ns / 1e9)
        end = time.perf_counter()

        elapsed = end - start

        print(f"\n  Multi-solver (5): {elapsed*1000:.2f} ms")

        assert elapsed < 2.0, (
            f"Multi-solver orchestrator too slow: {elapsed:.2f}s"
        )

    @pytest.mark.slow
    def test_orchestrator_with_fault_injection(self, orchestrator):
        """Benchmark orchestrator with scheduled fault injection."""
        n_steps = 1000
        step_ns = 50000

        def simple_stepper(step_ns: int) -> StepResult:
            return StepResult(solver_id="test", converged=True)

        orchestrator.register_stepper("test", simple_stepper)

        # Schedule faults
        for i in range(10):
            orchestrator.schedule_fault(i * 0.001, lambda: None)

        start = time.perf_counter()
        orchestrator.run(step_ns=step_ns, duration_s=n_steps * step_ns / 1e9)
        end = time.perf_counter()

        elapsed = end - start

        print(f"\n  With faults (10): {elapsed*1000:.2f} ms")

        assert elapsed < 1.5, (
            f"Orchestrator with faults too slow: {elapsed:.2f}s"
        )


# ── DataBus Benchmark ────────────────────────────────────────

class TestDataBusPerformance:
    """DataBus performance benchmarks."""

    @pytest.fixture
    def data_bus(self):
        """Create DataBus instance."""
        return DataBus(max_history=10000)

    @pytest.mark.slow
    def test_publish_subscribe_throughput(self, data_bus):
        """Benchmark DataBus publish/subscribe throughput."""
        n_calls = 10000
        received = []

        def callback(signal: Signal):
            received.append(signal)

        data_bus.subscribe("test_topic", callback)

        # Warmup
        for _ in range(100):
            sig = Signal(source="test://bench", signal_type="test", value=1.0)
            data_bus.publish("test_topic", sig)

        received.clear()

        # Benchmark
        start = time.perf_counter()
        for i in range(n_calls):
            sig = Signal(source="test://bench", signal_type="test", value=float(i))
            data_bus.publish("test_topic", sig)
        end = time.perf_counter()

        elapsed = end - start
        calls_per_sec = n_calls / elapsed if elapsed > 0 else float('inf')

        print(f"\n{'='*60}")
        print(f"DataBus Performance")
        print(f"{'='*60}")
        print(f"  Publish calls:  {n_calls:,}")
        print(f"  Total time:     {elapsed*1000:.2f} ms")
        print(f"  Calls/sec:      {calls_per_sec:,.0f}")
        print(f"  Received:       {len(received):,}")
        print(f"{'='*60}")

        # Target: > 100,000 calls/sec
        assert calls_per_sec > 100000, (
            f"DataBus throughput too low: {calls_per_sec:.0f} calls/sec"
        )
        assert len(received) == n_calls

    @pytest.mark.slow
    def test_publish_scalar_throughput(self, data_bus):
        """Benchmark publish_scalar convenience method."""
        n_calls = 10000

        start = time.perf_counter()
        for i in range(n_calls):
            data_bus.publish_scalar("test_topic", float(i), unit="V")
        end = time.perf_counter()

        elapsed = end - start
        calls_per_sec = n_calls / elapsed if elapsed > 0 else float('inf')

        print(f"\n  publish_scalar: {calls_per_sec:,.0f} calls/sec")

        assert calls_per_sec > 50000, (
            f"publish_scalar too slow: {calls_per_sec:.0f}"
        )

    @pytest.mark.slow
    def test_multi_topic_throughput(self, data_bus):
        """Benchmark DataBus with multiple topics."""
        n_topics = 10
        n_calls_per_topic = 1000

        start = time.perf_counter()
        for t in range(n_topics):
            for i in range(n_calls_per_topic):
                sig = Signal(
                    source=f"sensor://topic_{t}",
                    signal_type="test",
                    value=float(i)
                )
                data_bus.publish(f"topic_{t}", sig)
        end = time.perf_counter()

        total_calls = n_topics * n_calls_per_topic
        elapsed = end - start
        calls_per_sec = total_calls / elapsed if elapsed > 0 else float('inf')

        print(f"\n  Multi-topic ({n_topics}x{n_calls_per_topic}): {calls_per_sec:,.0f} calls/sec")

        assert calls_per_sec > 50000

    @pytest.mark.slow
    def test_history_read_performance(self, data_bus):
        """Benchmark history read performance."""
        # Fill history
        for i in range(5000):
            sig = Signal(source="test://fill", signal_type="test", value=float(i))
            data_bus.publish("test_topic", sig)

        n_reads = 1000

        start = time.perf_counter()
        for _ in range(n_reads):
            data_bus.read_history("test_topic", max_count=100)
        end = time.perf_counter()

        elapsed = end - start
        reads_per_sec = n_reads / elapsed if elapsed > 0 else float('inf')

        print(f"\n  History reads: {reads_per_sec:,.0f} reads/sec")

        assert reads_per_sec > 10000


# ── Memory Benchmark ─────────────────────────────────────────

class TestMemoryPerformance:
    """Memory usage benchmarks."""

    @pytest.mark.slow
    def test_orchestrator_memory_stability(self):
        """Test that orchestrator doesn't leak memory during long run."""
        cfg = OrchestratorConfig(
            dt_ns=50000,
            enable_energy_audit=True,
            energy_audit_period_steps=100,
        )
        orch = Orchestrator(cfg=cfg)

        call_count = [0]
        def counting_stepper(step_ns: int) -> StepResult:
            call_count[0] += 1
            return StepResult(solver_id="test", converged=True)

        orch.register_stepper("test", counting_stepper)

        # Run in chunks to measure memory
        chunk_size = 1000
        n_chunks = 5
        memory_samples = []

        mem_before = get_memory_usage_mb()

        for chunk in range(n_chunks):
            orch.run(
                step_ns=50000,
                duration_s=chunk_size * 50000 / 1e9
            )
            mem_after = get_memory_usage_mb()
            memory_samples.append(mem_after)

        mem_after = get_memory_usage_mb()

        # Check memory growth
        if mem_before > 0 and mem_after > 0:
            growth_mb = mem_after - mem_before
            print(f"\n{'='*60}")
            print(f"Memory Stability")
            print(f"{'='*60}")
            print(f"  Before:     {mem_before:.1f} MB")
            print(f"  After:      {mem_after:.1f} MB")
            print(f"  Growth:     {growth_mb:.1f} MB")
            print(f"  Steps:      {call_count[0]:,}")
            print(f"{'='*60}")

            # Allow some growth but not excessive
            # 5000 steps should not cause > 100MB growth
            assert growth_mb < 100, (
                f"Excessive memory growth: {growth_mb:.1f} MB"
            )
        else:
            print("\n  Memory measurement skipped (psutil not available)")

    @pytest.mark.slow
    def test_data_bus_memory_stability(self):
        """Test that DataBus doesn't leak memory during long run."""
        bus = DataBus(max_history=1000)

        mem_before = get_memory_usage_mb()

        # Publish many signals (history should be capped)
        for i in range(50000):
            sig = Signal(source="test://mem", signal_type="test", value=float(i))
            bus.publish("test_topic", sig)

        mem_after = get_memory_usage_mb()

        if mem_before > 0 and mem_after > 0:
            growth_mb = mem_after - mem_before
            print(f"\n  DataBus memory growth: {growth_mb:.1f} MB")

            # History capped at 1000, so growth should be minimal
            assert growth_mb < 50, (
                f"DataBus excessive memory: {growth_mb:.1f} MB"
            )

        # Verify history is capped
        history = bus.read_history("test_topic", max_count=10000)
        assert len(history) <= 1000, (
            f"History not capped: {len(history)} entries"
        )


# ── Report Generation ────────────────────────────────────────

def generate_orchestrator_report(output_path: Path) -> Dict:
    """Generate orchestrator/DataBus performance report.

    Args:
        output_path: Path to save JSON report

    Returns:
        Report dictionary
    """
    # Orchestrator benchmark
    cfg = OrchestratorConfig(dt_ns=50000, enable_energy_audit=False)
    orch = Orchestrator(cfg=cfg)

    def stepper(step_ns: int) -> StepResult:
        return StepResult(solver_id="test", converged=True)

    orch.register_stepper("test", stepper)

    n_steps = 1000
    step_ns = 50000

    orch_times = []
    for _ in range(5):
        orch.reset()
        start = time.perf_counter()
        orch.run(step_ns=step_ns, duration_s=n_steps * step_ns / 1e9)
        orch_times.append(time.perf_counter() - start)

    # DataBus benchmark
    bus = DataBus(max_history=10000)
    bus_times = []
    n_pub = 10000

    for _ in range(5):
        start = time.perf_counter()
        for i in range(n_pub):
            sig = Signal(source="test://report", signal_type="test", value=float(i))
            bus.publish("report_topic", sig)
        bus_times.append(time.perf_counter() - start)

    import statistics

    report = {
        "test_name": "Orchestrator & DataBus Performance",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "orchestrator": {
            "n_steps": n_steps,
            "mean_ms": round(statistics.mean(orch_times) * 1000, 2),
            "steps_per_sec": round(n_steps / statistics.mean(orch_times)),
            "target": "< 1000ms for 1000 steps",
        },
        "data_bus": {
            "n_publish": n_pub,
            "mean_ms": round(statistics.mean(bus_times) * 1000, 2),
            "calls_per_sec": round(n_pub / statistics.mean(bus_times)),
            "target": "> 100,000 calls/sec",
        },
        "memory": {
            "test": "long_simulation_stability",
            "target": "< 100MB growth for 5000 steps",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report


if __name__ == "__main__":
    report_path = Path(__file__).parent.parent.parent / ".sisyphus" / "evidence" / "task-23-orchestrator-report.json"
    report = generate_orchestrator_report(report_path)
    print(f"\nReport saved to: {report_path}")
    print(f"Orchestrator: {report['orchestrator']['steps_per_sec']:,} steps/sec")
    print(f"DataBus: {report['data_bus']['calls_per_sec']:,} calls/sec")
