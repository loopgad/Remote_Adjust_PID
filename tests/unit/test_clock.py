import time
import pytest
from unittest.mock import patch, MagicMock

from param_id_gui.core.clock import GlobalClock, ClockMode, ns_to_s, s_to_ns


class TestNsToS:
    def test_zero(self):
        assert ns_to_s(0) == 0.0

    def test_one_second(self):
        assert ns_to_s(1_000_000_000) == pytest.approx(1.0)

    def test_one_millisecond(self):
        assert ns_to_s(1_000_000) == pytest.approx(0.001)

    def test_one_microsecond(self):
        assert ns_to_s(1_000) == pytest.approx(0.000001)

    def test_one_nanosecond(self):
        assert ns_to_s(1) == pytest.approx(1e-9)

    def test_large_value(self):
        assert ns_to_s(5_000_000_000) == pytest.approx(5.0)

    def test_negative_value(self):
        assert ns_to_s(-1_000_000_000) == pytest.approx(-1.0)


class TestSToNs:
    def test_zero(self):
        assert s_to_ns(0.0) == 0

    def test_one_second(self):
        assert s_to_ns(1.0) == 1_000_000_000

    def test_one_millisecond(self):
        assert s_to_ns(0.001) == 1_000_000

    def test_one_microsecond(self):
        assert s_to_ns(0.000001) == 1_000

    def test_fractional_nanoseconds_truncated(self):
        result = s_to_ns(1e-10)
        assert isinstance(result, int)
        assert result == 0

    def test_large_value(self):
        assert s_to_ns(5.0) == 5_000_000_000

    def test_negative_value(self):
        assert s_to_ns(-1.0) == -1_000_000_000


class TestNsToSInverse:
    def test_roundtrip_one_second(self):
        assert s_to_ns(ns_to_s(1_000_000_000)) == 1_000_000_000

    def test_roundtrip_arbitrary(self):
        original = 123_456_789
        assert s_to_ns(ns_to_s(original)) == original


class TestClockMode:
    def test_offline_value(self):
        assert ClockMode.OFFLINE.value == "offline"

    def test_realtime_value(self):
        assert ClockMode.REALTIME.value == "realtime"

    def test_hil_value(self):
        assert ClockMode.HIL.value == "hil"

    def test_member_count(self):
        assert len(ClockMode) == 3

    def test_is_enum(self):
        from enum import Enum
        assert issubclass(ClockMode, Enum)


class TestGlobalClockInit:
    def test_default_mode(self):
        clock = GlobalClock()
        assert clock.mode == ClockMode.OFFLINE

    def test_default_rt_tolerance_ns(self):
        clock = GlobalClock()
        assert clock.rt_tolerance_ns == 1_000_000

    def test_default_dt_ns(self):
        clock = GlobalClock()
        assert clock.dt_ns == 50_000

    def test_initial_sim_time_ns(self):
        clock = GlobalClock()
        assert clock.sim_time_ns == 0

    def test_initial_step_count(self):
        clock = GlobalClock()
        assert clock.step_count == 0

    def test_initial_wall_start(self):
        clock = GlobalClock()
        assert clock._wall_start == 0.0

    def test_initial_diverged(self):
        clock = GlobalClock()
        assert clock._diverged is False

    def test_custom_mode(self):
        clock = GlobalClock(mode=ClockMode.HIL)
        assert clock.mode == ClockMode.HIL

    def test_custom_rt_tolerance_ns(self):
        clock = GlobalClock(rt_tolerance_ns=5_000_000)
        assert clock.rt_tolerance_ns == 5_000_000

    def test_custom_dt_ns(self):
        clock = GlobalClock(dt_ns=100_000)
        assert clock.dt_ns == 100_000


class TestGlobalClockProperties:
    def test_sim_time_s_initial(self):
        clock = GlobalClock()
        assert clock.sim_time_s == 0.0

    def test_sim_time_s_after_advance(self):
        clock = GlobalClock()
        clock.advance(1_000_000_000)
        assert clock.sim_time_s == pytest.approx(1.0)

    def test_dt_s_default(self):
        clock = GlobalClock()
        assert clock.dt_s == pytest.approx(0.00005)

    def test_dt_s_custom(self):
        clock = GlobalClock(dt_ns=1_000_000)
        assert clock.dt_s == pytest.approx(0.001)

    def test_wall_time_s_before_start(self):
        clock = GlobalClock()
        assert clock.wall_time_s == 0.0

    @patch("param_id_gui.core.clock.time.monotonic", return_value=100.0)
    def test_wall_time_s_after_start(self, mock_mono):
        clock = GlobalClock()
        clock.start()
        mock_mono.return_value = 101.5
        assert clock.wall_time_s == pytest.approx(1.5)

    def test_diverged_initial(self):
        clock = GlobalClock()
        assert clock.diverged is False

    def test_diverged_after_mark(self):
        clock = GlobalClock()
        clock.mark_diverged()
        assert clock.diverged is True


