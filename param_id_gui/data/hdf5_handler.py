"""HDF5 data handler for simulation data storage and playback."""

from typing import Any, Dict, List, Optional
from pathlib import Path
import numpy as np

try:
    import h5py
    HDF5_AVAILABLE = True
except ImportError:
    HDF5_AVAILABLE = False


class HDF5Handler:
    """HDF5 data handler for simulation data.
    
    This class provides methods for storing and retrieving simulation data
    in HDF5 format, including real-time recording and data playback.
    """
    
    def __init__(self, filename: str = "simulation_data.h5"):
        """Initialize HDF5 handler.
        
        Args:
            filename: HDF5 filename
        """
        if not HDF5_AVAILABLE:
            raise ImportError("h5py is required for HDF5 support. Install with: pip install h5py")
        
        self.filename = filename
        self._file: Optional[h5py.File] = None
        self._datasets: Dict[str, h5py.Dataset] = {}
    
    def open(self, mode: str = 'a'):
        """Open HDF5 file.
        
        Args:
            mode: File mode ('r' for read, 'w' for write, 'a' for append)
        """
        self._file = h5py.File(self.filename, mode)
    
    def close(self):
        """Close HDF5 file."""
        if self._file is not None:
            self._file.close()
            self._file = None
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def create_dataset(self, name: str, shape: tuple = (0,), maxshape: tuple = (None,), dtype: str = 'float64'):
        """Create a new dataset.
        
        Args:
            name: Dataset name
            shape: Initial shape
            maxshape: Maximum shape (None for unlimited)
            dtype: Data type
        """
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")
        
        self._datasets[name] = self._file.create_dataset(
            name,
            shape=shape,
            maxshape=maxshape,
            dtype=dtype,
            chunks=True,
        )
    
    def append_data(self, name: str, data: np.ndarray):
        """Append data to a dataset.
        
        Args:
            name: Dataset name
            data: Data to append
        """
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")
        
        if name not in self._datasets:
            self.create_dataset(name, shape=(0,), maxshape=(None,), dtype=data.dtype)
        
        dataset = self._datasets[name]
        current_size = dataset.shape[0]
        new_size = current_size + len(data)
        
        dataset.resize((new_size,))
        dataset[current_size:] = data
    
    def get_data(self, name: str, start: Optional[int] = None, end: Optional[int] = None) -> np.ndarray:
        """Get data from a dataset.
        
        Args:
            name: Dataset name
            start: Start index
            end: End index
            
        Returns:
            Data array
        """
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")
        
        if name not in self._file:
            raise KeyError(f"Dataset '{name}' not found")
        
        dataset = self._file[name]
        
        if start is None and end is None:
            return dataset[:]
        else:
            return dataset[start:end]
    
    def get_dataset_names(self) -> List[str]:
        """Get list of all dataset names.
        
        Returns:
            List of dataset names
        """
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")
        
        return list(self._file.keys())
    
    def get_dataset_info(self, name: str) -> Dict[str, Any]:
        """Get information about a dataset.
        
        Args:
            name: Dataset name
            
        Returns:
            Dictionary with dataset information
        """
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")
        
        if name not in self._file:
            raise KeyError(f"Dataset '{name}' not found")
        
        dataset = self._file[name]
        
        return {
            'name': name,
            'shape': dataset.shape,
            'dtype': str(dataset.dtype),
            'size': dataset.size,
        }
    
    def record_simulation_data(self, time: float, data: Dict[str, float]):
        """Record simulation data point.
        
        Args:
            time: Simulation time
            data: Dictionary of data values
        """
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")
        
        # Create time dataset if it doesn't exist
        if 'time' not in self._datasets:
            self.create_dataset('time', shape=(0,), maxshape=(None,), dtype='float64')
        
        # Append time
        self.append_data('time', np.array([time]))
        
        # Append each data value
        for key, value in data.items():
            if key not in self._datasets:
                self.create_dataset(key, shape=(0,), maxshape=(None,), dtype='float64')
            
            self.append_data(key, np.array([value]))
    
    def load_simulation_data(self) -> Dict[str, np.ndarray]:
        """Load all simulation data.
        
        Returns:
            Dictionary of data arrays
        """
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")
        
        data = {}
        for name in self.get_dataset_names():
            data[name] = self.get_data(name)
        
        return data
