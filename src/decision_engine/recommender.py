# ============================================================================
# Corrective Action Recommender
# Generates physics-informed corrective actions for batch deviations
# ============================================================================
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class CorrectiveAction:
    """A recommended corrective action."""
    parameter: str
    action: str
    adjustment_value: float
    adjustment_unit: str
    priority: int              # 1=highest
    confidence: float
    expected_impact: Dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    risk_level: str = "low"    # low, medium, high
    implementation_time_min: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "parameter": self.parameter,
            "action": self.action,
            "adjustment_value": round(self.adjustment_value, 3),
            "adjustment_unit": self.adjustment_unit,
            "priority": self.priority,
            "confidence": round(self.confidence, 3),
            "expected_impact": {
                k: round(v, 3) for k, v in self.expected_impact.items()
            },
            "rationale": self.rationale,
            "risk_level": self.risk_level,
            "implementation_time_min": self.implementation_time_min,
        }


class CorrectiveActionRecommender:
    """
    Generates physics-informed corrective action recommendations based on:
    1. Deviation type and magnitude
    2. Current process phase
    3. Historical correction effectiveness
    4. Multi-objective impact analysis
    5. Risk assessment for each action
    """

    def __init__(self):
        # Correction knowledge base: deviation → action mapping
        self.correction_rules = {
            "Temperature_C": {
                "high": [
                    {
                        "action": "Reduce heater setpoint",
                        "param_adjustment": -2.0,
                        "unit": "°C",
                        "impact": {"Hardness": 0.05, "Dissolution_Rate": -0.03},
                        "risk": "low",
                        "time": 5.0,
                    },
                    {
                        "action": "Increase cooling flow rate",
                        "param_adjustment": 2.0,
                        "unit": "LPM",
                        "impact": {"Energy_Consumption_kWh": -0.02},
                        "risk": "low",
                        "time": 2.0,
                    },
                ],
                "low": [
                    {
                        "action": "Increase heater setpoint",
                        "param_adjustment": 2.0,
                        "unit": "°C",
                        "impact": {"Hardness": -0.03, "Dissolution_Rate": 0.02},
                        "risk": "low",
                        "time": 5.0,
                    },
                ],
            },
            "Motor_Speed_RPM": {
                "high": [
                    {
                        "action": "Reduce motor speed gradually",
                        "param_adjustment": -20.0,
                        "unit": "RPM",
                        "impact": {"Vibration_mm_s": -0.1, "Power_Consumption_kW": -0.05},
                        "risk": "low",
                        "time": 1.0,
                    },
                ],
                "low": [
                    {
                        "action": "Increase motor speed",
                        "param_adjustment": 20.0,
                        "unit": "RPM",
                        "impact": {"Content_Uniformity": 0.02},
                        "risk": "low",
                        "time": 1.0,
                    },
                ],
            },
            "Compression_Force_kN": {
                "high": [
                    {
                        "action": "Reduce compression force",
                        "param_adjustment": -1.0,
                        "unit": "kN",
                        "impact": {"Hardness": -0.08, "Friability": 0.02, "Dissolution_Rate": 0.05},
                        "risk": "medium",
                        "time": 2.0,
                    },
                ],
                "low": [
                    {
                        "action": "Increase compression force",
                        "param_adjustment": 1.0,
                        "unit": "kN",
                        "impact": {"Hardness": 0.08, "Friability": -0.02, "Dissolution_Rate": -0.03},
                        "risk": "medium",
                        "time": 2.0,
                    },
                ],
            },
            "Vibration_mm_s": {
                "high": [
                    {
                        "action": "Reduce motor speed",
                        "param_adjustment": -30.0,
                        "unit": "RPM (Motor_Speed)",
                        "impact": {"Content_Uniformity": 0.03, "Equipment_Health": 0.05},
                        "risk": "low",
                        "time": 1.0,
                    },
                    {
                        "action": "Schedule maintenance check on bearings",
                        "param_adjustment": 0,
                        "unit": "",
                        "impact": {"Equipment_Health": 0.1},
                        "risk": "low",
                        "time": 30.0,
                    },
                ],
            },
            "Power_Consumption_kW": {
                "high": [
                    {
                        "action": "Optimize motor load distribution",
                        "param_adjustment": -5.0,
                        "unit": "kW",
                        "impact": {"Energy_Consumption_kWh": -0.08, "CO2_Emissions_kg": -0.05},
                        "risk": "low",
                        "time": 5.0,
                    },
                    {
                        "action": "Enable equipment standby during idle phases",
                        "param_adjustment": -10.0,
                        "unit": "kW",
                        "impact": {"Energy_Consumption_kWh": -0.15, "CO2_Emissions_kg": -0.1},
                        "risk": "low",
                        "time": 1.0,
                    },
                ],
            },
        }

        # Phase-specific adjustment limits
        self.phase_limits = {
            "Granulation": {
                "Temperature_C": (35, 65),
                "Motor_Speed_RPM": (200, 700),
            },
            "Drying": {
                "Temperature_C": (45, 75),
                "Flow_Rate_LPM": (5, 20),
            },
            "Compression": {
                "Compression_Force_kN": (3, 25),
                "Motor_Speed_RPM": (300, 900),
            },
            "Coating": {
                "Temperature_C": (35, 60),
                "Flow_Rate_LPM": (3, 18),
            },
        }

        # Track correction effectiveness
        self.correction_history: List[Dict] = []

    def recommend(
        self,
        deviations: List[Any],
        current_phase: str,
        current_params: Optional[Dict] = None,
        objectives: Optional[Dict] = None,
    ) -> List[CorrectiveAction]:
        """
        Generate corrective action recommendations for detected deviations.
        """
        if not deviations:
            return []

        all_actions = []

        for dev in deviations:
            param = dev.parameter
            direction = dev.direction
            magnitude = dev.magnitude

            if param in self.correction_rules and direction in self.correction_rules[param]:
                rules = self.correction_rules[param][direction]

                for rule in rules:
                    # Scale adjustment by deviation magnitude
                    scaled_adj = rule["param_adjustment"] * min(magnitude * 2, 1.5)

                    # Check phase limits
                    if current_phase in self.phase_limits:
                        phase_lim = self.phase_limits[current_phase]
                        if param in phase_lim:
                            lo, hi = phase_lim[param]
                            if current_params and param in current_params:
                                new_val = current_params[param] + scaled_adj
                                if new_val < lo or new_val > hi:
                                    scaled_adj = np.clip(
                                        new_val, lo, hi
                                    ) - current_params[param]

                    # Confidence based on magnitude match and historical effectiveness
                    confidence = self._compute_confidence(
                        param, direction, magnitude, rule
                    )

                    action = CorrectiveAction(
                        parameter=param,
                        action=rule["action"],
                        adjustment_value=scaled_adj,
                        adjustment_unit=rule["unit"],
                        priority=self._compute_priority(
                            dev, magnitude, rule["risk"]
                        ),
                        confidence=confidence,
                        expected_impact=rule["impact"],
                        rationale=(
                            f"Detected {dev.deviation_type} in {param} "
                            f"(magnitude={magnitude:.2f}, direction={direction}). "
                            f"Recommended during {current_phase} phase."
                        ),
                        risk_level=rule["risk"],
                        implementation_time_min=rule["time"],
                    )
                    all_actions.append(action)

        # Resolve conflicts (e.g., contradictory adjustments)
        resolved = self._resolve_conflicts(all_actions)

        # Sort by priority
        resolved.sort(key=lambda a: a.priority)

        return resolved

    def _compute_confidence(
        self, param: str, direction: str, magnitude: float, rule: Dict
    ) -> float:
        """Compute confidence score for a correction."""
        base_confidence = 0.7

        # Higher magnitude → slightly less confidence (more uncertain territory)
        if magnitude > 0.7:
            base_confidence -= 0.1
        elif magnitude < 0.3:
            base_confidence += 0.1

        # Check historical effectiveness
        history_factor = self._get_historical_effectiveness(param, direction)
        base_confidence = base_confidence * 0.7 + history_factor * 0.3

        # Risk penalty
        risk_penalty = {"low": 0, "medium": 0.05, "high": 0.1}
        base_confidence -= risk_penalty.get(rule.get("risk", "low"), 0)

        return np.clip(base_confidence, 0.1, 0.95)

    def _compute_priority(
        self, deviation: Any, magnitude: float, risk: str
    ) -> int:
        """Compute action priority (1 = highest)."""
        score = magnitude * 10

        if deviation.deviation_type == "spike":
            score += 3
        elif deviation.deviation_type == "drift":
            score += 1

        risk_scores = {"low": 0, "medium": 1, "high": 3}
        score += risk_scores.get(risk, 0)

        if score > 8:
            return 1
        elif score > 5:
            return 2
        elif score > 3:
            return 3
        return 4

    def _get_historical_effectiveness(
        self, param: str, direction: str
    ) -> float:
        """Get historical effectiveness score for a correction type."""
        relevant = [
            h for h in self.correction_history
            if h.get("parameter") == param and h.get("direction") == direction
        ]

        if not relevant:
            return 0.7  # Default

        successes = sum(1 for h in relevant if h.get("success", False))
        return successes / len(relevant)

    def record_outcome(
        self,
        action: CorrectiveAction,
        success: bool,
        actual_impact: Optional[Dict] = None,
    ):
        """Record the outcome of a corrective action for learning."""
        self.correction_history.append({
            "parameter": action.parameter,
            "action": action.action,
            "direction": "high" if action.adjustment_value > 0 else "low",
            "adjustment": action.adjustment_value,
            "success": success,
            "expected_impact": action.expected_impact,
            "actual_impact": actual_impact or {},
        })

    def _resolve_conflicts(
        self, actions: List[CorrectiveAction]
    ) -> List[CorrectiveAction]:
        """Resolve conflicting actions (e.g., increase + decrease same param)."""
        by_param: Dict[str, List[CorrectiveAction]] = {}
        for a in actions:
            if a.parameter not in by_param:
                by_param[a.parameter] = []
            by_param[a.parameter].append(a)

        resolved = []
        for param, param_actions in by_param.items():
            if len(param_actions) == 1:
                resolved.append(param_actions[0])
            else:
                # Check for conflicting directions
                directions = set()
                for a in param_actions:
                    if a.adjustment_value > 0:
                        directions.add("increase")
                    elif a.adjustment_value < 0:
                        directions.add("decrease")

                if len(directions) > 1:
                    # Conflict: pick highest confidence
                    best = max(param_actions, key=lambda a: a.confidence)
                    resolved.append(best)
                else:
                    resolved.extend(param_actions)

        return resolved

    def get_action_summary(
        self, actions: List[CorrectiveAction]
    ) -> Dict:
        """Summarize recommended actions."""
        return {
            "total_actions": len(actions),
            "by_priority": {
                "critical": sum(1 for a in actions if a.priority == 1),
                "high": sum(1 for a in actions if a.priority == 2),
                "medium": sum(1 for a in actions if a.priority == 3),
                "low": sum(1 for a in actions if a.priority == 4),
            },
            "by_risk": {
                "low": sum(1 for a in actions if a.risk_level == "low"),
                "medium": sum(1 for a in actions if a.risk_level == "medium"),
                "high": sum(1 for a in actions if a.risk_level == "high"),
            },
            "estimated_implementation_time_min": round(
                sum(a.implementation_time_min for a in actions), 1
            ),
            "actions": [a.to_dict() for a in actions],
        }
