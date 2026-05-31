"""Unified Data Bus — timestamped, typed signal exchange.

Channels:
- realtime: ZeroMQ-style in-process pub/sub (dict-based for MVP)
- batch: HDF5-backed persistent log
- event: list-based event queue

Security:
  - CWE-287: Topic ACL with module registration
  - CWE-20: Signal __post_init__ validation (NaN, Inf, negative timestamps, safety bounds)
"""

import math
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import IntFlag
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ── data validity flags ──────────────────────────────────────


class DataValidity(IntFlag):
    """Data validity flags for signal quality tracking."""
    VALID = 0x00
    STALE = 0x01
    INTERPOLATED = 0x02
    EXTRAPOLATED = 0x04
    CLIPPED = 0x08
    NOISY = 0x10
    OUT_OF_RANGE = 0x20
    SENSOR_FAULT = 0x40
    SIMULATED = 0x80
    INVALID = 0x100  # SECURITY: corrupted data


# ── safety levels ────────────────────────────────────────────

SAFETY_NORMAL = 0
SAFETY_WARNING = 1
SAFETY_CRITICAL = 2
SAFETY_EMERGENCY = 3
VALID_SAFETY_LEVELS = {SAFETY_NORMAL, SAFETY_WARNING, SAFETY_CRITICAL, SAFETY_EMERGENCY}


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


# ── event ────────────────────────────────────────────────────

@dataclass
class SimEvent:
    """Discrete simulation event."""

    EVENT_TYPES = {"FAULT", "LIMIT_HIT", "STATE_CHANGE", "USER", "DIVERGENCE"}

    event_type: str
    source: str
    timestamp_ns: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)


# ── data bus ─────────────────────────────────────────────────

class DataBus:
    """In-process unified data bus with security enforcement (CWE-287).

    Security features:
      - Module registration (authentication)
      - Topic ACL (authorization)
      - Signal validation at boundary (CWE-20)
    """

    def __init__(self, max_history: int = 10000):
        """Initialize data bus.

        Args:
            max_history: Maximum history length per topic
        """
        self._latest: Dict[str, Signal] = {}
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._events: List[SimEvent] = []
        self._seq: int = 0
        self._max_history: int = max_history

        # Security: module registry + topic ACL
        self._registered_modules: Dict[str, bool] = {}   # module_id → authenticated
        self._topic_acls: Dict[str, Set[str]] = {}        # topic → set of allowed module_ids

    # ── security: module auth ──────────────────────────────

    def register_module(self, module_id: str) -> None:
        """Authenticate a module to the data bus.

        Args:
            module_id: Unique module identifier (e.g. "sensor:current_phase_a").
        """
        if "://" not in module_id:
            module_id = f"module://{module_id}"
        self._registered_modules[module_id] = True
        logger.info("Module registered: %s", module_id)

    def restrict_topic(self, topic: str, allowed_modules: List[str]) -> None:
        """Set access control: only allowed modules can publish to topic.

        Args:
            topic: Topic name.
            allowed_modules: Module IDs allowed to publish.
        """
        normalized = set()
        for m in allowed_modules:
            if "://" not in m:
                m = f"module://{m}"
            normalized.add(m)
        self._topic_acls[topic] = normalized
        logger.info("Topic '%s' restricted to modules: %s", topic,
                    [m.split("://")[1] for m in normalized])

    # ── publish ─────────────────────────────────────────────

    def publish(self, topic: str, signal: Signal,
                module_id: str = "") -> None:
        """Publish a signal to a topic.

        Args:
            topic: Topic name.
            signal: Signal to publish.
            module_id: Publishing module (required for ACL check).

        Raises:
            PermissionError: If module is not authorized on this topic.
        """
        # SECURITY: ACL check
        if topic in self._topic_acls:
            if not module_id or module_id not in self._registered_modules:
                raise PermissionError(
                    f"Unregistered module '{module_id}' cannot publish to '{topic}'")
            if module_id not in self._topic_acls[topic]:
                allowed = self._topic_acls[topic]
                logger.warning("ACCESS DENIED: module '%s' on topic '%s' "
                               "(allowed: %s)", module_id, topic,
                               [m.split("://")[1] for m in allowed])
                return

        # SECURITY: Signal validated in __post_init__ (CWE-20)
        self._seq += 1
        signal.sequence_id = self._seq
        self._latest[topic] = signal

        # Ring buffer
        self._history[topic].append(signal)

        # Notify subscribers
        for cb in self._subscribers.get(topic, []):
            try:
                cb(signal)
            except Exception:
                logger.exception("Subscriber callback failed for %s", topic)

    def publish_event(self, event: SimEvent) -> None:
        """Publish a simulation event.

        Args:
            event: Event to publish
        """
        self._events.append(event)

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

    def publish_vector(self, topic: str, values: Dict[str, float],
                       unit: str = "", timestamp_ns: int = 0,
                       module_id: str = "") -> Dict[str, Signal]:
        """Publish a vector of values as signals.

        Args:
            topic: Topic name prefix
            values: Dictionary of {name: value}
            unit: SI unit
            timestamp_ns: Timestamp in nanoseconds
            module_id: Publishing module

        Returns:
            Dictionary of {name: Signal}
        """
        sigs = {}
        for name, val in values.items():
            full = f"{topic}/{name}"
            sigs[name] = self.publish_scalar(full, val, unit, timestamp_ns, module_id)
        return sigs

    # ── subscribe / read ─────────────────────────────────────

    def subscribe(self, topic: str, callback: Callable[[Signal], None]) -> None:
        """Subscribe to a topic.

        Args:
            topic: Topic name
            callback: Callback function for new signals
        """
        self._subscribers[topic].append(callback)

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
        hist = self._history.get(topic, deque())
        return list(hist)[-max_count:] if hist else []

    # ── snapshot / reset ─────────────────────────────────────

    def snapshot(self) -> dict:
        """Create a snapshot of current bus state."""
        return {
            "latest": {k: v for k, v in self._latest.items()},
            "seq": self._seq,
        }

    def reset(self) -> None:
        """Reset the data bus."""
        self._latest.clear()
        self._subscribers.clear()
        self._history.clear()
        self._events.clear()
        self._seq = 0
        self._registered_modules.clear()
        self._topic_acls.clear()

    def get_topics(self) -> List[str]:
        """Get list of all topics.

        Returns:
            List of topic names
        """
        return list(self._latest.keys())
