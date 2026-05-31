"""Levenberg-Marquardt optimization algorithm for parameter identification."""

from typing import Callable, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class LMConfig:
    """Levenberg-Marquardt configuration."""
    max_iterations: int = 1000
    tolerance: float = 1e-6
    lambda_init: float = 1e-3
    lambda_factor: float = 10.0
    lambda_min: float = 1e-10
    lambda_max: float = 1e10


class LevenbergMarquardt:
    """Levenberg-Marquardt optimization algorithm.
    
    This class implements the Levenberg-Marquardt algorithm for solving
    nonlinear least squares problems, commonly used for parameter identification.
    """
    
    def __init__(self, config: Optional[LMConfig] = None):
        """Initialize Levenberg-Marquardt optimizer.
        
        Args:
            config: LM configuration (uses defaults if None)
        """
        self.config = config or LMConfig()
        self._history: List[float] = []
        self._iterations = 0
    
    def optimize(
        self,
        residual_func: Callable[[np.ndarray], np.ndarray],
        jacobian_func: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        x0: Optional[np.ndarray] = None,
        bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    ) -> Tuple[np.ndarray, dict]:
        """Run Levenberg-Marquardt optimization.
        
        Args:
            residual_func: Function that computes residuals given parameters
            jacobian_func: Function that computes Jacobian (optional, uses finite differences)
            x0: Initial parameters
            bounds: Parameter bounds (lower, upper)
            
        Returns:
            Tuple of (optimal_parameters, optimization_info)
        """
        if x0 is None:
            raise ValueError("Initial parameters x0 must be provided")
        
        x = np.array(x0, dtype=float)
        n = len(x)
        
        # Initialize lambda
        lam = self.config.lambda_init
        
        # Compute initial residuals and cost
        residuals = residual_func(x)
        cost = 0.5 * np.sum(residuals**2)
        self._history = [cost]
        
        for iteration in range(self.config.max_iterations):
            self._iterations = iteration + 1
            
            # Compute Jacobian
            if jacobian_func is not None:
                J = jacobian_func(x)
            else:
                J = self._finite_difference_jacobian(residual_func, x)
            
            # Compute gradient and approximate Hessian
            gradient = J.T @ residuals
            H = J.T @ J
            
            # Levenberg-Marquardt step
            # (H + lambda * diag(H)) * delta = -gradient
            A = H + lam * np.diag(np.diag(H))
            
            try:
                delta = np.linalg.solve(A, -gradient)
            except np.linalg.LinAlgError:
                # Singular matrix, increase lambda
                lam *= self.config.lambda_factor
                continue
            
            # Try step
            x_new = x + delta
            
            # Apply bounds if provided
            if bounds is not None:
                x_new = np.clip(x_new, bounds[0], bounds[1])
            
            # Compute new residuals and cost
            residuals_new = residual_func(x_new)
            cost_new = 0.5 * np.sum(residuals_new**2)
            
            # Compute actual vs predicted reduction
            # predicted = 0.5 * delta.T @ (lam * np.diag(np.diag(H)) @ delta - gradient)
            actual_reduction = cost - cost_new
            predicted_reduction = -0.5 * delta.T @ (gradient + lam * np.diag(np.diag(H)) @ delta)
            
            if predicted_reduction > 0:
                rho = actual_reduction / predicted_reduction
            else:
                rho = 0
            
            # Update lambda based on reduction quality
            if rho > 0.75:
                # Good step, decrease lambda
                lam = max(lam / self.config.lambda_factor, self.config.lambda_min)
            elif rho < 0.25:
                # Poor step, increase lambda
                lam = min(lam * self.config.lambda_factor, self.config.lambda_max)
            
            # Accept or reject step
            if rho > 0:
                x = x_new
                residuals = residuals_new
                cost = cost_new
                self._history.append(cost)
            
            # Check convergence
            if len(self._history) > 1:
                cost_change = abs(self._history[-2] - self._history[-1])
                if cost_change < self.config.tolerance:
                    break
            
            # Check gradient norm
            gradient_norm = np.linalg.norm(gradient)
            if gradient_norm < self.config.tolerance:
                break
        
        # Compute final statistics
        info = {
            'iterations': self._iterations,
            'final_cost': cost,
            'cost_history': self._history.copy(),
            'converged': self._iterations < self.config.max_iterations,
        }
        
        return x, info
    
    def _finite_difference_jacobian(
        self, 
        residual_func: Callable[[np.ndarray], np.ndarray], 
        x: np.ndarray,
        eps: float = 1e-8
    ) -> np.ndarray:
        """Compute Jacobian using finite differences.
        
        Args:
            residual_func: Residual function
            x: Current parameters
            eps: Finite difference step size
            
        Returns:
            Jacobian matrix
        """
        n = len(x)
        residuals = residual_func(x)
        m = len(residuals)
        J = np.zeros((m, n))
        
        for i in range(n):
            x_plus = x.copy()
            x_plus[i] += eps
            residuals_plus = residual_func(x_plus)
            J[:, i] = (residuals_plus - residuals) / eps
        
        return J
    
    def get_history(self) -> List[float]:
        """Get optimization cost history.
        
        Returns:
            List of cost values
        """
        return self._history.copy()
    
    def get_iterations(self) -> int:
        """Get number of iterations.
        
        Returns:
            Number of iterations
        """
        return self._iterations
