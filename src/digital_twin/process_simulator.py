# ============================================================================
# Pharmaceutical Process Digital Twin
# Physics-based simulation of batch processes for what-if analysis
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SimulationState:
    """Current state of the digital twin simulation."""
    time_step: int = 0
    phase: str = "Preparation"
    temperature: float = 25.0
    pressure: float = 1.0
    humidity: float = 50.0
    motor_speed: float = 0.0
    compression_force: float = 0.0
    flow_rate: float = 0.0
    power_consumption: float = 0.0
    vibration: float = 0.0
    moisture_content: float = 8.0
    granule_size: float = 0.0
    tablet_density: float = 0.0
    coating_thickness: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "time_step": self.time_step,
            "phase": self.phase,
            "Temperature_C": round(self.temperature, 2),
            "Pressure_Bar": round(self.pressure, 3),
            "Humidity_%": round(self.humidity, 1),
            "Motor_Speed_RPM": round(self.motor_speed, 1),
            "Compression_Force_kN": round(self.compression_force, 2),
            "Flow_Rate_LPM": round(self.flow_rate, 2),
            "Power_Consumption_kW": round(self.power_consumption, 2),
            "Vibration_mm_s": round(self.vibration, 3),
            "Moisture_Content_%": round(self.moisture_content, 2),
        }


@dataclass
class SimulationResult:
    """Complete simulation result."""
    batch_id: str
    scenario_name: str
    parameters: Dict
    time_series: pd.DataFrame = field(default_factory=pd.DataFrame)
    quality_predictions: Dict = field(default_factory=dict)
    energy_metrics: Dict = field(default_factory=dict)
    phase_durations: Dict = field(default_factory=dict)
    total_time_minutes: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "batch_id": self.batch_id,
            "scenario_name": self.scenario_name,
            "parameters": self.parameters,
            "quality_predictions": {
                k: round(v, 3) for k, v in self.quality_predictions.items()
            },
            "energy_metrics": {
                k: round(v, 3) if isinstance(v, float) else v
                for k, v in self.energy_metrics.items()
            },
            "phase_durations": self.phase_durations,
            "total_time_minutes": round(self.total_time_minutes, 1),
        }


