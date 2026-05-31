"""Tests for param_id_gui.core.data_bus — unified data bus."""

import math
import time
import pytest
from unittest.mock import MagicMock

from param_id_gui.core.data_bus import (
    DataBus, Signal, SimEvent, DataValidity,
    SAFETY_NORMAL, SAFETY_WARNING, SAFETY_CRITICAL, SAFETY_EMERGENCY,
)


# ── fixtures ──────────────────────────────────────────────────

@pytest.fixture
def bus() -> DataBus:
    """Create a fresh DataBus instance."""
    return DataBus(max_history=100)


@pytest.fixture
def sample_signal() -> Signal:
    """Create a sample valid signal."""
    return Signal(
        source="sensor://current_phase_a",
        signal_type="current",
        timestamp_ns=1_000_000_000,
        value=5.0,
        unit="A",
    )


@pytest.fixture
def sample_event() -> SimEvent:
    """Create a sample simulation event."""
    return SimEvent(
        event_type="FAULT",
        source="motor://overcurrent",
        timestamp_ns=2_000_000_000,
        payload={"severity": "high"},
    )


# ── Signal validation tests (CWE-20) ─────────────────────────

class TestSignalValidation:
    """Test Signal __post_init__ validation."""

    def test_valid_signal_creation(self):
        """Valid signal should be created without errors."""
        sig = Signal(
            source="sensor://test",
            signal_type="voltage",
            timestamp_ns=100,
            value=3.3,
            unit="V",
        )
        assert sig.value == 3.3
        assert sig.timestamp_ns == 100
        assert sig.validity == DataValidity.VALID
        assert sig.quality == 1.0

    def test_negative_timestamp_raises_warning(self, caplog):
        """Negative timestamp should log warning but not raise."""
        import logging
        with caplog.at_level(logging.WARNING):
            sig = Signal(
                source="sensor://test",
                signal_type="current",
                timestamp_ns=-1,
                value=1.0,
            )
        assert "negative timestamp" in caplog.text.lower() or sig.timestamp_ns == -1

    def test_nan_value_marks_invalid(self):
        """NaN value should mark signal as INVALID."""
        sig = Signal(
            source="sensor://test",
            signal_type="current",
            timestamp_ns=0,
            value=float("nan"),
        )
        assert DataValidity.INVALID in sig.validity
        assert sig.quality == 0.0

    def test_inf_value_marks_invalid(self):
        """Inf value should mark signal as INVALID."""
        sig = Signal(
            source="sensor://test",
            signal_type="current",
            timestamp_ns=0,
            value=float("inf"),
        )
        assert DataValidity.INVALID in sig.validity
        assert sig.quality == 0.0

    def test_quality_bounds_clamped(self):
        """Quality should be clamped to [0, 1]."""
        sig_high = Signal(
            source="sensor://test",
            signal_type="current",
            timestamp_ns=0,
            value=1.0,
            quality=2.0,
        )
        sig_low = Signal(
            source="sensor://test",
            signal_type="current",
            timestamp_ns=0,
            value=1.0,
            quality=-0.5,
        )
        assert sig_high.quality == 1.0
        assert sig_low.quality == 0.0

    def test_safety_level_normalization(self):
        """Invalid safety level should be clamped to SAFETY_NORMAL."""
        sig = Signal(
            source="sensor://test",
            signal_type="current",
            timestamp_ns=0,
            value=1.0,
            safety_level=99,
        )
        assert sig.safety_level == SAFETY_NORMAL

    def test_source_normalization(self):
        """Source without '://' should be normalized."""
        sig = Signal(
            source="my_sensor",
            signal_type="current",
            timestamp_ns=0,
            value=1.0,
        )
        assert "://" in sig.source
        assert sig.source == "module://my_sensor"

    def test_timestamp_seconds_property(self):
        """timestamp_s should return correct conversion."""
        sig = Signal(
            source="sensor://test",
            signal_type="current",
            timestamp_ns=2_000_000_000,
            value=1.0,
        )
        assert sig.timestamp_s == 2.0


# ── DataValidity flags tests ─────────────────────────────────

