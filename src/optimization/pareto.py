# ============================================================================
# Pareto Analysis & Visualization Utilities
# ============================================================================
import numpy as np
from typing import Dict, List, Optional, Tuple
from src.optimization.nsga2 import ParetoSolution


def compute_pareto_dominance(solutions: List[ParetoSolution]) -> List[int]:
    """Compute Pareto dominance ranking for a set of solutions."""
    n = len(solutions)
    ranks = np.zeros(n, dtype=int)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # Check if j dominates i
            obj_i = list(solutions[i].objectives.values())
            obj_j = list(solutions[j].objectives.values())
            if all(oj <= oi for oj, oi in zip(obj_j, obj_i)) and \
               any(oj < oi for oj, oi in zip(obj_j, obj_i)):
                ranks[i] += 1

    return ranks.tolist()


def hypervolume_indicator(
    pareto_front: List[ParetoSolution],
    reference_point: Optional[List[float]] = None,
) -> float:
    """
    Compute hypervolume indicator for the Pareto front.
    Measures the volume of objective space dominated by the front.
    """
    if not pareto_front:
        return 0.0

    obj_names = list(pareto_front[0].objectives.keys())
    n_obj = len(obj_names)

    # Extract objective matrix
    obj_matrix = np.array([
        [sol.objectives[name] for name in obj_names]
        for sol in pareto_front
    ])

    if reference_point is None:
        reference_point = np.max(obj_matrix, axis=0) * 1.1

    reference_point = np.array(reference_point)

    if n_obj == 2:
        return _hypervolume_2d(obj_matrix, reference_point)
    else:
        # Monte Carlo approximation for higher dimensions
        return _hypervolume_mc(obj_matrix, reference_point, n_samples=10000)


def _hypervolume_2d(points: np.ndarray, ref: np.ndarray) -> float:
    """Exact 2D hypervolume computation."""
    sorted_idx = np.argsort(points[:, 0])
    sorted_points = points[sorted_idx]

    hv = 0.0
    prev_y = ref[1]

    for i in range(len(sorted_points)):
        x = sorted_points[i, 0]
        y = sorted_points[i, 1]

        if y < prev_y:
            if i < len(sorted_points) - 1:
                next_x = sorted_points[i + 1, 0]
            else:
                next_x = ref[0]
            hv += (next_x - x) * (prev_y - y)
            prev_y = y

    return float(hv)


def _hypervolume_mc(
    points: np.ndarray, ref: np.ndarray, n_samples: int = 10000
) -> float:
    """Monte Carlo hypervolume estimation."""
    ideal = np.min(points, axis=0)
    volume = np.prod(ref - ideal)

    # Random samples in bounding box
    rng = np.random.RandomState(42)
    samples = ideal + rng.random((n_samples, len(ref))) * (ref - ideal)

    # Count dominated samples
    dominated = 0
    for sample in samples:
        if any(np.all(point <= sample) for point in points):
            dominated += 1

    return float(volume * dominated / n_samples)


def rank_solutions(
    pareto_front: List[ParetoSolution],
    weights: Dict[str, float],
) -> List[Tuple[int, float, ParetoSolution]]:
    """
    Rank Pareto solutions using weighted score method.
    Returns list of (rank, score, solution) tuples.
    """
    if not pareto_front:
        return []

    obj_names = list(pareto_front[0].objectives.keys())

    # Normalize objectives to [0, 1]
    obj_matrix = np.array([
        [sol.objectives[name] for name in obj_names]
        for sol in pareto_front
    ])

    obj_min = obj_matrix.min(axis=0)
    obj_max = obj_matrix.max(axis=0)
    obj_range = obj_max - obj_min + 1e-10
    obj_normalized = (obj_matrix - obj_min) / obj_range

    # Compute weighted scores
    scores = []
    for i, sol in enumerate(pareto_front):
        score = 0
        for j, name in enumerate(obj_names):
            w = weights.get(name, 1.0)
            # Lower normalized value is better for minimization
            score += w * (1 - obj_normalized[i, j])
        scores.append(score)

    # Sort by score (descending)
    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True,
    )

    return [
        (rank + 1, score, pareto_front[idx])
        for rank, (idx, score) in enumerate(ranked)
    ]


def pareto_front_to_dict(
    pareto_front: List[ParetoSolution],
) -> List[Dict]:
    """Convert Pareto front to serializable dictionary format."""
    return [
        {
            "variables": sol.variables,
            "objectives": sol.objectives,
            "rank": sol.rank,
            "feasible": sol.feasible,
        }
        for sol in pareto_front
    ]
