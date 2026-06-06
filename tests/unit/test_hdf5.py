"""Tests for HDF5 data handler."""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path

try:
    import h5py
    HDF5_AVAILABLE = True
except ImportError:
    HDF5_AVAILABLE = False

from param_id_gui.data.hdf5_handler import HDF5Handler


@pytest.mark.skipif(not HDF5_AVAILABLE, reason="h5py not installed")
class TestHDF5Handler:
    """Tests for HDF5Handler class."""

    def test_init(self, tmp_path):
        """Test handler initialization."""
        filename = str(tmp_path / "test.h5")
        handler = HDF5Handler(filename)
        assert handler.filename == filename
        assert handler._file is None

    def test_context_manager(self, tmp_path):
        """Test context manager usage."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            assert handler._file is not None
        assert handler._file is None

    def test_create_dataset(self, tmp_path):
        """Test dataset creation."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            handler.create_dataset("test_data", shape=(0,), maxshape=(None,), dtype='float64')
            assert "test_data" in handler._datasets

    def test_append_data(self, tmp_path):
        """Test data appending."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            data = np.array([1.0, 2.0, 3.0])
            handler.append_data("test_data", data)
            
            result = handler.get_data("test_data")
            np.testing.assert_array_equal(result, data)

    def test_append_multiple(self, tmp_path):
        """Test multiple data appends."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            data1 = np.array([1.0, 2.0])
            data2 = np.array([3.0, 4.0])
            
            handler.append_data("test_data", data1)
            handler.append_data("test_data", data2)
            
            result = handler.get_data("test_data")
            np.testing.assert_array_equal(result, np.array([1.0, 2.0, 3.0, 4.0]))

    def test_get_data_slice(self, tmp_path):
        """Test getting data slice."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
            handler.append_data("test_data", data)
            
            result = handler.get_data("test_data", start=1, end=4)
            np.testing.assert_array_equal(result, np.array([2.0, 3.0, 4.0]))

    def test_get_dataset_names(self, tmp_path):
        """Test getting dataset names."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            handler.append_data("data1", np.array([1.0]))
            handler.append_data("data2", np.array([2.0]))
            
            names = handler.get_dataset_names()
            assert "data1" in names
            assert "data2" in names

    def test_get_dataset_info(self, tmp_path):
        """Test getting dataset info."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            data = np.array([1.0, 2.0, 3.0])
            handler.append_data("test_data", data)
            
            info = handler.get_dataset_info("test_data")
            assert info['name'] == "test_data"
            assert info['shape'] == (3,)
            assert info['dtype'] == 'float64'
            assert info['size'] == 3

    def test_record_simulation_data(self, tmp_path):
        """Test recording simulation data."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename, buffer_size=1) as handler:
            handler.record_simulation_data(0.0, {"voltage": 12.0, "current": 1.0})
            handler.record_simulation_data(0.1, {"voltage": 12.5, "current": 1.1})
            
            data = handler.load_simulation_data()
            assert "time" in data
            assert "voltage" in data
            assert "current" in data
            assert len(data["time"]) == 2
            np.testing.assert_array_equal(data["time"], np.array([0.0, 0.1]))
            np.testing.assert_array_equal(data["voltage"], np.array([12.0, 12.5]))

    def test_load_simulation_data(self, tmp_path):
        """Test loading simulation data."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename, buffer_size=1) as handler:
            handler.record_simulation_data(0.0, {"x": 1.0})
            handler.record_simulation_data(0.1, {"x": 2.0})
            handler.record_simulation_data(0.2, {"x": 3.0})
            
            data = handler.load_simulation_data()
            assert len(data["time"]) == 3
            assert len(data["x"]) == 3

    def test_buffer_init(self, tmp_path):
        """Test buffer initialization with default and custom sizes."""
        filename = str(tmp_path / "test.h5")
        handler = HDF5Handler(filename)
        assert handler._buffer == {}
        assert handler._buffer_size == 1000
        assert handler._buffer_count == 0

        handler2 = HDF5Handler(filename, buffer_size=500)
        assert handler2._buffer_size == 500

    def test_flush_empty_buffer(self, tmp_path):
        """Test flush with empty buffer does nothing."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            handler.flush()  # Should not raise
            assert handler._buffer == {}
            assert handler._buffer_count == 0

    def test_flush_writes_buffer(self, tmp_path):
        """Test flush writes buffered data to HDF5."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            # Buffer data without auto-flush (buffer_size=1000)
            handler.record_simulation_data(0.0, {"voltage": 12.0})
            handler.record_simulation_data(0.1, {"voltage": 12.5})
            assert handler._buffer_count == 2

            # Data should not be in file yet
            data = handler.load_simulation_data()
            assert len(data) == 0  # Empty - nothing written to HDF5 yet

            # Flush
            handler.flush()
            assert handler._buffer_count == 0
            assert handler._buffer == {}

            # Now data should be in file
            data = handler.load_simulation_data()
            assert "time" in data
            assert len(data["time"]) == 2

    def test_auto_flush_on_buffer_full(self, tmp_path):
        """Test auto-flush when buffer reaches threshold."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename, buffer_size=3) as handler:
            handler.record_simulation_data(0.0, {"x": 1.0})
            handler.record_simulation_data(0.1, {"x": 2.0})
            assert handler._buffer_count == 2  # Not flushed yet

            handler.record_simulation_data(0.2, {"x": 3.0})
            assert handler._buffer_count == 0  # Auto-flushed at buffer_size=3

            data = handler.load_simulation_data()
            assert len(data["time"]) == 3

    def test_set_buffer_size(self, tmp_path):
        """Test set_buffer_size method."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            assert handler._buffer_size == 1000

            handler.set_buffer_size(500)
            assert handler._buffer_size == 500

            # Minimum is 1
            handler.set_buffer_size(0)
            assert handler._buffer_size == 1

            handler.set_buffer_size(-5)
            assert handler._buffer_size == 1

    def test_close_flushes_buffer(self, tmp_path):
        """Test that close() flushes remaining buffer data."""
        filename = str(tmp_path / "test.h5")
        handler = HDF5Handler(filename)
        handler.open()
        handler.record_simulation_data(0.0, {"x": 1.0})
        handler.record_simulation_data(0.1, {"x": 2.0})
        assert handler._buffer_count == 2

        handler.close()
        assert handler._buffer_count == 0
        assert handler._file is None

        # Reopen and verify data was flushed
        handler2 = HDF5Handler(filename, mode='r') if False else HDF5Handler(filename)
        handler2.open('r')
        data = handler2.load_simulation_data()
        assert "time" in data
        assert len(data["time"]) == 2
        handler2.close()

    def test_record_simulation_data_no_file(self, tmp_path):
        """Test record_simulation_data raises error when file not opened."""
        filename = str(tmp_path / "test.h5")
        handler = HDF5Handler(filename)
        with pytest.raises(RuntimeError, match="not opened"):
            handler.record_simulation_data(0.0, {"x": 1.0})

    def test_file_not_opened_error(self, tmp_path):
        """Test error when file not opened."""
        filename = str(tmp_path / "test.h5")
        handler = HDF5Handler(filename)
        
        with pytest.raises(RuntimeError, match="not opened"):
            handler.create_dataset("test")

    def test_dataset_not_found_error(self, tmp_path):
        """Test error when dataset not found."""
        filename = str(tmp_path / "test.h5")
        with HDF5Handler(filename) as handler:
            with pytest.raises(KeyError, match="not found"):
                handler.get_data("nonexistent")

    def test_overwrite_mode(self, tmp_path):
        """Test overwrite mode."""
        filename = str(tmp_path / "test.h5")
        
        # Create initial data
        with HDF5Handler(filename) as handler:
            handler.append_data("test", np.array([1.0, 2.0]))
        
        # Overwrite - need to open in write mode from scratch
        handler2 = HDF5Handler(filename)
        handler2.open('w')
        handler2.append_data("test", np.array([3.0, 4.0]))
        result = handler2.get_data("test")
        np.testing.assert_array_equal(result, np.array([3.0, 4.0]))
        handler2.close()


class TestHDF5HandlerNotAvailable:
    """Tests for HDF5Handler when h5py is not available."""

    def test_import_error(self, monkeypatch):
        """Test ImportError when h5py not available."""
        import param_id_gui.data.hdf5_handler as module
        monkeypatch.setattr(module, 'HDF5_AVAILABLE', False)
        
        with pytest.raises(ImportError, match="h5py is required"):
            HDF5Handler("test.h5")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
