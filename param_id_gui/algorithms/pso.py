"""Particle Swarm Optimization algorithm for parameter identification."""

from typing import Callable, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class PSOConfig:
    """Particle Swarm Optimization configuration."""
    n_particles: int = 50
    max_iterations: int = 1000
    tolerance: float = 1e-6
    w: float = 0.7298    # Inertia weight
    c1: float = 1.4962   # Cognitive parameter
    c2: float = 1.4962   # Social parameter
    w_decay: float = 0.99  # Inertia weight decay


class ParticleSwarmOptimization:
    """Particle Swarm Optimization algorithm.
    
    This class implements the Particle Swarm Optimization (PSO) algorithm
    for global optimization, commonly used for parameter identification.
    """
    
    def __init__(self, config: Optional[PSOConfig] = None):
        """Initialize PSO optimizer.
        
        Args:
            config: PSO configuration (uses defaults if None)
        """
        self.config = config or PSOConfig()
        self._history: List[float] = []
        self._iterations = 0
    
    def optimize(
        self,
        objective_func: Callable[[np.ndarray], float],
        bounds: Tuple[np.ndarray, np.ndarray],
        x0: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, dict]:
        """Run Particle Swarm Optimization.
        
        Args:
            objective_func: Function to minimize given parameters
            bounds: Parameter bounds (lower, upper)
            x0: Initial parameters (optional, used to initialize one particle)
            
        Returns:
            Tuple of (optimal_parameters, optimization_info)
        """
        lower_bounds, upper_bounds = bounds
        n_dims = len(lower_bounds)
        
        # Initialize particles
        particles = self._initialize_particles(lower_bounds, upper_bounds, n_dims, x0)
        
        # Initialize velocities
        velocities = np.zeros((self.config.n_particles, n_dims))
        
        # Initialize personal best positions and costs
        personal_best_positions = particles.copy()
        personal_best_costs = np.full(self.config.n_particles, np.inf)
        
        # Initialize global best
        global_best_position = particles[0].copy()
        global_best_cost = np.inf
        
        # Evaluate initial particles
        for i in range(self.config.n_particles):
            cost = objective_func(particles[i])
            personal_best_costs[i] = cost
            
            if cost < global_best_cost:
                global_best_cost = cost
                global_best_position = particles[i].copy()
        
        self._history = [global_best_cost]
        w = self.config.w
        
        for iteration in range(self.config.max_iterations):
            self._iterations = iteration + 1
            
            # Update particles
            for i in range(self.config.n_particles):
                # Generate random numbers
                r1 = np.random.rand(n_dims)
                r2 = np.random.rand(n_dims)
                
                # Update velocity
                velocities[i] = (
                    w * velocities[i] +
                    self.config.c1 * r1 * (personal_best_positions[i] - particles[i]) +
                    self.config.c2 * r2 * (global_best_position - particles[i])
                )
                
                # Update position
                particles[i] = particles[i] + velocities[i]
                
                # Apply bounds
                particles[i] = np.clip(particles[i], lower_bounds, upper_bounds)
                
                # Evaluate new position
                cost = objective_func(particles[i])
                
                # Update personal best
                if cost < personal_best_costs[i]:
                    personal_best_costs[i] = cost
                    personal_best_positions[i] = particles[i].copy()
                    
                    # Update global best
                    if cost < global_best_cost:
                        global_best_cost = cost
                        global_best_position = particles[i].copy()
            
            # Decay inertia weight
            w *= self.config.w_decay
            
            # Record history
            self._history.append(global_best_cost)
            
            # Check convergence
            if len(self._history) > 1:
                cost_change = abs(self._history[-2] - self._history[-1])
                if cost_change < self.config.tolerance:
                    break
        
        # Compute final statistics
        info = {
            'iterations': self._iterations,
            'final_cost': global_best_cost,
            'cost_history': self._history.copy(),
            'converged': self._iterations < self.config.max_iterations,
        }
        
        return global_best_position, info
    
    def _initialize_particles(
        self,
        lower_bounds: np.ndarray,
        upper_bounds: np.ndarray,
        n_dims: int,
        x0: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Initialize particle positions.
        
        Args:
            lower_bounds: Lower bounds for each dimension
            upper_bounds: Upper bounds for each dimension
            n_dims: Number of dimensions
            x0: Initial parameters (optional, used to initialize one particle)
            
        Returns:
            Array of particle positions
        """
        # Initialize particles randomly within bounds
        particles = np.random.uniform(
            lower_bounds, 
            upper_bounds, 
            size=(self.config.n_particles, n_dims)
        )
        
        # If x0 provided, use it for the first particle
        if x0 is not None:
            particles[0] = x0.copy()
        
        return particles
    
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
