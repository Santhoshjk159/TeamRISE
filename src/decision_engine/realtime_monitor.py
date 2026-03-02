# ============================================================================
# Real-Time Decision Engine
# Monitors ongoing batches and generates corrective recommendations
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class DecisionType(str, Enum):
    CORRECTION = "correction"
    ALERT = "alert"
    RECOMMENDATION = "recommendation"
    OPTIMIZATION = "optimization"


class Decision:
    """A single decision/recommendation."""

    def __init__(
        self,
        decision_type: DecisionType,
        severity: AlertSeverity,
        batch_id: str,
        message: str,
        parameters: Optional[Dict] = None,
        expected_improvement: Optional[Dict] = None,
        confidence: float = 0.0,
    ):
        self.id = f"DEC_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self.timestamp = datetime.now().isoformat()
        self.decision_type = decision_type
        self.severity = severity
        self.batch_id = batch_id
        self.message = message
        self.parameters = parameters or {}
        self.expected_improvement = expected_improvement or {}
        self.confidence = confidence
        self.action_taken = False
        self.outcome: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.decision_type.value,
            "severity": self.severity.value,
            "batch_id": self.batch_id,
            "message": self.message,
            "parameters": self.parameters,
            "expected_improvement": self.expected_improvement,
            "confidence": round(self.confidence, 4),
            "action_taken": self.action_taken,
            "outcome": self.outcome,
        }


