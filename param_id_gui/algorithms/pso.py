"""Particle Swarm Optimization algorithm for parameter identification."""

from typing import Callable, List, Optional, Tuple
import numpy as np
from param_id_gui.core.types import PSOConfig


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
        # 目标函数缓存
        self._cost_cache: dict = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_max_size = 100000  # 防止内存无限增长
    
    def _cache_key(self, params: np.ndarray) -> str:
        """Generate cache key from parameter vector.
        
        Args:
            params: Parameter array to generate key for
            
        Returns:
            Cache key as bytes string
        """
        return params.tobytes()
    
    def optimize(
        self,
        objective_func: Callable[[np.ndarray], float],
        bounds: Tuple[np.ndarray, np.ndarray],
        x0: Optional[np.ndarray] = None,
        progress_callback: Optional[Callable[[int, float, np.ndarray], bool]] = None,
    ) -> Tuple[np.ndarray, dict]:
        """Run Particle Swarm Optimization.
        
        Args:
            objective_func: Function to minimize given parameters
            bounds: Parameter bounds (lower, upper)
            x0: Initial parameters (optional, used to initialize one particle)
            
        Returns:
            Tuple of (optimal_parameters, optimization_info)
        """
        # 清空缓存（避免跨次调用的陈旧数据）
        self._cost_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        
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
        
        # Evaluate initial particles (使用缓存)
        for i in range(self.config.n_particles):
            key = self._cache_key(particles[i])
            if key in self._cost_cache:
                cost = self._cost_cache[key]
                self._cache_hits += 1
            else:
                cost = objective_func(particles[i])
                if not np.isfinite(cost):
                    cost = np.inf
                self._cost_cache[key] = cost
                self._cache_misses += 1
            
            personal_best_costs[i] = cost
            
            if cost < global_best_cost:
                global_best_cost = cost
                global_best_position = particles[i].copy()
        
        self._history = [global_best_cost]
        w = self.config.w
        converged = False
        
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
                
                # Evaluate with cache
                key = self._cache_key(particles[i])
                if key in self._cost_cache:
                    cost = self._cost_cache[key]
                    self._cache_hits += 1
                else:
                    cost = objective_func(particles[i])
                    if not np.isfinite(cost):
                        cost = np.inf
                    # 限制缓存大小防止内存膨胀
                    if len(self._cost_cache) < self._cache_max_size:
                        self._cost_cache[key] = cost
                    self._cache_misses += 1
                
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
                    converged = True
                    break

            # Progress callback (return False to stop early)
            if progress_callback is not None:
                if not progress_callback(iteration + 1, global_best_cost, global_best_position):
                    break
        
        # Compute final statistics
        info = {
            'iterations': self._iterations,
            'final_cost': global_best_cost,
            'cost_history': self._history.copy(),
            'converged': converged,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
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
