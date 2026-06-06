"""Levenberg-Marquardt optimization algorithm for parameter identification."""

from typing import Callable, List, Optional, Tuple
import numpy as np
from param_id_gui.core.types import LMConfig


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
        progress_callback: Optional[Callable[[int, float, np.ndarray], bool]] = None,
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
        converged = False
        
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
            diag_H = np.diag(H)
            diag_H = np.maximum(diag_H, 1e-12)  # Prevent zero damping
            A = H + lam * np.diag(diag_H)
            
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
                # Use actual delta after clipping for predicted reduction
                actual_delta = x_new - x
            else:
                actual_delta = delta
            
            # Compute new residuals and cost
            residuals_new = residual_func(x_new)
            cost_new = 0.5 * np.sum(residuals_new**2)
            
            # Compute actual vs predicted reduction (use actual_delta)
            actual_reduction = cost - cost_new
            predicted_reduction = -0.5 * actual_delta.T @ (gradient + lam * np.diag(diag_H) @ actual_delta)

            if abs(predicted_reduction) < 1e-15:
                rho = 0
            elif predicted_reduction > 0:
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

                # Check convergence only after accepted step
                if len(self._history) > 1:
                    cost_change = abs(self._history[-2] - self._history[-1])
                    if cost_change < self.config.tolerance:
                        converged = True
                        break

                # Check gradient norm on accepted x
                gradient_norm = np.linalg.norm(gradient)
                if gradient_norm < self.config.tolerance:
                    converged = True
                    break

            # Progress callback (return False to stop early)
            if progress_callback is not None:
                if not progress_callback(iteration + 1, cost, x):
                    break
        
        # Compute final statistics
        info = {
            'iterations': self._iterations,
            'final_cost': cost,
            'cost_history': self._history.copy(),
            'converged': converged,
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
            h = eps * max(1.0, abs(x[i]))
            x_plus = x.copy()
            x_plus[i] += h
            x_minus = x.copy()
            x_minus[i] -= h
            residuals_plus = residual_func(x_plus)
            residuals_minus = residual_func(x_minus)
            J[:, i] = (residuals_plus - residuals_minus) / (2 * h)
        
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
