# ============================================================================
# Adaptive Carbon Target Engine
# Dynamic batch-level carbon emission target computation
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class CarbonTargetEngine:
    """
    Computes dynamic batch-level carbon emission targets using:

    Carbon Target = (Grid Intensity × Energy Use × Sustainability Weight)
                  − Historical Efficiency Offset

    Features:
    - Real-time grid carbon intensity tracking
    - Dynamic sustainability weight adjustment
    - Historical efficiency baseline computation
    - Production window optimization (shift to low-carbon periods)
    - kg CO₂e per kg product tracking
    """

    def __init__(
        self,
        grid_intensity: float = 0.4,  # kg CO2e/kWh
        sustainability_weight: float = 0.85,
        regulatory_cap: float = 200.0,  # kg CO2e per batch
        reduction_target_pct: float = 15.0,
    ):
        self.base_grid_intensity = grid_intensity
        self.current_grid_intensity = grid_intensity
        self.sustainability_weight = sustainability_weight
        self.regulatory_cap = regulatory_cap
        self.reduction_target_pct = reduction_target_pct

        # Historical tracking
        self.emission_history: deque = deque(maxlen=1000)
        self.target_history: deque = deque(maxlen=1000)
        self.grid_intensity_history: deque = deque(maxlen=168)  # 1 week hourly

        # Efficiency baseline
        self.historical_offset: float = 0.0
        self.best_efficiency: float = float("inf")

    def compute_batch_target(
        self,
        estimated_energy_kwh: float,
        grid_intensity: Optional[float] = None,
        production_weight_kg: float = 200.0,
    ) -> Dict:
        """
        Compute dynamic carbon target for a batch.

        Formula:
        Carbon Target = (Grid_Intensity × Energy_Use × Sustainability_Weight)
                      − Historical_Efficiency_Offset
        """
        gi = grid_intensity or self.current_grid_intensity

        # Base carbon footprint
        base_carbon = gi * estimated_energy_kwh

        # Apply sustainability weight (reduces target, making it harder to meet)
        weighted_carbon = base_carbon * self.sustainability_weight

        # Historical efficiency offset (reward for past performance)
        target = weighted_carbon - self.historical_offset

        # Apply regulatory cap
        target = min(target, self.regulatory_cap)

        # Specific carbon (per unit weight)
        specific_carbon = target / (production_weight_kg + 1e-10)

        # Carbon intensity category
        if specific_carbon < 0.3:
            category = "low_carbon"
        elif specific_carbon < 0.6:
            category = "moderate_carbon"
        elif specific_carbon < 1.0:
            category = "high_carbon"
        else:
            category = "critical_carbon"

        result = {
            "batch_carbon_target_kg": round(float(target), 4),
            "base_carbon_kg": round(float(base_carbon), 4),
            "sustainability_adjustment": round(float(base_carbon - weighted_carbon), 4),
            "efficiency_offset": round(float(self.historical_offset), 4),
            "regulatory_cap": self.regulatory_cap,
            "grid_intensity_used": round(float(gi), 4),
            "specific_carbon_per_kg": round(float(specific_carbon), 6),
            "category": category,
            "estimated_energy_kwh": estimated_energy_kwh,
        }

        self.target_history.append({
            "timestamp": datetime.now().isoformat(),
            **result,
        })

        return result

    def record_actual_emissions(
        self,
        batch_id: str,
        actual_energy_kwh: float,
        actual_emissions_kg: Optional[float] = None,
        production_weight_kg: float = 200.0,
    ) -> Dict:
        """Record actual batch emissions and update baselines."""
        if actual_emissions_kg is None:
            actual_emissions_kg = actual_energy_kwh * self.current_grid_intensity

        # Specific efficiency
        efficiency = actual_emissions_kg / (production_weight_kg + 1e-10)

        # Update best efficiency
        if efficiency < self.best_efficiency:
            self.best_efficiency = efficiency

        # Record
        record = {
            "batch_id": batch_id,
            "timestamp": datetime.now().isoformat(),
            "actual_energy_kwh": actual_energy_kwh,
            "actual_emissions_kg": actual_emissions_kg,
            "specific_emissions": efficiency,
            "production_weight_kg": production_weight_kg,
        }
        self.emission_history.append(record)

        # Update historical offset
        self._update_historical_offset()

        # Compute target for comparison
        target = self.compute_batch_target(actual_energy_kwh, production_weight_kg=production_weight_kg)

        status = "met" if actual_emissions_kg <= target["batch_carbon_target_kg"] else "exceeded"
        deviation = actual_emissions_kg - target["batch_carbon_target_kg"]

        return {
            **record,
            "target_kg": target["batch_carbon_target_kg"],
            "status": status,
            "deviation_kg": round(float(deviation), 4),
            "deviation_pct": round(
                float(deviation / (target["batch_carbon_target_kg"] + 1e-10) * 100), 2
            ),
        }

    def _update_historical_offset(self):
        """Update historical efficiency offset based on recent performance."""
        if len(self.emission_history) < 10:
            self.historical_offset = 0.0
            return

        recent = list(self.emission_history)[-50:]
        efficiencies = [r["specific_emissions"] for r in recent]

        # Offset = improvement from worst to current best practice
        worst = np.percentile(efficiencies, 90)
        best = np.percentile(efficiencies, 10)
        improvement = worst - best

        # Scale offset by batch size
        avg_production = np.mean([r["production_weight_kg"] for r in recent])
        self.historical_offset = max(0, improvement * avg_production * 0.5)

    def update_grid_intensity(self, intensity: float, timestamp: Optional[str] = None):
        """Update real-time grid carbon intensity."""
        self.current_grid_intensity = intensity
        self.grid_intensity_history.append({
            "timestamp": timestamp or datetime.now().isoformat(),
            "intensity": intensity,
        })

    def find_optimal_production_window(
        self,
        n_hours_ahead: int = 24,
        batch_duration_hours: float = 3.5,
    ) -> Dict:
        """
        Find optimal production window based on grid carbon intensity forecast.
        Recommends low-carbon production windows.
        """
        if len(self.grid_intensity_history) < 2:
            return {
                "recommended_start": "now",
                "reason": "Insufficient grid data for optimization",
                "estimated_savings_pct": 0.0,
            }

        # Simulate grid intensity pattern (real system would use forecast API)
        history = list(self.grid_intensity_history)
        intensities = [h["intensity"] for h in history]

        # Find periods of lowest intensity
        window_size = max(1, int(batch_duration_hours))
        min_avg = float("inf")
        best_start = 0

        for i in range(max(1, len(intensities) - window_size)):
            window_avg = np.mean(intensities[i:i + window_size])
            if window_avg < min_avg:
                min_avg = window_avg
                best_start = i

        current_avg = np.mean(intensities[-window_size:]) if len(intensities) >= window_size else np.mean(intensities)

        savings_pct = max(0, (current_avg - min_avg) / (current_avg + 1e-10) * 100)

        return {
            "recommended_start_offset_hours": best_start,
            "recommended_intensity": round(float(min_avg), 4),
            "current_intensity": round(float(current_avg), 4),
            "estimated_savings_pct": round(float(savings_pct), 2),
            "recommendation": (
                f"Delay production by ~{best_start}h for {savings_pct:.1f}% "
                f"carbon reduction" if savings_pct > 5
                else "Current production window is near-optimal"
            ),
        }

    def get_carbon_dashboard(self) -> Dict:
        """Get comprehensive carbon management dashboard data."""
        if not self.emission_history:
            return {
                "status": "no_data",
                "message": "No emission data recorded yet",
            }

        records = list(self.emission_history)
        emissions = [r["actual_emissions_kg"] for r in records]
        energies = [r["actual_energy_kwh"] for r in records]
        efficiencies = [r["specific_emissions"] for r in records]

        # Calculate trends
        if len(emissions) >= 10:
            recent = emissions[-10:]
            older = emissions[-20:-10] if len(emissions) >= 20 else emissions[:10]
            trend = np.mean(recent) - np.mean(older)
            trend_direction = "improving" if trend < 0 else "worsening"
        else:
            trend = 0.0
            trend_direction = "stable"

        # Targets met ratio
        met_count = 0
        total_count = 0
        for record in records:
            target = self.compute_batch_target(record["actual_energy_kwh"])
            if record["actual_emissions_kg"] <= target["batch_carbon_target_kg"]:
                met_count += 1
            total_count += 1

        return {
            "total_batches_tracked": len(records),
            "total_emissions_kg": round(sum(emissions), 2),
            "avg_emissions_per_batch": round(float(np.mean(emissions)), 2),
            "total_energy_kwh": round(sum(energies), 2),
            "avg_energy_per_batch": round(float(np.mean(energies)), 2),
            "avg_carbon_intensity": round(float(np.mean(efficiencies)), 6),
            "best_carbon_intensity": round(float(min(efficiencies)), 6),
            "targets_met_ratio": round(met_count / max(total_count, 1) * 100, 1),
            "trend": {
                "direction": trend_direction,
                "change_kg": round(float(trend), 4),
            },
            "current_grid_intensity": self.current_grid_intensity,
            "regulatory_cap": self.regulatory_cap,
            "historical_offset": round(self.historical_offset, 4),
            "production_window": self.find_optimal_production_window(),
        }
