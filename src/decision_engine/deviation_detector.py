# ============================================================================
# Deviation Detector
# Multi-dimensional deviation detection with root cause analysis
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Deviation:
    """Represents a detected deviation."""
    parameter: str
    deviation_type: str       # "drift", "spike", "oscillation", "flat"
    magnitude: float           # Normalized magnitude (0-1)
    direction: str             # "high", "low", "both"
    start_time: Optional[str] = None
    duration_minutes: float = 0.0
    probable_causes: List[str] = field(default_factory=list)
    corrective_actions: List[str] = field(default_factory=list)
    impact_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "parameter": self.parameter,
            "deviation_type": self.deviation_type,
            "magnitude": round(self.magnitude, 4),
            "direction": self.direction,
            "start_time": self.start_time,
            "duration_minutes": round(self.duration_minutes, 1),
            "probable_causes": self.probable_causes,
            "corrective_actions": self.corrective_actions,
            "impact_scores": {
                k: round(v, 4) for k, v in self.impact_scores.items()
            },
        }


class DeviationDetector:
    """
    Multi-method deviation detection:
    1. Statistical deviation (Z-score, rolling stats)
    2. Trend deviation (drift detection)
    3. Pattern deviation (oscillation, flatline)
    4. Cross-parameter cascading deviation analysis
    5. Root cause inference using causal relationships
    """

    def __init__(self):
        # Causal relationships between parameters
        self.causal_graph = {
            "Temperature_C": {
                "affected_by": ["Power_Consumption_kW", "Flow_Rate_LPM"],
                "affects": ["Hardness", "Dissolution_Rate", "Drying_Efficiency"],
            },
            "Motor_Speed_RPM": {
                "affected_by": ["Power_Consumption_kW"],
                "affects": ["Vibration_mm_s", "Granulation_Quality", "Tablet_Weight"],
            },
            "Compression_Force_kN": {
                "affected_by": ["Motor_Speed_RPM"],
                "affects": ["Hardness", "Friability", "Tablet_Weight"],
            },
            "Vibration_mm_s": {
                "affected_by": ["Motor_Speed_RPM", "Compression_Force_kN"],
                "affects": ["Content_Uniformity", "Equipment_Health"],
            },
            "Power_Consumption_kW": {
                "affected_by": ["Motor_Speed_RPM", "Compression_Force_kN"],
                "affects": ["Energy_Consumption_kWh", "CO2_Emissions_kg"],
            },
        }

        # Phase-specific expected behavior
        self.phase_expectations = {
            "Granulation": {
                "Temperature_C": {"range": (40, 60), "trend": "stable"},
                "Motor_Speed_RPM": {"range": (300, 600), "trend": "stable"},
            },
            "Drying": {
                "Temperature_C": {"range": (50, 70), "trend": "stable_high"},
                "Humidity_%": {"range": (20, 40), "trend": "decreasing"},
            },
            "Compression": {
                "Compression_Force_kN": {"range": (5, 20), "trend": "stable"},
                "Motor_Speed_RPM": {"range": (400, 800), "trend": "stable"},
            },
            "Coating": {
                "Temperature_C": {"range": (40, 55), "trend": "stable"},
                "Flow_Rate_LPM": {"range": (5, 15), "trend": "stable"},
            },
        }

    def detect_deviations(
        self,
        data: pd.DataFrame,
        baseline: Optional[pd.DataFrame] = None,
        phase: Optional[str] = None,
    ) -> List[Deviation]:
        """
        Run all deviation detection methods and return consolidated results.
        """
        deviations = []
        numeric_cols = data.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            if col in ["Timestamp", "Batch_ID"]:
                continue

            series = data[col].dropna()
            if len(series) < 5:
                continue

            # 1. Statistical deviation
            stat_dev = self._statistical_deviation(col, series, baseline)
            if stat_dev:
                deviations.append(stat_dev)

            # 2. Trend deviation
            trend_dev = self._trend_deviation(col, series, phase)
            if trend_dev:
                deviations.append(trend_dev)

            # 3. Pattern deviation
            pattern_devs = self._pattern_deviation(col, series)
            deviations.extend(pattern_devs)

        # 4. Cross-parameter cascade analysis
        cascade_devs = self._cascade_analysis(data, deviations)
        deviations.extend(cascade_devs)

        # 5. Root cause inference
        self._infer_root_causes(deviations)

        # Sort by magnitude (most severe first)
        deviations.sort(key=lambda d: d.magnitude, reverse=True)

        return deviations

    def _statistical_deviation(
        self, param: str, series: pd.Series, baseline: Optional[pd.DataFrame]
    ) -> Optional[Deviation]:
        """Detect statistical deviations using Z-score approach."""
        if baseline is not None and param in baseline.columns:
            mean = baseline[param].mean()
            std = baseline[param].std()
        else:
            mean = series.mean()
            std = series.std()

        if std == 0:
            return None

        # Calculate Z-score of recent values
        recent = series.tail(min(10, len(series)))
        z_scores = np.abs((recent.values - mean) / std)
        max_z = float(np.max(z_scores))

        if max_z > 3.0:
            direction = "high" if recent.iloc[-1] > mean else "low"
            magnitude = min(max_z / 5.0, 1.0)  # Normalize to 0-1
            return Deviation(
                parameter=param,
                deviation_type="spike",
                magnitude=magnitude,
                direction=direction,
                probable_causes=[f"Abnormal {param} reading"],
                corrective_actions=[f"Check {param} sensor and actuator"],
            )
        elif max_z > 2.0:
            direction = "high" if recent.iloc[-1] > mean else "low"
            magnitude = min(max_z / 5.0, 1.0)
            return Deviation(
                parameter=param,
                deviation_type="drift",
                magnitude=magnitude,
                direction=direction,
                probable_causes=[f"{param} trending outside normal range"],
                corrective_actions=[f"Monitor {param} closely"],
            )

        return None

    def _trend_deviation(
        self, param: str, series: pd.Series, phase: Optional[str]
    ) -> Optional[Deviation]:
        """Detect trend deviations (unexpected drift)."""
        if len(series) < 10:
            return None

        # Compute linear trend
        x = np.arange(len(series))
        coeffs = np.polyfit(x, series.values, 1)
        slope = coeffs[0]
        slope_normalized = slope / max(series.std(), 1e-6)

        # Check against phase expectations
        expected_trend = "stable"
        if phase and phase in self.phase_expectations:
            if param in self.phase_expectations[phase]:
                expected_trend = self.phase_expectations[phase][param].get(
                    "trend", "stable"
                )

        is_deviation = False
        direction = "high" if slope > 0 else "low"

        if expected_trend == "stable" and abs(slope_normalized) > 0.3:
            is_deviation = True
        elif expected_trend == "decreasing" and slope_normalized > 0.1:
            is_deviation = True
            direction = "high"
        elif expected_trend == "stable_high" and slope_normalized < -0.3:
            is_deviation = True
            direction = "low"

        if is_deviation:
            magnitude = min(abs(slope_normalized), 1.0)
            return Deviation(
                parameter=param,
                deviation_type="drift",
                magnitude=magnitude,
                direction=direction,
                duration_minutes=float(len(series)),
                probable_causes=[
                    f"Unexpected {direction} trend in {param} during {phase or 'process'}"
                ],
                corrective_actions=[
                    f"Investigate root cause of {param} {'increase' if slope > 0 else 'decrease'}"
                ],
            )

        return None

    def _pattern_deviation(self, param: str, series: pd.Series) -> List[Deviation]:
        """Detect pattern abnormalities: oscillation, flatline."""
        deviations = []

        # Oscillation detection
        if len(series) > 10:
            diffs = np.diff(series.values)
            sign_changes = np.sum(np.abs(np.diff(np.sign(diffs))) > 0)
            oscillation_ratio = sign_changes / max(len(diffs) - 1, 1)

            if oscillation_ratio > 0.7:
                amplitude = (series.max() - series.min()) / max(series.std(), 1e-6)
                magnitude = min(oscillation_ratio * (amplitude / 4), 1.0)
                deviations.append(Deviation(
                    parameter=param,
                    deviation_type="oscillation",
                    magnitude=magnitude,
                    direction="both",
                    probable_causes=[
                        f"Oscillating {param} - possible control loop instability",
                        "PID tuning issues or sensor noise",
                    ],
                    corrective_actions=[
                        f"Check {param} controller tuning",
                        "Verify sensor calibration",
                        "Consider damping adjustments",
                    ],
                ))

        # Flatline detection
        if len(series) > 20:
            recent = series.tail(20)
            if recent.std() < 0.001 * abs(recent.mean() + 1e-10):
                deviations.append(Deviation(
                    parameter=param,
                    deviation_type="flat",
                    magnitude=0.6,
                    direction="both",
                    probable_causes=[
                        f"{param} sensor may be frozen or disconnected",
                        "Actuator stuck at fixed position",
                    ],
                    corrective_actions=[
                        f"Verify {param} sensor operability",
                        "Check actuator response",
                    ],
                ))

        return deviations

    def _cascade_analysis(
        self, data: pd.DataFrame, existing_deviations: List[Deviation]
    ) -> List[Deviation]:
        """Analyze cross-parameter cascading effects."""
        cascade_deviations = []
        deviated_params = {d.parameter for d in existing_deviations}

        for param in deviated_params:
            if param not in self.causal_graph:
                continue

            affected = self.causal_graph[param].get("affects", [])
            for downstream in affected:
                if downstream in deviated_params:
                    # Update impact scores on existing deviations
                    for d in existing_deviations:
                        if d.parameter == downstream:
                            d.impact_scores[param] = 0.7

        return cascade_deviations

    def _infer_root_causes(self, deviations: List[Deviation]):
        """Infer probable root causes using causal graph."""
        for dev in deviations:
            param = dev.parameter
            if param in self.causal_graph:
                upstream = self.causal_graph[param].get("affected_by", [])
                for cause in upstream:
                    cause_msg = f"Possible root cause: {cause} change"
                    if cause_msg not in dev.probable_causes:
                        dev.probable_causes.append(cause_msg)

    def get_deviation_report(self, deviations: List[Deviation]) -> Dict:
        """Generate comprehensive deviation report."""
        if not deviations:
            return {
                "status": "nominal",
                "total_deviations": 0,
                "details": [],
            }

        critical = [d for d in deviations if d.magnitude > 0.7]
        warnings = [d for d in deviations if 0.3 < d.magnitude <= 0.7]
        minor = [d for d in deviations if d.magnitude <= 0.3]

        return {
            "status": "critical" if critical else ("warning" if warnings else "minor"),
            "total_deviations": len(deviations),
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "minor_count": len(minor),
            "details": [d.to_dict() for d in deviations],
            "affected_parameters": list({d.parameter for d in deviations}),
            "deviation_types": list({d.deviation_type for d in deviations}),
            "all_corrective_actions": list({
                action
                for d in deviations
                for action in d.corrective_actions
            }),
        }