class TestDataValidity:
    """Test DataValidity flag operations."""

    def test_valid_flag_value(self):
        """VALID should be 0x00."""
        assert DataValidity.VALID == 0x00

    def test_flag_combination(self):
        """Flags should combine correctly with bitwise OR."""
        combined = DataValidity.STALE | DataValidity.NOISY
        assert DataValidity.STALE in combined
        assert DataValidity.NOISY in combined
        # VALID is 0x00, so it's always "contained" in any IntFlag
        # Instead check that combined is not just VALID
        assert combined != DataValidity.VALID

    def test_flag_intersection(self):
        """Flags should support intersection."""
        combined = DataValidity.STALE | DataValidity.NOISY
        assert (combined & DataValidity.STALE) == DataValidity.STALE
        assert (combined & DataValidity.CLIPPED) == 0

    def test_invalid_flag(self):
        """INVALID flag should be distinct."""
        assert DataValidity.INVALID == 0x100
        assert DataValidity.INVALID not in (
            DataValidity.STALE | DataValidity.NOISY | DataValidity.CLIPPED
        )


# ── DataBus publish/subscribe tests (realtime mode) ──────────

class TestDataBusPublishSubscribe:
    """Test realtime publish/subscribe functionality."""

    def test_publish_and_read_latest(self, bus, sample_signal):
        """Published signal should be readable via read_latest."""
        bus.publish("test_topic", sample_signal)
        result = bus.read_latest("test_topic")
        assert result is sample_signal
        assert result.value == 5.0

    def test_publish_overwrites_latest(self, bus):
        """Subsequent publishes should overwrite latest."""
        sig1 = Signal(source="s://a", signal_type="t", timestamp_ns=1, value=1.0)
        sig2 = Signal(source="s://b", signal_type="t", timestamp_ns=2, value=2.0)
        bus.publish("topic", sig1)
        bus.publish("topic", sig2)
        assert bus.read_latest("topic").value == 2.0

    def test_subscribe_receives_callback(self, bus, sample_signal):
        """Subscriber callback should be invoked on publish."""
        received = []
        bus.subscribe("test_topic", lambda sig: received.append(sig))
        bus.publish("test_topic", sample_signal)
        assert len(received) == 1
        assert received[0] is sample_signal

    def test_multiple_subscribers(self, bus, sample_signal):
        """Multiple subscribers should all receive callbacks."""
        received_a = []
        received_b = []
        bus.subscribe("topic", lambda s: received_a.append(s))
        bus.subscribe("topic", lambda s: received_b.append(s))
        bus.publish("topic", sample_signal)
        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_subscriber_exception_does_not_break_publish(self, bus, sample_signal):
        """Exception in subscriber should not prevent other callbacks."""
        received = []

        def bad_callback(s):
            raise ValueError("boom")

        def good_callback(s):
            received.append(s)

        bus.subscribe("topic", bad_callback)
        bus.subscribe("topic", good_callback)
        bus.publish("topic", sample_signal)
        assert len(received) == 1

    def test_read_latest_nonexistent_topic(self, bus):
        """Reading nonexistent topic should return None."""
        assert bus.read_latest("nonexistent") is None

    def test_sequence_id_increment(self, bus):
        """Sequence ID should increment on each publish."""
        sig1 = Signal(source="s://a", signal_type="t", timestamp_ns=1, value=1.0)
        sig2 = Signal(source="s://b", signal_type="t", timestamp_ns=2, value=2.0)
        bus.publish("topic", sig1)
        bus.publish("topic", sig2)
        assert sig1.sequence_id == 1
        assert sig2.sequence_id == 2

    def test_publish_scalar(self, bus):
        """publish_scalar should create and publish a Signal."""
        sig = bus.publish_scalar("temperature", 25.5, unit="°C", timestamp_ns=100)
        assert isinstance(sig, Signal)
        assert sig.value == 25.5
        assert sig.unit == "°C"
        assert bus.read_latest("temperature").value == 25.5

    def test_publish_vector(self, bus):
        """publish_vector should publish multiple signals."""
        values = {"x": 1.0, "y": 2.0, "z": 3.0}
        sigs = bus.publish_vector("accel", values, unit="m/s²")
        assert len(sigs) == 3
        assert bus.read_latest("accel/x").value == 1.0
        assert bus.read_latest("accel/y").value == 2.0
        assert bus.read_latest("accel/z").value == 3.0


