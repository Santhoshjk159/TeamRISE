# ============================================================================
# Synthetic Data Generator for Manufacturing Intelligence Engine
# Generates realistic industrial batch process + production data
# ============================================================================
import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict
from datetime import datetime, timedelta


class SyntheticBatchDataGenerator:
    """
    Generates physically-realistic synthetic data for pharmaceutical
    tablet manufacturing batches, including process time-series and
    production outcome data with energy and carbon metrics.
    """

    PHASES = [
        ("Preparation", 0, 15),
        ("Granulation", 15, 55),
        ("Drying", 55, 95),
        ("Milling", 95, 115),
        ("Blending", 115, 140),
        ("Compression", 140, 180),
        ("Coating", 180, 200),
        ("Quality_Testing", 200, 210),
    ]

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)

    # ------------------------------------------------------------------ #
    #  Process time-series generation
    # ------------------------------------------------------------------ #
    def _generate_phase_profile(
        self, phase: str, t: np.ndarray, batch_params: Dict
    ) -> Dict[str, np.ndarray]:
        """Generate physically-consistent sensor profiles per phase."""
        n = len(t)
        noise = lambda scale: self.rng.normal(0, scale, n)

        profiles: Dict[str, np.ndarray] = {}

        if phase == "Preparation":
            profiles["Temperature_C"] = 22 + 3 * np.linspace(0, 1, n) + noise(0.8)
            profiles["Pressure_Bar"] = 1.0 + noise(0.08)
            profiles["Humidity_Percent"] = 40 + noise(4)
            profiles["Motor_Speed_RPM"] = np.zeros(n)
            profiles["Compression_Force_kN"] = np.zeros(n)
            profiles["Flow_Rate_LPM"] = np.zeros(n)
            profiles["Power_Consumption_kW"] = 2.0 + noise(0.5)
            profiles["Vibration_mm_s"] = 0.1 + noise(0.05)

        elif phase == "Granulation":
            gt = batch_params.get("Granulation_Time", 15)
            ba = batch_params.get("Binder_Amount", 8.5)
            profiles["Temperature_C"] = 28 + 8 * (1 - np.exp(-t / (gt * 0.6))) + noise(1.2)
            profiles["Pressure_Bar"] = 0.9 + 0.15 * np.sin(2 * np.pi * t / gt) + noise(0.06)
            profiles["Humidity_Percent"] = 35 + ba * 0.8 + noise(3)
            profiles["Motor_Speed_RPM"] = 200 + 50 * np.sin(np.pi * t / gt) + noise(15)
            profiles["Compression_Force_kN"] = np.zeros(n)
            profiles["Flow_Rate_LPM"] = ba / 10 * (1 + 0.3 * np.sin(np.pi * t / gt)) + noise(0.2)
            profiles["Power_Consumption_kW"] = 15 + 8 * np.sin(np.pi * t / gt) + noise(1.5)
            profiles["Vibration_mm_s"] = 2.5 + 1.5 * np.sin(np.pi * t / gt) + noise(0.4)

        elif phase == "Drying":
            dt_param = batch_params.get("Drying_Temp", 60)
            profiles["Temperature_C"] = dt_param + 5 * (1 - np.exp(-t / 10)) + noise(1.0)
            profiles["Pressure_Bar"] = 0.85 + noise(0.05)
            profiles["Humidity_Percent"] = 55 - 30 * (1 - np.exp(-t / 15)) + noise(2)
            profiles["Motor_Speed_RPM"] = 50 + noise(5)
            profiles["Compression_Force_kN"] = np.zeros(n)
            profiles["Flow_Rate_LPM"] = 3.0 + noise(0.3)
            profiles["Power_Consumption_kW"] = 35 + 10 * np.exp(-t / 20) + noise(2)
            profiles["Vibration_mm_s"] = 1.0 + noise(0.3)

        elif phase == "Milling":
            ms = batch_params.get("Machine_Speed", 150)
            profiles["Temperature_C"] = 30 + ms / 50 + noise(1.5)
            profiles["Pressure_Bar"] = 1.0 + noise(0.07)
            profiles["Humidity_Percent"] = 25 + noise(3)
            profiles["Motor_Speed_RPM"] = ms + 100 + noise(20)
            profiles["Compression_Force_kN"] = np.zeros(n)
            profiles["Flow_Rate_LPM"] = 1.0 + noise(0.2)
            profiles["Power_Consumption_kW"] = 20 + ms / 15 + noise(1.8)
            profiles["Vibration_mm_s"] = 3.5 + ms / 100 + noise(0.5)

        elif phase == "Blending":
            lc = batch_params.get("Lubricant_Conc", 1.0)
            profiles["Temperature_C"] = 28 + noise(0.8)
            profiles["Pressure_Bar"] = 1.0 + noise(0.05)
            profiles["Humidity_Percent"] = 30 + noise(2.5)
            profiles["Motor_Speed_RPM"] = 100 + 30 * lc + noise(10)
            profiles["Compression_Force_kN"] = np.zeros(n)
            profiles["Flow_Rate_LPM"] = 0.5 * lc + noise(0.1)
            profiles["Power_Consumption_kW"] = 10 + 5 * lc + noise(1.2)
            profiles["Vibration_mm_s"] = 1.5 + noise(0.3)

        elif phase == "Compression":
            cf = batch_params.get("Compression_Force", 12.5)
            ms = batch_params.get("Machine_Speed", 150)
            profiles["Temperature_C"] = 30 + cf / 3 + noise(1.0)
            profiles["Pressure_Bar"] = 1.0 + cf / 15 + noise(0.08)
            profiles["Humidity_Percent"] = 25 + noise(2)
            profiles["Motor_Speed_RPM"] = ms * 2 + noise(25)
            profiles["Compression_Force_kN"] = cf + 2 * np.sin(2 * np.pi * t / 20) + noise(0.5)
            profiles["Flow_Rate_LPM"] = np.zeros(n)
            profiles["Power_Consumption_kW"] = 25 + cf * 2 + ms / 10 + noise(2.5)
            profiles["Vibration_mm_s"] = 4.0 + cf / 5 + noise(0.6)

        elif phase == "Coating":
            profiles["Temperature_C"] = 45 + noise(1.5)
            profiles["Pressure_Bar"] = 0.95 + noise(0.06)
            profiles["Humidity_Percent"] = 35 + noise(3)
            profiles["Motor_Speed_RPM"] = 80 + noise(8)
            profiles["Compression_Force_kN"] = np.zeros(n)
            profiles["Flow_Rate_LPM"] = 2.5 + noise(0.3)
            profiles["Power_Consumption_kW"] = 18 + noise(2)
            profiles["Vibration_mm_s"] = 1.2 + noise(0.2)

        elif phase == "Quality_Testing":
            profiles["Temperature_C"] = 25 + noise(0.5)
            profiles["Pressure_Bar"] = 1.0 + noise(0.03)
            profiles["Humidity_Percent"] = 40 + noise(2)
            profiles["Motor_Speed_RPM"] = np.zeros(n)
            profiles["Compression_Force_kN"] = np.zeros(n)
            profiles["Flow_Rate_LPM"] = np.zeros(n)
            profiles["Power_Consumption_kW"] = 3.0 + noise(0.4)
            profiles["Vibration_mm_s"] = 0.1 + noise(0.03)

        # Clip to physical bounds
        for k in profiles:
            profiles[k] = np.clip(profiles[k], 0, None)

        return profiles

    def generate_process_timeseries(
        self, batch_id: str, batch_params: Dict
    ) -> pd.DataFrame:
        """Generate full time-series for one batch."""
        rows = []
        for phase_name, t_start, t_end in self.PHASES:
            t_local = np.arange(0, t_end - t_start, dtype=float)
            profiles = self._generate_phase_profile(phase_name, t_local, batch_params)
            for i, t_val in enumerate(t_local):
                row = {
                    "Batch_ID": batch_id,
                    "Time_Minutes": int(t_start + t_val),
                    "Phase": phase_name,
                }
                for col, arr in profiles.items():
                    row[col] = round(arr[i], 6)
                rows.append(row)
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------ #
    #  Production outcome generation (with physics-based correlations)
    # ------------------------------------------------------------------ #
    def _compute_quality_metrics(self, params: Dict) -> Dict:
        """
        Compute output quality metrics from input process parameters
        using approximate physics-based relationships.
        """
        gt = params["Granulation_Time"]
        ba = params["Binder_Amount"]
        dt_ = params["Drying_Temp"]
        dry_t = params["Drying_Time"]
        cf = params["Compression_Force"]
        ms = params["Machine_Speed"]
        lc = params["Lubricant_Conc"]

        # Moisture content: lower drying temp/time → higher moisture
        mc = 3.5 - 0.02 * dt_ - 0.03 * dry_t + 0.05 * ba + self.rng.normal(0, 0.2)
        mc = np.clip(mc, 0.2, 4.0)

        # Tablet weight: relatively consistent
        tw = 200 + 0.1 * cf - 0.05 * ms + self.rng.normal(0, 1.5)

        # Hardness: compression force is primary driver
        hardness = 50 + 4.0 * cf - 0.08 * ms + 2 * ba + self.rng.normal(0, 5)
        hardness = np.clip(hardness, 40, 140)

        # Friability: inverse of hardness, affected by binder and compression
        friability = 1.8 - 0.06 * cf + 0.05 * lc - 0.02 * ba + self.rng.normal(0, 0.1)
        friability = np.clip(friability, 0.2, 2.0)

        # Disintegration time: affected by compression, binder, coating
        disint = 4 + 0.4 * cf + 0.3 * ba - 0.02 * ms + self.rng.normal(0, 1.5)
        disint = np.clip(disint, 2, 20)

        # Dissolution rate: affected by particle size (milling), compression
        dissolution = 95 - 0.3 * cf + 0.1 * ms - 0.5 * ba + self.rng.normal(0, 2)
        dissolution = np.clip(dissolution, 75, 100)

        # Content uniformity: blending time and lubricant matter
        cu = 98 + 0.2 * gt - 0.3 * lc - 0.01 * ms + self.rng.normal(0, 1.5)
        cu = np.clip(cu, 88, 107)

        # Energy consumption: sum of phase-level energy
        energy = (
            2 * 15  # preparation
            + (15 + 8 * 0.5) * gt  # granulation
            + (35 + 5) * dry_t  # drying
            + (20 + ms / 15) * 20  # milling
            + (10 + 5 * lc) * 25  # blending
            + (25 + cf * 2 + ms / 10) * 40  # compression
            + 18 * 20  # coating
            + 3 * 10  # QC
        ) / 60  # Convert kW·min to kWh
        energy += self.rng.normal(0, energy * 0.05)

        # CO2 emissions: energy * grid carbon intensity + steam/gas usage
        co2 = energy * 0.4 + dry_t * 0.02 * dry_t / 60 + self.rng.normal(0, 2)
        co2 = max(co2, energy * 0.3)

        return {
            "Moisture_Content": round(mc, 2),
            "Tablet_Weight": round(tw, 1),
            "Hardness": round(hardness, 0),
            "Friability": round(friability, 2),
            "Disintegration_Time": round(disint, 1),
            "Dissolution_Rate": round(dissolution, 1),
            "Content_Uniformity": round(cu, 1),
            "Energy_Consumption_kWh": round(energy, 2),
            "CO2_Emissions_kg": round(co2, 2),
        }

    def generate_production_data(self, n_batches: int = 200) -> pd.DataFrame:
        """Generate production data for n batches with realistic variability."""
        records = []
        for i in range(1, n_batches + 1):
            batch_id = f"T{i:03d}"

            # Randomize input parameters with realistic ranges
            params = {
                "Granulation_Time": int(self.rng.uniform(9, 27)),
                "Binder_Amount": round(self.rng.uniform(5.5, 14.0), 1),
                "Drying_Temp": int(self.rng.uniform(42, 74)),
                "Drying_Time": int(self.rng.uniform(15, 48)),
                "Compression_Force": round(self.rng.uniform(4.5, 18.0), 1),
                "Machine_Speed": int(self.rng.uniform(90, 280)),
                "Lubricant_Conc": round(self.rng.uniform(0.3, 2.8), 1),
            }

            # Inject some anomalous batches (10% probability)
            if self.rng.random() < 0.10:
                anomaly_type = self.rng.choice(["high_energy", "low_quality", "drift"])
                if anomaly_type == "high_energy":
                    params["Machine_Speed"] = int(self.rng.uniform(250, 300))
                    params["Drying_Temp"] = int(self.rng.uniform(70, 80))
                elif anomaly_type == "low_quality":
                    params["Compression_Force"] = round(self.rng.uniform(3.0, 5.0), 1)
                    params["Binder_Amount"] = round(self.rng.uniform(4.0, 5.5), 1)
                elif anomaly_type == "drift":
                    params["Granulation_Time"] = int(self.rng.uniform(25, 35))

            # Compute quality outcomes
            outcomes = self._compute_quality_metrics(params)

            record = {"Batch_ID": batch_id, **params, **outcomes}
            records.append(record)

        return pd.DataFrame(records)

    def generate_full_dataset(
        self, n_batches: int = 200
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate both production and time-series data."""
        prod_df = self.generate_production_data(n_batches)
        ts_frames = []
        for _, row in prod_df.iterrows():
            params = {
                "Granulation_Time": row["Granulation_Time"],
                "Binder_Amount": row["Binder_Amount"],
                "Drying_Temp": row["Drying_Temp"],
                "Drying_Time": row["Drying_Time"],
                "Compression_Force": row["Compression_Force"],
                "Machine_Speed": row["Machine_Speed"],
                "Lubricant_Conc": row["Lubricant_Conc"],
            }
            ts = self.generate_process_timeseries(row["Batch_ID"], params)
            ts_frames.append(ts)
        ts_df = pd.concat(ts_frames, ignore_index=True)
        return prod_df, ts_df


def generate_and_save(
    n_batches: int = 200,
    output_dir: str = "data",
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate and save synthetic datasets."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    gen = SyntheticBatchDataGenerator(seed=seed)
    prod_df, ts_df = gen.generate_full_dataset(n_batches)

    prod_path = os.path.join(output_dir, "batch_production_data.csv")
    ts_path = os.path.join(output_dir, "batch_process_timeseries.csv")

    prod_df.to_csv(prod_path, index=False)
    ts_df.to_csv(ts_path, index=False)

    print(f"Production data: {prod_df.shape} → {prod_path}")
    print(f"Time-series data: {ts_df.shape} → {ts_path}")

    return prod_df, ts_df


if __name__ == "__main__":
    generate_and_save(n_batches=200)
