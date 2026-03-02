# ============================================================================
# Full System Demo Script
# End-to-end demonstration of all system capabilities
# ============================================================================
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import json


def demo_data_layer():
    """Demonstrate data pipeline capabilities."""
    print("\n" + "=" * 60)
    print("DEMO 1: Data Layer")
    print("=" * 60)

    from src.data_layer.synthetic_data import SyntheticBatchDataGenerator
    from src.data_layer.preprocessing import DataPreprocessor
    from src.data_layer.feature_engineering import FeatureEngineer

    # Generate data
    gen = SyntheticBatchDataGenerator(n_batches=50, seed=42)
    ts_data = gen.generate_time_series()
    batch_data = gen.generate_batch_summary()

    print(f"  Generated {ts_data['Batch_ID'].nunique()} batches")
    print(f"  Time-series: {len(ts_data)} rows × {len(ts_data.columns)} cols")
    print(f"  Batch summary: {len(batch_data)} rows × {len(batch_data.columns)} cols")

    # Preprocess
    preprocessor = DataPreprocessor()
    processed = preprocessor.full_pipeline(ts_data)
    print(f"  After preprocessing: {processed.shape}")

    # Feature engineering
    engineer = FeatureEngineer()
    features = engineer.engineer_all_batches(ts_data)
    print(f"  Engineered features: {features.shape}")
    print(f"  Feature columns: {list(features.columns[:10])}...")

    return ts_data, batch_data, features


def demo_predictive_layer(batch_data):
    """Demonstrate predictive capabilities."""
    print("\n" + "=" * 60)
    print("DEMO 2: Predictive Layer")
    print("=" * 60)

    from src.predictive.physics_informed import PharmaceuticalProcessPhysics

    physics = PharmaceuticalProcessPhysics()

    # Test physics predictions
    sample = {
        "Granulation_Time": 35, "Binder_Amount": 5.0,
        "Drying_Temp": 60, "Drying_Time": 45,
        "Compression_Force": 12, "Machine_Speed": 600,
        "Lubricant_Conc": 1.0, "Moisture_Content": 3.0,
    }

    physics_preds = physics.predict_all(sample)
    print(f"  Physics predictions for sample batch:")
    for k, v in physics_preds.items():
        print(f"    {k}: {v:.2f}")

    return physics_preds


def demo_energy_intelligence(ts_data):
    """Demonstrate energy pattern analysis."""
    print("\n" + "=" * 60)
    print("DEMO 3: Energy Intelligence")
    print("=" * 60)

    from src.energy_intelligence.spectral_analysis import SpectralAnalyzer
    from src.energy_intelligence.drift_detection import SignatureDriftDetector
    from src.energy_intelligence.reliability_scoring import ReliabilityScorer

    # Spectral analysis
    analyzer = SpectralAnalyzer()
    batch_T001 = ts_data[ts_data["Batch_ID"] == ts_data["Batch_ID"].unique()[0]]

    if "Power_Consumption_kW" in batch_T001.columns:
        signal = batch_T001["Power_Consumption_kW"].values
        features = analyzer.extract_spectral_features(signal)
        print(f"  Spectral features: {len(features)} extracted")
        for k, v in list(features.items())[:5]:
            print(f"    {k}: {v:.4f}")

    # Reliability scoring
    scorer = ReliabilityScorer()
    score = scorer.compute_reliability_score(batch_T001)
    print(f"\n  Reliability Score:")
    for k, v in score.items():
        print(f"    {k}: {v}")


def demo_optimization():
    """Demonstrate multi-objective optimization."""
    print("\n" + "=" * 60)
    print("DEMO 4: Multi-Objective Optimization")
    print("=" * 60)

    from src.optimization.nsga2 import NSGA2Optimizer

    optimizer = NSGA2Optimizer(
        n_variables=4,
        n_objectives=2,
        bounds=[(3, 25), (200, 1000), (40, 80), (0.5, 10)],
        pop_size=50,
    )

    def evaluate(x):
        hardness = 40 + 5.5 * x[0] - 2 * x[3]
        energy = 0.3 * x[0] * x[1] / 600 + 0.5 * x[2] / 60
        return [-hardness, energy]

    optimizer.evaluate = evaluate
    solutions = optimizer.optimize(n_generations=50)
    best = optimizer.get_best_solution(solutions)

    print(f"  Pareto front: {len(solutions)} solutions")
    print(f"  Best balanced:")
    print(f"    Hardness: {-best.objectives[0]:.1f}")
    print(f"    Energy: {best.objectives[1]:.2f} kWh")

    return solutions


def demo_golden_signature():
    """Demonstrate golden signature framework."""
    print("\n" + "=" * 60)
    print("DEMO 5: Golden Signature Framework")
    print("=" * 60)

    from src.golden_signature.signature import GoldenSignatureManager

    manager = GoldenSignatureManager()

    # Create signature from optimal parameters
    signature = manager.create_signature(
        process_parameters={
            "Compression_Force": 14.5,
            "Machine_Speed": 550,
            "Drying_Temp": 58,
            "Moisture_Content": 2.8,
        },
        quality_outcomes={
            "Hardness": 102,
            "Dissolution_Rate": 92,
            "Content_Uniformity": 98.5,
        },
        energy_metrics={"Total_kWh": 45, "CO2_kg": 22},
        scenario_tags=["optimal", "low_energy"],
    )

    print(f"  Created signature: {signature.signature_id}")
    print(f"  Confidence: {signature.confidence_score:.2f}")
    print(f"  Approved: {signature.approved}")

    # Approve it (HITL)
    manager.approve(signature.signature_id, True)
    print(f"  → Approved signature (HITL)")

    # Get best
    best = manager.get_best()
    print(f"  Best signature: {best.signature_id}")


