"""Input validation utilities for simulation parameters."""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


class InputValidator:
    """Input validation for simulation parameters.
    
    This class provides methods for validating input parameters,
    including type checking, range validation, and custom validation rules.
    """
    
    @staticmethod
    def validate_numeric(value: Any, name: str, allow_none: bool = False) -> Optional[float]:
        """Validate numeric input.
        
        Args:
            value: Value to validate
            name: Parameter name for error messages
            allow_none: Whether to allow None values
            
        Returns:
            Validated float value
            
        Raises:
            TypeError: If value is not numeric
            ValueError: If value is None and not allowed
        """
        if value is None:
            if allow_none:
                return None
            raise ValueError(f"Parameter '{name}' cannot be None")
        
        if not isinstance(value, (int, float, np.integer, np.floating)):
            raise TypeError(f"Parameter '{name}' must be numeric, got {type(value)}")
        
        return float(value)
    
    @staticmethod
    def validate_range(
        value: float,
        name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> float:
        """Validate numeric range.
        
        Args:
            value: Value to validate
            name: Parameter name for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Validated value
            
        Raises:
            ValueError: If value is out of range
        """
        if min_value is not None and value < min_value:
            raise ValueError(
                f"Parameter '{name}' must be >= {min_value}, got {value}"
            )
        
        if max_value is not None and value > max_value:
            raise ValueError(
                f"Parameter '{name}' must be <= {max_value}, got {value}"
            )
        
        return value
    
    @staticmethod
    def validate_positive(value: float, name: str) -> float:
        """Validate positive number.
        
        Args:
            value: Value to validate
            name: Parameter name for error messages
            
        Returns:
            Validated value
            
        Raises:
            ValueError: If value is not positive
        """
        if value <= 0:
            raise ValueError(f"Parameter '{name}' must be positive, got {value}")
        return value
    
    @staticmethod
    def validate_non_negative(value: float, name: str) -> float:
        """Validate non-negative number.
        
        Args:
            value: Value to validate
            name: Parameter name for error messages
            
        Returns:
            Validated value
            
        Raises:
            ValueError: If value is negative
        """
        if value < 0:
            raise ValueError(f"Parameter '{name}' must be non-negative, got {value}")
        return value
    
    @staticmethod
    def validate_array(
        value: Any,
        name: str,
        shape: Optional[Tuple[int, ...]] = None,
        dtype: Optional[type] = None,
    ) -> np.ndarray:
        """Validate array input.
        
        Args:
            value: Value to validate
            name: Parameter name for error messages
            shape: Expected shape
            dtype: Expected dtype
            
        Returns:
            Validated numpy array
            
        Raises:
            TypeError: If value cannot be converted to array
            ValueError: If shape doesn't match
        """
        try:
            arr = np.asarray(value, dtype=dtype)
        except (TypeError, ValueError) as e:
            raise TypeError(f"Parameter '{name}' cannot be converted to array: {e}")
        
        if shape is not None and arr.shape != shape:
            raise ValueError(
                f"Parameter '{name}' must have shape {shape}, got {arr.shape}"
            )
        
        return arr
    
    @staticmethod
    def validate_enum(value: Any, name: str, allowed_values: List[Any]) -> Any:
        """Validate enum value.
        
        Args:
            value: Value to validate
            name: Parameter name for error messages
            allowed_values: List of allowed values
            
        Returns:
            Validated value
            
        Raises:
            ValueError: If value is not in allowed values
        """
        if value not in allowed_values:
            raise ValueError(
                f"Parameter '{name}' must be one of {allowed_values}, got {value}"
            )
        return value
    
    @staticmethod
    def validate_dict(
        value: Any,
        name: str,
        required_keys: Optional[List[str]] = None,
        optional_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Validate dictionary input.
        
        Args:
            value: Value to validate
            name: Parameter name for error messages
            required_keys: Required keys
            optional_keys: Optional keys
            
        Returns:
            Validated dictionary
            
        Raises:
            TypeError: If value is not a dictionary
            ValueError: If required keys are missing
        """
        if not isinstance(value, dict):
            raise TypeError(f"Parameter '{name}' must be a dictionary, got {type(value)}")
        
        if required_keys is not None:
            missing_keys = set(required_keys) - set(value.keys())
            if missing_keys:
                raise ValueError(
                    f"Parameter '{name}' missing required keys: {missing_keys}"
                )
        
        return value
    
    @staticmethod
    def validate_callable(value: Any, name: str) -> callable:
        """Validate callable input.
        
        Args:
            value: Value to validate
            name: Parameter name for error messages
            
        Returns:
            Validated callable
            
        Raises:
            TypeError: If value is not callable
        """
        if not callable(value):
            raise TypeError(f"Parameter '{name}' must be callable, got {type(value)}")
        return value
