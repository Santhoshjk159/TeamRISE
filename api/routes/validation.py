# ============================================================================
# Validation / ROI Routes
# ============================================================================
from fastapi import APIRouter, HTTPException
from api.schemas.models import ROIRequest, ROIResponse

router = APIRouter(prefix="/validation", tags=["Validation & ROI"])


@router.post("/roi", response_model=ROIResponse)
async def calculate_roi(request: ROIRequest):
    """Calculate ROI of optimization system."""
    from src.validation.roi_calculator import ROICalculator

    calculator = ROICalculator()
    roi = calculator.calculate_roi(
        baseline_metrics=request.baseline_metrics,
        optimized_metrics=request.optimized_metrics,
        custom_params=request.custom_params,
    )

    result = roi.to_dict()
    result["executive_summary"] = calculator.generate_executive_summary(roi)

    return result


@router.post("/sensitivity")
async def sensitivity_analysis(body: dict):
    """Run ROI sensitivity analysis on a variable."""
    from src.validation.roi_calculator import ROICalculator

    calculator = ROICalculator()
    results = calculator.sensitivity_analysis(
        baseline_metrics=body.get("baseline_metrics", {}),
        optimized_metrics=body.get("optimized_metrics", {}),
        variable=body.get("variable", "energy_cost_per_kwh"),
        range_pct=body.get("range_pct", 50),
        steps=body.get("steps", 10),
    )

    return {"variable": body.get("variable"), "results": results}


@router.post("/replay")
async def replay_historical():
    """Replay historical batches through optimization system."""
    from api.main import app_state

    if app_state.replay_engine is None:
        return {"status": "replay_engine_not_initialized"}

    # Would replay from stored data
    return app_state.replay_engine.get_replay_summary()


@router.post("/pareto-analysis")
async def pareto_analysis(body: dict):
    """Analyze a Pareto front."""
    from src.validation.pareto_analysis import ParetoAnalyzer

    analyzer = ParetoAnalyzer()
    result = analyzer.analyze_pareto_front(
        solutions=body.get("solutions", []),
        objective_names=body.get("objective_names", []),
        minimize=body.get("minimize"),
    )

    return result