def demo_digital_twin():
    """Demonstrate digital twin simulation."""
    print("\n" + "=" * 60)
    print("DEMO 6: Digital Twin")
    print("=" * 60)

    from src.digital_twin.twin_engine import DigitalTwinEngine

    twin = DigitalTwinEngine()

    # Full simulation
    result = twin.simulate_full_batch(
        parameters={"compression_force": 14, "drying_temp": 55}
    )

    print(f"  Simulated batch: {result['batch_id']}")
    quality = result["process"]["quality_predictions"]
    print(f"  Quality predictions:")
    for k, v in quality.items():
        print(f"    {k}: {v:.2f}")

    energy = result["energy"]
    print(f"  Energy: {energy['total_energy_kwh']:.1f} kWh")
    print(f"  CO2: {energy['total_co2_kg']:.2f} kg")
    print(f"  All in spec: {result['quality_within_spec']['all_in_spec']}")

    # What-if analysis
    scenarios = twin.run_scenario_analysis(
        base_params=twin.process_twin._default_parameters(),
        scenarios={
            "high_compression": {"compression_force": 18},
            "low_compression": {"compression_force": 8},
            "fast_drying": {"drying_temp": 75, "drying_time": 30},
        },
    )

    print(f"\n  Scenario comparison ({len(scenarios['comparison_table'])} scenarios):")
    print(f"  Best scenario: {scenarios['best_scenario']}")


def demo_carbon_engine():
    """Demonstrate carbon target engine."""
    print("\n" + "=" * 60)
    print("DEMO 7: Carbon Target Engine")
    print("=" * 60)

    from src.carbon.target_engine import CarbonTargetEngine

    engine = CarbonTargetEngine()

    target = engine.compute_batch_target(batch_energy_kwh=50)
    print(f"  Carbon target: {target['target_co2_kg']:.2f} kg CO2")

    # Record some actuals
    for energy in [48, 52, 46, 50, 44]:
        engine.record_actual(energy * 0.5)

    dashboard = engine.get_dashboard()
    print(f"  Dashboard: {json.dumps(dashboard, indent=2, default=str)}")


def demo_decision_engine():
    """Demonstrate real-time decision engine."""
    print("\n" + "=" * 60)
    print("DEMO 8: Decision Engine")
    print("=" * 60)

    from src.decision_engine.realtime_monitor import RealTimeDecisionEngine
    from src.decision_engine.deviation_detector import DeviationDetector
    from src.decision_engine.recommender import CorrectiveActionRecommender

    engine = RealTimeDecisionEngine()
    detector = DeviationDetector()
    recommender = CorrectiveActionRecommender()

    # Simulate some sensor data with a deviation
    np.random.seed(42)
    n = 30
    data = pd.DataFrame({
        "Temperature_C": np.concatenate([
            np.ones(20) * 50 + np.random.normal(0, 1, 20),
            np.ones(10) * 58 + np.random.normal(0, 1, 10),  # Spike!
        ]),
        "Power_Consumption_kW": np.ones(n) * 15 + np.random.normal(0, 0.5, n),
        "Vibration_mm_s": np.ones(n) * 2 + np.random.normal(0, 0.2, n),
        "Motor_Speed_RPM": np.ones(n) * 500 + np.random.normal(0, 10, n),
        "Phase": ["Granulation"] * n,
    })

    # Monitor
    decisions = engine.monitor_batch("DEMO_001", data, "Granulation")
    print(f"  Decisions generated: {len(decisions)}")
    for d in decisions:
        print(f"    [{d.severity.value}] {d.message[:80]}")

    # Detect deviations
    devs = detector.detect_deviations(data, phase="Granulation")
    print(f"\n  Deviations detected: {len(devs)}")
    for d in devs:
        print(f"    {d.parameter}: {d.deviation_type} (magnitude={d.magnitude:.2f})")

    # Get recommendations
    if devs:
        actions = recommender.recommend(devs, "Granulation")
        print(f"\n  Corrective actions: {len(actions)}")
        for a in actions:
            print(f"    P{a.priority}: {a.action} ({a.adjustment_value:+.1f} {a.adjustment_unit})")


def demo_roi():
    """Demonstrate ROI calculation."""
    print("\n" + "=" * 60)
    print("DEMO 9: ROI Calculator")
    print("=" * 60)

    from src.validation.roi_calculator import ROICalculator

    calc = ROICalculator()
    roi = calc.calculate_roi(
        baseline_metrics={
            "overall_quality_score": 78,
            "defect_rate": 0.06,
            "rework_rate": 0.10,
            "avg_energy_kwh": 55,
            "avg_co2_kg": 28,
        },
        optimized_metrics={
            "overall_quality_score": 89,
            "defect_rate": 0.02,
            "rework_rate": 0.04,
            "avg_energy_kwh": 46,
            "avg_co2_kg": 22,
        },
    )

    print(calc.generate_executive_summary(roi))


def main():
    print("=" * 60)
    print("AI-DRIVEN MANUFACTURING INTELLIGENCE ENGINE")
    print("Full System Demonstration")
    print("=" * 60)

    ts_data, batch_data, features = demo_data_layer()
    demo_predictive_layer(batch_data)
    demo_energy_intelligence(ts_data)
    demo_optimization()
    demo_golden_signature()
    demo_digital_twin()
    demo_carbon_engine()
    demo_decision_engine()
    demo_roi()

    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
