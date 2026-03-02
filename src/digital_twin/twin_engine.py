# ============================================================================
# Digital Twin Engine
# Orchestrates process and energy simulations for decision support
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging

from src.digital_twin.process_simulator import PharmaceuticalDigitalTwin, SimulationResult
from src.digital_twin.energy_simulator import EnergyDigitalTwin

logger = logging.getLogger(__name__)


class DigitalTwinEngine:
    """
    Master digital twin orchestrator.

    Capabilities:
    1. Full batch simulation (process + energy)
    2. What-if scenario analysis
    3. Optimization pre-validation (test before real application)
    4. Equipment degradation forecasting
    5. Production scheduling optimization
    6. Risk assessment for parameter changes
    """

    def __init__(self):
        self.process_twin = PharmaceuticalDigitalTwin()
        self.energy_twin = EnergyDigitalTwin()
        self.simulation_history: List[Dict] = []

    def simulate_full_batch(
        self,
        parameters: Optional[Dict] = None,
        batch_id: str = "DT_001",
        start_hour: int = 6,
    ) -> Dict:
        """Run complete process + energy simulation."""
        # Process simulation
        process_result = self.process_twin.simulate_batch(
            batch_id=batch_id,
            scenario_name="full_simulation",
            parameters=parameters,
        )

        # Energy simulation using process phase durations
        energy_result = self.energy_twin.simulate_energy_profile(
            phase_durations=process_result.phase_durations,
            start_hour=start_hour,
        )

        combined = {
            "batch_id": batch_id,
            "process": process_result.to_dict(),
            "energy": energy_result["summary"],
            "energy_optimization": energy_result["optimization_opportunities"],
            "quality_within_spec": self._check_quality_specs(
                process_result.quality_predictions
            ),
        }

        self.simulation_history.append(combined)
        return combined

    def validate_optimization(
        self,
        proposed_params: Dict,
        current_params: Dict,
        n_simulations: int = 10,
    ) -> Dict:
        """
        Validate an optimization recommendation by running multiple
        simulations and comparing with current parameters.
        """
        current_results = []
        proposed_results = []

        for i in range(n_simulations):
            # Simulate current
            curr = self.process_twin.simulate_batch(
                batch_id=f"VAL_CURR_{i:03d}",
                scenario_name="current",
                parameters=current_params,
            )
            current_results.append(curr)

            # Simulate proposed
            prop = self.process_twin.simulate_batch(
                batch_id=f"VAL_PROP_{i:03d}",
                scenario_name="proposed",
                parameters=proposed_params,
            )
            proposed_results.append(prop)

        # Statistical comparison
        comparison = self._statistical_comparison(
            current_results, proposed_results
        )

        # Risk assessment
        risk = self._assess_risk(proposed_results)

        return {
            "recommendation": "accept" if comparison["overall_improvement"] else "reject",
            "comparison": comparison,
            "risk_assessment": risk,
            "n_simulations": n_simulations,
            "confidence": comparison.get("confidence", 0),
        }

    def run_scenario_analysis(
        self,
        base_params: Dict,
        scenarios: Dict[str, Dict],
    ) -> Dict:
        """
        Run named scenarios and compare results.

        scenarios: {"name": {param_overrides}}
        """
        results = {}

        # Baseline
        baseline = self.process_twin.simulate_batch(
            batch_id="SCEN_baseline",
            scenario_name="Baseline",
            parameters=base_params,
        )
        results["Baseline"] = baseline

        # Each scenario
        for name, overrides in scenarios.items():
            params = base_params.copy()
            params.update(overrides)
            result = self.process_twin.simulate_batch(
                batch_id=f"SCEN_{name}",
                scenario_name=name,
                parameters=params,
            )
            results[name] = result

        # Compare
        comparison_df = self.process_twin.compare_scenarios(list(results.values()))

        return {
            "comparison_table": comparison_df.to_dict(orient="records"),
            "scenarios": {
                name: r.to_dict() for name, r in results.items()
            },
            "best_scenario": self.process_twin.find_optimal_scenario(
                list(results.values())
            ).scenario_name,
        }

    def forecast_maintenance_impact(
        self,
        current_params: Dict,
        current_age_factor: float = 1.0,
        forecast_steps: int = 6,
    ) -> Dict:
        """
        Forecast how equipment degradation will impact
        quality and energy over time.
        """
        age_factors = [
            current_age_factor + 0.05 * i
            for i in range(forecast_steps)
        ]

        forecasts = []
        for age in age_factors:
            # Simulate with degraded equipment
            # Equipment age increases vibration, power consumption
            params = current_params.copy()
            result = self.process_twin.simulate_batch(
                batch_id=f"MAINT_{age:.2f}",
                scenario_name=f"age_factor={age:.2f}",
                parameters=params,
            )

            # Adjust for age factor impact
            quality = result.quality_predictions.copy()
            quality["Hardness"] *= (1 - 0.01 * (age - 1.0))
            quality["Content_Uniformity_%"] *= (1 - 0.02 * (age - 1.0))

            energy = result.energy_metrics.copy()
            energy["Total_Energy_kWh"] *= age

            forecasts.append({
                "age_factor": round(age, 2),
                "quality": quality,
                "energy": energy,
                "quality_risk": "high" if quality.get("Content_Uniformity_%", 100) < 92 else (
                    "medium" if quality.get("Content_Uniformity_%", 100) < 95 else "low"
                ),
                "energy_impact_pct": round((age - 1.0) * 100, 1),
            })

        # Find maintenance threshold
        maintenance_threshold = None
        for f in forecasts:
            if f["quality_risk"] == "high":
                maintenance_threshold = f["age_factor"]
                break

        return {
            "forecasts": forecasts,
            "maintenance_threshold": maintenance_threshold,
            "recommendation": (
                f"Schedule maintenance before age factor reaches "
                f"{maintenance_threshold:.2f}" if maintenance_threshold
                else "Equipment within acceptable range for all forecast periods"
            ),
        }

    def _check_quality_specs(self, quality: Dict) -> Dict:
        """Check quality predictions against specifications."""
        specs = {
            "Hardness": {"min": 60, "max": 130},
            "Friability_%": {"min": 0, "max": 1.0},
            "Dissolution_Rate_%": {"min": 80, "max": 100},
            "Content_Uniformity_%": {"min": 90, "max": 110},
            "Disintegration_Time_min": {"min": 2, "max": 15},
        }

        results = {}
        all_pass = True

        for metric, limits in specs.items():
            value = quality.get(metric, None)
            if value is not None:
                in_spec = limits["min"] <= value <= limits["max"]
                results[metric] = {
                    "value": round(value, 2),
                    "min": limits["min"],
                    "max": limits["max"],
                    "in_spec": in_spec,
                    "margin": round(min(
                        value - limits["min"],
                        limits["max"] - value,
                    ), 2),
                }
                if not in_spec:
                    all_pass = False

        return {
            "all_in_spec": all_pass,
            "details": results,
        }

    def _statistical_comparison(
        self,
        current: List[SimulationResult],
        proposed: List[SimulationResult],
    ) -> Dict:
        """Statistical comparison of two simulation sets."""
        metrics = [
            "Hardness", "Dissolution_Rate_%", "Content_Uniformity_%",
        ]

        comparison = {}
        improvements = 0
        total_metrics = 0

        for metric in metrics:
            curr_vals = [r.quality_predictions.get(metric, 0) for r in current]
            prop_vals = [r.quality_predictions.get(metric, 0) for r in proposed]

            curr_mean = np.mean(curr_vals)
            prop_mean = np.mean(prop_vals)
            improvement = (prop_mean - curr_mean) / (abs(curr_mean) + 1e-10) * 100

            comparison[metric] = {
                "current_mean": round(curr_mean, 2),
                "proposed_mean": round(prop_mean, 2),
                "improvement_pct": round(improvement, 2),
                "current_std": round(np.std(curr_vals), 2),
                "proposed_std": round(np.std(prop_vals), 2),
            }

            if improvement > 0:
                improvements += 1
            total_metrics += 1

        # Energy comparison
        curr_energy = [r.energy_metrics.get("Total_Energy_kWh", 0) for r in current]
        prop_energy = [r.energy_metrics.get("Total_Energy_kWh", 0) for r in proposed]
        energy_improvement = (
            (np.mean(curr_energy) - np.mean(prop_energy))
            / (np.mean(curr_energy) + 1e-10) * 100
        )

        comparison["Energy_kWh"] = {
            "current_mean": round(np.mean(curr_energy), 2),
            "proposed_mean": round(np.mean(prop_energy), 2),
            "improvement_pct": round(energy_improvement, 2),
        }

        if energy_improvement > 0:
            improvements += 1
        total_metrics += 1

        confidence = improvements / max(total_metrics, 1)

        return {
            "metrics": comparison,
            "overall_improvement": improvements > total_metrics / 2,
            "improvement_count": improvements,
            "total_metrics": total_metrics,
            "confidence": round(confidence, 3),
        }

    def _assess_risk(self, results: List[SimulationResult]) -> Dict:
        """Assess risk of proposed parameter changes."""
        # Check how many simulations produce out-of-spec quality
        spec_fails = 0
        for r in results:
            specs = self._check_quality_specs(r.quality_predictions)
            if not specs["all_in_spec"]:
                spec_fails += 1

        fail_rate = spec_fails / max(len(results), 1)

        return {
            "spec_failure_rate": round(fail_rate * 100, 1),
            "risk_level": (
                "high" if fail_rate > 0.3
                else "medium" if fail_rate > 0.1
                else "low"
            ),
            "total_simulations": len(results),
            "spec_failures": spec_fails,
        }

    def get_summary(self) -> Dict:
        """Return summary of all simulations run."""
        return {
            "total_simulations": len(self.simulation_history),
            "recent": self.simulation_history[-5:]
            if self.simulation_history else [],
        }
