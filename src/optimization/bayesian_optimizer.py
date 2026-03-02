# ============================================================================
# Bayesian Optimization Engine
# Surrogate-model based optimization for expensive objective functions
# ============================================================================
import numpy as np
from typing import Dict, List, Optional, Callable, Tuple
from scipy.optimize import minimize
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)


class BayesianOptimizer:
    """
    Bayesian Optimization using Gaussian Process surrogates.
    Efficient for optimizing expensive-to-evaluate batch processes.

    Uses Expected Improvement (EI) acquisition function.
    """

    def __init__(
        self,
        n_iter: int = 50,
        init_points: int = 10,
        seed: int = 42,
    ):
        self.n_iter = n_iter
        self.init_points = init_points
        self.rng = np.random.RandomState(seed)

        self.bounds: Dict[str, Tuple[float, float]] = {}
        self.objective_func: Optional[Callable] = None

        # History
        self.X_observed: List[np.ndarray] = []
        self.y_observed: List[float] = []
        self.best_params: Optional[Dict] = None
        self.best_score: float = -np.inf

    def set_bounds(self, bounds: Dict[str, Tuple[float, float]]):
        """Set parameter bounds."""
        self.bounds = bounds

    def set_objective(self, func: Callable):
        """Set objective function (will be maximized)."""
        self.objective_func = func

    def _initialize(self) -> List[Dict]:
        """Generate initial random points."""
        points = []
        for _ in range(self.init_points):
            point = {}
            for param, (low, high) in self.bounds.items():
                point[param] = self.rng.uniform(low, high)
            points.append(point)
        return points

    def _rbf_kernel(
        self, X1: np.ndarray, X2: np.ndarray,
        length_scale: float = 1.0, variance: float = 1.0,
    ) -> np.ndarray:
        """RBF (Squared Exponential) kernel."""
        sqdist = np.sum(X1 ** 2, axis=1).reshape(-1, 1) + \
                 np.sum(X2 ** 2, axis=1).reshape(1, -1) - \
                 2 * X1 @ X2.T
        return variance * np.exp(-0.5 * sqdist / length_scale ** 2)

    def _gp_predict(
        self, X_train: np.ndarray, y_train: np.ndarray,
        X_test: np.ndarray, noise: float = 1e-6,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Gaussian Process prediction."""
        K = self._rbf_kernel(X_train, X_train) + noise * np.eye(len(X_train))
        K_s = self._rbf_kernel(X_train, X_test)
        K_ss = self._rbf_kernel(X_test, X_test)

        try:
            L = np.linalg.cholesky(K)
            alpha = np.linalg.solve(L.T, np.linalg.solve(L, y_train))
            mu = K_s.T @ alpha

            v = np.linalg.solve(L, K_s)
            var = np.diag(K_ss - v.T @ v)
            var = np.maximum(var, 1e-10)
        except np.linalg.LinAlgError:
            # Fallback if Cholesky fails
            K_inv = np.linalg.pinv(K)
            mu = K_s.T @ K_inv @ y_train
            var = np.diag(K_ss - K_s.T @ K_inv @ K_s)
            var = np.maximum(var, 1e-10)

        return mu, var

    def _expected_improvement(
        self, X: np.ndarray, X_train: np.ndarray,
        y_train: np.ndarray, xi: float = 0.01,
    ) -> np.ndarray:
        """Expected Improvement acquisition function."""
        mu, var = self._gp_predict(X_train, y_train, X)
        sigma = np.sqrt(var)

        best_y = np.max(y_train)
        with np.errstate(divide="warn"):
            Z = (mu - best_y - xi) / (sigma + 1e-10)
            ei = (mu - best_y - xi) * norm.cdf(Z) + sigma * norm.pdf(Z)
            ei[sigma < 1e-10] = 0.0

        return ei

    def _propose_next(
        self, X_train: np.ndarray, y_train: np.ndarray
    ) -> np.ndarray:
        """Find next point to evaluate using EI maximization."""
        param_names = list(self.bounds.keys())
        n_dims = len(param_names)

        # Random candidate generation
        n_candidates = 1000
        candidates = np.zeros((n_candidates, n_dims))
        for j, param in enumerate(param_names):
            low, high = self.bounds[param]
            candidates[:, j] = self.rng.uniform(low, high, n_candidates)

        # Evaluate EI for all candidates
        ei_values = self._expected_improvement(candidates, X_train, y_train)

        # Return best candidate
        best_idx = np.argmax(ei_values)
        return candidates[best_idx]

    def optimize(self) -> Dict:
        """Run Bayesian optimization loop."""
        if not self.bounds or not self.objective_func:
            raise ValueError("Set bounds and objective function first")

        param_names = list(self.bounds.keys())
        n_dims = len(param_names)

        logger.info(
            f"Starting Bayesian Optimization: {n_dims} params, "
            f"{self.init_points} init + {self.n_iter} iterations"
        )

        # Initialization phase
        init_points = self._initialize()
        X_history = []
        y_history = []

        for point in init_points:
            try:
                score = self.objective_func(point)
                x = np.array([point[p] for p in param_names])
                X_history.append(x)
                y_history.append(score)

                if score > self.best_score:
                    self.best_score = score
                    self.best_params = point.copy()
            except Exception as e:
                logger.warning(f"Init point evaluation failed: {e}")

        X_train = np.array(X_history)
        y_train = np.array(y_history)

        # Optimization loop
        for i in range(self.n_iter):
            # Propose next point
            x_next = self._propose_next(X_train, y_train)

            # Convert to dict
            params = {
                param_names[j]: float(x_next[j])
                for j in range(n_dims)
            }

            # Evaluate
            try:
                score = self.objective_func(params)

                X_train = np.vstack([X_train, x_next.reshape(1, -1)])
                y_train = np.append(y_train, score)

                if score > self.best_score:
                    self.best_score = score
                    self.best_params = params.copy()
                    logger.info(f"Iter {i}: New best score = {score:.4f}")
            except Exception as e:
                logger.warning(f"Iteration {i} evaluation failed: {e}")

        self.X_observed = X_train.tolist()
        self.y_observed = y_train.tolist()

        logger.info(f"Bayesian Optimization complete. Best score: {self.best_score:.4f}")

        return {
            "best_params": self.best_params,
            "best_score": float(self.best_score),
            "n_evaluations": len(y_train),
            "convergence_history": y_train.tolist(),
        }
