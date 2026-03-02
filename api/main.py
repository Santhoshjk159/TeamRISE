# ============================================================================
# AI-Driven Manufacturing Intelligence Engine - FastAPI Application
# ============================================================================
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

logger = logging.getLogger(__name__)

START_TIME = time.time()


class AppState:
    """Global application state holding initialized modules."""

    def __init__(self):
        self.predictor = None
        self.hybrid_predictor = None
        self.physics = None
        self.explainer = None
        self.gs_manager = None
        self.carbon_engine = None
        self.decision_engine = None
        self.deviation_detector = None
        self.recommender = None
        self.digital_twin = None
        self.replay_engine = None
        self.data_pipeline = None


app_state = AppState()


def _init_modules():
    """Initialize all system modules at startup."""
    logger.info("Initializing Manufacturing Intelligence modules...")

    try:
        from src.golden_signature.signature import GoldenSignatureManager
        app_state.gs_manager = GoldenSignatureManager()
        logger.info("  ✓ Golden Signature Manager")
    except Exception as e:
        logger.warning(f"  ✗ Golden Signature Manager: {e}")

    try:
        from src.carbon.target_engine import CarbonTargetEngine
        app_state.carbon_engine = CarbonTargetEngine()
        logger.info("  ✓ Carbon Target Engine")
    except Exception as e:
        logger.warning(f"  ✗ Carbon Target Engine: {e}")

    try:
        from src.decision_engine.realtime_monitor import RealTimeDecisionEngine
        app_state.decision_engine = RealTimeDecisionEngine()
        logger.info("  ✓ Decision Engine")
    except Exception as e:
        logger.warning(f"  ✗ Decision Engine: {e}")

    try:
        from src.decision_engine.deviation_detector import DeviationDetector
        app_state.deviation_detector = DeviationDetector()
        logger.info("  ✓ Deviation Detector")
    except Exception as e:
        logger.warning(f"  ✗ Deviation Detector: {e}")

    try:
        from src.decision_engine.recommender import CorrectiveActionRecommender
        app_state.recommender = CorrectiveActionRecommender()
        logger.info("  ✓ Corrective Action Recommender")
    except Exception as e:
        logger.warning(f"  ✗ Corrective Action Recommender: {e}")

    try:
        from src.digital_twin.twin_engine import DigitalTwinEngine
        app_state.digital_twin = DigitalTwinEngine()
        logger.info("  ✓ Digital Twin Engine")
    except Exception as e:
        logger.warning(f"  ✗ Digital Twin Engine: {e}")

    try:
        from src.predictive.physics_informed import PharmaceuticalProcessPhysics
        app_state.physics = PharmaceuticalProcessPhysics()
        logger.info("  ✓ Physics Engine")
    except Exception as e:
        logger.warning(f"  ✗ Physics Engine: {e}")

    try:
        from src.validation.replay import HistoricalReplayEngine
        app_state.replay_engine = HistoricalReplayEngine()
        logger.info("  ✓ Replay Engine")
    except Exception as e:
        logger.warning(f"  ✗ Replay Engine: {e}")

    logger.info("Module initialization complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize modules on startup."""
    _init_modules()
    yield
    logger.info("Shutting down Manufacturing Intelligence Engine.")


# ─── FastAPI App ────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI-Driven Manufacturing Intelligence Engine",
    description=(
        "Adaptive Multi-Objective Optimization of Industrial Batch Processes "
        "with Energy Pattern Analytics for Asset Reliability, Process Optimization, "
        "and Carbon Management."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Register Routers ──────────────────────────────────────────────────────

from api.routes.prediction import router as prediction_router
from api.routes.optimization import router as optimization_router
from api.routes.golden_signature import router as golden_sig_router
from api.routes.carbon import router as carbon_router
from api.routes.decision import router as decision_router
from api.routes.digital_twin import router as digital_twin_router
from api.routes.validation import router as validation_router

app.include_router(prediction_router)
app.include_router(optimization_router)
app.include_router(golden_sig_router)
app.include_router(carbon_router)
app.include_router(decision_router)
app.include_router(digital_twin_router)
app.include_router(validation_router)


# ─── Root & Health Endpoints ───────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "AI-Driven Manufacturing Intelligence Engine",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    modules = {
        "predictor": "loaded" if app_state.predictor else "not_loaded",
        "physics": "loaded" if app_state.physics else "not_loaded",
        "golden_signature": "loaded" if app_state.gs_manager else "not_loaded",
        "carbon_engine": "loaded" if app_state.carbon_engine else "not_loaded",
        "decision_engine": "loaded" if app_state.decision_engine else "not_loaded",
        "digital_twin": "loaded" if app_state.digital_twin else "not_loaded",
        "replay_engine": "loaded" if app_state.replay_engine else "not_loaded",
    }

    return {
        "status": "healthy",
        "version": "1.0.0",
        "modules": modules,
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


@app.get("/system/summary")
async def system_summary():
    """Get a comprehensive system summary."""
    summary = {
        "system": "AI-Driven Manufacturing Intelligence Engine",
        "capabilities": {
            "track_a": "Predictive Modelling (XGBoost+RF ensemble, physics-informed hybrid, SHAP)",
            "track_b": "Multi-Objective Optimization (NSGA-II, Bayesian, RL Q-Learning)",
            "energy": "Spectral analysis, pattern clustering, drift detection, reliability scoring",
            "golden_signature": "Self-improving with human-in-the-loop approval",
            "carbon": "Dynamic target adaptation based on grid intensity",
            "decision": "Real-time deviation detection with corrective recommendations",
            "digital_twin": "Process + energy simulation for what-if analysis",
            "validation": "Historical replay, A/B testing, ROI calculation",
        },
        "data_domain": "Pharmaceutical Tablet Manufacturing",
        "process_phases": [
            "Preparation", "Granulation", "Drying", "Milling",
            "Blending", "Compression", "Coating", "Quality_Testing",
        ],
        "quality_targets": [
            "Hardness", "Dissolution_Rate", "Content_Uniformity",
            "Friability", "Disintegration_Time", "Tablet_Weight",
        ],
        "optimization_objectives": [
            "Maximize quality (multi-target)",
            "Minimize energy consumption",
            "Minimize carbon emissions",
            "Maximize asset reliability",
        ],
    }

    return summary
