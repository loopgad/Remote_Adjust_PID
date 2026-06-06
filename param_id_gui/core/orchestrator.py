"""Simulation Orchestrator — global scheduling and coordination.

Manages:
- Global clock and multi-rate scheduling
- Model lifecycle (init → step → finalize)
- Fault injection coordination
- Checkpoint / rollback
- Energy conservation checks
"""

import logging
import math
import time
import threading
import heapq
from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from .types import SimulationState
from .clock import GlobalClock

logger = logging.getLogger(__name__)

# Module-level constants
MAX_SIMULATION_STEPS = 10_000_000
PAUSE_POLL_INTERVAL_S = 0.05
PROGRESS_REPORT_INTERVAL = 100


# ── Step Result ───────────────────────────────────────────────

@dataclass
class StepResult:
    """Result of one simulation step for a solver."""
    solver_id: str
    converged: bool = True
    error_estimate: float = 0.0
    computation_ns: int = 0


# ── Convergence Audit ─────────────────────────────────────────

@dataclass
class ConvergenceAudit:
    """Convergence quality metrics from a simulation period.

    Tracks error estimates from stepper results to detect
    potential divergence (high error = convergence issues).
    """
    max_error: float = 0.0
    avg_error: float = 0.0
    sample_count: int = 0

    @property
    def convergence_pct(self) -> float:
        """Convergence quality as percentage (100% = perfect, 0% = diverged)."""
        if self.max_error <= 0:
            return 100.0
        # Map error to 0-100%: error=0 → 100%, error≥1 → 0%
        return max(0.0, (1.0 - self.max_error) * 100.0)


# ── Orchestrator Config ──────────────────────────────────────

@dataclass
class OrchestratorConfig:
    """Orchestrator configuration."""
    dt_ns: int = 50000  # 50μs default step
    enable_energy_audit: bool = True
    energy_audit_period_steps: int = 1000
    divergence_threshold: float = 0.1  # 10% energy imbalance
    auto_step_halving: bool = True
    max_step_halving: int = 3


# ── Orchestrator ──────────────────────────────────────────────

