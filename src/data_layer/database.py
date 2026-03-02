# ============================================================================
# Database Layer
# SQLAlchemy models and database operations
# ============================================================================
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, DateTime, Boolean,
    JSON, Text, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional

Base = declarative_base()


class BatchRecord(Base):
    """Production batch record."""
    __tablename__ = "batch_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(20), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Process parameters
    granulation_time = Column(Float)
    binder_amount = Column(Float)
    drying_temp = Column(Float)
    drying_time = Column(Float)
    compression_force = Column(Float)
    machine_speed = Column(Float)
    lubricant_conc = Column(Float)

    # Quality outcomes
    moisture_content = Column(Float)
    tablet_weight = Column(Float)
    hardness = Column(Float)
    friability = Column(Float)
    disintegration_time = Column(Float)
    dissolution_rate = Column(Float)
    content_uniformity = Column(Float)

    # Energy & Carbon
    energy_consumption_kwh = Column(Float)
    co2_emissions_kg = Column(Float)
    specific_energy = Column(Float)

    # Scores
    quality_score = Column(Float)
    yield_score = Column(Float)
    performance_score = Column(Float)
    overall_score = Column(Float)

    # Relationships
    golden_signature_id = Column(Integer, ForeignKey("golden_signatures.id"), nullable=True)


class ProcessTimeSeries(Base):
    """Time-series process data."""
    __tablename__ = "process_timeseries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(20), nullable=False, index=True)
    time_minutes = Column(Integer, nullable=False)
    phase = Column(String(50))

    temperature_c = Column(Float)
    pressure_bar = Column(Float)
    humidity_percent = Column(Float)
    motor_speed_rpm = Column(Float)
    compression_force_kn = Column(Float)
    flow_rate_lpm = Column(Float)
    power_consumption_kw = Column(Float)
    vibration_mm_s = Column(Float)

    __table_args__ = (
        Index("idx_batch_time", "batch_id", "time_minutes"),
    )


class GoldenSignatureRecord(Base):
    """Golden Signature storage."""
    __tablename__ = "golden_signatures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signature_id = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Scenario tags
    scenario_tag = Column(String(100))
    material_type = Column(String(50))
    season = Column(String(20))

    # Optimized parameters (JSON)
    process_parameters = Column(JSON)
    energy_fingerprint = Column(JSON)
    phase_profile = Column(JSON)
    asset_health_score = Column(Float)
    carbon_intensity = Column(Float)
    confidence_score = Column(Float)

    # Target metrics
    target_quality = Column(Float)
    target_yield = Column(Float)
    target_performance = Column(Float)
    target_energy = Column(Float)
    target_carbon = Column(Float)

    # Status
    is_active = Column(Boolean, default=True)
    approved = Column(Boolean, default=False)
    approved_by = Column(String(50), nullable=True)
    replaced_by = Column(String(50), nullable=True)

    # History
    version = Column(Integer, default=1)
    parent_id = Column(Integer, nullable=True)


class CarbonTarget(Base):
    """Dynamic carbon targets."""
    __tablename__ = "carbon_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    batch_id = Column(String(20), nullable=True)

    grid_intensity = Column(Float)
    energy_use = Column(Float)
    sustainability_weight = Column(Float)
    historical_offset = Column(Float)
    target_value = Column(Float)
    actual_value = Column(Float)
    deviation = Column(Float)
    status = Column(String(20))  # "met", "exceeded", "pending"


class OptimizationResult(Base):
    """Optimization run results."""
    __tablename__ = "optimization_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    method = Column(String(30))  # nsga2, bayesian, rl, hybrid
    objectives = Column(JSON)
    constraints = Column(JSON)
    pareto_solutions = Column(JSON)
    best_solution = Column(JSON)
    improvement_pct = Column(JSON)
    runtime_seconds = Column(Float)


class DecisionLog(Base):
    """Decision engine action log."""
    __tablename__ = "decision_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    batch_id = Column(String(20))
    decision_type = Column(String(50))  # correction, alert, recommendation
    severity = Column(String(20))  # info, warning, critical
    description = Column(Text)
    parameters = Column(JSON)
    action_taken = Column(Boolean, default=False)
    outcome = Column(Text, nullable=True)


class HumanFeedback(Base):
    """Human-in-the-loop feedback records."""
    __tablename__ = "human_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(50))
    feedback_type = Column(String(50))  # approve, reject, reprioritize
    target_id = Column(String(50))  # signature ID or optimization run ID
    original_values = Column(JSON)
    new_values = Column(JSON)
    reason = Column(Text, nullable=True)


# ------------------------------------------------------------------ #
# Database Manager
# ------------------------------------------------------------------ #
class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, db_url: str = "sqlite:///manufacturing_intelligence.db"):
        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """Get a new database session."""
        return self.Session()

    def drop_tables(self):
        """Drop all tables (for testing)."""
        Base.metadata.drop_all(self.engine)
