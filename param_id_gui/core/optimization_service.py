"""Optimization service — core layer abstraction for optimization algorithms.

Provides a unified interface for running LM and PSO algorithms,
decoupling the GUI layer from the algorithms layer.
"""

from typing import Any, Callable, Dict, Optional, Tuple
import numpy as np

from param_id_gui.algorithms.lm import LevenbergMarquardt
from param_id_gui.algorithms.pso import ParticleSwarmOptimization
from param_id_gui.core.types import LMConfig, PSOConfig


class OptimizationService:
    """Core layer service for optimization algorithms."""

    @staticmethod
    def run_lm(
        config: LMConfig,
        residual_fn: Callable[[np.ndarray], np.ndarray],
        x0: np.ndarray,
        bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None,
        progress_callback: Optional[Callable[[int, float, np.ndarray], bool]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Run Levenberg-Marquardt optimization.

        Args:
            config: LM configuration
            residual_fn: Residual function to minimize
            x0: Initial parameter guess
            bounds: Optional (lower, upper) bounds
            progress_callback: Optional callback(iteration, cost, params) -> continue

        Returns:
            Tuple of (optimized parameters, info dict)
        """
        lm = LevenbergMarquardt(config=config)
        return lm.optimize(
            residual_fn,
            x0=x0,
            bounds=bounds,
            progress_callback=progress_callback,
        )

    @staticmethod
    def run_pso(
        config: PSOConfig,
        objective_fn: Callable[[np.ndarray], float],
        bounds: Tuple[np.ndarray, np.ndarray],
        x0: Optional[np.ndarray] = None,
        progress_callback: Optional[Callable[[int, float, np.ndarray], bool]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Run Particle Swarm Optimization.

        Args:
            config: PSO configuration
            objective_fn: Objective function to minimize
            bounds: (lower, upper) bounds for each parameter
            x0: Optional initial guess
            progress_callback: Optional callback(iteration, cost, params) -> continue

        Returns:
            Tuple of (optimized parameters, info dict)
        """
        pso = ParticleSwarmOptimization(config=config)
        return pso.optimize(
            objective_fn,
            bounds=bounds,
            x0=x0,
            progress_callback=progress_callback,
        )
