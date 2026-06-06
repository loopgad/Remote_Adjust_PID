"""Performance benchmark: Model update() calls per second.

Measures throughput of:
  - PMSM dq-axis model step() / update()
  - DC-DC Buck/Boost converter update()
  - FOC controller update()

Target: > 10,000 calls/sec for each model.
"""

import json
import statistics
import time
from pathlib import Path
from typing import Dict, List

import pytest

from param_id_gui.models.motor.pmsm_dq import PMSMdqModel
from param_id_gui.models.power.power_models import BuckConverter, BoostConverter
from param_id_gui.models.controller.foc import FOCController


# ── Benchmark Helpers ────────────────────────────────────────

def benchmark_model_update(
    model, update_fn, n_calls: int = 10000,
    n_runs: int = 10, n_warmup: int = 5
) -> Dict:
    """Benchmark model update() throughput.

    Args:
        model: Model instance to benchmark
        update_fn: Function to call for each update
        n_calls: Number of calls per run
        n_runs: Number of benchmark runs
        n_warmup: Number of warmup runs

    Returns:
        Dictionary with benchmark results
    """
    # Warmup
    for _ in range(n_warmup):
        for _ in range(min(100, n_calls)):
            update_fn()

    # Benchmark
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        for _ in range(n_calls):
            update_fn()
        end = time.perf_counter()
        times.append(end - start)

    mean_time = statistics.mean(times)
    calls_per_sec = n_calls / mean_time if mean_time > 0 else float('inf')

    return {
        "n_calls": n_calls,
        "mean_time": mean_time,
        "min_time": min(times),
        "max_time": max(times),
        "std_time": statistics.stdev(times) if len(times) > 1 else 0.0,
        "calls_per_sec": calls_per_sec,
    }


# ── PMSM Model Benchmark ────────────────────────────────────

class TestPMSMPerformance:
    """PMSM model performance benchmarks."""

    @pytest.fixture
    def pmsm_model(self):
        """Create PMSM model with default parameters."""
        return PMSMdqModel(
            Rs=0.5, Ld=5e-4, Lq=1e-3,
            flux_pm=0.03, J=1e-4, B=1e-3, Pp=4
        )

    @pytest.mark.slow
    def test_pmsm_step_throughput(self, pmsm_model):
        """Benchmark PMSM step() calls per second."""
        n_calls = 10000
        dt = 50e-6  # 50μs

        def update():
            pmsm_model.step_dq(vd=0.0, vq=5.0, tl=0.0, dt=dt)

        result = benchmark_model_update(pmsm_model, update, n_calls=n_calls)

        print(f"\n{'='*60}")
        print(f"PMSM Model Performance (step)")
        print(f"{'='*60}")
        print(f"  Calls:          {n_calls:,}")
        print(f"  Mean time:      {result['mean_time']*1000:.2f} ms")
        print(f"  Calls/sec:      {result['calls_per_sec']:,.0f}")
        print(f"  Min time:       {result['min_time']*1000:.2f} ms")
        print(f"  Max time:       {result['max_time']*1000:.2f} ms")
        print(f"{'='*60}")

        # Target: > 10,000 calls/sec
        assert result["calls_per_sec"] > 10000, (
            f"PMSM throughput too low: {result['calls_per_sec']:.0f} calls/sec"
        )


# ── DC-DC Model Benchmark ───────────────────────────────────

class TestDCDCPerformance:
    """DC-DC converter model performance benchmarks."""

    @pytest.mark.slow
    def test_buck_converter_throughput(self):
        """Benchmark Buck converter update() calls per second."""
        model = BuckConverter()
        model.set_input(duty_cycle=0.5, load_current=1.0)
        dt = 1e-6  # 1μs

        def update():
            model.update(dt=dt)

        result = benchmark_model_update(model, update, n_calls=10000)

        print(f"\n{'='*60}")
        print(f"Buck Converter Performance")
        print(f"{'='*60}")
        print(f"  Calls/sec: {result['calls_per_sec']:,.0f}")
        print(f"{'='*60}")

        assert result["calls_per_sec"] > 10000, (
            f"Buck throughput too low: {result['calls_per_sec']:.0f}"
        )

    @pytest.mark.slow
    def test_boost_converter_throughput(self):
        """Benchmark Boost converter update() calls per second."""
        model = BoostConverter()
        model.set_input(duty_cycle=0.6, load_current=0.5)
        dt = 1e-6

        def update():
            model.update(dt=dt)

        result = benchmark_model_update(model, update, n_calls=10000)

        print(f"\n  Boost Converter: {result['calls_per_sec']:,.0f} calls/sec")

        assert result["calls_per_sec"] > 10000, (
            f"Boost throughput too low: {result['calls_per_sec']:.0f}"
        )


# ── FOC Controller Benchmark ────────────────────────────────

