# ============================================================================
# Golden Signature Routes
# ============================================================================
from fastapi import APIRouter, HTTPException
from api.schemas.models import GoldenSignatureResponse, GoldenSignatureApproveRequest

router = APIRouter(prefix="/golden-signature", tags=["Golden Signature"])


@router.get("/current")
async def get_current_signature():
    """Get the current best approved golden signature."""
    from api.main import app_state

    if app_state.gs_manager is None:
        raise HTTPException(503, "Golden signature manager not initialized")

    best = app_state.gs_manager.get_best()
    if best is None:
        return {"status": "no_signature", "message": "No approved golden signature available"}

    return {
        "signature_id": best.signature_id,
        "version": best.version,
        "approved": best.approved,
        "confidence_score": best.confidence_score,
        "process_parameters": best.process_parameters,
        "carbon_intensity": best.carbon_intensity,
        "asset_health_score": best.asset_health_score,
        "scenario_tags": best.scenario_tags,
    }


@router.get("/all")
async def list_signatures():
    """List all golden signatures."""
    from api.main import app_state

    if app_state.gs_manager is None:
        raise HTTPException(503, "Golden signature manager not initialized")

    signatures = app_state.gs_manager.export()
    return {"signatures": signatures, "count": len(signatures)}


@router.post("/approve")
async def approve_signature(request: GoldenSignatureApproveRequest):
    """Approve or reject a golden signature (HITL)."""
    from api.main import app_state

    if app_state.gs_manager is None:
        raise HTTPException(503, "Golden signature manager not initialized")

    success = app_state.gs_manager.approve(
        request.signature_id, request.approved
    )
    if not success:
        raise HTTPException(404, f"Signature {request.signature_id} not found")

    return {
        "signature_id": request.signature_id,
        "approved": request.approved,
        "message": "Signature approved" if request.approved else "Signature rejected",
    }


@router.post("/reprioritize")
async def reprioritize_targets(feedback: dict):
    """HITL: Reprioritize optimization targets based on operator feedback."""
    from api.main import app_state

    if app_state.gs_manager is None:
        raise HTTPException(503, "Golden signature manager not initialized")

    new_weights = feedback.get("weights", {})
    app_state.gs_manager.reprioritize_targets(new_weights)

    return {
        "status": "updated",
        "new_weights": new_weights,
    }
