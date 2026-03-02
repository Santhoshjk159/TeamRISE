# ============================================================================
# Train Models Script
# Trains ML models on batch data (real or synthetic)
# ============================================================================
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import json
from src.predictive.training_pipeline import TrainingPipeline


def main():
    print("=" * 60)
    print("Training Manufacturing Intelligence Models")
    print("=" * 60)

    # Check for data
    data_sources = [
        "data/synthetic_batch_data.csv",
        "_h_batch_production_data.xlsx",
    ]

    data_path = None
    for src in data_sources:
        if os.path.exists(src):
            data_path = src
            break

    if data_path is None:
        print("No data found. Run scripts/generate_data.py first.")
        print("  python scripts/generate_data.py")
        return

    print(f"\nUsing data: {data_path}")

    # Load data
    if data_path.endswith(".xlsx"):
        df = pd.read_excel(data_path)
    else:
        df = pd.read_csv(data_path)

    print(f"  Loaded {len(df)} records with {len(df.columns)} features")

    # Initialize pipeline
    pipeline = TrainingPipeline()

    # Run training
    print("\nStarting training pipeline...")
    print("-" * 40)

    try:
        results = pipeline.run(batch_data=df)

        print("\n" + "=" * 40)
        print("TRAINING RESULTS")
        print("=" * 40)

        if "metrics" in results:
            for target, metrics in results["metrics"].items():
                print(f"\n  {target}:")
                for metric, value in metrics.items():
                    print(f"    {metric}: {value:.4f}")

        # Save results
        os.makedirs("models", exist_ok=True)
        results_path = "models/training_results.json"

        serializable = {}
        for key, val in results.items():
            if isinstance(val, dict):
                serializable[key] = {
                    k: (float(v) if hasattr(v, "__float__") else str(v))
                    for k, v in val.items()
                }
            else:
                serializable[key] = str(val)

        with open(results_path, "w") as f:
            json.dump(serializable, f, indent=2, default=str)

        print(f"\n✓ Training complete! Results saved to {results_path}")

    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
