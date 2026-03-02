# ============================================================================
# Multi-Target Prediction Model
# XGBoost + Random Forest ensemble with multi-output regression
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from sklearn.model_selection import cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    mean_absolute_percentage_error,
)
import xgboost as xgb
import joblib
import logging
import os

logger = logging.getLogger(__name__)


class MultiTargetPredictor:
    """
    Multi-target regression system for simultaneous prediction of:
    - Primary: Quality (Hardness, Dissolution Rate, Content Uniformity)
    - Secondary: Energy Consumption, CO2 Emissions
    - Yield: Tablet Weight, Friability

    Uses ensemble of XGBoost + Random Forest with stacking.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.models: Dict[str, Any] = {}
        self.feature_names: List[str] = []
        self.target_names: List[str] = []
        self.metrics: Dict[str, Dict[str, float]] = {}
        self._fitted = False

        # Default targets
        self.primary_targets = [
            "Hardness", "Dissolution_Rate", "Content_Uniformity"
        ]
        self.secondary_targets = [
            "Energy_Consumption_kWh", "CO2_Emissions_kg"
        ]
        self.yield_targets = [
            "Tablet_Weight", "Friability"
        ]

    @property
    def all_targets(self) -> List[str]:
        return self.primary_targets + self.secondary_targets + self.yield_targets

    def _create_xgboost_model(self, target: str) -> xgb.XGBRegressor:
        """Create an XGBoost model for a single target."""
        params = self.config.get("xgb_params", {})
        return xgb.XGBRegressor(
            n_estimators=params.get("n_estimators", 300),
            max_depth=params.get("max_depth", 6),
            learning_rate=params.get("learning_rate", 0.05),
            subsample=params.get("subsample", 0.8),
            colsample_bytree=params.get("colsample_bytree", 0.8),
            reg_alpha=params.get("reg_alpha", 0.1),
            reg_lambda=params.get("reg_lambda", 1.0),
            random_state=42,
            n_jobs=-1,
            objective="reg:squarederror",
        )

    def _create_rf_model(self, target: str) -> RandomForestRegressor:
        """Create a Random Forest model for a single target."""
        return RandomForestRegressor(
            n_estimators=200,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.DataFrame,
        targets: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Train ensemble models for each target.
        Returns cross-validation metrics.
        """
        if targets is None:
            targets = [t for t in self.all_targets if t in y.columns]

        self.feature_names = X.columns.tolist()
        self.target_names = targets

        X_np = X.values
        metrics = {}

        for target in targets:
            if target not in y.columns:
                logger.warning(f"Target '{target}' not found in data, skipping")
                continue

            y_target = y[target].values
            valid_mask = ~np.isnan(y_target)
            X_valid = X_np[valid_mask]
            y_valid = y_target[valid_mask]

            # Train XGBoost
            xgb_model = self._create_xgboost_model(target)
            xgb_model.fit(X_valid, y_valid)

            # Train Random Forest
            rf_model = self._create_rf_model(target)
            rf_model.fit(X_valid, y_valid)

            # Ensemble prediction (weighted average)
            self.models[target] = {
                "xgboost": xgb_model,
                "random_forest": rf_model,
                "weight_xgb": 0.6,
                "weight_rf": 0.4,
            }

            # Cross-validation metrics
            kf = KFold(n_splits=5, shuffle=True, random_state=42)
            cv_predictions = np.zeros_like(y_valid)

            for train_idx, val_idx in kf.split(X_valid):
                X_tr, X_val = X_valid[train_idx], X_valid[val_idx]
                y_tr, y_val = y_valid[train_idx], y_valid[val_idx]

                xgb_cv = self._create_xgboost_model(target)
                xgb_cv.fit(X_tr, y_tr)
                rf_cv = self._create_rf_model(target)
                rf_cv.fit(X_tr, y_tr)

                pred = 0.6 * xgb_cv.predict(X_val) + 0.4 * rf_cv.predict(X_val)
                cv_predictions[val_idx] = pred

            mae = mean_absolute_error(y_valid, cv_predictions)
            rmse = np.sqrt(mean_squared_error(y_valid, cv_predictions))
            r2 = r2_score(y_valid, cv_predictions)
            mape = mean_absolute_percentage_error(y_valid, cv_predictions) * 100

            metrics[target] = {
                "MAE": round(mae, 4),
                "RMSE": round(rmse, 4),
                "R2": round(r2, 4),
                "MAPE": round(mape, 2),
                "Accuracy": round((1 - mape / 100) * 100, 2),
                "n_samples": len(y_valid),
            }

            logger.info(
                f"[{target}] R²={r2:.4f}, MAE={mae:.4f}, "
                f"RMSE={rmse:.4f}, Accuracy={metrics[target]['Accuracy']:.1f}%"
            )

        self.metrics = metrics
        self._fitted = True
        return metrics

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Predict all targets for given features."""
        if not self._fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        predictions = {}
        X_np = X.values

        for target, model_dict in self.models.items():
            xgb_pred = model_dict["xgboost"].predict(X_np)
            rf_pred = model_dict["random_forest"].predict(X_np)
            ensemble_pred = (
                model_dict["weight_xgb"] * xgb_pred
                + model_dict["weight_rf"] * rf_pred
            )
            predictions[target] = ensemble_pred

        return pd.DataFrame(predictions, index=X.index)

    def predict_single(self, features: Dict[str, float]) -> Dict[str, float]:
        """Predict for a single batch (feature dict)."""
        X = pd.DataFrame([features])[self.feature_names]
        preds = self.predict(X)
        return preds.iloc[0].to_dict()

    def get_feature_importance(self, target: str) -> pd.DataFrame:
        """Get feature importance for a specific target."""
        if target not in self.models:
            raise ValueError(f"No model for target: {target}")

        xgb_imp = self.models[target]["xgboost"].feature_importances_
        rf_imp = self.models[target]["random_forest"].feature_importances_

        # Weighted average importance
        combined = 0.6 * xgb_imp + 0.4 * rf_imp

        importance_df = pd.DataFrame({
            "feature": self.feature_names,
            "importance_combined": combined,
            "importance_xgb": xgb_imp,
            "importance_rf": rf_imp,
        }).sort_values("importance_combined", ascending=False)

        return importance_df

    def save(self, model_dir: str = "models"):
        """Save all models to disk."""
        os.makedirs(model_dir, exist_ok=True)
        for target, model_dict in self.models.items():
            path = os.path.join(model_dir, f"model_{target}.joblib")
            joblib.dump(model_dict, path)
        # Save metadata
        meta = {
            "feature_names": self.feature_names,
            "target_names": self.target_names,
            "metrics": self.metrics,
        }
        joblib.dump(meta, os.path.join(model_dir, "model_metadata.joblib"))
        logger.info(f"Models saved to {model_dir}")

    def load(self, model_dir: str = "models"):
        """Load models from disk."""
        meta = joblib.load(os.path.join(model_dir, "model_metadata.joblib"))
        self.feature_names = meta["feature_names"]
        self.target_names = meta["target_names"]
        self.metrics = meta["metrics"]

        for target in self.target_names:
            path = os.path.join(model_dir, f"model_{target}.joblib")
            if os.path.exists(path):
                self.models[target] = joblib.load(path)

        self._fitted = True
        logger.info(f"Models loaded from {model_dir}")
