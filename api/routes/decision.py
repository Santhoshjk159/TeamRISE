# ============================================================================
# Decision Engine Routes
# ============================================================================
from fastapi import APIRouter, HTTPException
from api.schemas.models import MonitorBatchRequest, DecisionResponse
import pandas as pd

router = APIRouter(prefix="/decision", tags=["Decision Engine"])


@router.post("/monitor", response_model=DecisionResponse)
async def monitor_batch(request: MonitorBatchRequest):
    """Monitor a running batch and get real-time decisions."""
    from api.main import app_state

    if app_state.decision_engine is None:
        raise HTTPException(503, "Decision engine not initialized")

    # Convert sensor data to DataFrame
    try:
        df = pd.DataFrame(request.sensor_data)
    except Exception as e:
        raise HTTPException(400, f"Invalid sensor data: {str(e)}")

    decisions = app_state.decision_engine.monitor_batch(
        batch_id=request.batch_id,
        current_data=df,
        current_phase=request.current_phase,
    )

    # Also run deviation detection
    deviations = []
    corrective_actions = []

    if app_state.deviation_detector is not None:
        from src.decision_engine.deviation_detector import DeviationDetector
        devs = app_state.deviation_detector.detect_deviations(
            df, phase=request.current_phase
        )
        deviations = [d.to_dict() for d in devs]

        if app_state.recommender is not None and devs:
            actions = app_state.recommender.recommend(
                devs, current_phase=request.current_phase
            )
            corrective_actions = [a.to_dict() for a in actions]

    return DecisionResponse(
        batch_id=request.batch_id,
        decisions=[d.to_dict() for d in decisions],
        active_alerts=len(app_state.decision_engine.active_alerts),
        deviations=deviations,
        corrective_actions=corrective_actions,
    )


@router.get("/alerts")
async def get_active_alerts():
    """Get currently active alerts."""
    from api.main import app_state

    if app_state.decision_engine is None:
        raise HTTPException(503, "Decision engine not initialized")

    return {
        "alerts": app_state.decision_engine.get_active_alerts(),
        "summary": app_state.decision_engine.get_decision_summary(),
    }


@router.post("/acknowledge/{decision_id}")
async def acknowledge_alert(decision_id: str, outcome: str = "resolved"):
    """Acknowledge and resolve an alert."""
    from api.main import app_state

    if app_state.decision_engine is None:
        raise HTTPException(503, "Decision engine not initialized")

    success = app_state.decision_engine.acknowledge_alert(decision_id, outcome)
    if not success:
        raise HTTPException(404, f"Alert {decision_id} not found")

    return {"status": "acknowledged", "decision_id": decision_id}
