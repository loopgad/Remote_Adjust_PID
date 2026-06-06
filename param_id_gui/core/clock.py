"""Global Clock — simulation time management.

Provides:
- Nanosecond-precision simulation time
- Wall-clock synchronization for real-time mode
- Divergence detection
"""

import time
import logging
import threading
from enum import Enum

logger = logging.getLogger(__name__)


def ns_to_s(ns: int) -> float:
    """Convert nanoseconds to seconds."""
    return ns / 1e9


def s_to_ns(s: float) -> int:
    """Convert seconds to nanoseconds."""
    return int(s * 1e9)


class ClockMode(Enum):
    """Clock operating modes."""
    OFFLINE = "offline"     # As fast as possible (simulation)
    REALTIME = "realtime"   # Wall-clock synchronized
    HIL = "hil"            # Hardware-in-the-loop (strict timing)


class GlobalClock:
    """Global simulation clock with nanosecond precision.

    Supports offline (as-fast-as-possible) and real-time modes.
    """

    def __init__(self, mode: ClockMode = ClockMode.OFFLINE,
                 rt_tolerance_ns: int = 1000000,
                 dt_ns: int = 50000):
        """Initialize global clock.

        Args:
            mode: Clock operating mode
            rt_tolerance_ns: Real-time tolerance [ns] (default: 1ms)
            dt_ns: Default time step [ns] (default: 50μs)
        """
        self.mode = mode
        self.rt_tolerance_ns = rt_tolerance_ns
        self.dt_ns = dt_ns

        self.sim_time_ns: int = 0
        self.step_count: int = 0
        self._wall_start: float = 0.0
        self._diverged: bool = False
        self._lock = threading.Lock()

    @property
    def sim_time_s(self) -> float:
        """Get simulation time in seconds."""
        with self._lock:
            return ns_to_s(self.sim_time_ns)

    @property
    def dt_s(self) -> float:
        """Get default time step in seconds."""
        return ns_to_s(self.dt_ns)

    @property
    def wall_time_s(self) -> float:
        """Get wall-clock time since start in seconds."""
        if self._wall_start == 0.0:
            return 0.0
        return time.monotonic() - self._wall_start

    @property
    def diverged(self) -> bool:
        """Check if clock has diverged."""
        with self._lock:
            return self._diverged

    def start(self) -> None:
        """Start the clock."""
        self._wall_start = time.monotonic()
        logger.info("Clock started in %s mode", self.mode.value)

    def advance(self, step_ns: int) -> None:
        """Advance simulation time by step_ns.

        Args:
            step_ns: Time step in nanoseconds (must be positive)
        """
        if step_ns <= 0:
            raise ValueError(f"step_ns must be positive, got {step_ns}")
        with self._lock:
            self.sim_time_ns += step_ns
            self.step_count += 1

        # Real-time synchronization
        if self.mode == ClockMode.REALTIME:
            self._sync_realtime()

    def _sync_realtime(self) -> None:
        """Synchronize with wall-clock time."""
        if self._wall_start == 0.0:
            return

        wall_elapsed = time.monotonic() - self._wall_start
        sim_elapsed = self.sim_time_s

        # If simulation is ahead of wall clock, sleep
        if sim_elapsed > wall_elapsed:
            sleep_time = sim_elapsed - wall_elapsed
            time.sleep(sleep_time)
        # If simulation is behind wall clock, check tolerance
        elif wall_elapsed - sim_elapsed > ns_to_s(self.rt_tolerance_ns):
            logger.warning("Clock divergence: sim=%.6fs, wall=%.6fs, diff=%.6fs",
                          sim_elapsed, wall_elapsed, wall_elapsed - sim_elapsed)

    def mark_diverged(self) -> None:
        """Mark clock as diverged."""
        with self._lock:
            self._diverged = True
        logger.error("Clock marked as diverged at t=%.6fs", self.sim_time_s)

    def reset(self) -> None:
        """Reset clock to initial state."""
        with self._lock:
            self.sim_time_ns = 0
            self.step_count = 0
            self._wall_start = 0.0
            self._diverged = False
        logger.info("Clock reset")

    def get_timing_stats(self) -> dict:
        """Get timing statistics.

        Returns:
            Dictionary of timing statistics
        """
        return {
            "sim_time_s": self.sim_time_s,
            "wall_time_s": self.wall_time_s,
            "step_count": self.step_count,
            "mode": self.mode.value,
            "diverged": self._diverged,
        }
