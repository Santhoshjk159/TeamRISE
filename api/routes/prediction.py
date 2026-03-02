# ============================================================================
# Prediction Routes
# ============================================================================
from fastapi import APIRouter, HTTPException
from api.schemas.models import (
    PredictionRequest, PredictionResponse, BatchProcessParams,
)

router = APIRouter(prefix="/predict", tags=["Predictions"])


@router.post("/quality", response_model=PredictionResponse)
async def predict_quality(request: PredictionRequest):
    """Predict batch quality from process parameters."""
    from api.main import app_state

    if app_state.predictor is None:
        raise HTTPException(503, "Prediction model not loaded")

    params = request.parameters.dict()

    try:
        predictions = app_state.predictor.predict_single(params)
    except Exception as e:
        raise HTTPException(500, f"Prediction failed: {str(e)}")

    response = {"predictions": predictions}

    if request.include_physics and app_state.physics is not None:
        try:
            physics_preds = app_state.physics.predict_all(params)
            response["physics_predictions"] = physics_preds
        except Exception:
            pass

    if request.include_explainability and app_state.explainer is not None:
        try:
            explanation = app_state.explainer.explain_prediction(params)
            response["explanations"] = explanation
        except Exception:
            pass

    return response


@router.post("/batch_forecast")
async def batch_forecast(params: BatchProcessParams):
    """Quick forecast for a batch without full explainability."""
    from api.main import app_state

    if app_state.predictor is None:
        raise HTTPException(503, "Model not loaded")

    try:
        predictions = app_state.predictor.predict_single(params.dict())
        return {"predictions": predictions}
    except Exception as e:
        raise HTTPException(500, str(e))
