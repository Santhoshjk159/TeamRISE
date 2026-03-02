# ============================================================================
# Training Pipeline
# End-to-end model training, validation, and deployment pipeline
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from sklearn.model_selection import train_test_split
import logging
import os
import json
from datetime import datetime

from src.data_layer.ingestion import DataIngestionPipeline
from src.data_layer.preprocessing import DataPreprocessor
from src.data_layer.feature_engineering import FeatureEngineer
from src.predictive.multi_target_model import MultiTargetPredictor
from src.predictive.hybrid_model import HybridPredictor
from src.predictive.explainability import ModelExplainer

logger = logging.getLogger(__name__)


class TrainingPipeline:
    """
    Complete training pipeline:
    1. Data loading & validation
    2. Preprocessing
    3. Feature engineering
    4. Model training (standard + hybrid)
    5. Evaluation & explainability
    6. Model saving
    """

    def __init__(self, data_dir: str = "data", model_dir: str = "models"):
        self.data_dir = data_dir
        self.model_dir = model_dir
        self.ingestion = DataIngestionPipeline(data_dir)
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()
        self.predictor = MultiTargetPredictor()
        self.hybrid_predictor = HybridPredictor()
        self.explainer = ModelExplainer()

        # Pipeline artifacts
        self.production_df: Optional[pd.DataFrame] = None
        self.timeseries_df: Optional[pd.DataFrame] = None
        self.engineered_features: Optional[pd.DataFrame] = None
        self.X_train: Optional[pd.DataFrame] = None
        self.X_test: Optional[pd.DataFrame] = None
        self.y_train: Optional[pd.DataFrame] = None
        self.y_test: Optional[pd.DataFrame] = None
        self.metrics: Dict = {}

    def run(self, use_hybrid: bool = True) -> Dict:
        """Execute the complete training pipeline."""
        logger.info("=" * 60)
        logger.info("TRAINING PIPELINE STARTED")
        logger.info("=" * 60)

        results = {}

        # Step 1: Load data
        logger.info("Step 1: Loading data...")
        self.production_df, self.timeseries_df = self.ingestion.load_default_data()
        results["data_shape"] = {
            "production": self.production_df.shape,
            "timeseries": self.timeseries_df.shape,
        }

        # Step 2: Preprocess
        logger.info("Step 2: Preprocessing...")
        validation = self.preprocessor.validate_data(self.production_df)
        results["data_validation"] = validation

        self.production_df = self.preprocessor.impute_missing(self.production_df)
        self.production_df = self.preprocessor.handle_outliers(
            self.production_df,
            columns=[c for c in self.production_df.select_dtypes(include=[np.number]).columns
                     if c not in ["Batch_ID"]],
        )

        # Step 3: Feature engineering
        logger.info("Step 3: Engineering features...")
        self.engineered_features = self.feature_engineer.engineer_all_batches(
            self.timeseries_df, self.production_df
        )

        # Merge production parameters with engineered features
        merged = self.production_df.merge(
            self.engineered_features, on="Batch_ID", how="inner"
        )

        # Define feature and target columns
        feature_cols = [
            c for c in merged.columns
            if c not in ["Batch_ID"] + self.predictor.all_targets
        ]
        target_cols = [
            c for c in self.predictor.all_targets if c in merged.columns
        ]

        X = merged[feature_cols].fillna(0)
        y = merged[target_cols]

        # Step 4: Split
        logger.info("Step 4: Train/test split...")
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Step 5: Train models
        logger.info("Step 5: Training models...")
        standard_metrics = self.predictor.fit(self.X_train, self.y_train)
        results["standard_model_metrics"] = standard_metrics

        if use_hybrid:
            logger.info("Step 5b: Training hybrid model...")
            prod_train = self.production_df.iloc[self.X_train.index]
            hybrid_metrics = self.hybrid_predictor.fit(
                self.X_train, self.y_train, prod_train
            )
            results["hybrid_model_metrics"] = hybrid_metrics

        # Step 6: Evaluate on test set
        logger.info("Step 6: Test evaluation...")
        test_predictions = self.predictor.predict(self.X_test)
        test_metrics = {}
        for target in target_cols:
            if target in test_predictions.columns:
                actual = self.y_test[target].values
                predicted = test_predictions[target].values
                valid = ~np.isnan(actual)
                if valid.sum() > 0:
                    from sklearn.metrics import (
                        mean_absolute_error, mean_squared_error, r2_score,
                        mean_absolute_percentage_error,
                    )
                    mae = mean_absolute_error(actual[valid], predicted[valid])
                    rmse = np.sqrt(mean_squared_error(actual[valid], predicted[valid]))
                    r2 = r2_score(actual[valid], predicted[valid])
                    mape = mean_absolute_percentage_error(actual[valid], predicted[valid]) * 100

                    test_metrics[target] = {
                        "MAE": round(mae, 4),
                        "RMSE": round(rmse, 4),
                        "R2": round(r2, 4),
                        "MAPE": round(mape, 2),
                        "Accuracy": round((1 - mape / 100) * 100, 2),
                    }
        results["test_metrics"] = test_metrics

        # Step 7: Explainability
        logger.info("Step 7: Computing explainability...")
        explainability = {}
        for target in target_cols[:3]:  # Top 3 targets
            if target in self.predictor.models:
                importance = self.predictor.get_feature_importance(target)
                explainability[target] = importance.head(10).to_dict("records")
        results["feature_importance"] = explainability

        # Step 8: Save
        logger.info("Step 8: Saving models...")
        self.predictor.save(self.model_dir)

        # Save pipeline metadata
        meta = {
            "timestamp": datetime.now().isoformat(),
            "data_shape": {k: list(v) for k, v in results["data_shape"].items()},
            "n_features": len(feature_cols),
            "n_targets": len(target_cols),
            "test_metrics": results["test_metrics"],
        }
        os.makedirs(self.model_dir, exist_ok=True)
        with open(os.path.join(self.model_dir, "pipeline_metadata.json"), "w") as f:
            json.dump(meta, f, indent=2, default=str)

        self.metrics = results
        logger.info("=" * 60)
        logger.info("TRAINING PIPELINE COMPLETE")
        logger.info("=" * 60)

        return results