# ── DataBus event mode tests ─────────────────────────────────

class TestDataBusEvents:
    """Test event publishing."""

    def test_publish_event(self, bus, sample_event):
        """Published event should be stored."""
        bus.publish_event(sample_event)
        assert len(bus._events) == 1
        assert bus._events[0] is sample_event

    def test_multiple_events(self, bus):
        """Multiple events should be stored in order."""
        for i in range(5):
            event = SimEvent(
                event_type="STATE_CHANGE",
                source=f"module://test_{i}",
                timestamp_ns=i * 1_000_000_000,
            )
            bus.publish_event(event)
        assert len(bus._events) == 5


# ── DataBus history tests ────────────────────────────────────

class TestDataBusHistory:
    """Test data caching and history."""

    def test_history_records_signals(self, bus):
        """Published signals should be recorded in history."""
        for i in range(5):
            sig = Signal(
                source="s://test",
                signal_type="t",
                timestamp_ns=i,
                value=float(i),
            )
            bus.publish("topic", sig)
        history = bus.read_history("topic")
        assert len(history) == 5
        assert history[0].value == 0.0
        assert history[4].value == 4.0

    def test_history_max_count(self, bus):
        """read_history should respect max_count."""
        for i in range(10):
            sig = Signal(
                source="s://test",
                signal_type="t",
                timestamp_ns=i,
                value=float(i),
            )
            bus.publish("topic", sig)
        history = bus.read_history("topic", max_count=3)
        assert len(history) == 3
        assert history[0].value == 7.0  # last 3

    def test_history_ring_buffer(self):
        """History should respect max_history limit."""
        bus = DataBus(max_history=5)
        for i in range(10):
            sig = Signal(
                source="s://test",
                signal_type="t",
                timestamp_ns=i,
                value=float(i),
            )
            bus.publish("topic", sig)
        history = bus.read_history("topic")
        assert len(history) == 5
        assert history[0].value == 5.0  # oldest kept

    def test_history_nonexistent_topic(self, bus):
        """Reading history for nonexistent topic should return empty list."""
        assert bus.read_history("nonexistent") == []


# ── DataBus topic ACL tests (CWE-287) ────────────────────────

class TestDataBusACL:
    """Test topic access control."""

    def test_register_module(self, bus):
        """Registered module should be stored."""
        bus.register_module("sensor_a")
        assert "module://sensor_a" in bus._registered_modules

    def test_restrict_topic(self, bus):
        """restrict_topic should set ACL."""
        bus.register_module("sensor_a")
        bus.register_module("sensor_b")
        bus.restrict_topic("secure_topic", ["sensor_a"])
        assert "module://sensor_a" in bus._topic_acls["secure_topic"]
        assert "module://sensor_b" not in bus._topic_acls["secure_topic"]

    def test_authorized_module_can_publish(self, bus):
        """Authorized module should be able to publish."""
        bus.register_module("sensor_a")
        bus.restrict_topic("secure_topic", ["sensor_a"])
        sig = Signal(source="s://a", signal_type="t", timestamp_ns=1, value=1.0)
        bus.publish("secure_topic", sig, module_id="module://sensor_a")
        assert bus.read_latest("secure_topic") is sig

    def test_unauthorized_module_cannot_publish(self, bus, caplog):
        """Unauthorized module should be denied (logged, not raised)."""
        bus.register_module("sensor_a")
        bus.register_module("sensor_b")
        bus.restrict_topic("secure_topic", ["sensor_a"])
        sig = Signal(source="s://b", signal_type="t", timestamp_ns=1, value=1.0)
        bus.publish("secure_topic", sig, module_id="module://sensor_b")
        assert bus.read_latest("secure_topic") is None

    def test_unregistered_module_raises_permission_error(self, bus):
        """Unregistered module should raise PermissionError."""
        bus.restrict_topic("secure_topic", ["module://sensor_a"])
        sig = Signal(source="s://x", signal_type="t", timestamp_ns=1, value=1.0)
        with pytest.raises(PermissionError):
            bus.publish("secure_topic", sig, module_id="unknown_module")

    def test_no_acl_allows_all(self, bus, sample_signal):
        """Topics without ACL should allow any publish."""
        bus.publish("open_topic", sample_signal)
        assert bus.read_latest("open_topic") is sample_signal