class PharmaceuticalDigitalTwin:
    """
    Digital twin simulator for pharmaceutical tablet manufacturing.

    Simulates the complete batch lifecycle:
    1. Preparation → 2. Granulation → 3. Drying → 4. Milling →
    5. Blending → 6. Compression → 7. Coating → 8. Quality_Testing

    Physics models:
    - Granulation: Binder distribution kinetics (Avrami-like)
    - Drying: First-order moisture removal with Arrhenius temperature dependence
    - Compression: Modified Heckel equation for tablet density
    - Coating: Film growth model with spray rate dependence
    - Energy: Phase-specific power consumption models
    """

    PHASES = [
        "Preparation", "Granulation", "Drying", "Milling",
        "Blending", "Compression", "Coating", "Quality_Testing",
    ]

    # Default phase durations in minutes
    DEFAULT_PHASE_DURATIONS = {
        "Preparation": 15,
        "Granulation": 35,
        "Drying": 45,
        "Milling": 20,
        "Blending": 25,
        "Compression": 40,
        "Coating": 30,
        "Quality_Testing": 20,
    }

    def __init__(self):
        self.noise_level = 0.02  # 2% sensor noise

    def simulate_batch(
        self,
        batch_id: str = "SIM_001",
        scenario_name: str = "baseline",
        parameters: Optional[Dict] = None,
    ) -> SimulationResult:
        """
        Run a full batch simulation.

        Parameters can include:
        - granulation_time, binder_amount, granulation_temp, granulation_speed
        - drying_temp, drying_time
        - compression_force, machine_speed
        - coating_spray_rate, coating_temp
        - lubricant_conc, moisture_content
        """
        params = self._default_parameters()
        if parameters:
            params.update(parameters)

        state = SimulationState()
        time_series_records = []
        phase_durations = {}

        total_time = 0
        for phase in self.PHASES:
            duration = int(params.get(
                f"{phase.lower()}_duration",
                self.DEFAULT_PHASE_DURATIONS[phase],
            ))
            phase_durations[phase] = duration

            for t in range(duration):
                state.time_step = total_time + t
                state.phase = phase
                self._step(state, phase, t, duration, params)
                record = state.to_dict()
                record["Batch_ID"] = batch_id
                record["Elapsed_Minutes"] = total_time + t
                time_series_records.append(record)

            total_time += duration

        ts_df = pd.DataFrame(time_series_records)

        # Predict final quality from process trajectory
        quality = self._predict_quality(ts_df, params)
        energy = self._compute_energy_metrics(ts_df, phase_durations)

        return SimulationResult(
            batch_id=batch_id,
            scenario_name=scenario_name,
            parameters=params,
            time_series=ts_df,
            quality_predictions=quality,
            energy_metrics=energy,
            phase_durations=phase_durations,
            total_time_minutes=float(total_time),
        )

    def _step(
        self,
        state: SimulationState,
        phase: str,
        t: int,
        duration: int,
        params: Dict,
    ):
        """Advance simulation by one time step."""
        noise = lambda: np.random.normal(0, self.noise_level)

        if phase == "Preparation":
            state.temperature = 25 + 2 * np.sin(t / 5) + noise()
            state.motor_speed = 50 + noise() * 10
            state.power_consumption = 3.0 + noise()
            state.vibration = 0.3 + noise() * 0.1

        elif phase == "Granulation":
            target_temp = params.get("granulation_temp", 50)
            ramp = min(t / 10, 1.0)
            state.temperature = 25 + (target_temp - 25) * ramp + noise() * target_temp
            state.motor_speed = params.get("granulation_speed", 450) + noise() * 20
            state.humidity = 55 - 10 * (t / duration) + noise() * 5
            state.power_consumption = 15 + 5 * ramp + noise() * 2
            state.vibration = 1.5 + 0.5 * (state.motor_speed / 600) + noise()
            # Granule growth (Avrami-like)
            k = 0.05 * params.get("binder_amount", 5) / 5
            state.granule_size = 200 * (1 - np.exp(-k * t)) + noise() * 10

        elif phase == "Drying":
            target_temp = params.get("drying_temp", 60)
            state.temperature = target_temp + noise() * target_temp
            state.humidity = max(20, 50 - 30 * (t / duration)) + noise() * 3
            # First-order drying kinetics with Arrhenius
            k_dry = 0.03 * np.exp(-3000 / (target_temp + 273.15) * (1 - 1 / (60 + 273.15)))
            state.moisture_content = 8.0 * np.exp(-k_dry * t) + noise()
            state.power_consumption = 20 + 3 * (target_temp / 60) + noise() * 2
            state.motor_speed = 100 + noise() * 10
            state.vibration = 0.5 + noise() * 0.2

        elif phase == "Milling":
            state.temperature = 35 + noise() * 3
            state.motor_speed = 500 + noise() * 30
            state.power_consumption = 12 + noise() * 2
            state.vibration = 2.0 + noise() * 0.5
            # Granule size reduction
            state.granule_size = max(
                50, state.granule_size * (1 - 0.05 * (1 + noise()))
            )

        elif phase == "Blending":
            state.temperature = 30 + noise() * 2
            state.motor_speed = params.get("blending_speed", 200) + noise() * 15
            state.power_consumption = 8 + noise() * 1.5
            state.vibration = 1.0 + noise() * 0.3

        elif phase == "Compression":
            force = params.get("compression_force", 12)
            speed = params.get("machine_speed", 600)
            state.compression_force = force + noise() * force * 0.5
            state.motor_speed = speed + noise() * 20
            state.temperature = 35 + 0.1 * force + noise() * 3
            state.power_consumption = 10 + 0.8 * force + 0.005 * speed + noise() * 2
            state.vibration = 1.0 + 0.15 * (speed / 600) + noise() * 0.3
            # Heckel equation for density
            P = force * 1e6  # Convert to Pa
            Py = 100e6  # Yield pressure
            state.tablet_density = 1.2 * (
                1 - np.exp(-P / Py)
            ) + noise() * 0.02

        elif phase == "Coating":
            spray_rate = params.get("coating_spray_rate", 10)
            coat_temp = params.get("coating_temp", 45)
            state.temperature = coat_temp + noise() * coat_temp
            state.flow_rate = spray_rate + noise() * spray_rate * 0.5
            state.motor_speed = 100 + noise() * 10
            state.power_consumption = 10 + noise() * 2
            state.vibration = 0.8 + noise() * 0.2
            # Coating growth
            state.coating_thickness += 0.5 * (spray_rate / 10) * (1 + noise())

        elif phase == "Quality_Testing":
            state.temperature = 25 + noise() * 2
            state.motor_speed = 0
            state.power_consumption = 5 + noise()
            state.vibration = 0.1 + noise() * 0.05

    def _predict_quality(
        self, ts_df: pd.DataFrame, params: Dict
    ) -> Dict[str, float]:
        """Predict final quality metrics from simulation trajectory."""
        # Extract key process features
        comp_data = ts_df[ts_df["Phase"] == "Compression"]
        dry_data = ts_df[ts_df["Phase"] == "Drying"]

        avg_comp_force = comp_data["Compression_Force_kN"].mean() if len(comp_data) > 0 else 12
        avg_comp_speed = comp_data["Motor_Speed_RPM"].mean() if len(comp_data) > 0 else 600
        final_moisture = dry_data["Moisture_Content_%"].iloc[-1] if len(dry_data) > 0 else 3.0

        # Physics-based quality predictions
        # Hardness: increases with compression force (Heckel), decreases with moisture
        hardness = (
            40 + 5.5 * avg_comp_force
            - 2 * final_moisture
            + np.random.normal(0, 3)
        )
        hardness = np.clip(hardness, 40, 160)

        # Tablet weight: depends on fill depth and compression
        tablet_weight = (
            250 + 5 * avg_comp_force
            - 0.02 * avg_comp_speed
            + np.random.normal(0, 5)
        )

        # Friability: inversely related to hardness
        friability = max(0.1, 1.5 - 0.008 * hardness + np.random.normal(0, 0.1))

        # Dissolution rate: depends on porosity (inverse of compression)
        dissolution_rate = (
            95 - 0.5 * avg_comp_force
            + 0.5 * final_moisture
            + np.random.normal(0, 3)
        )
        dissolution_rate = np.clip(dissolution_rate, 50, 100)

        # Disintegration time: related to compression force
        disintegration_time = (
            3 + 0.6 * avg_comp_force
            - 0.3 * final_moisture
            + np.random.normal(0, 1)
        )
        disintegration_time = max(1, disintegration_time)

        # Content uniformity
        avg_vibration = ts_df["Vibration_mm_s"].mean()
        content_uniformity = (
            100 - 0.5 * avg_vibration
            + np.random.normal(0, 1.5)
        )
        content_uniformity = np.clip(content_uniformity, 85, 105)

        return {
            "Hardness": float(hardness),
            "Tablet_Weight_mg": float(tablet_weight),
            "Friability_%": float(friability),
            "Dissolution_Rate_%": float(dissolution_rate),
            "Disintegration_Time_min": float(disintegration_time),
            "Content_Uniformity_%": float(content_uniformity),
        }

    def _compute_energy_metrics(
        self, ts_df: pd.DataFrame, phase_durations: Dict
    ) -> Dict:
        """Compute energy metrics from simulation."""
        total_energy = ts_df["Power_Consumption_kW"].sum() / 60  # kWh
        peak_power = ts_df["Power_Consumption_kW"].max()
        avg_power = ts_df["Power_Consumption_kW"].mean()

        phase_energy = {}
        for phase in self.PHASES:
            phase_data = ts_df[ts_df["Phase"] == phase]
            if len(phase_data) > 0:
                phase_energy[phase] = round(
                    phase_data["Power_Consumption_kW"].sum() / 60, 3
                )

        co2_factor = 0.5  # kg CO2 per kWh
        return {
            "Total_Energy_kWh": float(total_energy),
            "Peak_Power_kW": float(peak_power),
            "Average_Power_kW": float(avg_power),
            "CO2_Emissions_kg": float(total_energy * co2_factor),
            "Phase_Energy_kWh": phase_energy,
            "Specific_Energy_kWh_per_unit": float(total_energy / 1000),
        }

    def _default_parameters(self) -> Dict:
        """Default simulation parameters."""
        return {
            "granulation_temp": 50,
            "granulation_speed": 450,
            "binder_amount": 5.0,
            "drying_temp": 60,
            "drying_time": 45,
            "compression_force": 12,
            "machine_speed": 600,
            "blending_speed": 200,
            "coating_spray_rate": 10,
            "coating_temp": 45,
            "lubricant_conc": 1.0,
            "moisture_content": 8.0,
        }

    def run_what_if(
        self,
        base_params: Dict,
        variations: Dict[str, List[float]],
        batch_id_prefix: str = "WIF",
    ) -> List[SimulationResult]:
        """
        Run what-if analysis: vary one or more parameters
        and compare outcomes.
        """
        results = []
        scenario_idx = 0

        # Generate combinations
        import itertools
        param_names = list(variations.keys())
        param_values = list(variations.values())

        for combo in itertools.product(*param_values):
            params = base_params.copy()
            scenario_parts = []
            for name, val in zip(param_names, combo):
                params[name] = val
                scenario_parts.append(f"{name}={val}")

            scenario_name = " | ".join(scenario_parts)
            result = self.simulate_batch(
                batch_id=f"{batch_id_prefix}_{scenario_idx:03d}",
                scenario_name=scenario_name,
                parameters=params,
            )
            results.append(result)
            scenario_idx += 1

        return results

    def compare_scenarios(
        self, results: List[SimulationResult]
    ) -> pd.DataFrame:
        """
        Compare multiple simulation scenarios side by side.
        """
        rows = []
        for r in results:
            row = {
                "Scenario": r.scenario_name,
                "Batch_ID": r.batch_id,
                "Total_Time_min": r.total_time_minutes,
            }
            row.update(r.quality_predictions)
            row.update({
                "Energy_kWh": r.energy_metrics.get("Total_Energy_kWh", 0),
                "CO2_kg": r.energy_metrics.get("CO2_Emissions_kg", 0),
                "Peak_Power_kW": r.energy_metrics.get("Peak_Power_kW", 0),
            })
            rows.append(row)

        df = pd.DataFrame(rows)
        return df

    def find_optimal_scenario(
        self,
        results: List[SimulationResult],
        objectives: Optional[Dict[str, str]] = None,
    ) -> SimulationResult:
        """
        Find the best scenario based on multi-objective scoring.

        objectives: dict of metric_name → "maximize" or "minimize"
        """
        if not objectives:
            objectives = {
                "Hardness": "maximize",
                "Dissolution_Rate_%": "maximize",
                "Content_Uniformity_%": "maximize",
                "Energy_kWh": "minimize",
                "CO2_kg": "minimize",
            }

        comparison = self.compare_scenarios(results)
        scores = np.zeros(len(comparison))

        for metric, direction in objectives.items():
            if metric in comparison.columns:
                col = comparison[metric].values
                if col.std() > 0:
                    normalized = (col - col.min()) / (col.max() - col.min() + 1e-10)
                    if direction == "minimize":
                        normalized = 1 - normalized
                    scores += normalized

        best_idx = int(np.argmax(scores))
        return results[best_idx]
