# ============================================================================
# Generate Synthetic Data Script
# Creates realistic pharmaceutical batch data for training and testing
# ============================================================================
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.data_layer.synthetic_data import SyntheticBatchDataGenerator


def main():
    print("=" * 60)
    print("Generating Synthetic Pharmaceutical Batch Data")
    print("=" * 60)

    generator = SyntheticBatchDataGenerator(n_batches=200, seed=42)

    # Generate time-series data
    print("\n[1/3] Generating time-series process data...")
    ts_data = generator.generate_time_series()
    ts_path = os.path.join("data", "synthetic_process_data.csv")
    os.makedirs("data", exist_ok=True)
    ts_data.to_csv(ts_path, index=False)
    print(f"  → Saved {len(ts_data)} rows to {ts_path}")
    print(f"  → Batches: {ts_data['Batch_ID'].nunique()}")
    print(f"  → Columns: {list(ts_data.columns)}")

    # Generate batch-level production data
    print("\n[2/3] Generating batch-level production data...")
    batch_data = generator.generate_batch_summary()
    batch_path = os.path.join("data", "synthetic_batch_data.csv")
    batch_data.to_csv(batch_path, index=False)
    print(f"  → Saved {len(batch_data)} batches to {batch_path}")
    print(f"  → Columns: {list(batch_data.columns)}")

    # Data summary
    print("\n[3/3] Data Summary:")
    print(f"  Quality metrics:")
    for col in ["Hardness", "Dissolution_Rate", "Content_Uniformity"]:
        if col in batch_data.columns:
            print(f"    {col}: mean={batch_data[col].mean():.1f}, "
                  f"std={batch_data[col].std():.1f}, "
                  f"range=[{batch_data[col].min():.1f}, {batch_data[col].max():.1f}]")

    print(f"\n  Energy metrics:")
    for col in ["Energy_Consumption_kWh", "CO2_Emissions_kg"]:
        if col in batch_data.columns:
            print(f"    {col}: mean={batch_data[col].mean():.1f}, "
                  f"std={batch_data[col].std():.1f}")

    print(f"\n✓ Data generation complete!")


if __name__ == "__main__":
    main()
