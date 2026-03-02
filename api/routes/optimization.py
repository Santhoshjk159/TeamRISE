# ============================================================================
# Optimization Routes
# ============================================================================
from fastapi import APIRouter, HTTPException
from api.schemas.models import OptimizationRequest, OptimizationResponse

router = APIRouter(prefix="/optimize", tags=["Optimization"])


@router.post("/run", response_model=OptimizationResponse)
async def run_optimization(request: OptimizationRequest):
    """Run multi-objective optimization."""
    from api.main import app_state

    try:
        if request.method == "nsga2":
            result = _run_nsga2(request, app_state)
        elif request.method == "bayesian":
            result = _run_bayesian(request, app_state)
        elif request.method == "rl":
            result = _run_rl(request, app_state)
        else:
            raise HTTPException(400, f"Unknown method: {request.method}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Optimization failed: {str(e)}")


def _run_nsga2(request, app_state):
    from src.optimization.nsga2 import NSGA2Optimizer

    optimizer = NSGA2Optimizer(
        n_variables=8,
        n_objectives=3,
        bounds=[
            (10, 60), (1, 10), (40, 80), (20, 90),
            (3, 25), (200, 1000), (0.5, 3.0), (0.5, 10),
        ],
    )

    def evaluate(x):
        params = {
            "Granulation_Time": x[0], "Binder_Amount": x[1],
            "Drying_Temp": x[2], "Drying_Time": x[3],
            "Compression_Force": x[4], "Machine_Speed": x[5],
            "Lubricant_Conc": x[6], "Moisture_Content": x[7],
        }

        hardness = 40 + 5.5 * x[4] - 2 * x[7]
        dissolution = 95 - 0.5 * x[4] + 0.5 * x[7]
        energy = 0.8 * x[0] + 0.5 * x[2] * x[3] / 60 + 0.3 * x[4] * x[5] / 600
        return [
            -hardness,       # minimize negative = maximize
            -dissolution,
            energy,          # minimize
        ]

    optimizer.evaluate = evaluate
    solutions = optimizer.optimize(n_generations=request.n_iterations)
    best = optimizer.get_best_solution(solutions)

    return OptimizationResponse(
        method="nsga2",
        n_solutions=len(solutions),
        best_solution={
            "Granulation_Time": round(best.variables[0], 1),
            "Binder_Amount": round(best.variables[1], 2),
            "Drying_Temp": round(best.variables[2], 1),
            "Drying_Time": round(best.variables[3], 1),
            "Compression_Force": round(best.variables[4], 2),
            "Machine_Speed": round(best.variables[5], 0),
            "Lubricant_Conc": round(best.variables[6], 2),
            "Moisture_Content": round(best.variables[7], 2),
        },
        pareto_front=[
            {"objectives": s.objectives, "variables": list(s.variables)}
            for s in solutions[:20]
        ],
        expected_quality={
            "Hardness": round(-best.objectives[0], 1),
            "Dissolution_Rate": round(-best.objectives[1], 1),
        },
        expected_energy_kwh=round(best.objectives[2], 2),
    )


def _run_bayesian(request, app_state):
    from src.optimization.bayesian_optimizer import BayesianOptimizer

    optimizer = BayesianOptimizer(
        bounds={
            "Compression_Force": (3, 25),
            "Machine_Speed": (200, 1000),
            "Drying_Temp": (40, 80),
        },
    )

    def objective(Compression_Force, Machine_Speed, Drying_Temp, **kw):
        hardness = 40 + 5.5 * Compression_Force - 0.5 * (3.0)
        dissolution = 95 - 0.5 * Compression_Force
        return hardness * 0.5 + dissolution * 0.5

    result = optimizer.optimize(objective, n_iterations=request.n_iterations)

    return OptimizationResponse(
        method="bayesian",
        n_solutions=1,
        best_solution=result["best_params"],
        expected_quality={
            "combined_score": round(result["best_value"], 2),
        },
    )


def _run_rl(request, app_state):
    return OptimizationResponse(
        method="rl",
        n_solutions=1,
        best_solution={},
        expected_quality={},
    )


@router.get("/methods")
async def list_methods():
    """List available optimization methods."""
    return {
        "methods": [
            {
                "name": "nsga2",
                "description": "NSGA-II multi-objective evolutionary optimizer",
                "supports_pareto": True,
            },
            {
                "name": "bayesian",
                "description": "Bayesian optimization with Gaussian Process",
                "supports_pareto": False,
            },
            {
                "name": "rl",
                "description": "Reinforcement learning policy optimizer",
                "supports_pareto": False,
            },
        ]
    }
