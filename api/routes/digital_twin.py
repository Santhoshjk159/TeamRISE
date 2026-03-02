# ============================================================================
# Digital Twin Routes
# ============================================================================
from fastapi import APIRouter, HTTPException
from api.schemas.models import SimulationRequest, WhatIfRequest, SimulationResponse

router = APIRouter(prefix="/digital-twin", tags=["Digital Twin"])


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_batch(request: SimulationRequest):
    """Run a full batch simulation."""
    from api.main import app_state

    if app_state.digital_twin is None:
        raise HTTPException(503, "Digital twin not initialized")

    params = request.parameters.dict() if request.parameters else None

    result = app_state.digital_twin.simulate_full_batch(
        parameters=params,
        start_hour=request.start_hour,
    )

    process = result["process"]
    return SimulationResponse(
        batch_id=process["batch_id"],
        scenario_name=process["scenario_name"],
        quality_predictions=process["quality_predictions"],
        energy_metrics=result["energy"],
        total_time_minutes=process["total_time_minutes"],
        quality_in_spec=result["quality_within_spec"]["all_in_spec"],
    )


@router.post("/what-if")
async def what_if_analysis(request: WhatIfRequest):
    """Run what-if scenario analysis."""
    from api.main import app_state

    if app_state.digital_twin is None:
        raise HTTPException(503, "Digital twin not initialized")

    base_params = request.base_parameters.dict()

    results = app_state.digital_twin.process_twin.run_what_if(
        base_params=base_params,
        variations=request.variations,
    )

    comparison = app_state.digital_twin.process_twin.compare_scenarios(results)

    return {
        "n_scenarios": len(results),
        "comparison": comparison.to_dict(orient="records"),
        "best_scenario": app_state.digital_twin.process_twin.find_optimal_scenario(
            results
        ).scenario_name,
    }


@router.post("/validate-optimization")
async def validate_optimization(body: dict):
    """Validate optimization recommendations via digital twin simulation."""
    from api.main import app_state

    if app_state.digital_twin is None:
        raise HTTPException(503, "Digital twin not initialized")

    proposed = body.get("proposed_params", {})
    current = body.get("current_params", {})
    n_sims = body.get("n_simulations", 10)

    result = app_state.digital_twin.validate_optimization(
        proposed_params=proposed,
        current_params=current,
        n_simulations=n_sims,
    )

    return result


@router.get("/energy/optimal-start")
async def optimal_start_time(objective: str = "balanced"):
    """Find optimal batch start time based on energy/carbon."""
    from api.main import app_state

    if app_state.digital_twin is None:
        raise HTTPException(503, "Digital twin not initialized")

    default_durations = {
        "Preparation": 15, "Granulation": 35, "Drying": 45,
        "Milling": 20, "Blending": 25, "Compression": 40,
        "Coating": 30, "Quality_Testing": 20,
    }

    result = app_state.digital_twin.energy_twin.optimize_start_time(
        phase_durations=default_durations,
        objective=objective,
    )

    return result


@router.get("/maintenance-forecast")
async def maintenance_forecast():
    """Forecast maintenance impact on quality and energy."""
    from api.main import app_state

    if app_state.digital_twin is None:
        raise HTTPException(503, "Digital twin not initialized")

    default_params = app_state.digital_twin.process_twin._default_parameters()
    return app_state.digital_twin.forecast_maintenance_impact(default_params)
