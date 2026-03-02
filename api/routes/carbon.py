# ============================================================================
# Carbon Management Routes
# ============================================================================
from fastapi import APIRouter, HTTPException
from api.schemas.models import CarbonTargetRequest, CarbonTargetResponse

router = APIRouter(prefix="/carbon", tags=["Carbon Management"])


@router.post("/target", response_model=CarbonTargetResponse)
async def compute_carbon_target(request: CarbonTargetRequest):
    """Compute dynamic carbon target for a batch."""
    from api.main import app_state

    if app_state.carbon_engine is None:
        raise HTTPException(503, "Carbon engine not initialized")

    target = app_state.carbon_engine.compute_batch_target(
        batch_energy_kwh=request.batch_energy_kwh,
        sustainability_weight=request.sustainability_weight,
    )

    return CarbonTargetResponse(
        target_co2_kg=target["target_co2_kg"],
        grid_intensity=target["grid_intensity_gco2_kwh"],
    )


@router.get("/dashboard")
async def carbon_dashboard():
    """Get carbon management dashboard data."""
    from api.main import app_state

    if app_state.carbon_engine is None:
        raise HTTPException(503, "Carbon engine not initialized")

    return app_state.carbon_engine.get_dashboard()


@router.get("/optimal-window")
async def optimal_production_window():
    """Find the optimal production window for lowest carbon."""
    from api.main import app_state

    if app_state.carbon_engine is None:
        raise HTTPException(503, "Carbon engine not initialized")

    return app_state.carbon_engine.find_optimal_window()
