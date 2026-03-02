# ============================================================================
# API Schemas - Pydantic models for request/response validation
# ============================================================================
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum


# ─── Enums ──────────────────────────────────────────────────────────────────

class BatchStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationObjective(str, Enum):
    QUALITY = "quality"
    ENERGY = "energy"
    CARBON = "carbon"
    BALANCED = "balanced"


# ─── Batch Schemas ──────────────────────────────────────────────────────────

class BatchProcessParams(BaseModel):
    granulation_time: float = Field(30, ge=10, le=60)
    binder_amount: float = Field(5.0, ge=1, le=10)
    drying_temp: float = Field(60, ge=40, le=80)
    drying_time: float = Field(45, ge=20, le=90)
    compression_force: float = Field(12, ge=3, le=25)
    machine_speed: float = Field(600, ge=200, le=1000)
    lubricant_conc: float = Field(1.0, ge=0.5, le=3.0)
    moisture_content: float = Field(3.0, ge=0.5, le=10)


class BatchCreateRequest(BaseModel):
    batch_id: Optional[str] = None
    parameters: BatchProcessParams


class BatchResponse(BaseModel):
    batch_id: str
    status: str
    parameters: Dict[str, float]
    quality_predictions: Optional[Dict[str, float]] = None
    energy_metrics: Optional[Dict[str, float]] = None


# ─── Prediction Schemas ────────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    parameters: BatchProcessParams
    include_physics: bool = True
    include_explainability: bool = False


class PredictionResponse(BaseModel):
    predictions: Dict[str, float]
    confidence: Optional[Dict[str, float]] = None
    physics_predictions: Optional[Dict[str, float]] = None
    explanations: Optional[Dict[str, Any]] = None


# ─── Optimization Schemas ──────────────────────────────────────────────────

class OptimizationRequest(BaseModel):
    objective: OptimizationObjective = OptimizationObjective.BALANCED
    constraints: Optional[Dict[str, Dict[str, float]]] = None
    current_parameters: Optional[BatchProcessParams] = None
    n_iterations: int = Field(50, ge=10, le=500)
    method: str = Field("nsga2", pattern="^(nsga2|bayesian|rl)$")


class OptimizationResponse(BaseModel):
    method: str
    n_solutions: int
    best_solution: Dict[str, float]
    pareto_front: Optional[List[Dict[str, float]]] = None
    expected_quality: Dict[str, float]
    expected_energy_kwh: Optional[float] = None
    expected_co2_kg: Optional[float] = None
    improvement_pct: Optional[Dict[str, float]] = None


# ─── Golden Signature Schemas ──────────────────────────────────────────────

class GoldenSignatureResponse(BaseModel):
    signature_id: str
    version: int
    approved: bool
    process_parameters: Dict[str, float]
    confidence_score: float
    carbon_intensity: float
    asset_health_score: float
    scenario_tags: List[str]


class GoldenSignatureApproveRequest(BaseModel):
    signature_id: str
    approved: bool
    feedback: Optional[str] = None


# ─── Carbon Schemas ────────────────────────────────────────────────────────

class CarbonTargetRequest(BaseModel):
    batch_energy_kwh: float = Field(50.0, ge=0)
    grid_intensity_gco2_kwh: Optional[float] = None
    sustainability_weight: float = Field(1.0, ge=0.1, le=2.0)


class CarbonTargetResponse(BaseModel):
    target_co2_kg: float
    actual_co2_kg: Optional[float] = None
    grid_intensity: float
    optimal_window: Optional[Dict] = None


# ─── Decision Engine Schemas ───────────────────────────────────────────────

class MonitorBatchRequest(BaseModel):
    batch_id: str
    current_phase: str
    sensor_data: Dict[str, List[float]]


class DecisionResponse(BaseModel):
    batch_id: str
    decisions: List[Dict]
    active_alerts: int
    deviations: Optional[List[Dict]] = None
    corrective_actions: Optional[List[Dict]] = None


# ─── Digital Twin Schemas ──────────────────────────────────────────────────

class SimulationRequest(BaseModel):
    parameters: Optional[BatchProcessParams] = None
    start_hour: int = Field(6, ge=0, le=23)
    scenario_name: str = "simulation"


class WhatIfRequest(BaseModel):
    base_parameters: BatchProcessParams
    variations: Dict[str, List[float]]


class SimulationResponse(BaseModel):
    batch_id: str
    scenario_name: str
    quality_predictions: Dict[str, float]
    energy_metrics: Dict[str, float]
    total_time_minutes: float
    quality_in_spec: bool


# ─── Validation / ROI Schemas ──────────────────────────────────────────────

class ROIRequest(BaseModel):
    baseline_metrics: Dict[str, float]
    optimized_metrics: Dict[str, float]
    custom_params: Optional[Dict[str, float]] = None


class ROIResponse(BaseModel):
    quality: Dict
    energy_carbon: Dict
    financial: Dict
    operational: Dict
    executive_summary: Optional[str] = None


# ─── Health / System Schemas ───────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    modules: Dict[str, str]
    uptime_seconds: float
