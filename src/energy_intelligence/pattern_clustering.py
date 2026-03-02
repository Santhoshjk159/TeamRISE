# ============================================================================
# Energy Pattern Clustering
# Clusters energy consumption waveforms to identify operational modes
# ============================================================================
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from typing import Dict, List, Optional, Tuple
from scipy.spatial.distance import cdist
import logging

logger = logging.getLogger(__name__)


class EnergyPatternClustering:
    """
    Clusters energy consumption patterns across batches to:
    - Identify operational modes/regimes
    - Detect anomalous energy profiles
    - Group similar batches for golden signature matching
    - Map energy patterns to process states
    """

    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.kmeans: Optional[KMeans] = None
        self.scaler = StandardScaler()
        self.cluster_centers: Optional[np.ndarray] = None
        self.cluster_labels: Optional[np.ndarray] = None
        self.cluster_profiles: Dict[int, Dict] = {}
        self._fitted = False

    def _extract_waveform_features(
        self, ts_df: pd.DataFrame, batch_id: str,
        power_col: str = "Power_Consumption_kW",
    ) -> Dict[str, float]:
        """Extract feature vector from a batch's energy waveform."""
        batch_data = ts_df[ts_df["Batch_ID"] == batch_id]
        power = batch_data[power_col].values

        if len(power) == 0:
            return {}

        features = {}

        # Statistical features
        features["power_mean"] = float(np.mean(power))
        features["power_std"] = float(np.std(power))
        features["power_max"] = float(np.max(power))
        features["power_min"] = float(np.min(power))
        features["power_range"] = float(np.ptp(power))
        features["power_skew"] = float(pd.Series(power).skew())
        features["power_kurtosis"] = float(pd.Series(power).kurtosis())

        # Energy total (kWh)
        features["total_energy"] = float(np.sum(power) / 60.0)

        # Peak-to-average ratio
        features["peak_avg_ratio"] = float(
            np.max(power) / (np.mean(power) + 1e-10)
        )

        # Ramp characteristics
        diff_power = np.diff(power)
        if len(diff_power) > 0:
            features["max_ramp_up"] = float(np.max(diff_power))
            features["max_ramp_down"] = float(np.min(diff_power))
            features["avg_ramp_rate"] = float(np.mean(np.abs(diff_power)))
        else:
            features["max_ramp_up"] = 0.0
            features["max_ramp_down"] = 0.0
            features["avg_ramp_rate"] = 0.0

        # Phase-level energy distribution
        for phase, group in batch_data.groupby("Phase"):
            phase_power = group[power_col].values
            features[f"phase_{phase}_energy_pct"] = float(
                np.sum(phase_power) / (np.sum(power) + 1e-10) * 100
            )

        # Autocorrelation lag-1
        if len(power) > 1:
            autocorr = np.corrcoef(power[:-1], power[1:])[0, 1]
            features["autocorrelation_lag1"] = float(autocorr) if not np.isnan(autocorr) else 0.0
        else:
            features["autocorrelation_lag1"] = 0.0

        return features

    def fit(
        self, ts_df: pd.DataFrame,
        batch_ids: Optional[List[str]] = None,
    ) -> Dict:
        """
        Fit clustering model on energy waveform features.
        """
        if batch_ids is None:
            batch_ids = ts_df["Batch_ID"].unique().tolist()

        # Extract features for all batches
        feature_dicts = []
        valid_ids = []
        for bid in batch_ids:
            features = self._extract_waveform_features(ts_df, bid)
            if features:
                feature_dicts.append(features)
                valid_ids.append(bid)

        if len(feature_dicts) < self.n_clusters:
            logger.warning(
                f"Not enough batches ({len(feature_dicts)}) for "
                f"{self.n_clusters} clusters"
            )
            self.n_clusters = max(2, len(feature_dicts) // 2)

        feature_df = pd.DataFrame(feature_dicts, index=valid_ids).fillna(0)

        # Scale features
        X_scaled = self.scaler.fit_transform(feature_df)

        # Find optimal n_clusters using silhouette score
        best_score = -1
        best_k = self.n_clusters
        for k in range(2, min(self.n_clusters + 3, len(valid_ids))):
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels)
            if score > best_score:
                best_score = score
                best_k = k

        # Final clustering
        self.n_clusters = best_k
        self.kmeans = KMeans(
            n_clusters=self.n_clusters, random_state=42, n_init=10
        )
        self.cluster_labels = self.kmeans.fit_predict(X_scaled)
        self.cluster_centers = self.kmeans.cluster_centers_

        # Build cluster profiles
        for cluster_id in range(self.n_clusters):
            mask = self.cluster_labels == cluster_id
            cluster_features = feature_df[mask]
            self.cluster_profiles[cluster_id] = {
                "n_batches": int(mask.sum()),
                "batch_ids": [valid_ids[i] for i in np.where(mask)[0]],
                "avg_energy": float(cluster_features["total_energy"].mean()),
                "avg_power": float(cluster_features["power_mean"].mean()),
                "avg_peak_ratio": float(cluster_features["peak_avg_ratio"].mean()),
                "silhouette_score": float(best_score),
            }

        self._fitted = True

        return {
            "n_clusters": self.n_clusters,
            "silhouette_score": round(best_score, 4),
            "cluster_profiles": self.cluster_profiles,
        }

    def predict_cluster(
        self, ts_df: pd.DataFrame, batch_id: str
    ) -> Dict:
        """Predict which cluster a new batch belongs to."""
        if not self._fitted:
            raise ValueError("Model not fitted")

        features = self._extract_waveform_features(ts_df, batch_id)
        if not features:
            return {"cluster": -1, "confidence": 0.0}

        # Use same feature columns as training
        feature_vec = pd.DataFrame([features]).fillna(0)
        # Align columns with training data
        training_cols = self.scaler.feature_names_in_
        for col in training_cols:
            if col not in feature_vec.columns:
                feature_vec[col] = 0.0
        feature_vec = feature_vec[training_cols]

        X_scaled = self.scaler.transform(feature_vec)
        cluster = self.kmeans.predict(X_scaled)[0]

        # Confidence based on distance to cluster center
        distances = cdist(X_scaled, self.cluster_centers, metric="euclidean")[0]
        min_dist = distances[cluster]
        max_dist = np.max(distances)
        confidence = 1 - (min_dist / (max_dist + 1e-10))

        return {
            "cluster": int(cluster),
            "confidence": round(float(confidence), 4),
            "distances_to_centers": {
                str(i): round(float(d), 4)
                for i, d in enumerate(distances)
            },
            "cluster_profile": self.cluster_profiles.get(cluster, {}),
        }

    def detect_anomalous_pattern(
        self, ts_df: pd.DataFrame, batch_id: str,
        threshold: float = 2.0,
    ) -> Dict:
        """
        Detect if a batch has an anomalous energy pattern
        (far from all cluster centers).
        """
        result = self.predict_cluster(ts_df, batch_id)

        if result["cluster"] == -1:
            return {"is_anomalous": True, "reason": "No features extracted"}

        min_distance = min(
            float(d) for d in result["distances_to_centers"].values()
        )

        # Compare to average intra-cluster distance
        avg_intra_dist = np.mean([
            np.mean(cdist(
                self.cluster_centers[[i]],
                self.scaler.transform(
                    pd.DataFrame([
                        self._extract_waveform_features(ts_df, bid)
                        for bid in self.cluster_profiles[i].get("batch_ids", [])[:5]
                    ]).fillna(0).reindex(
                        columns=self.scaler.feature_names_in_, fill_value=0
                    )
                ),
                metric="euclidean",
            ))
            for i in range(self.n_clusters)
            if len(self.cluster_profiles[i].get("batch_ids", [])) > 0
        ])

        is_anomalous = min_distance > threshold * avg_intra_dist

        return {
            "is_anomalous": bool(is_anomalous),
            "anomaly_score": round(float(min_distance / (avg_intra_dist + 1e-10)), 4),
            "threshold": threshold,
            "min_distance": round(float(min_distance), 4),
            "avg_intra_distance": round(float(avg_intra_dist), 4),
            "assigned_cluster": result["cluster"],
        }
