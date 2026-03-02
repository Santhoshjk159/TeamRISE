# ============================================================================
# Asset Reliability Scoring
# Computes reliability scores from energy pattern analysis
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from src.energy_intelligence.spectral_analysis import SpectralAnalyzer
from src.energy_intelligence.drift_detection import SignatureDriftDetector
from src.energy_intelligence.pattern_clustering import EnergyPatternClustering
import logging

logger = logging.getLogger(__name__)


class ReliabilityScorer:
    """
    Computes comprehensive reliability scores by mapping energy
    consumption patterns to asset and process health indicators.

    Outputs:
    - Asset Reliability Score (0-100)
    - Process Inefficiency Probability (0-1)
    - Maintenance Risk Index (0-100)

    Energy patterns are mapped to:
    - Viscosity changes → motor load patterns
    - Oxygen limitations → not applicable (pharma context: drying efficiency)
    - Mechanical stress → vibration-power correlation
    - Cooling demand variation → temperature-power relationship
    """

    def __init__(self):
        self.spectral_analyzer = SpectralAnalyzer()
        self.drift_detector = SignatureDriftDetector()
        self.pattern_clusterer = EnergyPatternClustering()

        # Scoring weights
        self.reliability_weights = {
            "spectral_health": 0.25,
            "drift_stability": 0.25,
            "vibration_health": 0.20,
            "power_efficiency": 0.15,
            "pattern_consistency": 0.15,
        }

    def compute_spectral_health(
        self, ts_df: pd.DataFrame, batch_id: str
    ) -> Dict[str, float]:
        """
        Compute spectral health score from power spectrum analysis.
        Low THD and stable spectrum = healthy equipment.
        """
        batch_data = ts_df[ts_df["Batch_ID"] == batch_id]
        if len(batch_data) < 4:
            return {"spectral_health_score": 50.0, "details": "insufficient_data"}

        analysis = self.spectral_analyzer.analyze_batch_power(batch_data)
        harmonics = analysis.get("harmonics", {})
        spectral = analysis.get("spectral_features", {})

        # THD scoring (lower is better)
        thd = harmonics.get("THD_percent", 0)
        thd_score = max(0, 100 - thd * 2)

        # Spectral entropy scoring (moderate is ideal)
        entropy = spectral.get("spectral_entropy", 0)
        entropy_score = 100 - abs(entropy - 3.0) * 15  # Optimal around 3.0

        # Spectral flatness (high = noise-like, low = periodic = healthy)
        flatness = spectral.get("spectral_flatness", 0.5)
        flatness_score = (1 - flatness) * 100

        # Combined spectral health
        score = 0.4 * thd_score + 0.3 * entropy_score + 0.3 * flatness_score
        score = float(np.clip(score, 0, 100))

        return {
            "spectral_health_score": round(score, 2),
            "thd_score": round(thd_score, 2),
            "entropy_score": round(entropy_score, 2),
            "flatness_score": round(flatness_score, 2),
            "thd_percent": round(thd, 2),
        }

    def compute_vibration_health(
        self, ts_df: pd.DataFrame, batch_id: str
    ) -> Dict[str, float]:
        """
        Compute mechanical health score from vibration-power relationship.
        """
        batch_data = ts_df[ts_df["Batch_ID"] == batch_id]

        if "Vibration_mm_s" not in batch_data.columns:
            return {"vibration_health_score": 75.0, "details": "no_vibration_data"}

        vibration = batch_data["Vibration_mm_s"].values
        power = batch_data["Power_Consumption_kW"].values

        # High vibration during high power = normal
        # High vibration during low power = mechanical issue
        mask_low_power = power < np.percentile(power, 30)
        mask_high_power = power > np.percentile(power, 70)

        vib_at_low_power = vibration[mask_low_power] if mask_low_power.any() else np.array([0])
        vib_at_high_power = vibration[mask_high_power] if mask_high_power.any() else np.array([0])

        # Excessive vibration at low power indicates bearing/alignment issues
        abnormal_vib = float(np.mean(vib_at_low_power)) / (float(np.mean(vib_at_high_power)) + 1e-10)

        # Vibration trend
        if len(vibration) > 10:
            vib_trend = np.polyfit(np.arange(len(vibration)), vibration, 1)[0]
        else:
            vib_trend = 0.0

        # Overall vibration level
        vib_level = float(np.mean(vibration))
        vib_score = max(0, 100 - vib_level * 8)

        # Trend penalty (increasing vibration is bad)
        trend_penalty = max(0, vib_trend * 50)

        # Abnormal ratio penalty
        ratio_penalty = max(0, (abnormal_vib - 0.5) * 40)

        score = vib_score - trend_penalty - ratio_penalty
        score = float(np.clip(score, 0, 100))

        return {
            "vibration_health_score": round(score, 2),
            "avg_vibration": round(vib_level, 4),
            "vibration_trend": round(float(vib_trend), 6),
            "abnormal_ratio": round(float(abnormal_vib), 4),
            "mechanical_risk": "high" if score < 40 else (
                "medium" if score < 70 else "low"
            ),
        }

    def compute_power_efficiency(
        self, ts_df: pd.DataFrame, batch_id: str
    ) -> Dict[str, float]:
        """Compute power efficiency score."""
        batch_data = ts_df[ts_df["Batch_ID"] == batch_id]
        power = batch_data["Power_Consumption_kW"].values

        if len(power) == 0:
            return {"power_efficiency_score": 50.0}

        # Peak-to-average ratio (lower is more efficient)
        par = float(np.max(power) / (np.mean(power) + 1e-10))
        par_score = max(0, 100 - (par - 1.5) * 20)

        # Power factor proxy (steadier is better)
        cv = float(np.std(power) / (np.mean(power) + 1e-10))
        cv_score = max(0, 100 - cv * 80)

        # Idle power waste
        idle_threshold = np.percentile(power, 10)
        productive_threshold = np.percentile(power, 50)
        idle_ratio = float(np.mean(power < idle_threshold + 1))
        idle_score = max(0, 100 - idle_ratio * 200)

        score = 0.4 * par_score + 0.3 * cv_score + 0.3 * idle_score
        score = float(np.clip(score, 0, 100))

        return {
            "power_efficiency_score": round(score, 2),
            "peak_to_avg_ratio": round(par, 4),
            "coefficient_of_variation": round(cv, 4),
            "idle_ratio": round(idle_ratio, 4),
        }

    def compute_reliability_score(
        self, ts_df: pd.DataFrame, batch_id: str
    ) -> Dict:
        """
        Compute comprehensive Asset Reliability Score.
        Combines spectral, vibration, power efficiency, and drift analysis.
        """
        results = {}

        # Individual component scores
        spectral = self.compute_spectral_health(ts_df, batch_id)
        vibration = self.compute_vibration_health(ts_df, batch_id)
        power_eff = self.compute_power_efficiency(ts_df, batch_id)

        results["spectral_health"] = spectral
        results["vibration_health"] = vibration
        results["power_efficiency"] = power_eff

        # Drift analysis
        batch_data = ts_df[ts_df["Batch_ID"] == batch_id]
        drift = self.drift_detector.analyze_batch_drift(ts_df, batch_id)
        drift_score = 100.0
        if drift.get("overall", {}).get("overall_drift_detected", False):
            severity = drift["overall"].get("drift_severity", "normal")
            drift_score = {"critical": 20, "warning": 50, "minor": 75, "normal": 100}.get(severity, 100)

        results["drift_analysis"] = {
            "drift_stability_score": drift_score,
            "severity": drift.get("overall", {}).get("drift_severity", "normal"),
        }

        # Weighted composite score
        w = self.reliability_weights
        composite = (
            w["spectral_health"] * spectral["spectral_health_score"]
            + w["drift_stability"] * drift_score
            + w["vibration_health"] * vibration["vibration_health_score"]
            + w["power_efficiency"] * power_eff["power_efficiency_score"]
            + w["pattern_consistency"] * 75  # Default for pattern consistency
        )
        composite = float(np.clip(composite, 0, 100))

        # Derived metrics
        process_inefficiency = 1 - composite / 100
        maintenance_risk = max(0, 100 - composite)

        results["composite"] = {
            "asset_reliability_score": round(composite, 2),
            "process_inefficiency_probability": round(process_inefficiency, 4),
            "maintenance_risk_index": round(maintenance_risk, 2),
            "overall_status": (
                "critical" if composite < 40 else
                "warning" if composite < 60 else
                "good" if composite < 80 else
                "excellent"
            ),
            "recommendation": self._generate_recommendation(
                composite, spectral, vibration, power_eff, drift_score
            ),
        }

        return results

    def _generate_recommendation(
        self, composite, spectral, vibration, power_eff, drift_score
    ) -> str:
        """Generate actionable maintenance recommendation."""
        issues = []

        if spectral["spectral_health_score"] < 50:
            issues.append("High harmonic distortion detected - check motor health")
        if vibration["vibration_health_score"] < 50:
            issues.append("Abnormal vibration patterns - inspect bearings and alignment")
        if power_eff["power_efficiency_score"] < 50:
            issues.append("Low power efficiency - review load balancing and idle management")
        if drift_score < 50:
            issues.append("Significant parameter drift - calibration review needed")

        if not issues:
            return "Equipment operating within normal parameters. Continue standard monitoring."

        return "Issues detected: " + "; ".join(issues)