class TestGlobalClockStart:
    @patch("param_id_gui.core.clock.time.monotonic", return_value=50.0)
    def test_start_sets_wall_start(self, mock_mono):
        clock = GlobalClock()
        clock.start()
        assert clock._wall_start == 50.0

    @patch("param_id_gui.core.clock.time.monotonic", return_value=0.0)
    def test_start_called_twice(self, mock_mono):
        clock = GlobalClock()
        clock.start()
        mock_mono.return_value = 10.0
        clock.start()
        assert clock._wall_start == 10.0


class TestGlobalClockAdvance:
    def test_advance_positive(self):
        clock = GlobalClock()
        clock.advance(1000)
        assert clock.sim_time_ns == 1000
        assert clock.step_count == 1

    def test_advance_accumulates(self):
        clock = GlobalClock()
        clock.advance(500)
        clock.advance(300)
        assert clock.sim_time_ns == 800
        assert clock.step_count == 2

    def test_advance_zero_raises(self):
        clock = GlobalClock()
        with pytest.raises(ValueError, match="step_ns must be positive"):
            clock.advance(0)

    def test_advance_negative_raises(self):
        clock = GlobalClock()
        with pytest.raises(ValueError, match="step_ns must be positive"):
            clock.advance(-1)

    def test_advance_large_value(self):
        clock = GlobalClock()
        clock.advance(1_000_000_000_000)
        assert clock.sim_time_ns == 1_000_000_000_000

    def test_advance_does_not_call_sync_in_offline_mode(self):
        clock = GlobalClock(mode=ClockMode.OFFLINE)
        with patch.object(clock, "_sync_realtime") as mock_sync:
            clock.advance(1000)
            mock_sync.assert_not_called()

    @patch("param_id_gui.core.clock.time.monotonic", return_value=100.0)
    @patch("param_id_gui.core.clock.time.sleep")
    def test_advance_calls_sync_in_realtime_mode(self, mock_sleep, mock_mono):
        clock = GlobalClock(mode=ClockMode.REALTIME)
        clock.start()
        mock_mono.return_value = 100.0
        clock.advance(1_000_000_000)
        mock_sleep.assert_called_once()


class TestGlobalClockSyncRealtime:
    @patch("param_id_gui.core.clock.time.monotonic", return_value=100.0)
    @patch("param_id_gui.core.clock.time.sleep")
    def test_sync_sleeps_when_sim_ahead(self, mock_sleep, mock_mono):
        clock = GlobalClock(mode=ClockMode.REALTIME)
        clock.start()
        mock_mono.return_value = 100.0
        clock.advance(2_000_000_000)
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args[0][0] == pytest.approx(2.0)

    @patch("param_id_gui.core.clock.time.monotonic", return_value=100.0)
    def test_sync_no_sleep_when_wall_ahead(self, mock_mono):
        clock = GlobalClock(mode=ClockMode.REALTIME)
        clock.start()
        mock_mono.return_value = 105.0
        clock.advance(1_000_000_000)

    def test_sync_noop_when_not_started(self):
        clock = GlobalClock(mode=ClockMode.REALTIME)
        clock.advance(1_000_000_000)

    @patch("param_id_gui.core.clock.time.monotonic", return_value=100.0)
    def test_sync_logs_warning_on_divergence(self, mock_mono):
        clock = GlobalClock(mode=ClockMode.REALTIME, rt_tolerance_ns=100_000)
        clock.start()
        mock_mono.return_value = 110.0
        with patch("param_id_gui.core.clock.logger") as mock_logger:
            clock.advance(1_000)
            mock_logger.warning.assert_called_once()


class TestGlobalClockMarkDiverged:
    def test_mark_diverged_sets_flag(self):
        clock = GlobalClock()
        assert clock.diverged is False
        clock.mark_diverged()
        assert clock.diverged is True

    def test_mark_diverged_idempotent(self):
        clock = GlobalClock()
        clock.mark_diverged()
        clock.mark_diverged()
        assert clock.diverged is True