class RealTimeDecisionEngine:
    """
    Real-time decision engine that:
    1. Monitors incoming batch data against golden signature
    2. Detects deviations in quality, energy, and process parameters
    3. Generates corrective actions with confidence scores
    4. Provides mid-batch parameter adjustment recommendations
    5. Tracks decision outcomes for continuous improvement

    Decision categories:
    - Process corrections (temperature, pressure, speed adjustments)
    - Energy optimization (load shifting, power management)
    - Quality interventions (parameter adjustments for spec compliance)
    - Safety alerts (out-of-bounds conditions)
    """

    def __init__(self, predictor=None, golden_signature_manager=None):
        self.predictor = predictor
        self.gs_manager = golden_signature_manager

        # Thresholds
        self.deviation_thresholds = {
            "Temperature_C": {"warning": 3.0, "critical": 5.0},
            "Pressure_Bar": {"warning": 0.1, "critical": 0.2},
            "Motor_Speed_RPM": {"warning": 30, "critical": 60},
            "Power_Consumption_kW": {"warning": 5.0, "critical": 10.0},
            "Vibration_mm_s": {"warning": 1.5, "critical": 3.0},
            "Hardness": {"warning": 10, "critical": 20},
            "Dissolution_Rate": {"warning": 5, "critical": 10},
            "Content_Uniformity": {"warning": 3, "critical": 5},
        }

        # Quality spec limits
        self.quality_specs = {
            "Hardness": {"min": 60, "max": 130, "target": 95},
            "Friability": {"min": 0, "max": 1.0, "target": 0.5},
            "Dissolution_Rate": {"min": 80, "max": 100, "target": 90},
            "Content_Uniformity": {"min": 90, "max": 110, "target": 100},
            "Disintegration_Time": {"min": 2, "max": 15, "target": 8},
        }

        # Decision history
        self.decision_log: deque = deque(maxlen=1000)
        self.active_alerts: List[Decision] = []

    def monitor_batch(
        self,
        batch_id: str,
        current_data: pd.DataFrame,
        current_phase: str,
        golden_signature: Optional[Any] = None,
    ) -> List[Decision]:
        """
        Monitor a running batch and generate decisions.
        """
        decisions = []

        # 1. Check process parameter deviations
        param_decisions = self._check_parameter_deviations(
            batch_id, current_data, current_phase
        )
        decisions.extend(param_decisions)

        # 2. Compare against golden signature
        if golden_signature is not None:
            gs_decisions = self._compare_golden_signature(
                batch_id, current_data, golden_signature
            )
            decisions.extend(gs_decisions)

        # 3. Predict end-of-batch quality
        if self.predictor is not None:
            quality_decisions = self._predict_quality_outcome(
                batch_id, current_data
            )
            decisions.extend(quality_decisions)

        # 4. Energy optimization opportunities
        energy_decisions = self._check_energy_optimization(
            batch_id, current_data, current_phase
        )
        decisions.extend(energy_decisions)

        # 5. Safety checks
        safety_decisions = self._safety_boundary_check(
            batch_id, current_data
        )
        decisions.extend(safety_decisions)

        # Log all decisions
        for d in decisions:
            self.decision_log.append(d)
            if d.severity in [AlertSeverity.WARNING, AlertSeverity.CRITICAL]:
                self.active_alerts.append(d)

        return decisions

    def _check_parameter_deviations(
        self, batch_id: str, data: pd.DataFrame, phase: str
    ) -> List[Decision]:
        """Check for parameter deviations from expected ranges."""
        decisions = []
        latest = data.iloc[-1] if len(data) > 0 else None
        if latest is None:
            return decisions

        for param, thresholds in self.deviation_thresholds.items():
            if param not in data.columns:
                continue

            current_val = latest[param]
            # Compare with rolling mean
            if len(data) > 5:
                expected = data[param].rolling(5, min_periods=1).mean().iloc[-2]
            else:
                expected = data[param].mean()

            deviation = abs(current_val - expected)

            if deviation > thresholds["critical"]:
                decisions.append(Decision(
                    decision_type=DecisionType.CORRECTION,
                    severity=AlertSeverity.CRITICAL,
                    batch_id=batch_id,
                    message=(
                        f"CRITICAL deviation in {param}: current={current_val:.2f}, "
                        f"expected={expected:.2f}, deviation={deviation:.2f}"
                    ),
                    parameters={
                        "parameter": param,
                        "current_value": float(current_val),
                        "expected_value": float(expected),
                        "deviation": float(deviation),
                        "phase": phase,
                    },
                    confidence=0.9,
                ))
            elif deviation > thresholds["warning"]:
                decisions.append(Decision(
                    decision_type=DecisionType.ALERT,
                    severity=AlertSeverity.WARNING,
                    batch_id=batch_id,
                    message=(
                        f"Warning: {param} trending away from expected "
                        f"(current={current_val:.2f}, expected={expected:.2f})"
                    ),
                    parameters={
                        "parameter": param,
                        "current_value": float(current_val),
                        "expected_value": float(expected),
                        "deviation": float(deviation),
                        "phase": phase,
                    },
                    confidence=0.75,
                ))

        return decisions

    def _compare_golden_signature(
        self, batch_id: str, data: pd.DataFrame, golden_sig: Any
    ) -> List[Decision]:
        """Compare batch progress against golden signature."""
        decisions = []

        if not hasattr(golden_sig, "phase_profile") or not golden_sig.phase_profile:
            return decisions

        # Compare phase-level metrics
        phase_profile = golden_sig.phase_profile
        if hasattr(phase_profile, "phase_power_means"):
            for phase, group in data.groupby("Phase"):
                if phase in phase_profile.phase_power_means:
                    expected_power = phase_profile.phase_power_means[phase]
                    actual_power = group["Power_Consumption_kW"].mean()

                    if abs(actual_power - expected_power) > expected_power * 0.15:
                        decisions.append(Decision(
                            decision_type=DecisionType.RECOMMENDATION,
                            severity=AlertSeverity.WARNING,
                            batch_id=batch_id,
                            message=(
                                f"Phase '{phase}' power deviation from golden signature: "
                                f"actual={actual_power:.1f}kW vs expected={expected_power:.1f}kW"
                            ),
                            parameters={
                                "phase": phase,
                                "actual_power_kw": float(actual_power),
                                "expected_power_kw": float(expected_power),
                            },
                            confidence=0.8,
                        ))

        return decisions

    def _predict_quality_outcome(
        self, batch_id: str, data: pd.DataFrame
    ) -> List[Decision]:
        """Predict end-of-batch quality and alert if below spec."""
        decisions = []
        # This would use the ML predictor in a full implementation
        # For now, use heuristic based on current sensor readings

        if len(data) < 10:
            return decisions

        # Check vibration trend (high vibration → compression issues)
        if "Vibration_mm_s" in data.columns:
            vib_trend = np.polyfit(
                np.arange(min(20, len(data))),
                data["Vibration_mm_s"].tail(min(20, len(data))).values,
                1,
            )[0]

            if vib_trend > 0.1:
                decisions.append(Decision(
                    decision_type=DecisionType.RECOMMENDATION,
                    severity=AlertSeverity.WARNING,
                    batch_id=batch_id,
                    message=(
                        "Increasing vibration trend detected. "
                        "Predicted impact on tablet hardness uniformity. "
                        "Consider adjusting compression force or checking die tooling."
                    ),
                    parameters={
                        "vibration_trend": float(vib_trend),
                        "recommendation": "reduce_compression_force",
                        "suggested_adjustment": -1.0,
                    },
                    confidence=0.7,
                ))

        return decisions

    def _check_energy_optimization(
        self, batch_id: str, data: pd.DataFrame, phase: str
    ) -> List[Decision]:
        """Identify energy optimization opportunities."""
        decisions = []

        if "Power_Consumption_kW" not in data.columns:
            return decisions

        power = data["Power_Consumption_kW"].values
        if len(power) < 5:
            return decisions

        # Detect idle energy waste
        recent_power = power[-10:]
        if np.std(recent_power) < 0.5 and np.mean(recent_power) > 5:
            if phase in ["Preparation", "Quality_Testing"]:
                decisions.append(Decision(
                    decision_type=DecisionType.OPTIMIZATION,
                    severity=AlertSeverity.INFO,
                    batch_id=batch_id,
                    message=(
                        f"Idle energy consumption detected in {phase} phase "
                        f"({np.mean(recent_power):.1f} kW with low activity). "
                        "Consider equipment standby mode."
                    ),
                    parameters={
                        "phase": phase,
                        "idle_power_kw": float(np.mean(recent_power)),
                        "potential_savings_pct": 40.0,
                    },
                    confidence=0.85,
                ))

        # Peak power management
        peak_power = np.max(power)
        avg_power = np.mean(power)
        if peak_power > 3 * avg_power:
            decisions.append(Decision(
                decision_type=DecisionType.OPTIMIZATION,
                severity=AlertSeverity.INFO,
                batch_id=batch_id,
                message=(
                    f"High peak-to-average power ratio ({peak_power:.1f}/{avg_power:.1f}). "
                    "Consider load smoothing or staggered phase starts."
                ),
                parameters={
                    "peak_power_kw": float(peak_power),
                    "avg_power_kw": float(avg_power),
                    "ratio": float(peak_power / avg_power),
                },
                confidence=0.65,
            ))

        return decisions

    def _safety_boundary_check(
        self, batch_id: str, data: pd.DataFrame
    ) -> List[Decision]:
        """Check for safety-critical boundary violations."""
        decisions = []
        latest = data.iloc[-1] if len(data) > 0 else None
        if latest is None:
            return decisions

        safety_limits = {
            "Temperature_C": {"min": 10, "max": 80},
            "Pressure_Bar": {"min": 0.5, "max": 2.0},
            "Motor_Speed_RPM": {"min": 0, "max": 1000},
            "Vibration_mm_s": {"min": 0, "max": 15},
        }

        for param, limits in safety_limits.items():
            if param not in data.columns:
                continue

            val = latest[param]
            if val < limits["min"] or val > limits["max"]:
                decisions.append(Decision(
                    decision_type=DecisionType.ALERT,
                    severity=AlertSeverity.CRITICAL,
                    batch_id=batch_id,
                    message=(
                        f"SAFETY: {param} out of safe bounds! "
                        f"Value={val:.2f}, Limits=[{limits['min']}, {limits['max']}]"
                    ),
                    parameters={
                        "parameter": param,
                        "value": float(val),
                        "safe_min": limits["min"],
                        "safe_max": limits["max"],
                    },
                    confidence=1.0,
                ))

        return decisions

    def get_active_alerts(self) -> List[Dict]:
        """Get currently active alerts."""
        return [d.to_dict() for d in self.active_alerts]

    def acknowledge_alert(self, decision_id: str, outcome: str = "resolved"):
        """Acknowledge and close an alert."""
        for d in self.active_alerts:
            if d.id == decision_id:
                d.action_taken = True
                d.outcome = outcome
                self.active_alerts.remove(d)
                return True
        return False

    def get_decision_summary(self) -> Dict:
        """Get summary of all decisions."""
        decisions = list(self.decision_log)
        return {
            "total_decisions": len(decisions),
            "active_alerts": len(self.active_alerts),
            "by_severity": {
                "critical": sum(1 for d in decisions if d.severity == AlertSeverity.CRITICAL),
                "warning": sum(1 for d in decisions if d.severity == AlertSeverity.WARNING),
                "info": sum(1 for d in decisions if d.severity == AlertSeverity.INFO),
            },
            "by_type": {
                "correction": sum(1 for d in decisions if d.decision_type == DecisionType.CORRECTION),
                "alert": sum(1 for d in decisions if d.decision_type == DecisionType.ALERT),
                "recommendation": sum(1 for d in decisions if d.decision_type == DecisionType.RECOMMENDATION),
                "optimization": sum(1 for d in decisions if d.decision_type == DecisionType.OPTIMIZATION),
            },
            "action_rate": round(
                sum(1 for d in decisions if d.action_taken) / max(len(decisions), 1) * 100, 1
            ),
        }
