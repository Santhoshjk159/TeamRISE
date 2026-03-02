# ============================================================================
# Signature Drift Detection
# Detects drift in energy consumption patterns over time
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy import stats
from collections import deque
import logging

logger = logging.getLogger(__name__)


class SignatureDriftDetector:
    """
    Detects drift in energy consumption signatures indicating:
    - Equipment degradation
    - Process parameter shifts
    - Calibration needs
    - Environmental changes

    Uses multiple detection methods:
    - CUSUM (Cumulative Sum)
    - Page-Hinkley test
    - Exponential Weighted Moving Average
    - Statistical process control (SPC)
    """

    def __init__(
        self,
        window_size: int = 20,
        drift_threshold: float = 0.15,
        cusum_threshold: float = 5.0,
    ):
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.cusum_threshold = cusum_threshold

        # Historical tracking
        self.baseline_stats: Dict[str, Dict] = {}
        self.history: deque = deque(maxlen=500)
        self.drift_events: List[Dict] = []

    def set_baseline(
        self, reference_data: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ):
        """Establish baseline statistics from reference (good) batches."""
        if columns is None:
            columns = reference_data.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            values = reference_data[col].dropna().values
            if len(values) > 0:
                self.baseline_stats[col] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "median": float(np.median(values)),
                    "q1": float(np.percentile(values, 25)),
                    "q3": float(np.percentile(values, 75)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "n_samples": len(values),
                }

    def cusum_test(
        self, values: np.ndarray, target: Optional[float] = None,
        threshold: Optional[float] = None,
    ) -> Dict:
        """
        CUSUM (Cumulative Sum) test for mean shift detection.
        Detects both upward and downward shifts.
        """
        if target is None:
            target = np.mean(values[:min(20, len(values))])
        if threshold is None:
            threshold = self.cusum_threshold

        n = len(values)
        s_pos = np.zeros(n)  # Upper CUSUM
        s_neg = np.zeros(n)  # Lower CUSUM

        # Slack parameter (typically 0.5 * shift to detect)
        k = 0.5 * np.std(values)

        drift_points = []
        for i in range(1, n):
            s_pos[i] = max(0, s_pos[i - 1] + values[i] - target - k)
            s_neg[i] = max(0, s_neg[i - 1] - values[i] + target - k)

            if s_pos[i] > threshold:
                drift_points.append({
                    "index": i,
                    "type": "upward_shift",
                    "cusum_value": float(s_pos[i]),
                })
                s_pos[i] = 0  # Reset

            if s_neg[i] > threshold:
                drift_points.append({
                    "index": i,
                    "type": "downward_shift",
                    "cusum_value": float(s_neg[i]),
                })
                s_neg[i] = 0  # Reset

        return {
            "drift_detected": len(drift_points) > 0,
            "n_drift_points": len(drift_points),
            "drift_points": drift_points,
            "final_cusum_pos": float(s_pos[-1]),
            "final_cusum_neg": float(s_neg[-1]),
        }

    def page_hinkley_test(
        self, values: np.ndarray,
        delta: float = 0.005,
        threshold: float = 50.0,
    ) -> Dict:
        """
        Page-Hinkley test for gradual drift detection.
        More sensitive to slow drifts than CUSUM.
        """
        n = len(values)
        m = np.cumsum(values) / np.arange(1, n + 1)  # Running mean
        U = np.cumsum(values - m - delta)
        M = np.minimum.accumulate(U)
        PH = U - M

        drift_idx = np.where(PH > threshold)[0]

        return {
            "drift_detected": len(drift_idx) > 0,
            "first_drift_point": int(drift_idx[0]) if len(drift_idx) > 0 else -1,
            "max_ph_statistic": float(np.max(PH)),
            "drift_severity": float(np.max(PH) / threshold) if threshold > 0 else 0,
        }

    def ewma_control(
        self, values: np.ndarray,
        lambda_param: float = 0.2,
        L: float = 3.0,
    ) -> Dict:
        """
        EWMA (Exponentially Weighted Moving Average) control chart.
        Detects small sustained shifts.
        """
        n = len(values)
        mean = np.mean(values[:min(20, n)])
        std = np.std(values[:min(20, n)])

        ewma = np.zeros(n)
        ewma[0] = mean

        for i in range(1, n):
            ewma[i] = lambda_param * values[i] + (1 - lambda_param) * ewma[i - 1]

        # Control limits
        sigma_ewma = std * np.sqrt(
            lambda_param / (2 - lambda_param)
            * (1 - (1 - lambda_param) ** (2 * np.arange(1, n + 1)))
        )
        ucl = mean + L * sigma_ewma
        lcl = mean - L * sigma_ewma

        violations = (ewma > ucl) | (ewma < lcl)

        return {
            "drift_detected": bool(violations.any()),
            "n_violations": int(violations.sum()),
            "first_violation": int(np.argmax(violations)) if violations.any() else -1,
            "ewma_final": float(ewma[-1]),
            "ucl_final": float(ucl[-1]),
            "lcl_final": float(lcl[-1]),
        }

    def detect_drift(
        self, current_values: np.ndarray, feature_name: str,
    ) -> Dict:
        """
        Comprehensive drift detection using multiple methods.
        Returns consensus result.
        """
        results = {}

        # Run all tests
        cusum = self.cusum_test(current_values)
        ph = self.page_hinkley_test(current_values)
        ewma = self.ewma_control(current_values)

        results["cusum"] = cusum
        results["page_hinkley"] = ph
        results["ewma"] = ewma

        # Consensus
        drift_votes = sum([
            cusum["drift_detected"],
            ph["drift_detected"],
            ewma["drift_detected"],
        ])

        # Compare with baseline if available
        baseline_drift = False
        if feature_name in self.baseline_stats:
            baseline = self.baseline_stats[feature_name]
            current_mean = float(np.mean(current_values))
            baseline_mean = baseline["mean"]
            baseline_std = baseline["std"] + 1e-10

            z_score = abs(current_mean - baseline_mean) / baseline_std
            baseline_drift = z_score > 2.0

            results["baseline_comparison"] = {
                "current_mean": current_mean,
                "baseline_mean": baseline_mean,
                "z_score": round(float(z_score), 4),
                "drift_from_baseline": baseline_drift,
                "pct_change": round(
                    float((current_mean - baseline_mean) / baseline_mean * 100), 2
                ),
            }

        results["consensus"] = {
            "drift_detected": drift_votes >= 2 or baseline_drift,
            "confidence": round(drift_votes / 3.0, 2),
            "severity": "high" if drift_votes == 3 else (
                "medium" if drift_votes == 2 else "low"
            ),
            "recommendation": self._get_recommendation(
                drift_votes, feature_name, current_values
            ),
        }

        # Log drift event
        if results["consensus"]["drift_detected"]:
            event = {
                "feature": feature_name,
                "severity": results["consensus"]["severity"],
                "confidence": results["consensus"]["confidence"],
                "n_samples": len(current_values),
            }
            self.drift_events.append(event)

        return results

    def _get_recommendation(
        self, drift_votes: int, feature_name: str, values: np.ndarray
    ) -> str:
        """Generate actionable recommendation based on drift analysis."""
        if drift_votes >= 3:
            return (
                f"CRITICAL: Significant drift detected in {feature_name}. "
                "Immediate investigation required. Check equipment calibration, "
                "process parameters, and raw material variability."
            )
        elif drift_votes == 2:
            return (
                f"WARNING: Moderate drift in {feature_name}. "
                "Schedule maintenance check and review recent process changes."
            )
        elif drift_votes == 1:
            return (
                f"MONITOR: Minor drift signal in {feature_name}. "
                "Continue monitoring; no immediate action required."
            )
        return "No significant drift detected."

    def analyze_batch_drift(
        self, ts_df: pd.DataFrame, batch_id: str,
        columns: Optional[List[str]] = None,
    ) -> Dict:
        """Analyze drift for all relevant signals in a batch."""
        if columns is None:
            columns = [
                "Power_Consumption_kW", "Temperature_C",
                "Vibration_mm_s", "Motor_Speed_RPM",
            ]

        batch_data = ts_df[ts_df["Batch_ID"] == batch_id]
        results = {}

        for col in columns:
            if col in batch_data.columns:
                values = batch_data[col].dropna().values
                if len(values) >= 10:
                    results[col] = self.detect_drift(values, col)

        # Overall drift assessment
        drift_count = sum(
            1 for r in results.values()
            if r.get("consensus", {}).get("drift_detected", False)
        )

        results["overall"] = {
            "signals_with_drift": drift_count,
            "total_signals_analyzed": len(results) - 1,
            "overall_drift_detected": drift_count > 0,
            "drift_severity": (
                "critical" if drift_count >= 3 else
                "warning" if drift_count >= 2 else
                "minor" if drift_count >= 1 else
                "normal"
            ),
        }

        return results