class TestGlobalClockReset:
    def test_reset_clears_sim_time(self):
        clock = GlobalClock()
        clock.advance(5_000_000_000)
        clock.reset()
        assert clock.sim_time_ns == 0

    def test_reset_clears_step_count(self):
        clock = GlobalClock()
        clock.advance(100)
        clock.advance(200)
        clock.reset()
        assert clock.step_count == 0

    def test_reset_clears_wall_start(self):
        clock = GlobalClock()
        with patch("param_id_gui.core.clock.time.monotonic", return_value=10.0):
            clock.start()
        clock.reset()
        assert clock._wall_start == 0.0

    def test_reset_clears_diverged(self):
        clock = GlobalClock()
        clock.mark_diverged()
        clock.reset()
        assert clock.diverged is False

    def test_reset_preserves_mode(self):
        clock = GlobalClock(mode=ClockMode.HIL)
        clock.reset()
        assert clock.mode == ClockMode.HIL

    def test_reset_preserves_dt_ns(self):
        clock = GlobalClock(dt_ns=999)
        clock.reset()
        assert clock.dt_ns == 999

    def test_reset_preserves_rt_tolerance(self):
        clock = GlobalClock(rt_tolerance_ns=777)
        clock.reset()
        assert clock.rt_tolerance_ns == 777


class TestGlobalClockGetTimingStats:
    def test_stats_initial(self):
        clock = GlobalClock()
        stats = clock.get_timing_stats()
        assert stats["sim_time_s"] == 0.0
        assert stats["wall_time_s"] == 0.0
        assert stats["step_count"] == 0
        assert stats["mode"] == "offline"
        assert stats["diverged"] is False

    def test_stats_keys(self):
        clock = GlobalClock()
        stats = clock.get_timing_stats()
        assert set(stats.keys()) == {
            "sim_time_s", "wall_time_s", "step_count", "mode", "diverged"
        }

    def test_stats_after_advance(self):
        clock = GlobalClock()
        clock.advance(1_000_000_000)
        clock.advance(500_000_000)
        stats = clock.get_timing_stats()
        assert stats["sim_time_s"] == pytest.approx(1.5)
        assert stats["step_count"] == 2

    def test_stats_after_diverged(self):
        clock = GlobalClock()
        clock.mark_diverged()
        stats = clock.get_timing_stats()
        assert stats["diverged"] is True

    def test_stats_mode_realtime(self):
        clock = GlobalClock(mode=ClockMode.REALTIME)
        stats = clock.get_timing_stats()
        assert stats["mode"] == "realtime"

    @patch("param_id_gui.core.clock.time.monotonic", return_value=100.0)
    def test_stats_wall_time_after_start(self, mock_mono):
        clock = GlobalClock()
        clock.start()
        mock_mono.return_value = 103.0
        stats = clock.get_timing_stats()
        assert stats["wall_time_s"] == pytest.approx(3.0)


class TestGlobalClockEdgeCases:
    def test_multiple_resets(self):
        clock = GlobalClock()
        clock.advance(1_000_000)
        clock.reset()
        clock.advance(2_000_000)
        clock.reset()
        assert clock.sim_time_ns == 0
        assert clock.step_count == 0
        assert clock.diverged is False

    def test_advance_after_reset(self):
        clock = GlobalClock()
        clock.advance(500)
        clock.reset()
        clock.advance(300)
        assert clock.sim_time_ns == 300
        assert clock.step_count == 1

    def test_start_after_reset(self):
        clock = GlobalClock()
        with patch("param_id_gui.core.clock.time.monotonic", return_value=1.0):
            clock.start()
        clock.reset()
        with patch("param_id_gui.core.clock.time.monotonic", return_value=99.0):
            clock.start()
        assert clock._wall_start == 99.0

    def test_wall_time_resets_to_zero_on_reset(self):
        clock = GlobalClock()
        with patch("param_id_gui.core.clock.time.monotonic", return_value=0.0):
            clock.start()
        clock.reset()
        assert clock.wall_time_s == 0.0

    def test_advance_one_nanosecond(self):
        clock = GlobalClock()
        clock.advance(1)
        assert clock.sim_time_ns == 1
        assert clock.sim_time_s == pytest.approx(1e-9)

    @patch("param_id_gui.core.clock.time.monotonic", return_value=0.0)
    def test_realtime_mode_sync_skipped_when_not_started(self, mock_mono):
        clock = GlobalClock(mode=ClockMode.REALTIME)
        clock._sync_realtime()