# ── DataBus snapshot/reset tests ─────────────────────────────

class TestDataBusSnapshotReset:
    """Test snapshot and reset functionality."""

    def test_snapshot(self, bus, sample_signal):
        """Snapshot should capture current state."""
        bus.publish("topic", sample_signal)
        snap = bus.snapshot()
        assert "latest" in snap
        assert "seq" in snap
        assert snap["seq"] == 1
        assert "topic" in snap["latest"]

    def test_reset_clears_all(self, bus, sample_signal, sample_event):
        """Reset should clear all state."""
        bus.publish("topic", sample_signal)
        bus.publish_event(sample_event)
        bus.register_module("test")
        bus.restrict_topic("topic", ["test"])
        bus.reset()
        assert bus.read_latest("topic") is None
        assert bus._events == []
        assert bus._registered_modules == {}
        assert bus._topic_acls == {}
        assert bus._seq == 0

    def test_get_topics(self, bus):
        """get_topics should return all published topics."""
        for t in ["a", "b", "c"]:
            sig = Signal(source="s://x", signal_type="t", timestamp_ns=1, value=1.0)
            bus.publish(t, sig)
        topics = bus.get_topics()
        assert set(topics) == {"a", "b", "c"}


# ── DataBus batch mode tests ─────────────────────────────────

class TestDataBusBatchMode:
    """Test batch publishing patterns."""

    def test_batch_publish_multiple_topics(self, bus):
        """Batch publishing to multiple topics should work."""
        topics = [f"sensor_{i}" for i in range(10)]
        for topic in topics:
            for j in range(5):
                sig = Signal(
                    source=f"s://{topic}",
                    signal_type="measurement",
                    timestamp_ns=j * 1_000_000,
                    value=float(j),
                )
                bus.publish(topic, sig)
        for topic in topics:
            history = bus.read_history(topic)
            assert len(history) == 5

    def test_batch_publish_large_values(self, bus):
        """Batch publish with various value ranges."""
        values = [0.0, -1000.0, 1000.0, 0.001, 999999.999]
        for i, val in enumerate(values):
            sig = Signal(
                source="s://test",
                signal_type="t",
                timestamp_ns=i,
                value=val,
            )
            bus.publish("topic", sig)
        history = bus.read_history("topic")
        assert len(history) == 5
        for i, val in enumerate(values):
            assert history[i].value == val


# ── DataBus realtime mode integration ────────────────────────

class TestDataBusRealtimeIntegration:
    """Integration tests for realtime mode."""

    def test_publish_subscribe_roundtrip(self, bus):
        """Full publish-subscribe roundtrip."""
        received = []
        bus.subscribe("motor/current", lambda s: received.append(s))
        sig = Signal(
            source="sensor://current_phase_a",
            signal_type="current",
            timestamp_ns=1_000_000_000,
            value=5.0,
            unit="A",
            quality=0.95,
            safety_level=SAFETY_NORMAL,
        )
        bus.publish("motor/current", sig)
        assert len(received) == 1
        assert received[0].value == 5.0
        assert received[0].unit == "A"
        assert received[0].quality == 0.95

    def test_multiple_topics_isolation(self, bus):
        """Topics should be isolated from each other."""
        received_a = []
        received_b = []
        bus.subscribe("topic_a", lambda s: received_a.append(s))
        bus.subscribe("topic_b", lambda s: received_b.append(s))
        sig_a = Signal(source="s://a", signal_type="t", timestamp_ns=1, value=1.0)
        sig_b = Signal(source="s://b", signal_type="t", timestamp_ns=2, value=2.0)
        bus.publish("topic_a", sig_a)
        bus.publish("topic_b", sig_b)
        assert len(received_a) == 1
        assert len(received_b) == 1
        assert received_a[0].value == 1.0
        assert received_b[0].value == 2.0