class TestFOCPerformance:
    """FOC controller performance benchmarks."""

    @pytest.fixture
    def foc_controller(self):
        """Create FOC controller with default parameters."""
        return FOCController(
            kp_id=5.0, ki_id=500.0,
            kp_iq=5.0, ki_iq=500.0,
            ts=50e-6, v_bus=48.0
        )

    @pytest.mark.slow
    def test_foc_update_throughput(self, foc_controller):
        """Benchmark FOC controller update() calls per second."""
        n_calls = 10000
        theta = 0.0

        def update():
            nonlocal theta
            foc_controller.update(
                ia=1.0, ib=-0.5, ic=-0.5,
                theta_e=theta, id_ref=0.0, iq_ref=5.0
            )
            theta += 0.01

        result = benchmark_model_update(foc_controller, update, n_calls=n_calls)

        print(f"\n{'='*60}")
        print(f"FOC Controller Performance")
        print(f"{'='*60}")
        print(f"  Calls/sec: {result['calls_per_sec']:,.0f}")
        print(f"{'='*60}")

        assert result["calls_per_sec"] > 10000, (
            f"FOC throughput too low: {result['calls_per_sec']:.0f}"
        )

    @pytest.mark.slow
    def test_foc_with_svpwm_throughput(self, foc_controller):
        """Benchmark FOC with SVPWM computation."""
        n_calls = 10000
        theta = 0.0

        def update():
            nonlocal theta
            da, db, dc = foc_controller.update(
                ia=1.0, ib=-0.5, ic=-0.5,
                theta_e=theta, id_ref=0.0, iq_ref=5.0
            )
            theta += 0.01
            return da, db, dc

        result = benchmark_model_update(foc_controller, update, n_calls=n_calls)

        print(f"\n  FOC + SVPWM: {result['calls_per_sec']:,.0f} calls/sec")

        assert result["calls_per_sec"] > 10000, (
            f"FOC+SVPWM throughput too low: {result['calls_per_sec']:.0f}"
        )


# ── Report Generation ────────────────────────────────────────

def generate_model_report(output_path: Path) -> Dict:
    """Generate model performance report.

    Args:
        output_path: Path to save JSON report

    Returns:
        Report dictionary
    """
    n_calls = 10000
    n_runs = 10

    # PMSM
    pmsm = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
    pmsm_result = benchmark_model_update(
        pmsm, lambda: pmsm.step_dq(vd=0.0, vq=5.0, tl=0.0, dt=50e-6),
        n_calls=n_calls, n_runs=n_runs
    )

    # Buck
    buck = BuckConverter()
    buck.set_input(duty_cycle=0.5, load_current=1.0)
    buck_result = benchmark_model_update(
        buck, lambda: buck.update(dt=1e-6),
        n_calls=n_calls, n_runs=n_runs
    )

    # Boost
    boost = BoostConverter()
    boost.set_input(duty_cycle=0.6, load_current=0.5)
    boost_result = benchmark_model_update(
        boost, lambda: boost.update(dt=1e-6),
        n_calls=n_calls, n_runs=n_runs
    )

    # FOC
    foc = FOCController(kp_id=5.0, ki_id=500.0, kp_iq=5.0, ki_iq=500.0, ts=50e-6, v_bus=48.0)
    theta_ref = [0.0]
    def foc_update():
        foc.update(ia=1.0, ib=-0.5, ic=-0.5, theta_e=theta_ref[0], id_ref=0.0, iq_ref=5.0)
        theta_ref[0] += 0.01
    foc_result = benchmark_model_update(foc, foc_update, n_calls=n_calls, n_runs=n_runs)

    report = {
        "test_name": "Model Performance Benchmark",
        "n_calls": n_calls,
        "n_runs": n_runs,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "models": {
            "pmsm": {
                "calls_per_sec": round(pmsm_result["calls_per_sec"]),
                "mean_ms": round(pmsm_result["mean_time"] * 1000, 2),
            },
            "buck_converter": {
                "calls_per_sec": round(buck_result["calls_per_sec"]),
                "mean_ms": round(buck_result["mean_time"] * 1000, 2),
            },
            "boost_converter": {
                "calls_per_sec": round(boost_result["calls_per_sec"]),
                "mean_ms": round(boost_result["mean_time"] * 1000, 2),
            },
            "foc_controller": {
                "calls_per_sec": round(foc_result["calls_per_sec"]),
                "mean_ms": round(foc_result["mean_time"] * 1000, 2),
            },
        },
        "target_calls_per_sec": 10000,
        "all_passed": all(
            m["calls_per_sec"] > 10000
            for m in [pmsm_result, buck_result, boost_result, foc_result]
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report


if __name__ == "__main__":
    report_path = Path(__file__).parent.parent.parent / ".sisyphus" / "evidence" / "task-23-model-report.json"
    report = generate_model_report(report_path)
    print(f"\nReport saved to: {report_path}")
    for name, data in report["models"].items():
        print(f"  {name}: {data['calls_per_sec']:,} calls/sec")
