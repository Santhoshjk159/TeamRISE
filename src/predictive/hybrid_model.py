# ============================================================================
# Hybrid Model: Physics-Informed + ML Ensemble
# Combines domain knowledge with data-driven learning
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from src.predictive.physics_informed import PharmaceuticalProcessPhysics
from src.predictive.multi_target_model import MultiTargetPredictor
import logging

logger = logging.getLogger(__name__)


class HybridPredictor:
    """
    Hybrid prediction model that combines:
    1. Physics-informed predictions (domain knowledge)
    2. ML-based predictions (data-driven)
    3. Residual learning (ML corrects physics model errors)

    Architecture:
    - Physics model provides baseline predictions
    - ML model learns residuals (actual - physics_predicted)
    - Final prediction = physics + ML_residual
    - Adaptive weighting based on prediction confidence
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.physics_model = PharmaceuticalProcessPhysics()
        self.residual_model = MultiTargetPredictor(config)
        self.direct_model = MultiTargetPredictor(config)
        self.physics_weight = 0.3  # Learnable
        self.ml_weight = 0.7
        self._fitted = False

    def _compute_physics_features(
        self, production_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Compute physics-based predictions for all batches."""
        physics_features = []
        for _, row in production_df.iterrows():
            params = {
                "Granulation_Time": row.get("Granulation_Time", 15),
                "Binder_Amount": row.get("Binder_Amount", 8.5),
                "Drying_Temp": row.get("Drying_Temp", 60),
                "Drying_Time": row.get("Drying_Time", 25),
                "Compression_Force": row.get("Compression_Force", 12.5),
                "Machine_Speed": row.get("Machine_Speed", 150),
                "Lubricant_Conc": row.get("Lubricant_Conc", 1.0),
            }
            physics_pred = self.physics_model.predict_all(params)
            physics_features.append(physics_pred)

        return pd.DataFrame(physics_features, index=production_df.index)

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.DataFrame,
        production_df: pd.DataFrame,
        targets: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Train the hybrid model:
        1. Compute physics predictions
        2. Calculate residuals
        3. Train ML model on residuals
        4. Optimize mixing weights
        """
        if targets is None:
            targets = [t for t in self.residual_model.all_targets if t in y.columns]

        # Step 1: Physics predictions
        physics_df = self._compute_physics_features(production_df)

        # Step 2: Augment features with physics predictions
        X_augmented = pd.concat([X, physics_df], axis=1)
        # Remove duplicate or all-NaN columns
        X_augmented = X_augmented.loc[:, ~X_augmented.columns.duplicated()]
        X_augmented = X_augmented.dropna(axis=1, how="all")
        X_augmented = X_augmented.fillna(0)

        # Step 3: Train direct model with augmented features
        direct_metrics = self.direct_model.fit(X_augmented, y, targets)

        # Step 4: Compute residuals for physics-correctable targets
        target_mapping = {
            "Hardness": "physics_predicted_hardness",
            "Friability": "physics_predicted_friability",
            "Energy_Consumption_kWh": "physics_total_energy_kwh",
        }

        residuals = y.copy()
        for target, physics_col in target_mapping.items():
            if target in y.columns and physics_col in physics_df.columns:
                residuals[target] = y[target] - physics_df[physics_col]

        # Step 5: Train residual model
        residual_targets = [t for t in targets if t in target_mapping]
        if residual_targets:
            self.residual_model.fit(X, residuals, residual_targets)

        # Step 6: Optimize weights using validation performance
        self._optimize_weights(X_augmented, y, physics_df, targets, target_mapping)

        self._fitted = True

        logger.info(
            f"Hybrid model trained. Physics weight: {self.physics_weight:.2f}, "
            f"ML weight: {self.ml_weight:.2f}"
        )

        return direct_metrics

    def _optimize_weights(
        self, X_aug, y, physics_df, targets, target_mapping
    ):
        """Find optimal physics/ML mixing weights."""
        best_weight = 0.3
        best_score = -np.inf

        for w in np.arange(0.0, 0.5, 0.05):
            scores = []
            for target in targets:
                if target in target_mapping:
                    phys_col = target_mapping[target]
                    if phys_col in physics_df.columns:
                        phys_pred = physics_df[phys_col].values
                        ml_pred = self.direct_model.predict(X_aug)[target].values
                        hybrid_pred = w * phys_pred + (1 - w) * ml_pred

                        actual = y[target].values
                        valid = ~np.isnan(actual)
                        if valid.sum() > 0:
                            ss_res = np.sum((actual[valid] - hybrid_pred[valid]) ** 2)
                            ss_tot = np.sum((actual[valid] - actual[valid].mean()) ** 2)
                            r2 = 1 - ss_res / (ss_tot + 1e-10)
                            scores.append(r2)

            if scores and np.mean(scores) > best_score:
                best_score = np.mean(scores)
                best_weight = w

        self.physics_weight = best_weight
        self.ml_weight = 1 - best_weight

    def predict(
        self, X: pd.DataFrame, production_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate hybrid predictions."""
        if not self._fitted:
            raise ValueError("Model not fitted")

        # Physics predictions
        physics_df = self._compute_physics_features(production_df)

        # Augmented features
        X_aug = pd.concat([X, physics_df], axis=1)
        X_aug = X_aug.loc[:, ~X_aug.columns.duplicated()]
        X_aug = X_aug.fillna(0)

        # ML predictions
        ml_predictions = self.direct_model.predict(X_aug)

        # Hybrid combination for physics-mappable targets
        target_mapping = {
            "Hardness": "physics_predicted_hardness",
            "Friability": "physics_predicted_friability",
            "Energy_Consumption_kWh": "physics_total_energy_kwh",
        }

        result = ml_predictions.copy()
        for target, physics_col in target_mapping.items():
            if target in result.columns and physics_col in physics_df.columns:
                result[target] = (
                    self.physics_weight * physics_df[physics_col].values
                    + self.ml_weight * ml_predictions[target].values
                )

        return result

    def get_prediction_confidence(
        self, X: pd.DataFrame, production_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Estimate prediction confidence based on physics-ML agreement.
        High agreement → high confidence.
        """
        physics_df = self._compute_physics_features(production_df)
        X_aug = pd.concat([X, physics_df], axis=1)
        X_aug = X_aug.loc[:, ~X_aug.columns.duplicated()]
        X_aug = X_aug.fillna(0)

        ml_pred = self.direct_model.predict(X_aug)

        confidence = {}
        target_mapping = {
            "Hardness": "physics_predicted_hardness",
            "Energy_Consumption_kWh": "physics_total_energy_kwh",
        }

        for target, phys_col in target_mapping.items():
            if target in ml_pred.columns and phys_col in physics_df.columns:
                deviation = np.abs(
                    ml_pred[target].values - physics_df[phys_col].values
                )
                max_val = np.maximum(
                    np.abs(ml_pred[target].values),
                    np.abs(physics_df[phys_col].values)
                ) + 1e-10
                confidence[target] = 1 - np.clip(deviation / max_val, 0, 1)

        return pd.DataFrame(confidence, index=X.index)
