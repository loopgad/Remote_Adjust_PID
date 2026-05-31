"""Numerical safety utilities for simulation."""

from typing import Any, Optional, Union
import numpy as np
import math


class NumericalSafety:
    """Numerical safety utilities for simulation.
    
    This class provides methods for detecting and handling numerical
    issues like NaN, Inf, and overflow in simulation data.
    """
    
    @staticmethod
    def check_nan(value: Any, name: str = "value") -> bool:
        """Check if value is NaN.
        
        Args:
            value: Value to check
            name: Parameter name for error messages
            
        Returns:
            True if value is NaN
            
        Raises:
            ValueError: If value is NaN
        """
        if isinstance(value, (int, float)):
            if math.isnan(value):
                raise ValueError(f"Parameter '{name}' is NaN")
        elif isinstance(value, np.ndarray):
            if np.any(np.isnan(value)):
                raise ValueError(f"Parameter '{name}' contains NaN values")
        
        return False
    
    @staticmethod
    def check_inf(value: Any, name: str = "value") -> bool:
        """Check if value is Inf.
        
        Args:
            value: Value to check
            name: Parameter name for error messages
            
        Returns:
            True if value is Inf
            
        Raises:
            ValueError: If value is Inf
        """
        if isinstance(value, (int, float)):
            if math.isinf(value):
                raise ValueError(f"Parameter '{name}' is Inf")
        elif isinstance(value, np.ndarray):
            if np.any(np.isinf(value)):
                raise ValueError(f"Parameter '{name}' contains Inf values")
        
        return False
    
    @staticmethod
    def check_nan_inf(value: Any, name: str = "value") -> bool:
        """Check if value is NaN or Inf.
        
        Args:
            value: Value to check
            name: Parameter name for error messages
            
        Returns:
            True if value is NaN or Inf
            
        Raises:
            ValueError: If value is NaN or Inf
        """
        NumericalSafety.check_nan(value, name)
        NumericalSafety.check_inf(value, name)
        return False
    
    @staticmethod
    def safe_divide(
        numerator: float,
        denominator: float,
        default: float = 0.0,
        name: str = "division",
    ) -> float:
        """Safe division with default value.
        
        Args:
            numerator: Numerator
            denominator: Denominator
            default: Default value if division is invalid
            name: Operation name for error messages
            
        Returns:
            Result of division or default value
        """
        if denominator == 0:
            return default
        
        result = numerator / denominator
        
        if math.isnan(result) or math.isinf(result):
            return default
        
        return result
    
    @staticmethod
    def safe_sqrt(value: float, name: str = "sqrt") -> float:
        """Safe square root.
        
        Args:
            value: Value to compute square root of
            name: Operation name for error messages
            
        Returns:
            Square root of value or 0.0 if value is negative
        """
        if value < 0:
            return 0.0
        
        return math.sqrt(value)
    
    @staticmethod
    def safe_log(value: float, name: str = "log") -> float:
        """Safe logarithm.
        
        Args:
            value: Value to compute logarithm of
            name: Operation name for error messages
            
        Returns:
            Logarithm of value or -inf if value is zero or negative
        """
        if value <= 0:
            return float('-inf')
        
        return math.log(value)
    
    @staticmethod
    def clamp(value: float, min_value: float, max_value: float) -> float:
        """Clamp value to range.
        
        Args:
            value: Value to clamp
            min_value: Minimum value
            max_value: Maximum value
            
        Returns:
            Clamped value
        """
        return max(min_value, min(max_value, value))
    
    @staticmethod
    def normalize(value: float, min_value: float, max_value: float) -> float:
        """Normalize value to [0, 1] range.
        
        Args:
            value: Value to normalize
            min_value: Minimum value
            max_value: Maximum value
            
        Returns:
            Normalized value
        """
        if max_value == min_value:
            return 0.0
        
        return (value - min_value) / (max_value - min_value)
    
    @staticmethod
    def denormalize(normalized: float, min_value: float, max_value: float) -> float:
        """Denormalize value from [0, 1] range.
        
        Args:
            normalized: Normalized value
            min_value: Minimum value
            max_value: Maximum value
            
        Returns:
            Denormalized value
        """
        return normalized * (max_value - min_value) + min_value
    
    @staticmethod
    def check_overflow(value: float, name: str = "value", max_value: float = 1e308) -> bool:
        """Check for potential overflow.
        
        Args:
            value: Value to check
            name: Parameter name for error messages
            max_value: Maximum safe value
            
        Returns:
            True if value is safe
            
        Raises:
            ValueError: If value may cause overflow
        """
        if abs(value) > max_value:
            raise ValueError(
                f"Parameter '{name}' may cause overflow: {value}"
            )
        return True
    
    @staticmethod
    def safe_array_operation(
        operation: callable,
        *args: Any,
        default: Optional[np.ndarray] = None,
        name: str = "operation",
    ) -> np.ndarray:
        """Safe array operation with error handling.
        
        Args:
            operation: Operation to perform
            *args: Arguments for operation
            default: Default value if operation fails
            name: Operation name for error messages
            
        Returns:
            Result of operation or default value
        """
        try:
            result = operation(*args)
            
            # Check for NaN/Inf
            if isinstance(result, np.ndarray):
                if np.any(np.isnan(result)) or np.any(np.isinf(result)):
                    return default if default is not None else np.zeros_like(result)
            
            return result
            
        except Exception as e:
            if default is not None:
                return default
            raise ValueError(f"Operation '{name}' failed: {e}")
