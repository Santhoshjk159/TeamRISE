# ============================================================================
# SHAP Explainability Module
# Feature importance, SHAP values, and model interpretability
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ModelExplainer:
    """
    Provides model explainability through:
    - SHAP value computation
    - Feature importance ranking
    - Prediction attribution
    - Counterfactual analysis
    """

    def __init__(self):
        self.shap_values_cache: Dict[str, Any] = {}
        self.explainer_cache: Dict[str, Any] = {}

    def compute_shap_values(
        self, model: Any, X: pd.DataFrame, target: str,
        max_samples: int = 100,
    ) -> Dict:
        """Compute SHAP values for a trained model."""
        try:
            import shap

            # Use appropriate explainer based on model type
            xgb_model = model["xgboost"]

            # TreeExplainer for tree-based models
            explainer = shap.TreeExplainer(xgb_model)

            # Subsample for performance
            if len(X) > max_samples:
                X_sample = X.sample(max_samples, random_state=42)
            else:
                X_sample = X

            shap_values = explainer.shap_values(X_sample)

            self.shap_values_cache[target] = shap_values
            self.explainer_cache[target] = explainer

            # Compute summary stats
            mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
            feature_ranking = sorted(
                zip(X.columns, mean_abs_shap),
                key=lambda x: x[1],
                reverse=True,
            )

            return {
                "target": target,
                "shap_values": shap_values,
                "feature_importance": [
                    {"feature": f, "importance": round(float(v), 6)}
                    for f, v in feature_ranking
                ],
                "top_features": [f for f, _ in feature_ranking[:10]],
                "expected_value": float(explainer.expected_value)
                if isinstance(explainer.expected_value, (int, float))
                else float(explainer.expected_value[0]),
            }
        except ImportError:
            logger.warning("SHAP not available, using feature importance fallback")
            return self._fallback_importance(model, X, target)

    def _fallback_importance(
        self, model: Any, X: pd.DataFrame, target: str
    ) -> Dict:
        """Fallback feature importance when SHAP is not available."""
        xgb_imp = model["xgboost"].feature_importances_
        rf_imp = model["random_forest"].feature_importances_
        combined = 0.6 * xgb_imp + 0.4 * rf_imp

        feature_ranking = sorted(
            zip(X.columns, combined),
            key=lambda x: x[1],
            reverse=True,
        )

        return {
            "target": target,
            "feature_importance": [
                {"feature": f, "importance": round(float(v), 6)}
                for f, v in feature_ranking
            ],
            "top_features": [f for f, _ in feature_ranking[:10]],
            "method": "fallback_feature_importance",
        }

    def explain_prediction(
        self, model: Any, X_single: pd.DataFrame, target: str,
        X_background: Optional[pd.DataFrame] = None,
    ) -> Dict:
        """
        Explain a single prediction - what features drive it
        above or below the baseline.
        """
        try:
            import shap

            xgb_model = model["xgboost"]
            if X_background is not None:
                explainer = shap.TreeExplainer(xgb_model)
            elif target in self.explainer_cache:
                explainer = self.explainer_cache[target]
            else:
                explainer = shap.TreeExplainer(xgb_model)

            shap_vals = explainer.shap_values(X_single)

            if len(shap_vals.shape) == 1:
                shap_vals = shap_vals.reshape(1, -1)

            contributions = sorted(
                zip(X_single.columns, shap_vals[0], X_single.iloc[0]),
                key=lambda x: abs(x[1]),
                reverse=True,
            )

            return {
                "target": target,
                "base_value": float(explainer.expected_value)
                if isinstance(explainer.expected_value, (int, float))
                else float(explainer.expected_value[0]),
                "prediction": float(
                    model["weight_xgb"] * xgb_model.predict(X_single)[0]
                    + model["weight_rf"] * model["random_forest"].predict(X_single)[0]
                ),
                "contributions": [
                    {
                        "feature": str(f),
                        "value": float(v),
                        "shap_impact": round(float(s), 4),
                        "direction": "positive" if s > 0 else "negative",
                    }
                    for f, s, v in contributions[:15]
                ],
            }
        except ImportError:
            return {"target": target, "method": "unavailable"}

    def counterfactual_analysis(
        self, model: Any, X_single: pd.DataFrame, target: str,
        desired_change: str = "increase",
        n_suggestions: int = 5,
    ) -> List[Dict]:
        """
        Generate counterfactual suggestions:
        "What would need to change to improve the prediction?"
        """
        explanation = self.explain_prediction(model, X_single, target)
        if "contributions" not in explanation:
            return []

        suggestions = []
        for contrib in explanation["contributions"][:n_suggestions]:
            feature = contrib["feature"]
            current_val = contrib["value"]
            shap_impact = contrib["shap_impact"]

            if desired_change == "increase" and shap_impact < 0:
                suggestion = {
                    "feature": feature,
                    "current_value": current_val,
                    "suggested_direction": "increase" if shap_impact < 0 else "decrease",
                    "estimated_impact": abs(shap_impact),
                    "reasoning": f"Increasing {feature} could improve {target} "
                                 f"by approximately {abs(shap_impact):.2f} units",
                }
                suggestions.append(suggestion)
            elif desired_change == "decrease" and shap_impact > 0:
                suggestion = {
                    "feature": feature,
                    "current_value": current_val,
                    "suggested_direction": "decrease",
                    "estimated_impact": abs(shap_impact),
                    "reasoning": f"Decreasing {feature} could lower {target} "
                                 f"by approximately {abs(shap_impact):.2f} units",
                }
                suggestions.append(suggestion)

        return suggestions
