# ============================================================================
# Feature Engineering Module
# Creates derived features for enhanced model performance
# ============================================================================
import numpy as np
import pandas as pd
from scipy import signal, fft as scipy_fft
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Creates advanced engineered features including:
    - Rolling statistics (mean, std, min, max, slope)
    - Spectral energy features (FFT)
    - Change-point detection features
    - Phase-level aggregations
    - Energy-specific features (specific energy per unit)
    - Cross-feature interactions
    """

    def __init__(self):
        self.feature_names: List[str] = []

    # ------------------------------------------------------------------ #
    # Time-series feature extraction (per batch)
    # ------------------------------------------------------------------ #
    def extract_rolling_features(
        self, ts_df: pd.DataFrame, window_sizes: List[int] = [5, 10, 20],
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Compute rolling statistics for time-series columns."""
        if columns is None:
            columns = [
                "Temperature_C", "Pressure_Bar", "Power_Consumption_kW",
                "Motor_Speed_RPM", "Vibration_mm_s", "Flow_Rate_LPM",
            ]

        result = ts_df.copy()
        for col in columns:
            if col not in result.columns:
                continue
            for w in window_sizes:
                result[f"{col}_roll_mean_{w}"] = (
                    result[col].rolling(window=w, min_periods=1).mean()
                )
                result[f"{col}_roll_std_{w}"] = (
                    result[col].rolling(window=w, min_periods=1).std().fillna(0)
                )
                result[f"{col}_roll_max_{w}"] = (
                    result[col].rolling(window=w, min_periods=1).max()
                )
                # Rate of change
                result[f"{col}_roc_{w}"] = result[col].diff(w).fillna(0)

        return result

    def extract_spectral_features(
        self, ts_df: pd.DataFrame,
        column: str = "Power_Consumption_kW",
        n_harmonics: int = 5,
    ) -> Dict[str, float]:
        """
        Extract FFT-based spectral energy features from a time series.
        Returns dominant frequencies, spectral entropy, and harmonic amplitudes.
        """
        signal_data = ts_df[column].values
        n = len(signal_data)

        if n < 4:
            return {
                f"{column}_spectral_energy": 0.0,
                f"{column}_dominant_freq": 0.0,
                f"{column}_spectral_entropy": 0.0,
            }

        # Apply Hann window to reduce spectral leakage
        windowed = signal_data * np.hanning(n)
        fft_vals = np.fft.rfft(windowed)
        freqs = np.fft.rfftfreq(n, d=1.0)
        magnitudes = np.abs(fft_vals)
        power_spectrum = magnitudes ** 2

        features = {}

        # Total spectral energy
        features[f"{column}_spectral_energy"] = float(np.sum(power_spectrum))

        # Dominant frequency
        if len(magnitudes) > 1:
            dom_idx = np.argmax(magnitudes[1:]) + 1
            features[f"{column}_dominant_freq"] = float(freqs[dom_idx])
            features[f"{column}_dominant_amplitude"] = float(magnitudes[dom_idx])
        else:
            features[f"{column}_dominant_freq"] = 0.0
            features[f"{column}_dominant_amplitude"] = 0.0

        # Spectral entropy (measure of spectral complexity)
        ps_norm = power_spectrum / (np.sum(power_spectrum) + 1e-10)
        spectral_entropy = -np.sum(ps_norm * np.log2(ps_norm + 1e-10))
        features[f"{column}_spectral_entropy"] = float(spectral_entropy)

        # Harmonic amplitudes
        for h in range(1, min(n_harmonics + 1, len(magnitudes))):
            features[f"{column}_harmonic_{h}"] = float(magnitudes[h])

        # Spectral centroid
        if np.sum(magnitudes) > 0:
            features[f"{column}_spectral_centroid"] = float(
                np.sum(freqs * magnitudes) / np.sum(magnitudes)
            )
        else:
            features[f"{column}_spectral_centroid"] = 0.0

        # Spectral bandwidth
        centroid = features[f"{column}_spectral_centroid"]
        if np.sum(magnitudes) > 0:
            features[f"{column}_spectral_bandwidth"] = float(
                np.sqrt(np.sum(((freqs - centroid) ** 2) * magnitudes) / np.sum(magnitudes))
            )
        else:
            features[f"{column}_spectral_bandwidth"] = 0.0

        return features

    def detect_change_points(
        self, ts_df: pd.DataFrame,
        column: str = "Power_Consumption_kW",
        window: int = 10,
        threshold: float = 2.0,
    ) -> Dict[str, float]:
        """
        Detect change points using CUSUM-based method.
        Returns number of change points and their characteristics.
        """
        signal_data = ts_df[column].values
        n = len(signal_data)

        if n < window * 2:
            return {
                f"{column}_n_changepoints": 0,
                f"{column}_max_shift": 0.0,
                f"{column}_mean_shift": 0.0,
            }

        # Rolling mean difference
        rolling_mean = pd.Series(signal_data).rolling(window=window, min_periods=1).mean()
        diffs = rolling_mean.diff(window).abs().fillna(0)
        std_val = diffs.std() + 1e-10

        # Detect significant changes
        changepoints = diffs > threshold * std_val

        return {
            f"{column}_n_changepoints": int(changepoints.sum()),
            f"{column}_max_shift": float(diffs.max()),
            f"{column}_mean_shift": float(diffs.mean()),
            f"{column}_shift_std": float(diffs.std()),
        }

    def compute_phase_aggregations(
        self, ts_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Aggregate time-series features per phase.
        Returns phase-level statistics.
        """
        features = {}
        numeric_cols = [
            "Temperature_C", "Pressure_Bar", "Power_Consumption_kW",
            "Motor_Speed_RPM", "Vibration_mm_s",
        ]

        for phase, group in ts_df.groupby("Phase"):
            for col in numeric_cols:
                if col not in group.columns:
                    continue
                phase_key = f"{phase}_{col}"
                features[f"{phase_key}_mean"] = float(group[col].mean())
                features[f"{phase_key}_std"] = float(group[col].std())
                features[f"{phase_key}_max"] = float(group[col].max())
                features[f"{phase_key}_min"] = float(group[col].min())
                features[f"{phase_key}_energy"] = float(
                    np.sum(group[col].values ** 2)
                )

        return features

    def compute_energy_features(
        self, ts_df: pd.DataFrame, production_row: Optional[pd.Series] = None
    ) -> Dict[str, float]:
        """
        Compute energy-specific derived features.
        """
        power = ts_df["Power_Consumption_kW"].values
        features = {}

        # Total energy (kWh - assuming 1-minute intervals)
        features["total_energy_kwh"] = float(np.sum(power) / 60.0)

        # Peak power
        features["peak_power_kw"] = float(np.max(power))

        # Average power
        features["avg_power_kw"] = float(np.mean(power))

        # Power factor proxy (ratio of avg to peak)
        features["power_factor"] = float(
            np.mean(power) / (np.max(power) + 1e-10)
        )

        # Energy ramp rate
        power_diff = np.diff(power)
        features["max_ramp_rate"] = float(np.max(np.abs(power_diff))) if len(power_diff) > 0 else 0.0
        features["avg_ramp_rate"] = float(np.mean(np.abs(power_diff))) if len(power_diff) > 0 else 0.0

        # Phase-level energy distribution
        total_energy = features["total_energy_kwh"]
        for phase, group in ts_df.groupby("Phase"):
            phase_energy = float(np.sum(group["Power_Consumption_kW"].values) / 60.0)
            features[f"{phase}_energy_kwh"] = phase_energy
            features[f"{phase}_energy_pct"] = (
                phase_energy / (total_energy + 1e-10) * 100
            )

        # Specific energy per unit (if production data available)
        if production_row is not None and "Tablet_Weight" in production_row.index:
            features["specific_energy_per_unit"] = (
                total_energy / (production_row.get("Tablet_Weight", 200) + 1e-10)
            )

        # Vibration-energy correlation
        if "Vibration_mm_s" in ts_df.columns:
            corr = np.corrcoef(power, ts_df["Vibration_mm_s"].values)[0, 1]
            features["vibration_energy_correlation"] = float(corr) if not np.isnan(corr) else 0.0

        return features

    def engineer_batch_features(
        self,
        ts_df: pd.DataFrame,
        production_row: Optional[pd.Series] = None,
    ) -> Dict[str, float]:
        """
        Full feature engineering pipeline for a single batch.
        Combines all feature types into a single feature vector.
        """
        features = {}

        # 1. Phase aggregations
        features.update(self.compute_phase_aggregations(ts_df))

        # 2. Spectral features for key signals
        for col in ["Power_Consumption_kW", "Vibration_mm_s", "Motor_Speed_RPM"]:
            if col in ts_df.columns:
                features.update(self.extract_spectral_features(ts_df, col))

        # 3. Change point features
        for col in ["Power_Consumption_kW", "Temperature_C", "Vibration_mm_s"]:
            if col in ts_df.columns:
                features.update(self.detect_change_points(ts_df, col))

        # 4. Energy-specific features
        features.update(self.compute_energy_features(ts_df, production_row))

        # 5. Cross-feature interactions
        if "Motor_Speed_RPM" in ts_df.columns and "Power_Consumption_kW" in ts_df.columns:
            motor = ts_df["Motor_Speed_RPM"].values
            power = ts_df["Power_Consumption_kW"].values
            mask = motor > 0
            if mask.sum() > 0:
                features["energy_per_rpm"] = float(
                    np.mean(power[mask] / motor[mask])
                )
            else:
                features["energy_per_rpm"] = 0.0

        return features

    def engineer_all_batches(
        self,
        ts_df: pd.DataFrame,
        production_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Engineer features for all batches.
        Returns a DataFrame with one row per batch.
        """
        batch_features = []

        for batch_id in ts_df["Batch_ID"].unique():
            batch_ts = ts_df[ts_df["Batch_ID"] == batch_id]

            prod_row = None
            if production_df is not None:
                match = production_df[production_df["Batch_ID"] == batch_id]
                if len(match) > 0:
                    prod_row = match.iloc[0]

            features = self.engineer_batch_features(batch_ts, prod_row)
            features["Batch_ID"] = batch_id
            batch_features.append(features)

        result = pd.DataFrame(batch_features)
        self.feature_names = [c for c in result.columns if c != "Batch_ID"]
        logger.info(f"Engineered {len(self.feature_names)} features for {len(batch_features)} batches")
        return result
