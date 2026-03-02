# ============================================================================
# Energy Digital Twin
# Simulates energy consumption patterns for optimization testing
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class EnergyDigitalTwin:
    """
    Energy subsystem digital twin that models:
    1. Phase-level power consumption profiles
    2. Grid interaction (time-of-use pricing, carbon intensity)
    3. Load shifting opportunities
    4. Equipment degradation impact on energy
    5. HVAC and auxiliary system loads
    """

    def __init__(self):
        # Phase-level power profiles (kW)
        self.phase_power_profiles = {
            "Preparation": {"base": 3.0, "peak": 5.0, "ramp_time": 2},
            "Granulation": {"base": 15.0, "peak": 22.0, "ramp_time": 5},
            "Drying": {"base": 18.0, "peak": 25.0, "ramp_time": 8},
            "Milling": {"base": 10.0, "peak": 15.0, "ramp_time": 3},
            "Blending": {"base": 6.0, "peak": 10.0, "ramp_time": 4},
            "Compression": {"base": 12.0, "peak": 18.0, "ramp_time": 5},
            "Coating": {"base": 8.0, "peak": 14.0, "ramp_time": 6},
            "Quality_Testing": {"base": 4.0, "peak": 6.0, "ramp_time": 1},
        }

        # Time-of-use tariff ($/kWh by hour of day)
        self.tou_tariff = self._default_tou_tariff()

        # Grid carbon intensity by hour (gCO2/kWh)
        self.grid_carbon = self._default_carbon_profile()

    def simulate_energy_profile(
        self,
        phase_durations: Dict[str, int],
        start_hour: int = 6,
        equipment_age_factor: float = 1.0,
        ambient_temp_c: float = 25.0,
    ) -> Dict:
        """
        Simulate detailed energy profile for a batch.

        Returns energy time series, cost analysis, and optimization opportunities.
        """
        records = []
        total_minutes = 0

        for phase, duration in phase_durations.items():
            profile = self.phase_power_profiles.get(phase, {
                "base": 5.0, "peak": 8.0, "ramp_time": 3,
            })

            for t in range(duration):
                minute = total_minutes + t
                hour = (start_hour + minute // 60) % 24

                # Power model: ramp-up → steady → ramp-down
                ramp = profile["ramp_time"]
                if t < ramp:
                    power_factor = t / ramp
                elif t > duration - ramp:
                    power_factor = (duration - t) / ramp
                else:
                    power_factor = 1.0

                base_power = profile["base"] + (
                    profile["peak"] - profile["base"]
                ) * power_factor

                # Equipment degradation increases consumption
                degradation_factor = 1.0 + 0.05 * (equipment_age_factor - 1.0)

                # Temperature compensation (HVAC load)
                hvac_load = max(0, (ambient_temp_c - 22) * 0.3)

                # Add noise
                noise = np.random.normal(0, 0.02) * base_power

                total_power = base_power * degradation_factor + hvac_load + noise

                # Costs and carbon
                energy_cost = total_power / 60 * self.tou_tariff.get(hour, 0.10)
                carbon = total_power / 60 * self.grid_carbon.get(hour, 400) / 1000

                records.append({
                    "Minute": minute,
                    "Phase": phase,
                    "Hour_of_Day": hour,
                    "Power_kW": round(total_power, 2),
                    "Energy_kWh": round(total_power / 60, 4),
                    "Cost_USD": round(energy_cost, 4),
                    "CO2_kg": round(carbon, 4),
                    "TOU_Tariff": self.tou_tariff.get(hour, 0.10),
                    "Grid_Carbon_gCO2_kWh": self.grid_carbon.get(hour, 400),
                })

            total_minutes += duration

        df = pd.DataFrame(records)

        return {
            "time_series": df,
            "summary": self._summarize(df),
            "optimization_opportunities": self._find_opportunities(df),
        }

    def optimize_start_time(
        self,
        phase_durations: Dict[str, int],
        equipment_age_factor: float = 1.0,
        objective: str = "cost",  # "cost", "carbon", "balanced"
    ) -> Dict:
        """
        Find optimal batch start time by simulating all 24 start hours.
        """
        results = []

        for start_hour in range(24):
            sim = self.simulate_energy_profile(
                phase_durations, start_hour, equipment_age_factor
            )
            summary = sim["summary"]
            results.append({
                "start_hour": start_hour,
                "total_cost_usd": summary["total_cost_usd"],
                "total_co2_kg": summary["total_co2_kg"],
                "total_energy_kwh": summary["total_energy_kwh"],
                "peak_power_kw": summary["peak_power_kw"],
            })

        results_df = pd.DataFrame(results)

        if objective == "cost":
            best_idx = results_df["total_cost_usd"].idxmin()
        elif objective == "carbon":
            best_idx = results_df["total_co2_kg"].idxmin()
        else:
            # Balanced: normalize and combine
            cost_norm = (results_df["total_cost_usd"] - results_df["total_cost_usd"].min()) / (
                results_df["total_cost_usd"].max() - results_df["total_cost_usd"].min() + 1e-10
            )
            carbon_norm = (results_df["total_co2_kg"] - results_df["total_co2_kg"].min()) / (
                results_df["total_co2_kg"].max() - results_df["total_co2_kg"].min() + 1e-10
            )
            combined = 0.5 * cost_norm + 0.5 * carbon_norm
            best_idx = combined.idxmin()

        best = results_df.iloc[best_idx]
        worst_cost = results_df.iloc[results_df["total_cost_usd"].idxmax()]

        return {
            "optimal_start_hour": int(best["start_hour"]),
            "optimal_cost_usd": round(best["total_cost_usd"], 2),
            "optimal_co2_kg": round(best["total_co2_kg"], 3),
            "worst_cost_usd": round(worst_cost["total_cost_usd"], 2),
            "potential_savings_usd": round(
                worst_cost["total_cost_usd"] - best["total_cost_usd"], 2
            ),
            "potential_savings_pct": round(
                (worst_cost["total_cost_usd"] - best["total_cost_usd"])
                / worst_cost["total_cost_usd"] * 100, 1
            ),
            "all_hours": results,
        }

    def simulate_degradation_impact(
        self,
        phase_durations: Dict[str, int],
        age_factors: List[float] = None,
    ) -> pd.DataFrame:
        """
        Simulate how equipment degradation affects energy consumption over time.
        """
        if age_factors is None:
            age_factors = [1.0, 1.05, 1.10, 1.15, 1.20, 1.30]

        rows = []
        for age in age_factors:
            sim = self.simulate_energy_profile(
                phase_durations, equipment_age_factor=age
            )
            summary = sim["summary"]
            rows.append({
                "Equipment_Age_Factor": age,
                "Total_Energy_kWh": summary["total_energy_kwh"],
                "Total_Cost_USD": summary["total_cost_usd"],
                "Total_CO2_kg": summary["total_co2_kg"],
                "Peak_Power_kW": summary["peak_power_kw"],
                "Energy_Increase_Pct": round(
                    (summary["total_energy_kwh"] / rows[0]["Total_Energy_kWh"] - 1) * 100
                    if rows else 0, 1
                ),
            })

        return pd.DataFrame(rows)

    def _summarize(self, df: pd.DataFrame) -> Dict:
        """Summarize energy simulation results."""
        return {
            "total_energy_kwh": round(df["Energy_kWh"].sum(), 3),
            "total_cost_usd": round(df["Cost_USD"].sum(), 2),
            "total_co2_kg": round(df["CO2_kg"].sum(), 3),
            "peak_power_kw": round(df["Power_kW"].max(), 2),
            "avg_power_kw": round(df["Power_kW"].mean(), 2),
            "duration_minutes": len(df),
            "phase_energy": {
                phase: round(group["Energy_kWh"].sum(), 3)
                for phase, group in df.groupby("Phase")
            },
            "phase_cost": {
                phase: round(group["Cost_USD"].sum(), 3)
                for phase, group in df.groupby("Phase")
            },
        }

    def _find_opportunities(self, df: pd.DataFrame) -> List[Dict]:
        """Find energy optimization opportunities in the profile."""
        opportunities = []

        # 1. Peak demand reduction
        peak = df["Power_kW"].max()
        avg = df["Power_kW"].mean()
        if peak > 2 * avg:
            opportunities.append({
                "type": "peak_demand_reduction",
                "description": f"Peak power ({peak:.1f} kW) is {peak/avg:.1f}x average. "
                "Consider load staggering.",
                "potential_savings_pct": 10,
            })

        # 2. Off-peak shifting
        on_peak = df[df["TOU_Tariff"] > 0.12]["Cost_USD"].sum()
        off_peak = df[df["TOU_Tariff"] <= 0.12]["Cost_USD"].sum()
        if on_peak > 0.6 * df["Cost_USD"].sum():
            opportunities.append({
                "type": "off_peak_shifting",
                "description": f"{on_peak/(on_peak+off_peak)*100:.0f}% of energy cost during peak hours. "
                "Consider shifting batch start time.",
                "potential_savings_pct": 15,
            })

        # 3. Idle power
        for phase, group in df.groupby("Phase"):
            power_cv = group["Power_kW"].std() / (group["Power_kW"].mean() + 1e-10)
            if power_cv < 0.05 and group["Power_kW"].mean() > 5:
                opportunities.append({
                    "type": "idle_power",
                    "description": f"Phase '{phase}' shows constant low-variation power "
                    f"({group['Power_kW'].mean():.1f} kW). Possible idle equipment.",
                    "potential_savings_pct": 5,
                })

        return opportunities

    def _default_tou_tariff(self) -> Dict[int, float]:
        """Default time-of-use tariff structure."""
        tariff = {}
        for h in range(24):
            if 7 <= h <= 11 or 17 <= h <= 21:
                tariff[h] = 0.15  # Peak
            elif 12 <= h <= 16:
                tariff[h] = 0.12  # Mid-peak
            else:
                tariff[h] = 0.08  # Off-peak
        return tariff

    def _default_carbon_profile(self) -> Dict[int, float]:
        """Default grid carbon intensity profile (gCO2/kWh)."""
        profile = {}
        for h in range(24):
            # Higher during peak demand, lower at night (more renewables)
            base = 350
            peak_addition = 150 * max(0, np.sin((h - 6) * np.pi / 18))
            profile[h] = base + peak_addition
        return profile
