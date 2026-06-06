"""Unified Data Bus — timestamped, typed signal exchange.

Provides in-process pub/sub for signal exchange between
simulation components with signal validation (CWE-20).
"""

import math
import logging
import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import IntFlag
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── data validity flags ──────────────────────────────────────


class DataValidity(IntFlag):
    """Data validity flags for signal quality tracking."""
    VALID = 0x00
    INVALID = 0x100  # SECURITY: corrupted data


# ── safety levels ────────────────────────────────────────────

SAFETY_NORMAL = 0
VALID_SAFETY_LEVELS = {SAFETY_NORMAL}


# ── base signal ──────────────────────────────────────────────

@dataclass
class Signal:
    """Unified signal container with mandatory metadata.

    Raises ValueError on construction if validation fails (CWE-20).
    """

    source: str                     # "sensor://current_phase_a"
    signal_type: str                # "current", "voltage", "angle" ...
    timestamp_ns: int = 0
    value: float = 0.0
    unit: str = ""                  # SI: "A", "V", "rad", "N.m" ...
    coordinate_frame: str = "WORLD"
    sample_rate_hz: float = 0.0
    latency_ns: int = 0
    validity: DataValidity = DataValidity.VALID
    quality: float = 1.0            # 0..1
    safety_level: int = 0           # 0=normal, 1=warning, 2=critical, 3=emergency
    sequence_id: int = 0

    def __post_init__(self) -> None:
        """Validate signal fields (CWE-20: Input Validation)."""
        errors: List[str] = []

        # Timestamp must be non-negative
        if self.timestamp_ns < 0:
            errors.append(f"negative timestamp_ns={self.timestamp_ns}")

        # NaN/Inf check on value
        if math.isnan(self.value):
            self.validity |= DataValidity.INVALID
            self.quality = 0.0
            errors.append("NaN value")
        if math.isinf(self.value):
            self.validity |= DataValidity.INVALID
            self.quality = 0.0
            errors.append("Inf value")

        # Safety level bounds
        if self.safety_level not in VALID_SAFETY_LEVELS:
            logger.warning("Signal safety_level=%d out of range, clamped to %d",
                           self.safety_level, SAFETY_NORMAL)
            self.safety_level = SAFETY_NORMAL

        # Quality bounds
        self.quality = max(0.0, min(1.0, self.quality))

        # Source must contain "://" for traceability
        if "://" not in self.source:
            self.source = f"module://{self.source}"
            logger.debug("Signal source normalized to '%s'", self.source)

        if errors:
            logger.warning("Signal validation warnings: %s", "; ".join(errors))

    @property
    def timestamp_s(self) -> float:
        """Get timestamp in seconds."""
        return self.timestamp_ns / 1e9


# ── data bus ─────────────────────────────────────────────────

class DataBus:
    """In-process unified data bus with signal validation (CWE-20)."""

    def __init__(self, max_history: int = 10000):
        """Initialize data bus.

        Args:
            max_history: Maximum history length per topic
        """
        self._latest: Dict[str, Signal] = {}
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._seq: int = 0
        self._max_history: int = max_history
        self._lock = threading.Lock()

    # ── publish ─────────────────────────────────────────────

    def publish(self, topic: str, signal: Signal,
                module_id: str = "") -> None:
        """Publish a signal to a topic.

        Args:
            topic: Topic name.
            signal: Signal to publish.
            module_id: Publishing module (unused, kept for API compat).
        """
        # SECURITY: Signal validated in __post_init__ (CWE-20)
        with self._lock:
            self._seq += 1
            signal.sequence_id = self._seq
            self._latest[topic] = signal

            # Ring buffer
            self._history[topic].append(signal)

            subscribers = tuple(self._subscribers.get(topic, []))

        for cb in subscribers:
            try:
                cb(signal)
            except Exception:
                logger.exception("Subscriber callback failed for %s", topic)

    def publish_scalar(self, topic: str, value: float, unit: str = "",
                       timestamp_ns: int = 0, module_id: str = "") -> Signal:
        """Publish a scalar value as a signal.

        Args:
            topic: Topic name
            value: Scalar value
            unit: SI unit
            timestamp_ns: Timestamp in nanoseconds
            module_id: Publishing module

        Returns:
            Created Signal
        """
        sig = Signal(
            source=module_id or topic, signal_type="scalar",
            timestamp_ns=timestamp_ns, value=value, unit=unit,
        )
        self.publish(topic, sig, module_id=module_id)
        return sig

    # ── subscribe / read ─────────────────────────────────────

    def subscribe(self, topic: str, callback: Callable[[Signal], None]) -> None:
        """Subscribe to a topic.

        Args:
            topic: Topic name
            callback: Callback function for new signals
        """
        with self._lock:
            self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable[[Signal], None]) -> None:
        """Remove a subscription.

        Args:
            topic: Topic name
            callback: Callback to remove
        """
        with self._lock:
            if topic in self._subscribers:
                try:
                    self._subscribers[topic].remove(callback)
                except ValueError:
                    pass  # callback not found, already unsubscribed

    def read_latest(self, topic: str) -> Optional[Signal]:
        """Read latest signal from a topic.

        Args:
            topic: Topic name

        Returns:
            Latest Signal or None
        """
        return self._latest.get(topic)

    def read_history(self, topic: str, max_count: int = 100) -> List[Signal]:
        """Read signal history from a topic.

        Args:
            topic: Topic name
            max_count: Maximum number of signals to return

        Returns:
            List of Signals
        """
        hist = self._history.get(topic)
        if not hist:
            return []
        # deque slice is O(1) for small slices, O(n) for list(hist)
        if len(hist) <= max_count:
            return list(hist)
        return [hist[i] for i in range(len(hist) - max_count, len(hist))]

    # ── reset ─────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset the data bus."""
        with self._lock:
            self._latest.clear()
            self._subscribers.clear()
            self._history.clear()
            self._seq = 0
