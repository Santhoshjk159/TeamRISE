# ============================================================================
# Pareto Visualization & Analysis Utilities
# ============================================================================
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ParetoAnalyzer:
    """
    Pareto front analysis and visualization data generation.
    Generates data structures for Pareto front plots, trade-off analysis,
    and solution space exploration.
    """

    def __init__(self):
        pass

    def analyze_pareto_front(
        self,
        solutions: List[Dict],
        objective_names: List[str],
        minimize: Optional[List[bool]] = None,
    ) -> Dict:
        """
        Analyze a Pareto front and generate visualization data.

        solutions: List of dicts with objective values
        objective_names: Names of objectives
        minimize: Whether each objective is minimized (default: all True)
        """
        if not solutions or not objective_names:
            return {"status": "no_data"}

        if minimize is None:
            minimize = [True] * len(objective_names)

        # Extract objective values
        obj_matrix = np.array([
            [s.get(name, 0) for name in objective_names]
            for s in solutions
        ])

        # Find non-dominated solutions
        pareto_mask = self._compute_pareto_mask(obj_matrix, minimize)
        pareto_solutions = [
            s for s, m in zip(solutions, pareto_mask) if m
        ]

        # Compute spread and hypervolume
        pareto_matrix = obj_matrix[pareto_mask]
        spread = self._compute_spread(pareto_matrix) if len(pareto_matrix) > 1 else 0

        # Identify trade-off regions
        trade_offs = self._identify_trade_offs(
            pareto_matrix, objective_names, minimize
        )

        # Knee point detection
        knee = self._find_knee_point(pareto_matrix, minimize)

        return {
            "total_solutions": len(solutions),
            "pareto_size": sum(pareto_mask),
            "pareto_solutions": pareto_solutions,
            "spread": round(spread, 4),
            "trade_offs": trade_offs,
            "knee_point_index": int(knee) if knee is not None else None,
            "knee_point": pareto_solutions[knee] if knee is not None and knee < len(pareto_solutions) else None,
            "objective_ranges": {
                name: {
                    "min": round(float(obj_matrix[:, i].min()), 4),
                    "max": round(float(obj_matrix[:, i].max()), 4),
                    "pareto_min": round(float(pareto_matrix[:, i].min()), 4) if len(pareto_matrix) > 0 else None,
                    "pareto_max": round(float(pareto_matrix[:, i].max()), 4) if len(pareto_matrix) > 0 else None,
                }
                for i, name in enumerate(objective_names)
            },
        }

    def _compute_pareto_mask(
        self, obj_matrix: np.ndarray, minimize: List[bool]
    ) -> np.ndarray:
        """Identify non-dominated solutions."""
        n = len(obj_matrix)
        is_pareto = np.ones(n, dtype=bool)

        # Flip objectives that should be maximized
        adj_matrix = obj_matrix.copy()
        for i, mini in enumerate(minimize):
            if not mini:
                adj_matrix[:, i] = -adj_matrix[:, i]

        for i in range(n):
            if not is_pareto[i]:
                continue
            for j in range(i + 1, n):
                if not is_pareto[j]:
                    continue

                # Check if i dominates j
                if np.all(adj_matrix[i] <= adj_matrix[j]) and np.any(
                    adj_matrix[i] < adj_matrix[j]
                ):
                    is_pareto[j] = False
                # Check if j dominates i
                elif np.all(adj_matrix[j] <= adj_matrix[i]) and np.any(
                    adj_matrix[j] < adj_matrix[i]
                ):
                    is_pareto[i] = False
                    break

        return is_pareto

    def _compute_spread(self, pareto_matrix: np.ndarray) -> float:
        """Compute spread metric of the Pareto front."""
        if len(pareto_matrix) < 2:
            return 0.0

        # Normalize
        mins = pareto_matrix.min(axis=0)
        maxs = pareto_matrix.max(axis=0)
        ranges = maxs - mins + 1e-10
        normalized = (pareto_matrix - mins) / ranges

        # Compute distances between consecutive points
        sorted_idx = np.argsort(normalized[:, 0])
        sorted_points = normalized[sorted_idx]

        distances = np.sqrt(
            np.sum(np.diff(sorted_points, axis=0) ** 2, axis=1)
        )

        if len(distances) == 0:
            return 0.0

        avg_dist = np.mean(distances)
        uniformity = 1 - np.std(distances) / (avg_dist + 1e-10)

        return float(uniformity * np.sqrt(np.sum(ranges ** 2)))

    def _identify_trade_offs(
        self,
        pareto_matrix: np.ndarray,
        names: List[str],
        minimize: List[bool],
    ) -> List[Dict]:
        """Identify trade-off regions in the Pareto front."""
        if len(pareto_matrix) < 3 or len(names) < 2:
            return []

        trade_offs = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                # Correlation between objectives
                corr = np.corrcoef(pareto_matrix[:, i], pareto_matrix[:, j])[0, 1]

                trade_offs.append({
                    "objectives": [names[i], names[j]],
                    "correlation": round(float(corr), 3),
                    "relationship": (
                        "strong_conflict" if abs(corr) > 0.7
                        else "moderate_conflict" if abs(corr) > 0.4
                        else "weak_conflict" if abs(corr) > 0.2
                        else "independent"
                    ),
                })

        return trade_offs

    def _find_knee_point(
        self, pareto_matrix: np.ndarray, minimize: List[bool]
    ) -> Optional[int]:
        """Find knee point of the Pareto front using distance to line method."""
        if len(pareto_matrix) < 3:
            return 0 if len(pareto_matrix) > 0 else None

        # Normalize
        mins = pareto_matrix.min(axis=0)
        maxs = pareto_matrix.max(axis=0)
        ranges = maxs - mins + 1e-10
        normalized = (pareto_matrix - mins) / ranges

        # Sort by first objective
        sorted_idx = np.argsort(normalized[:, 0])
        sorted_points = normalized[sorted_idx]

        # Line from first to last point
        p1 = sorted_points[0]
        p2 = sorted_points[-1]
        line_vec = p2 - p1
        line_len = np.linalg.norm(line_vec)

        if line_len < 1e-10:
            return 0

        line_unit = line_vec / line_len

        # Distance from each point to the line
        distances = []
        for p in sorted_points:
            vec = p - p1
            proj_len = np.dot(vec, line_unit)
            proj = p1 + proj_len * line_unit
            dist = np.linalg.norm(p - proj)
            distances.append(dist)

        knee_local = int(np.argmax(distances))
        return int(sorted_idx[knee_local])

    def generate_plot_data(
        self,
        solutions: List[Dict],
        x_axis: str,
        y_axis: str,
        z_axis: Optional[str] = None,
        color_by: Optional[str] = None,
    ) -> Dict:
        """Generate data suitable for Pareto front plotting."""
        x_vals = [s.get(x_axis, 0) for s in solutions]
        y_vals = [s.get(y_axis, 0) for s in solutions]

        plot_data = {
            "x_axis": x_axis,
            "y_axis": y_axis,
            "x_values": [round(v, 4) for v in x_vals],
            "y_values": [round(v, 4) for v in y_vals],
            "n_points": len(solutions),
        }

        if z_axis:
            z_vals = [s.get(z_axis, 0) for s in solutions]
            plot_data["z_axis"] = z_axis
            plot_data["z_values"] = [round(v, 4) for v in z_vals]

        if color_by:
            c_vals = [s.get(color_by, 0) for s in solutions]
            plot_data["color_by"] = color_by
            plot_data["color_values"] = [round(v, 4) for v in c_vals]

        return plot_data
