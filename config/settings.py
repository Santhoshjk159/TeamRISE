# ============================================================================
# AI-Driven Manufacturing Intelligence Engine
# Configuration Settings
# ============================================================================
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class OptimizationMode(str, Enum):
    NSGA2 = "nsga2"
    BAYESIAN = "bayesian"
    REINFORCEMENT = "reinforcement"
    HYBRID = "hybrid"


class MetabolicPhase(str, Enum):
    PREPARATION = "Preparation"
    GRANULATION = "Granulation"
    DRYING = "Drying"
    MILLING = "Milling"
    BLENDING = "Blending"
    COMPRESSION = "Compression"
    COATING = "Coating"
    QUALITY_TESTING = "Quality_Testing"


@dataclass
class DatabaseConfig:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    name: str = os.getenv("DB_NAME", "manufacturing_intelligence")
    user: str = os.getenv("DB_USER", "admin")
    password: str = os.getenv("DB_PASSWORD", "admin")

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sqlite_url(self) -> str:
        return "sqlite:///manufacturing_intelligence.db"


@dataclass
class MLConfig:
    """Machine Learning Configuration"""
    # Multi-target prediction
    prediction_targets_primary: List[str] = field(default_factory=lambda: [
        "Hardness", "Dissolution_Rate", "Content_Uniformity"
    ])
    prediction_targets_secondary: List[str] = field(default_factory=lambda: [
        "Energy_Consumption_kWh", "CO2_Emissions_kg"
    ])
    prediction_targets_yield: List[str] = field(default_factory=lambda: [
        "Tablet_Weight", "Friability"
    ])

    # Process parameters (input features)
    process_features: List[str] = field(default_factory=lambda: [
        "Granulation_Time", "Binder_Amount", "Drying_Temp", "Drying_Time",
        "Compression_Force", "Machine_Speed", "Lubricant_Conc", "Moisture_Content"
    ])

    # Time-series features from process data
    timeseries_features: List[str] = field(default_factory=lambda: [
        "Temperature_C", "Pressure_Bar", "Humidity_Percent",
        "Motor_Speed_RPM", "Compression_Force_kN", "Flow_Rate_LPM",
        "Power_Consumption_kW", "Vibration_mm_s"
    ])

    # Model parameters
    test_size: float = 0.2
    random_state: int = 42
    cv_folds: int = 5
    accuracy_target: float = 0.90

    # XGBoost params
    xgb_params: Dict = field(default_factory=lambda: {
        "n_estimators": 300,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
    })

    # LSTM params
    lstm_params: Dict = field(default_factory=lambda: {
        "units": 64,
        "dropout": 0.2,
        "epochs": 100,
        "batch_size": 16,
        "sequence_length": 30,
    })


@dataclass
class OptimizationConfig:
    """Optimization Engine Configuration"""
    mode: OptimizationMode = OptimizationMode.HYBRID

    # NSGA-II params
    nsga2_pop_size: int = 100
    nsga2_n_gen: int = 200
    nsga2_crossover_prob: float = 0.9
    nsga2_mutation_prob: float = 0.1

    # Bayesian Optimization params
    bayesian_n_iter: int = 50
    bayesian_init_points: int = 10

    # RL params
    rl_learning_rate: float = 0.001
    rl_discount_factor: float = 0.99
    rl_epsilon: float = 0.1
    rl_episodes: int = 1000

    # Objective weights (default priority)
    objective_weights: Dict[str, float] = field(default_factory=lambda: {
        "yield": 0.25,
        "quality": 0.25,
        "performance": 0.20,
        "energy": 0.15,
        "carbon": 0.15,
    })

    # Constraints
    max_energy_kwh: float = 500.0
    max_carbon_kg: float = 150.0
    min_quality_score: float = 85.0
    min_yield_percent: float = 90.0
    min_dissolution_rate: float = 80.0
    max_friability: float = 1.0


@dataclass
class CarbonConfig:
    """Carbon Management Configuration"""
    grid_carbon_intensity_kg_per_kwh: float = 0.4  # kg CO2e per kWh
    natural_gas_factor: float = 0.184  # kg CO2e per kWh thermal
    steam_factor: float = 0.2  # kg CO2e per kg steam
    sustainability_weight: float = 0.85
    regulatory_cap_kg_per_batch: float = 200.0
    reduction_target_percent: float = 15.0  # Year-over-year reduction target


@dataclass
class GoldenSignatureConfig:
    """Golden Signature Framework Configuration"""
    min_confidence_score: float = 0.85
    benchmark_improvement_threshold: float = 0.02  # 2% improvement required
    max_history_depth: int = 100
    approval_required: bool = True
    auto_update_enabled: bool = False


@dataclass
class EnergyPatternConfig:
    """Energy Pattern Intelligence Configuration"""
    fft_window_size: int = 64
    spectral_resolution: float = 0.1
    drift_threshold: float = 0.15
    anomaly_z_threshold: float = 3.0
    clustering_n_clusters: int = 5
    harmonic_orders: List[int] = field(default_factory=lambda: [1, 2, 3, 5, 7])


@dataclass
class DigitalTwinConfig:
    """Digital Twin Configuration"""
    simulation_dt: float = 0.1  # minutes
    process_noise: float = 0.02
    measurement_noise: float = 0.01
    max_simulation_time: float = 250.0  # minutes


@dataclass
class SystemConfig:
    """Root Configuration"""
    project_name: str = "AI-Driven Manufacturing Intelligence Engine"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    carbon: CarbonConfig = field(default_factory=CarbonConfig)
    golden_signature: GoldenSignatureConfig = field(default_factory=GoldenSignatureConfig)
    energy_pattern: EnergyPatternConfig = field(default_factory=EnergyPatternConfig)
    digital_twin: DigitalTwinConfig = field(default_factory=DigitalTwinConfig)

    # File paths
    data_dir: str = os.getenv("DATA_DIR", "data")
    model_dir: str = os.getenv("MODEL_DIR", "models")
    log_dir: str = os.getenv("LOG_DIR", "logs")


# Global configuration instance
settings = SystemConfig()
