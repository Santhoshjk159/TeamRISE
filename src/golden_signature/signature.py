# ============================================================================
# Golden Signature Framework
# Structured representation of optimal batch parameter profiles
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class EnergyFingerprint:
    """Energy consumption fingerprint of a batch."""
    total_energy_kwh: float = 0.0
    peak_power_kw: float = 0.0
    avg_power_kw: float = 0.0
    power_factor: float = 0.0
    phase_energy_distribution: Dict[str, float] = field(default_factory=dict)
    spectral_signature: Dict[str, float] = field(default_factory=dict)
    thd_percent: float = 0.0


@dataclass
class PhaseProfile:
    """Process phase profile."""
    phase_durations: Dict[str, float] = field(default_factory=dict)
    phase_temperatures: Dict[str, float] = field(default_factory=dict)
    phase_power_means: Dict[str, float] = field(default_factory=dict)
    phase_vibration_means: Dict[str, float] = field(default_factory=dict)
    transition_rates: Dict[str, float] = field(default_factory=dict)


@dataclass
class GoldenSignature:
    """
    Golden Signature: Optimized parameter set for multi-objective targets.

    Structure:
    - Process Parameters: Optimal input settings
    - Energy Fingerprint: Expected energy pattern
    - Phase Profile: Expected phase-level behavior
    - Asset Health Score: Equipment condition requirement
    - Carbon Intensity Context: Carbon constraint
    - Confidence Score: Statistical confidence
    """
    # Identification
    signature_id: str = ""
    version: int = 1
    created_at: str = ""
    updated_at: str = ""

    # Scenario tagging
    scenario_tag: str = "default"
    material_type: str = "standard"
    season: str = "all"

    # Core components
    process_parameters: Dict[str, float] = field(default_factory=dict)
    energy_fingerprint: EnergyFingerprint = field(default_factory=EnergyFingerprint)
    phase_profile: PhaseProfile = field(default_factory=PhaseProfile)
    asset_health_score: float = 100.0
    carbon_intensity: float = 0.0
    confidence_score: float = 0.0

    # Target metrics achieved
    targets: Dict[str, float] = field(default_factory=dict)

    # Status
    is_active: bool = True
    approved: bool = False
    approved_by: Optional[str] = None
    replaced_by: Optional[str] = None
    parent_id: Optional[str] = None

    # History
    performance_history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = asdict(self)
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "GoldenSignature":
        """Create from dictionary."""
        ef_data = data.pop("energy_fingerprint", {})
        pp_data = data.pop("phase_profile", {})

        ef = EnergyFingerprint(**ef_data) if isinstance(ef_data, dict) else EnergyFingerprint()
        pp = PhaseProfile(**pp_data) if isinstance(pp_data, dict) else PhaseProfile()

        return cls(energy_fingerprint=ef, phase_profile=pp, **data)

    def generate_id(self) -> str:
        """Generate unique signature ID based on scenario."""
        content = f"{self.scenario_tag}_{self.material_type}_{self.season}_{self.version}"
        self.signature_id = f"GS_{hashlib.md5(content.encode()).hexdigest()[:12]}"
        return self.signature_id


