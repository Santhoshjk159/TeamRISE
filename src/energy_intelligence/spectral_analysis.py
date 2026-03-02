# ============================================================================
# Power Spectral Density Analysis
# FFT-based spectral analysis for energy consumption patterns
# ============================================================================
import numpy as np
import pandas as pd
from scipy import signal, fft as scipy_fft
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SpectralAnalyzer:
    """
    Performs power spectral density analysis on energy consumption
    time series to detect:
    - Dominant frequencies (equipment cycling patterns)
    - Harmonic distortion (motor health indicators)
    - Spectral anomalies (process deviations)
    - Energy waveform characteristics
    """

    def __init__(self, sampling_rate: float = 1.0):
        """
        Args:
            sampling_rate: Samples per minute (1.0 = 1 sample/minute)
        """
        self.sampling_rate = sampling_rate
        self.reference_spectrum: Optional[np.ndarray] = None

    def compute_psd(
        self, signal_data: np.ndarray, method: str = "welch",
        nperseg: int = 64,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute Power Spectral Density using Welch's method.

        Returns:
            (frequencies, power_spectral_density)
        """
        n = len(signal_data)
        nperseg = min(nperseg, n)

        if method == "welch":
            freqs, psd = signal.welch(
                signal_data,
                fs=self.sampling_rate,
                nperseg=nperseg,
                noverlap=nperseg // 2,
                window="hann",
                scaling="density",
            )
        elif method == "periodogram":
            freqs, psd = signal.periodogram(
                signal_data,
                fs=self.sampling_rate,
                window="hann",
                scaling="density",
            )
        else:
            # Raw FFT
            fft_vals = np.fft.rfft(signal_data * np.hanning(n))
            freqs = np.fft.rfftfreq(n, d=1.0 / self.sampling_rate)
            psd = np.abs(fft_vals) ** 2 / n

        return freqs, psd

    def harmonic_analysis(
        self, signal_data: np.ndarray,
        fundamental_freq: Optional[float] = None,
        n_harmonics: int = 7,
    ) -> Dict[str, float]:
        """
        Analyze harmonic content of the power signal.
        High harmonic distortion indicates motor or equipment issues.
        """
        freqs, psd = self.compute_psd(signal_data)

        # Find fundamental frequency if not provided
        if fundamental_freq is None:
            if len(psd) > 1:
                fund_idx = np.argmax(psd[1:]) + 1
                fundamental_freq = freqs[fund_idx]
            else:
                fundamental_freq = freqs[0] if len(freqs) > 0 else 1.0

        if fundamental_freq == 0:
            fundamental_freq = 0.01  # Avoid division by zero

        # Compute harmonic amplitudes
        harmonics = {}
        total_harmonic_power = 0
        fundamental_power = 0

        for h in range(1, n_harmonics + 1):
            target_freq = h * fundamental_freq
            if target_freq > freqs[-1]:
                break

            # Find closest frequency bin
            idx = np.argmin(np.abs(freqs - target_freq))
            power = psd[idx]

            harmonics[f"harmonic_{h}_freq"] = float(freqs[idx])
            harmonics[f"harmonic_{h}_power"] = float(power)

            if h == 1:
                fundamental_power = power
            else:
                total_harmonic_power += power

        # Total Harmonic Distortion (THD)
        if fundamental_power > 0:
            thd = np.sqrt(total_harmonic_power / fundamental_power) * 100
        else:
            thd = 0.0

        harmonics["THD_percent"] = float(thd)
        harmonics["fundamental_frequency"] = float(fundamental_freq)
        harmonics["fundamental_power"] = float(fundamental_power)

        # Harmonic distortion levels
        if thd < 5:
            harmonics["distortion_level"] = "normal"
        elif thd < 15:
            harmonics["distortion_level"] = "moderate"
        elif thd < 30:
            harmonics["distortion_level"] = "high"
        else:
            harmonics["distortion_level"] = "critical"

        return harmonics

    def spectral_features(
        self, signal_data: np.ndarray
    ) -> Dict[str, float]:
        """
        Extract comprehensive spectral features from power signal.
        """
        freqs, psd = self.compute_psd(signal_data)

        if len(psd) == 0:
            return {}

        features = {}

        # Spectral centroid
        total_power = np.sum(psd)
        if total_power > 0:
            features["spectral_centroid"] = float(
                np.sum(freqs * psd) / total_power
            )
        else:
            features["spectral_centroid"] = 0.0

        # Spectral bandwidth (spread)
        centroid = features["spectral_centroid"]
        if total_power > 0:
            features["spectral_bandwidth"] = float(
                np.sqrt(np.sum(((freqs - centroid) ** 2) * psd) / total_power)
            )
        else:
            features["spectral_bandwidth"] = 0.0

        # Spectral rolloff (95% energy)
        cumulative_power = np.cumsum(psd)
        rolloff_threshold = 0.95 * total_power
        rolloff_idx = np.searchsorted(cumulative_power, rolloff_threshold)
        rolloff_idx = min(rolloff_idx, len(freqs) - 1)
        features["spectral_rolloff"] = float(freqs[rolloff_idx])

        # Spectral flatness (tonality)
        log_psd = np.log(psd + 1e-10)
        features["spectral_flatness"] = float(
            np.exp(np.mean(log_psd)) / (np.mean(psd) + 1e-10)
        )

        # Spectral entropy
        psd_norm = psd / (total_power + 1e-10)
        features["spectral_entropy"] = float(
            -np.sum(psd_norm * np.log2(psd_norm + 1e-10))
        )

        # Spectral flux (change rate)
        if self.reference_spectrum is not None and len(self.reference_spectrum) == len(psd):
            features["spectral_flux"] = float(
                np.sum((psd - self.reference_spectrum) ** 2)
            )
        else:
            features["spectral_flux"] = 0.0

        # Peak frequency
        if len(psd) > 1:
            peak_idx = np.argmax(psd[1:]) + 1
            features["peak_frequency"] = float(freqs[peak_idx])
            features["peak_power"] = float(psd[peak_idx])
        else:
            features["peak_frequency"] = 0.0
            features["peak_power"] = 0.0

        # Band energies
        n_bands = 4
        band_edges = np.linspace(0, freqs[-1], n_bands + 1)
        for i in range(n_bands):
            mask = (freqs >= band_edges[i]) & (freqs < band_edges[i + 1])
            features[f"band_{i+1}_energy"] = float(np.sum(psd[mask]))

        # Update reference
        self.reference_spectrum = psd.copy()

        return features

    def analyze_batch_power(
        self, ts_df: pd.DataFrame,
        power_col: str = "Power_Consumption_kW",
    ) -> Dict[str, any]:
        """
        Complete spectral analysis for a batch's power consumption.
        Returns spectral features, harmonics, and health indicators.
        """
        power_signal = ts_df[power_col].values
        results = {}

        # Overall spectral features
        results["spectral_features"] = self.spectral_features(power_signal)

        # Harmonic analysis
        results["harmonics"] = self.harmonic_analysis(power_signal)

        # Phase-level analysis
        phase_spectra = {}
        for phase, group in ts_df.groupby("Phase"):
            if len(group) >= 4:
                phase_power = group[power_col].values
                phase_spectra[phase] = self.spectral_features(phase_power)
        results["phase_spectra"] = phase_spectra

        return results
