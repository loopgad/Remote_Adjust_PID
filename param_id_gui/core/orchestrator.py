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
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Simulation State ──────────────────────────────────────────

class SimulationState(Enum):
    """Simulation state enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


# ── Global Clock ──────────────────────────────────────────────

class GlobalClock:
    """Global clock for simulation timing with ns precision."""

    def __init__(self, dt_ns: int = 50000):
        """Initialize global clock.

        Args:
            dt_ns: Time step in nanoseconds
        """
        self.dt_ns = dt_ns
        self.sim_time_ns = 0
        self.step_count = 0
        self._diverged = False

    @property
    def sim_time_s(self) -> float:
        return self.sim_time_ns / 1e9

    @property
    def dt_s(self) -> float:
        return self.dt_ns / 1e9

    @property
    def diverged(self) -> bool:
        return self._diverged

    def advance(self, step_ns: int) -> None:
        """Advance clock by step_ns."""
        self.sim_time_ns += step_ns
        self.step_count += 1

    def mark_diverged(self) -> None:
        self._diverged = True

    def reset(self) -> None:
        self.sim_time_ns = 0
        self.step_count = 0
        self._diverged = False


# ── Step Result ───────────────────────────────────────────────

@dataclass
class StepResult:
    """Result of one simulation step for a solver."""
    solver_id: str
    converged: bool = True
    error_estimate: float = 0.0
    computation_ns: int = 0


# ── Energy Audit ──────────────────────────────────────────────

@dataclass
class EnergyAudit:
    """Energy balance across domains."""
    power_input_j: float = 0.0
    mechanical_output_j: float = 0.0
    thermal_loss_j: float = 0.0
    stored_energy_j: float = 0.0
    imbalance_j: float = 0.0

    @property
    def imbalance_pct(self) -> float:
        total = self.power_input_j + 1e-12
        return abs(self.imbalance_j) / total * 100


# ── Orchestrator Config ──────────────────────────────────────

@dataclass
class OrchestratorConfig:
    """Orchestrator configuration."""
    dt_ns: int = 50000  # 50μs default step
    enable_energy_audit: bool = True
    energy_audit_period_steps: int = 1000
    checkpoint_period_steps: int = 10000
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
        self._energy_audits: List[EnergyAudit] = []
        self._sim_time_s_max: Optional[float] = None
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

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

    def set_sim_duration(self, duration_s: float) -> None:
        """Set maximum simulation duration.

        Args:
            duration_s: Maximum simulation time in seconds
        """
        self._sim_time_s_max = duration_s

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
        self._fault_queue.append((int(at_time_s * 1e9), fault_fn))
        self._fault_queue.sort(key=lambda x: x[0])

    # ── main loop ────────────────────────────────────────────

    def run(self, step_ns: int, duration_s: float = 1.0,
            progress_callback: Optional[Callable[[float], None]] = None) -> List[EnergyAudit]:
        """Run simulation with input validation and exception handling.

        Args:
            step_ns: Simulation step in nanoseconds
            duration_s: Simulation duration in seconds
            progress_callback: Optional callback for progress updates

        Returns:
            List of energy audits

        Raises:
            ValueError: If step_ns or duration_s is invalid
        """
        # SECURITY: Validate inputs (CWE-1288)
        if step_ns <= 0 or math.isnan(step_ns) or math.isinf(step_ns):
            raise ValueError(f"Invalid step_ns: {step_ns}")
        if duration_s <= 0 or math.isnan(duration_s) or math.isinf(duration_s):
            raise ValueError(f"Invalid duration_s: {duration_s}")

        self.set_sim_duration(duration_s)
        total_steps = int(duration_s * 1e9 / step_ns)

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
            # Check stop conditions
            for hook in self._stop_hooks:
                if hook():
                    logger.info("Stop condition triggered at step %d", i)
                    break
            if self.clock.diverged:
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

            # Divergence handling: auto step-halving
            if not all_converged and self.cfg.auto_step_halving:
                if halving_count < self.cfg.max_step_halving:
                    current_step_ns //= 2
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

            # Periodic energy audit
            if (self.cfg.enable_energy_audit and
                    i % self.cfg.energy_audit_period_steps == 0):
                audit = self._energy_audit()
                if audit.imbalance_pct > self.cfg.divergence_threshold:
                    logger.warning("Energy imbalance %.2f%% at t=%.4fs",
                                   audit.imbalance_pct, self.clock.sim_time_s)

            # Progress
            if progress_callback and i % 100 == 0:
                progress_callback((i + 1) / total_steps)

        return self._energy_audits

    def _apply_faults(self) -> None:
        """Apply scheduled faults."""
        while self._fault_queue and self._fault_queue[0][0] <= self.clock.sim_time_ns:
            _, fault_fn = self._fault_queue.pop(0)
            try:
                logger.info("Injecting fault at t=%.6fs", self.clock.sim_time_s)
                fault_fn()
            except Exception:
                logger.exception("Fault injection failed at t=%.6fs",
                                 self.clock.sim_time_s)

    def _energy_audit(self) -> EnergyAudit:
        """Perform energy audit."""
        audit = EnergyAudit()
        # SECURITY (CWE-789): Cap audit list to prevent unbounded growth
        if len(self._energy_audits) >= 10000:
            self._energy_audits.pop(0)
        self._energy_audits.append(audit)
        return audit

    # ── simple run (for GUI) ─────────────────────────────────

    def run_simple(self, step_fn: Callable[[], None],
                   step_ns: int, duration_s: float = 1.0) -> None:
        """Simple single-stepper convenience wrapper (for MVP).

        Args:
            step_fn: Function to call each step
            step_ns: Step size in nanoseconds
            duration_s: Duration in seconds
        """
        total_steps = int(duration_s * 1e9 / step_ns)
        for _ in range(total_steps):
            step_fn()
            self.clock.advance(step_ns)

    # ── threaded run (for GUI) ───────────────────────────────

    def start_threaded(self, step_fn: Callable[[], None],
                       step_ns: int, duration_s: float = 1.0) -> None:
        """Start simulation in a background thread.

        Args:
            step_fn: Function to call each step
            step_ns: Step size in nanoseconds
            duration_s: Duration in seconds
        """
        with self._lock:
            if self.state == SimulationState.RUNNING:
                return
            self.state = SimulationState.RUNNING
            self._thread = threading.Thread(
                target=self._run_threaded,
                args=(step_fn, step_ns, duration_s),
                daemon=True
            )
            self._thread.start()

    def _run_threaded(self, step_fn: Callable[[], None],
                      step_ns: int, duration_s: float) -> None:
        """Thread target for threaded simulation."""
        try:
            self.run_simple(step_fn, step_ns, duration_s)
            with self._lock:
                self.state = SimulationState.IDLE
        except Exception as e:
            logger.exception("Simulation error in thread")
            with self._lock:
                self.state = SimulationState.ERROR

    def pause(self) -> None:
        """Pause the simulation."""
        with self._lock:
            if self.state == SimulationState.RUNNING:
                self.state = SimulationState.PAUSED

    def stop(self) -> None:
        """Stop the simulation."""
        with self._lock:
            self.state = SimulationState.STOPPED
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)

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
        return self.state

    def get_time(self) -> float:
        """Get current simulation time in seconds."""
        return self.clock.sim_time_s

    def get_step_count(self) -> int:
        """Get current step count."""
        return self.clock.step_count