class Orchestrator:
    """Central coordinator for multi-model simulation.

    Manages simulation lifecycle, fault injection, energy audit,
    and automatic step-size adjustment.
    """

    def __init__(self, cfg: Optional[OrchestratorConfig] = None):
        """Initialize orchestrator.

        Args:
            cfg: Orchestrator configuration (uses defaults if None)
        """
        self.cfg = cfg or OrchestratorConfig()
        self.clock = GlobalClock(dt_ns=self.cfg.dt_ns)
        self.state = SimulationState.IDLE
        self._steppers: Dict[str, Callable[[int], StepResult]] = {}
        self._initializers: Dict[str, Callable[[], None]] = {}
        self._stop_hooks: List[Callable[[], bool]] = []
        self._fault_queue: List[Tuple[int, Callable[[], None]]] = []
        self._energy_audits: deque[ConvergenceAudit] = deque(maxlen=10000)
        self._last_error_estimates: deque[float] = deque(maxlen=1000)
        self._lock = threading.Lock()

    # ── model registration ───────────────────────────────────

    def register_stepper(self, solver_id: str,
                         stepper: Callable[[int], StepResult]) -> None:
        """Register a solver stepper function.

        Args:
            solver_id: Unique solver identifier
            stepper: Function that advances solver by one step
        """
        self._steppers[solver_id] = stepper

    def register_initializer(self, solver_id: str,
                             init_fn: Callable[[], None]) -> None:
        """Register a solver initializer.

        Args:
            solver_id: Unique solver identifier
            init_fn: Function that initializes solver state
        """
        self._initializers[solver_id] = init_fn

    # ── run control ──────────────────────────────────────────

    def add_stop_condition(self, condition: Callable[[], bool]) -> None:
        """Add a stop condition.

        Args:
            condition: Function that returns True when simulation should stop
        """
        self._stop_hooks.append(condition)

    # ── fault injection ──────────────────────────────────────

    def schedule_fault(self, at_time_s: float, fault_fn: Callable[[], None]) -> None:
        """Schedule a fault injection at a specific time.

        Args:
            at_time_s: Time to inject fault (seconds)
            fault_fn: Function to execute when fault is injected
        """
        # SECURITY (CWE-754): NaN/Inf guard on time
        if math.isnan(at_time_s) or math.isinf(at_time_s) or at_time_s < 0:
            logger.warning("Invalid fault time: %s, skipping", at_time_s)
            return
        with self._lock:
            heapq.heappush(self._fault_queue, (int(at_time_s * 1e9), fault_fn))

    # ── main loop ────────────────────────────────────────────

    def _validate_sim_params(self, step_ns: int, duration_s: float) -> int:
        """Validate simulation parameters and return total steps.

        Args:
            step_ns: Simulation step in nanoseconds
            duration_s: Simulation duration in seconds

        Returns:
            Total number of simulation steps

        Raises:
            ValueError: If parameters are invalid
        """
        if step_ns <= 0 or math.isnan(step_ns) or math.isinf(step_ns):
            raise ValueError(f"Invalid step_ns: {step_ns}")
        if duration_s <= 0 or math.isnan(duration_s) or math.isinf(duration_s):
            raise ValueError(f"Invalid duration_s: {duration_s}")

        total_steps = int(duration_s * 1e9 / step_ns)
        if total_steps <= 0:
            raise ValueError(f"Simulation produces 0 steps (step_ns={step_ns}, duration_s={duration_s})")
        if total_steps > MAX_SIMULATION_STEPS:
            raise ValueError(f"Simulation exceeds 10M steps ({total_steps}), check step_ns/duration_s")
        return total_steps

    def run(self, step_ns: int, duration_s: float = 1.0,
            progress_callback: Optional[Callable[[float], None]] = None) -> List[ConvergenceAudit]:
        """Run simulation with input validation and exception handling.

        Args:
            step_ns: Simulation step in nanoseconds
            duration_s: Simulation duration in seconds
            progress_callback: Optional callback(progress_pct) called periodically

        Returns:
            List of energy audits

        Raises:
            ValueError: If step_ns or duration_s is invalid
        """
        total_steps = self._validate_sim_params(step_ns, duration_s)

        with self._lock:
            self.state = SimulationState.RUNNING

        # Initialize all models with exception safety
        for solver_id, init_fn in self._initializers.items():
            try:
                logger.debug("Initializing %s", solver_id)
                init_fn()
            except Exception:
                logger.exception("Init failed for %s, skipping", solver_id)

        current_step_ns = step_ns
        halving_count = 0

        for i in range(total_steps):
            # Pause support: spin-wait while paused
            while True:
                with self._lock:
                    if self.state != SimulationState.PAUSED:
                        break
                time.sleep(PAUSE_POLL_INTERVAL_S)
            with self._lock:
                if self.state == SimulationState.STOPPED:
                    break

            # Check stop conditions
            should_stop = False
            for hook in self._stop_hooks:
                if hook():
                    logger.info("Stop condition triggered at step %d", i)
                    should_stop = True
                    break
            if should_stop or self.clock.diverged:
                break

            # Inject scheduled faults
            self._apply_faults()

            # Step all solvers with exception safety
            all_converged = True
            max_error = 0.0
            for solver_id, stepper in self._steppers.items():
                try:
                    result = stepper(current_step_ns)
                    if not result.converged:
                        all_converged = False
                        max_error = max(max_error, result.error_estimate)
                except Exception:
                    logger.exception("Solver %s crashed at step %d", solver_id, i)
                    all_converged = False

            # Collect error estimates for energy audit
            if max_error > 0:
                self._last_error_estimates.append(max_error)

            # Divergence handling: auto step-halving
            if not all_converged and self.cfg.auto_step_halving:
                if halving_count < self.cfg.max_step_halving:
                    current_step_ns = max(1, current_step_ns // 2)
                    halving_count += 1
                    logger.warning("Step halved to %d ns (halving %d/%d)",
                                   current_step_ns, halving_count,
                                   self.cfg.max_step_halving)
                    continue
                else:
                    self.clock.mark_diverged()
                    logger.error("Simulation diverged after %d halvings",
                                 halving_count)

            # Advance clock
            self.clock.advance(current_step_ns)

            # Periodic convergence audit
            if (self.cfg.enable_energy_audit and
                    i % self.cfg.energy_audit_period_steps == 0):
                audit = self._energy_audit()
                convergence_threshold = (1.0 - self.cfg.divergence_threshold) * 100.0
                if audit.convergence_pct < convergence_threshold:
                    logger.warning("Convergence quality %.2f%% at t=%.4fs",
                                   audit.convergence_pct, self.clock.sim_time_s)

            # Progress
            if progress_callback and i % PROGRESS_REPORT_INTERVAL == 0:
                progress_callback((i + 1) / total_steps)

        if progress_callback:
            progress_callback(1.0)

        with self._lock:
            if self.state not in (SimulationState.STOPPED, SimulationState.ERROR):
                self.state = SimulationState.IDLE

        return self._energy_audits

    def _apply_faults(self) -> None:
        """Apply scheduled faults."""
        while True:
            with self._lock:
                if not self._fault_queue or self._fault_queue[0][0] > self.clock.sim_time_ns:
                    break
                _, fault_fn = heapq.heappop(self._fault_queue)
            try:
                logger.info("Injecting fault at t=%.6fs", self.clock.sim_time_s)
                fault_fn()
            except Exception:
                logger.exception("Fault injection failed at t=%.6fs",
                                 self.clock.sim_time_s)

    def _energy_audit(self) -> ConvergenceAudit:
        """Perform convergence audit.

        Aggregates error estimates from the last period of steps to detect
        potential divergence (high error = convergence issues).
        """
        audit = ConvergenceAudit()
        if self._last_error_estimates:
            audit.avg_error = sum(self._last_error_estimates) / len(self._last_error_estimates)
            audit.max_error = max(self._last_error_estimates)
            audit.sample_count = len(self._last_error_estimates)
        self._energy_audits.append(audit)  # deque(maxlen) auto-evicts oldest
        self._last_error_estimates.clear()
        return audit

    # ── threaded run (for GUI) ───────────────────────────────

    def pause(self) -> None:
        """Pause the simulation."""
        with self._lock:
            if self.state == SimulationState.RUNNING:
                self.state = SimulationState.PAUSED

    def stop(self) -> None:
        """Stop the simulation."""
        with self._lock:
            self.state = SimulationState.STOPPED

    def reset(self) -> None:
        """Reset the simulation."""
        with self._lock:
            self.state = SimulationState.IDLE
            self.clock.reset()
            self._fault_queue.clear()
            self._energy_audits.clear()

    # ── state access ─────────────────────────────────────────

    def get_state(self) -> SimulationState:
        """Get current simulation state."""
        with self._lock:
            return self.state

    def set_state(self, new_state: SimulationState) -> None:
        """Thread-safe state transition."""
        with self._lock:
            self.state = new_state

    def get_time(self) -> float:
        """Get current simulation time in seconds."""
        return self.clock.sim_time_s

    def get_step_count(self) -> int:
        """Get current step count."""
        return self.clock.step_count