class GoldenSignatureManager:
    """
    Manages the lifecycle of Golden Signatures:
    - Creation from optimization results
    - Storage, retrieval, comparison
    - Version management
    - Human-in-the-loop approval
    - Self-improvement (automatic updates when performance exceeds benchmark)
    """

    def __init__(self):
        self.signatures: Dict[str, GoldenSignature] = {}
        self.archived_signatures: List[GoldenSignature] = []
        self.pending_approvals: List[Dict] = []
        self.feedback_history: List[Dict] = []

    def create_signature(
        self,
        process_params: Dict[str, float],
        targets: Dict[str, float],
        energy_data: Optional[Dict] = None,
        phase_data: Optional[Dict] = None,
        scenario_tag: str = "default",
        material_type: str = "standard",
        season: str = "all",
    ) -> GoldenSignature:
        """Create a new Golden Signature from optimization results."""
        sig = GoldenSignature(
            scenario_tag=scenario_tag,
            material_type=material_type,
            season=season,
            process_parameters=process_params,
            targets=targets,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        if energy_data:
            sig.energy_fingerprint = EnergyFingerprint(**energy_data)
        if phase_data:
            sig.phase_profile = PhaseProfile(**phase_data)

        # Compute confidence score based on target achievements
        sig.confidence_score = self._compute_confidence(targets)

        sig.generate_id()

        logger.info(
            f"Created Golden Signature {sig.signature_id} "
            f"for scenario '{scenario_tag}' with confidence {sig.confidence_score:.2f}"
        )

        return sig

    def _compute_confidence(self, targets: Dict[str, float]) -> float:
        """
        Compute confidence score based on how well targets meet specifications.
        """
        scores = []

        # Quality targets
        hardness = targets.get("Hardness", 90)
        scores.append(min(1.0, hardness / 100))

        dissolution = targets.get("Dissolution_Rate", 90)
        scores.append(min(1.0, dissolution / 95))

        cu = targets.get("Content_Uniformity", 98)
        scores.append(1.0 - abs(cu - 100) / 10)

        # Friability (lower is better, <1.0 required)
        friability = targets.get("Friability", 0.7)
        scores.append(max(0, 1.0 - friability))

        # Energy efficiency (lower is better)
        energy = targets.get("Energy_Consumption_kWh", 300)
        scores.append(max(0, 1.0 - energy / 500))

        return float(np.clip(np.mean(scores), 0, 1))

    def save_signature(
        self, signature: GoldenSignature, require_approval: bool = True
    ) -> str:
        """Save a signature (optionally pending approval)."""
        if require_approval and not signature.approved:
            self.pending_approvals.append({
                "signature": signature,
                "submitted_at": datetime.now().isoformat(),
                "status": "pending",
            })
            logger.info(f"Signature {signature.signature_id} submitted for approval")
            return f"pending:{signature.signature_id}"

        self.signatures[signature.signature_id] = signature
        logger.info(f"Signature {signature.signature_id} saved")
        return signature.signature_id

    def approve_signature(
        self, signature_id: str, approved_by: str, approved: bool = True
    ) -> bool:
        """Human-in-the-loop approval of a signature."""
        for i, pending in enumerate(self.pending_approvals):
            sig = pending["signature"]
            if sig.signature_id == signature_id:
                if approved:
                    sig.approved = True
                    sig.approved_by = approved_by
                    sig.updated_at = datetime.now().isoformat()
                    self.signatures[sig.signature_id] = sig
                    self.pending_approvals[i]["status"] = "approved"
                    logger.info(f"Signature {signature_id} approved by {approved_by}")
                else:
                    self.pending_approvals[i]["status"] = "rejected"
                    logger.info(f"Signature {signature_id} rejected by {approved_by}")

                self.feedback_history.append({
                    "action": "approve" if approved else "reject",
                    "signature_id": signature_id,
                    "user": approved_by,
                    "timestamp": datetime.now().isoformat(),
                })
                return True

        return False

    def get_best_signature(
        self, scenario_tag: Optional[str] = None,
        target_priorities: Optional[Dict[str, float]] = None,
    ) -> Optional[GoldenSignature]:
        """Find the best matching golden signature."""
        candidates = [
            sig for sig in self.signatures.values()
            if sig.is_active and (scenario_tag is None or sig.scenario_tag == scenario_tag)
        ]

        if not candidates:
            return None

        if target_priorities is None:
            target_priorities = {
                "Hardness": 0.25,
                "Dissolution_Rate": 0.2,
                "Content_Uniformity": 0.2,
                "Energy_Consumption_kWh": -0.2,
                "CO2_Emissions_kg": -0.15,
            }

        best_sig = None
        best_score = -np.inf

        for sig in candidates:
            score = sig.confidence_score
            for target, weight in target_priorities.items():
                if target in sig.targets:
                    score += weight * sig.targets[target] / 100
            if score > best_score:
                best_score = score
                best_sig = sig

        return best_sig

    def compare_with_signature(
        self, current_metrics: Dict[str, float],
        signature: GoldenSignature,
    ) -> Dict:
        """
        Compare current batch metrics against a golden signature.
        Returns deviation analysis.
        """
        deviations = {}
        overall_score = 0
        n_targets = 0

        for target, golden_value in signature.targets.items():
            if target in current_metrics:
                current = current_metrics[target]
                deviation = current - golden_value
                pct_deviation = deviation / (abs(golden_value) + 1e-10) * 100

                # For energy/carbon, negative deviation is good
                is_energy_target = target in [
                    "Energy_Consumption_kWh", "CO2_Emissions_kg", "Friability"
                ]

                if is_energy_target:
                    status = "better" if deviation < 0 else (
                        "worse" if abs(pct_deviation) > 5 else "on_target"
                    )
                    match_score = max(0, 1 - abs(pct_deviation) / 100)
                else:
                    status = "better" if deviation > 0 else (
                        "worse" if abs(pct_deviation) > 5 else "on_target"
                    )
                    match_score = max(0, 1 - abs(pct_deviation) / 100)

                deviations[target] = {
                    "golden_value": golden_value,
                    "current_value": current,
                    "deviation": round(deviation, 4),
                    "pct_deviation": round(pct_deviation, 2),
                    "status": status,
                    "match_score": round(match_score, 4),
                }

                overall_score += match_score
                n_targets += 1

        overall_match = overall_score / (n_targets + 1e-10) * 100

        return {
            "signature_id": signature.signature_id,
            "target_deviations": deviations,
            "overall_match_percent": round(overall_match, 2),
            "recommendation": self._comparison_recommendation(
                overall_match, deviations
            ),
        }

    def check_and_update(
        self, current_metrics: Dict[str, float],
        current_params: Dict[str, float],
        scenario_tag: str = "default",
        improvement_threshold: float = 0.02,
    ) -> Optional[Dict]:
        """
        Self-improvement: Check if current performance exceeds
        the golden signature and propose an update.
        """
        current_sig = self.get_best_signature(scenario_tag)
        if current_sig is None:
            # No existing signature - create new
            new_sig = self.create_signature(
                current_params, current_metrics, scenario_tag=scenario_tag
            )
            return {
                "action": "create_new",
                "signature": new_sig,
                "reason": "No existing golden signature for this scenario",
            }

        # Compare
        comparison = self.compare_with_signature(current_metrics, current_sig)

        # Check if improvement threshold met
        if comparison["overall_match_percent"] > 100 * (1 + improvement_threshold):
            new_sig = self.create_signature(
                current_params, current_metrics,
                scenario_tag=scenario_tag,
            )
            new_sig.parent_id = current_sig.signature_id

            return {
                "action": "propose_update",
                "new_signature": new_sig,
                "old_signature_id": current_sig.signature_id,
                "improvement": comparison["overall_match_percent"] - 100,
                "comparison": comparison,
                "requires_approval": True,
            }

        return None

    def reprioritize_targets(
        self, signature_id: str,
        new_priorities: Dict[str, float],
        user_id: str,
    ) -> Dict:
        """Human-in-the-loop: reprioritize optimization targets."""
        self.feedback_history.append({
            "action": "reprioritize",
            "signature_id": signature_id,
            "user": user_id,
            "new_priorities": new_priorities,
            "timestamp": datetime.now().isoformat(),
        })

        return {
            "status": "priorities_updated",
            "signature_id": signature_id,
            "new_priorities": new_priorities,
        }

    def _comparison_recommendation(
        self, overall_match: float, deviations: Dict
    ) -> str:
        """Generate recommendation from comparison."""
        if overall_match >= 95:
            return "Batch performing excellently - matches golden signature closely."
        elif overall_match >= 80:
            worse_targets = [
                k for k, v in deviations.items() if v["status"] == "worse"
            ]
            if worse_targets:
                return f"Good performance. Review parameters affecting: {', '.join(worse_targets)}"
            return "Good overall performance with minor deviations."
        elif overall_match >= 60:
            return "Significant deviation from golden signature. Process review recommended."
        else:
            return "ALERT: Major deviation detected. Immediate process investigation required."

    def get_historical_metrics(self) -> Dict:
        """Get historical tracking metrics across all signatures."""
        return {
            "total_signatures": len(self.signatures),
            "active_signatures": sum(
                1 for s in self.signatures.values() if s.is_active
            ),
            "pending_approvals": len([
                p for p in self.pending_approvals if p["status"] == "pending"
            ]),
            "total_feedback": len(self.feedback_history),
            "avg_confidence": round(
                np.mean([s.confidence_score for s in self.signatures.values()])
                if self.signatures else 0, 4
            ),
        }

    def export_signatures(self) -> List[Dict]:
        """Export all signatures as JSON-serializable dicts."""
        return [sig.to_dict() for sig in self.signatures.values()]
