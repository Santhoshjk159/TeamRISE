# ============================================================================
# Data Preprocessing Pipeline
# Cleaning, normalization, outlier detection, missing value imputation
# ============================================================================
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import KNNImputer
import logging

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Comprehensive data preprocessing including:
    - Missing value detection and imputation
    - Outlier detection (Z-score, IQR, Isolation Forest)
    - Normalization and scaling
    - Validation checks
    """

    def __init__(self):
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_stats: Dict[str, Dict] = {}
        self._fitted = False

    def detect_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze and report missing values."""
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        report = pd.DataFrame({
            "missing_count": missing,
            "missing_percent": missing_pct,
            "dtype": df.dtypes,
        })
        return report[report["missing_count"] > 0]

    def impute_missing(
        self, df: pd.DataFrame, method: str = "knn", n_neighbors: int = 5
    ) -> pd.DataFrame:
        """Impute missing values using KNN, median, or forward-fill."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        non_numeric = df.select_dtypes(exclude=[np.number])

        if method == "knn":
            imputer = KNNImputer(n_neighbors=n_neighbors)
            imputed = pd.DataFrame(
                imputer.fit_transform(df[numeric_cols]),
                columns=numeric_cols,
                index=df.index,
            )
        elif method == "median":
            imputed = df[numeric_cols].fillna(df[numeric_cols].median())
        elif method == "ffill":
            imputed = df[numeric_cols].fillna(method="ffill").fillna(method="bfill")
        else:
            imputed = df[numeric_cols].fillna(0)

        result = pd.concat([non_numeric, imputed], axis=1)
        return result[df.columns]

    def detect_outliers(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "iqr",
        z_threshold: float = 3.0,
    ) -> pd.DataFrame:
        """
        Detect outliers using IQR or Z-score method.
        Returns boolean mask where True indicates outlier.
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        outlier_mask = pd.DataFrame(False, index=df.index, columns=columns)

        for col in columns:
            if method == "zscore":
                z_scores = np.abs(stats.zscore(df[col].dropna()))
                mask = pd.Series(False, index=df.index)
                mask[df[col].dropna().index] = z_scores > z_threshold
                outlier_mask[col] = mask
            elif method == "iqr":
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                outlier_mask[col] = (df[col] < lower) | (df[col] > upper)

        return outlier_mask

    def handle_outliers(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "clip",
    ) -> pd.DataFrame:
        """Handle outliers by clipping, removing, or replacing."""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        result = df.copy()
        for col in columns:
            Q1 = result[col].quantile(0.25)
            Q3 = result[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            if method == "clip":
                result[col] = result[col].clip(lower, upper)
            elif method == "median":
                mask = (result[col] < lower) | (result[col] > upper)
                result.loc[mask, col] = result[col].median()

        return result

    def fit_scalers(
        self, df: pd.DataFrame, columns: Optional[List[str]] = None,
        scaler_type: str = "standard"
    ) -> None:
        """Fit scalers on training data."""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            if scaler_type == "standard":
                scaler = StandardScaler()
            elif scaler_type == "minmax":
                scaler = MinMaxScaler()
            elif scaler_type == "robust":
                scaler = RobustScaler()
            else:
                scaler = StandardScaler()

            scaler.fit(df[[col]])
            self.scalers[col] = scaler

            self.feature_stats[col] = {
                "mean": df[col].mean(),
                "std": df[col].std(),
                "min": df[col].min(),
                "max": df[col].max(),
                "median": df[col].median(),
            }

        self._fitted = True

    def transform(
        self, df: pd.DataFrame, columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Apply fitted scalers to data."""
        result = df.copy()
        if columns is None:
            columns = [c for c in df.columns if c in self.scalers]

        for col in columns:
            if col in self.scalers:
                result[col] = self.scalers[col].transform(df[[col]])

        return result

    def inverse_transform(
        self, df: pd.DataFrame, columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Reverse scaling."""
        result = df.copy()
        if columns is None:
            columns = [c for c in df.columns if c in self.scalers]

        for col in columns:
            if col in self.scalers:
                result[col] = self.scalers[col].inverse_transform(df[[col]])

        return result

    def validate_data(self, df: pd.DataFrame) -> Dict:
        """Run data quality validation checks."""
        checks = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "missing_values": int(df.isnull().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_columns": len(df.select_dtypes(include=[np.number]).columns),
            "issues": [],
        }

        if checks["missing_values"] > 0:
            checks["issues"].append(
                f"Found {checks['missing_values']} missing values"
            )
        if checks["duplicate_rows"] > 0:
            checks["issues"].append(
                f"Found {checks['duplicate_rows']} duplicate rows"
            )

        # Check for constant columns
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].std() == 0:
                checks["issues"].append(f"Column '{col}' has zero variance")

        checks["valid"] = len(checks["issues"]) == 0
        return checks

    def full_pipeline(
        self,
        df: pd.DataFrame,
        handle_missing: bool = True,
        handle_outliers_flag: bool = True,
        scale: bool = True,
    ) -> pd.DataFrame:
        """Run complete preprocessing pipeline."""
        result = df.copy()

        # 1. Handle missing values
        if handle_missing:
            missing_report = self.detect_missing_values(result)
            if len(missing_report) > 0:
                logger.info(f"Imputing {len(missing_report)} columns with missing values")
                result = self.impute_missing(result)

        # 2. Handle outliers
        if handle_outliers_flag:
            result = self.handle_outliers(result)

        # 3. Scale
        if scale:
            numeric_cols = result.select_dtypes(include=[np.number]).columns.tolist()
            if not self._fitted:
                self.fit_scalers(result, numeric_cols)
            result = self.transform(result, numeric_cols)

        return result
