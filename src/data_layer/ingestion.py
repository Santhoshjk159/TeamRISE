# ============================================================================
# Data Ingestion Pipeline
# Handles real-time and batch data ingestion from multiple sources
# ============================================================================
import pandas as pd
import numpy as np
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """
    Handles data ingestion from:
    - Excel/CSV files (historical data)
    - Real-time simulated IIoT streams
    - Database connections
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._cache: Dict[str, pd.DataFrame] = {}

    def load_excel_data(
        self, process_file: str, production_file: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load data from Excel files (original hackathon data)."""
        process_df = pd.read_excel(process_file)
        production_df = pd.read_excel(production_file)
        logger.info(
            f"Loaded process data: {process_df.shape}, "
            f"production data: {production_df.shape}"
        )
        return process_df, production_df

    def load_csv_data(
        self,
        process_file: Optional[str] = None,
        production_file: Optional[str] = None,
    ) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Load from CSV files (synthetic or processed)."""
        process_df = None
        production_df = None
        if process_file and os.path.exists(process_file):
            process_df = pd.read_csv(process_file)
        if production_file and os.path.exists(production_file):
            production_df = pd.read_csv(production_file)
        return process_df, production_df

    def load_default_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load the default generated dataset."""
        prod_path = os.path.join(self.data_dir, "batch_production_data.csv")
        ts_path = os.path.join(self.data_dir, "batch_process_timeseries.csv")

        if not os.path.exists(prod_path):
            # Generate if not available
            from src.data_layer.synthetic_data import generate_and_save
            generate_and_save(n_batches=200, output_dir=self.data_dir)

        prod_df = pd.read_csv(prod_path)
        ts_df = pd.read_csv(ts_path)

        self._cache["production"] = prod_df
        self._cache["timeseries"] = ts_df
        return prod_df, ts_df

    def simulate_realtime_batch(
        self, batch_params: Dict, noise_level: float = 0.05
    ) -> pd.DataFrame:
        """Simulate a real-time IIoT data stream for a new batch."""
        from src.data_layer.synthetic_data import SyntheticBatchDataGenerator
        gen = SyntheticBatchDataGenerator(seed=int(datetime.now().timestamp()) % 10000)
        ts = gen.generate_process_timeseries("LIVE_001", batch_params)
        return ts

    def get_batch_data(
        self, batch_id: str
    ) -> Tuple[Optional[pd.Series], Optional[pd.DataFrame]]:
        """Retrieve production + time-series data for a specific batch."""
        prod_df = self._cache.get("production")
        ts_df = self._cache.get("timeseries")

        production_row = None
        timeseries = None

        if prod_df is not None:
            match = prod_df[prod_df["Batch_ID"] == batch_id]
            if len(match) > 0:
                production_row = match.iloc[0]

        if ts_df is not None:
            timeseries = ts_df[ts_df["Batch_ID"] == batch_id].copy()

        return production_row, timeseries

    def get_batch_ids(self) -> List[str]:
        """Return all available batch IDs."""
        prod_df = self._cache.get("production")
        if prod_df is not None:
            return prod_df["Batch_ID"].unique().tolist()
        return []
