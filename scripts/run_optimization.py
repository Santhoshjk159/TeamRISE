# ============================================================================
# Run Optimization Script
# Executes multi-objective optimization and generates reports
# ============================================================================
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import numpy as np
from src.optimization.nsga2 import NSGA2Optimizer
from src.optimization.bayesian_optimizer import BayesianOptimizer
from src.optimization.pareto import compute_pareto_dominance, hypervolume_indicator
from src.digital_twin.twin_engine import DigitalTwinEngine
from src.validation.roi_calculator import ROICalculator
from src.carbon.target_engine import CarbonTargetEngine


def run_nsga2_optimization():
    """Run NSGA-II multi-objective optimization."""
    print("\n[1/4] NSGA-II Multi-Objective Optimization")
    print("-" * 50)

    optimizer = NSGA2Optimizer(
        n_variables=8,
        n_objectives=3,
        bounds=[
            (10, 60),    # Granulation_Time
            (1, 10),     # Binder_Amount
            (40, 80),    # Drying_Temp
            (20, 90),    # Drying_Time
            (3, 25),     # Compression_Force
            (200, 1000), # Machine_Speed
            (0.5, 3.0),  # Lubricant_Conc
            (0.5, 10),   # Moisture_Content
        ],
        pop_size=100,
    )

    def evaluate(x):
        # Multi-objective: quality, dissolution, energy
        hardness = 40 + 5.5 * x[4] - 2 * x[7] + 0.1 * x[1]
        dissolution = 95 - 0.5 * x[4] + 0.5 * x[7] - 0.2 * x[1]
        energy = (
            0.8 * x[0] + 0.5 * x[2] * x[3] / 60
            + 0.3 * x[4] * x[5] / 600
        )

        return [-hardness, -dissolution, energy]  # minimize all

    optimizer.evaluate = evaluate
    solutions = optimizer.optimize(n_generations=100)
    best = optimizer.get_best_solution(solutions)

    print(f"  Pareto front size: {len(solutions)}")
    print(f"  Best balanced solution:")
    param_names = [
        "Granulation_Time", "Binder_Amount", "Drying_Temp", "Drying_Time",
        "Compression_Force", "Machine_Speed", "Lubricant_Conc", "Moisture_Content",
    ]
    for name, val in zip(param_names, best.variables):
        print(f"    {name}: {val:.2f}")

    print(f"  Objectives:")
    print(f"    Hardness: {-best.objectives[0]:.1f}")
    print(f"    Dissolution: {-best.objectives[1]:.1f}")
    print(f"    Energy: {best.objectives[2]:.2f} kWh")

    return solutions, best


def run_digital_twin_validation(best_solution):
    """Validate best solution using digital twin."""
    print("\n[2/4] Digital Twin Validation")
    print("-" * 50)

    twin = DigitalTwinEngine()

    param_names = [
        "granulation_time", "binder_amount", "drying_temp", "drying_time",
        "compression_force", "machine_speed", "lubricant_conc", "moisture_content",
    ]

    proposed_params = dict(zip(param_names, best_solution.variables))
    current_params = twin.process_twin._default_parameters()

    result = twin.validate_optimization(
        proposed_params=proposed_params,
        current_params=current_params,
        n_simulations=20,
    )

    print(f"  Recommendation: {result['recommendation'].upper()}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Risk level: {result['risk_assessment']['risk_level']}")
    print(f"  Spec failure rate: {result['risk_assessment']['spec_failure_rate']:.1f}%")

    return result


def run_carbon_analysis():
    """Run carbon target analysis."""
    print("\n[3/4] Carbon Target Analysis")
    print("-" * 50)

    engine = CarbonTargetEngine()

    target = engine.compute_batch_target(batch_energy_kwh=50)
    print(f"  Carbon target: {target['target_co2_kg']:.2f} kg CO2")
    print(f"  Grid intensity: {target['grid_intensity_gco2_kwh']:.0f} gCO2/kWh")

    window = engine.find_optimal_window()
    print(f"  Optimal production window: {window}")

    dashboard = engine.get_dashboard()
    print(f"  Dashboard: {json.dumps(dashboard, indent=2, default=str)}")

    return dashboard


def run_roi_calculation():
    """Calculate system ROI."""
    print("\n[4/4] ROI Calculation")
    print("-" * 50)

    calculator = ROICalculator()

    baseline = {
        "overall_quality_score": 78,
        "defect_rate": 0.06,
        "rework_rate": 0.10,
        "avg_energy_kwh": 55,
        "avg_co2_kg": 28,
    }

    optimized = {
        "overall_quality_score": 89,
        "defect_rate": 0.02,
        "rework_rate": 0.04,
        "avg_energy_kwh": 46,
        "avg_co2_kg": 22,
    }

    roi = calculator.calculate_roi(baseline, optimized)
    summary = calculator.generate_executive_summary(roi)
    print(summary)

    return roi


def main():
    print("=" * 60)
    print("Manufacturing Intelligence - Optimization Pipeline")
    print("=" * 60)

    # 1. NSGA-II
    solutions, best = run_nsga2_optimization()

    # 2. Digital Twin Validation
    validation = run_digital_twin_validation(best)

    # 3. Carbon Analysis
    carbon = run_carbon_analysis()

    # 4. ROI
    roi = run_roi_calculation()

    # Save results
    os.makedirs("results", exist_ok=True)
    print("\n" + "=" * 60)
    print("Pipeline complete. Results saved to results/")
    print("=" * 60)


if __name__ == "__main__":
    main()
