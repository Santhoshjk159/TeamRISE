# AI-Driven Manufacturing Intelligence Engine

**Adaptive Multi-Objective Optimization of Industrial Batch Processes with Energy Pattern Analytics for Asset Reliability, Process Optimization, and Carbon Management**

---

## Overview

A competition-grade, industry-ready system for batch-level adaptive multi-objective optimization in pharmaceutical tablet manufacturing. The system implements a closed-loop intelligent optimization framework that goes beyond dashboards and generic predictions — it continuously learns, adapts, and improves manufacturing outcomes.

### Key Capabilities

| Capability | Implementation |
|---|---|
| **Predictive Modelling (Track A)** | XGBoost + Random Forest ensemble, physics-informed hybrid models, SHAP explainability |
| **Optimization Engine (Track B)** | NSGA-II, Bayesian Optimization, RL Q-Learning with Pareto front analysis |
| **Energy Intelligence** | FFT spectral analysis, KMeans pattern clustering, CUSUM/Page-Hinkley/EWMA drift detection |
| **Golden Signature** | Self-improving reference profiles with human-in-the-loop approval workflow |
| **Carbon Management** | Dynamic carbon targets adapted to grid intensity with optimal production windows |
| **Decision Engine** | Real-time deviation detection, root cause analysis, corrective action recommendations |
| **Digital Twin** | Full batch process + energy simulation for what-if analysis and optimization pre-validation |
| **Validation** | Historical replay, A/B testing, cross-validation, comprehensive ROI calculation |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend                          │
│  /predict   /optimize   /golden-signature   /carbon                │
│  /decision  /digital-twin   /validation   /health                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────-─┐  │
│  │ Predictive Layer │  │ Optimization     │  │ Energy            │ │
│  │                  │  │ Engine           │  │ Intelligence      │ │
│  │ ──────────────── │  │ ──────────────── │  │ Engine            │ │
│  │ XGBoost + RF     │  │ NSGA-II          │  │ FFT Spectral      │ │
│  │ Physics Hybrid   │  │ Bayesian Opt     │  │ Pattern Clustering│ │
│  │ SHAP Explain     │  │ RL (Q-Learning)  │  │ Drift Detection   │ │
│  │                  │  │ Pareto Frontier  │  │ Reliability Score │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Golden Signature │  │ Carbon Target    │  │ Decision Engine  │  │
│  │ Module           │  │ Module           │  │                  │  │
│  │ ──────────────── │  │ ──────────────── │  │ ──────────────── │  │
│  │ Self-Improving   │  │ Dynamic Targets  │  │ Real-Time Monitor│  │
│  │ HITL Approval    │  │ Grid-Aware Logic │  │ Deviation Detect │  │
│  │ Version Control  │  │ Optimal Windows  │  │ Root Cause       │  │
│  │                  │  │                  │  │ Corrective Action│  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                    │
│  ┌────────────────────────┐  ┌────────────────────────────┐        │
│  │ Digital Twin           │  │ Validation & ROI Engine    │        │
│  │ ────────────────────── │  │ ────────────────────────── │        │
│  │ Process Simulator      │  │ Historical Replay          │        │
│  │ Energy Simulator       │  │ A/B Testing                │        │
│  │ What-If Analysis       │  │ Cross Validation           │        │
│  │ Maintenance Forecast   │  │ ROI Calculator (NPV/IRR)   │        │
│  └────────────────────────┘  └────────────────────────────┘        │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                              Data Layer                            │
│                                                                    │
│  Ingestion → Preprocessing → Feature Engineering → Storage         │
│                                                                    │
│  Sources: Excel / CSV / IoT Streams                                │
│  Cleaning: KNN Imputation, Z-Score Outliers                        │
│  Features: FFT, Rolling Stats, Phase Aggregation, Energy Metric    │
│  Storage: Time-Series DB + Model Registry                          │
└────────────────────────────────────────────────────────────────────┘
```

---

## Process Domain

**Pharmaceutical Tablet Manufacturing** with 8 process phases:

1. **Preparation** → Raw material setup
2. **Granulation** → Wet/dry granulation with binder
3. **Drying** → Moisture removal (first-order kinetics)
4. **Milling** → Particle size reduction
5. **Blending** → Uniform mixing
6. **Compression** → Tablet forming (Heckel equation)
7. **Coating** → Film coating application
8. **Quality Testing** → Final inspection

**Quality Targets:** Hardness, Dissolution Rate, Content Uniformity, Friability, Disintegration Time, Tablet Weight

**Optimization Objectives:** Maximize quality (multi-target) | Minimize energy consumption | Minimize CO₂ emissions | Maximize asset reliability

---

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone repository
cd Aveva

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Generate Data & Train Models

```bash
# Generate synthetic pharmaceutical batch data
python scripts/generate_data.py

# Train ML models
python scripts/train_models.py

# Run optimization pipeline
python scripts/run_optimization.py
```

### Run Demo

```bash
# Full system demonstration (all 9 modules)
python scripts/demo.py
```

### Start API Server

```bash
# Start FastAPI server
uvicorn api.main:app --reload --port 8000

# API docs available at http://localhost:8000/docs
```

### Docker

```bash
docker compose up --build
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | System health and module status |
| `/system/summary` | GET | Full system capabilities summary |
| `/predict/quality` | POST | Predict batch quality from parameters |
| `/predict/batch_forecast` | POST | Quick quality forecast |
| `/optimize/run` | POST | Run multi-objective optimization (NSGA-II/Bayesian/RL) |
| `/optimize/methods` | GET | List available optimization methods |
| `/golden-signature/current` | GET | Get current best golden signature |
| `/golden-signature/approve` | POST | HITL: Approve/reject signature |
| `/golden-signature/reprioritize` | POST | HITL: Adjust optimization weights |
| `/carbon/target` | POST | Compute dynamic carbon target |
| `/carbon/dashboard` | GET | Carbon management dashboard |
| `/carbon/optimal-window` | GET | Find lowest-carbon production window |
| `/decision/monitor` | POST | Real-time batch monitoring with decisions |
| `/decision/alerts` | GET | Active alerts and decision summary |
| `/digital-twin/simulate` | POST | Run full batch simulation |
| `/digital-twin/what-if` | POST | What-if scenario analysis |
| `/digital-twin/validate-optimization` | POST | Validate optimization via simulation |
| `/digital-twin/energy/optimal-start` | GET | Optimal batch start time |
| `/digital-twin/maintenance-forecast` | GET | Equipment degradation forecast |
| `/validation/roi` | POST | Calculate comprehensive ROI |
| `/validation/sensitivity` | POST | ROI sensitivity analysis |
| `/validation/pareto-analysis` | POST | Pareto front analysis |

---

## Project Structure

```
Aveva/
├── api/
│   ├── main.py                      # FastAPI application
│   ├── routes/
│   │   ├── prediction.py            # Prediction endpoints
│   │   ├── optimization.py          # Optimization endpoints
│   │   ├── golden_signature.py      # Golden signature endpoints
│   │   ├── carbon.py                # Carbon management endpoints
│   │   ├── decision.py              # Decision engine endpoints
│   │   ├── digital_twin.py          # Digital twin endpoints
│   │   └── validation.py            # Validation & ROI endpoints
│   └── schemas/
│       └── models.py                # Pydantic request/response models
├── config/
│   └── settings.py                  # System configuration
├── src/
│   ├── data_layer/
│   │   ├── ingestion.py             # Data loading (Excel/CSV)
│   │   ├── preprocessing.py         # KNN imputation, outlier detection
│   │   ├── feature_engineering.py   # FFT, rolling stats, phase features
│   │   ├── synthetic_data.py        # Physics-based synthetic data gen
│   │   └── database.py              # SQLAlchemy ORM models
│   ├── predictive/
│   │   ├── multi_target_model.py    # XGBoost + RF ensemble
│   │   ├── physics_informed.py      # Pharmaceutical physics models
│   │   ├── hybrid_model.py          # Physics + ML hybrid predictor
│   │   ├── explainability.py        # SHAP explanations
│   │   └── training_pipeline.py     # End-to-end training pipeline
│   ├── energy_intelligence/
│   │   ├── spectral_analysis.py     # FFT/Welch PSD analysis
│   │   ├── pattern_clustering.py    # KMeans energy clustering
│   │   ├── drift_detection.py       # CUSUM/PH/EWMA detection
│   │   └── reliability_scoring.py   # Asset reliability scoring
│   ├── optimization/
│   │   ├── nsga2.py                 # NSGA-II optimizer
│   │   ├── bayesian_optimizer.py    # Bayesian optimization (GP + EI)
│   │   ├── rl_policy.py             # RL Q-Learning policy
│   │   └── pareto.py                # Pareto utilities & hypervolume
│   ├── golden_signature/
│   │   └── signature.py             # Golden signature management
│   ├── carbon/
│   │   └── target_engine.py         # Dynamic carbon target engine
│   ├── decision_engine/
│   │   ├── realtime_monitor.py      # Real-time decision engine
│   │   ├── deviation_detector.py    # Multi-method deviation detection
│   │   └── recommender.py           # Corrective action recommender
│   ├── digital_twin/
│   │   ├── process_simulator.py     # Full batch process simulation
│   │   ├── energy_simulator.py      # Energy consumption simulation
│   │   └── twin_engine.py           # Digital twin orchestrator
│   └── validation/
│       ├── replay.py                # Historical replay & A/B testing
│       ├── roi_calculator.py        # Financial ROI calculation
│       └── pareto_analysis.py       # Pareto front analysis
├── scripts/
│   ├── generate_data.py             # Synthetic data generation
│   ├── train_models.py              # Model training
│   ├── run_optimization.py          # Run optimization pipeline
│   └── demo.py                      # Full system demo
├── tests/                           # Test suite
├── Dockerfile                       # Container definition
├── docker-compose.yml               # Multi-service orchestration
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
└── README.md                        # This file
```

---

## Innovation Highlights

### 1. Physics-Informed Hybrid Prediction
ML models augmented with pharmaceutical physics (Avrami granulation kinetics, Arrhenius drying, Heckel compression equation). The hybrid model learns *residuals* between physics and reality, combining the best of both approaches.

### 2. Self-Improving Golden Signature
Golden signatures evolve over time — when a batch outperforms the current signature above a threshold, the system proposes an updated signature for human approval. This creates a continuous improvement loop.

### 3. Dynamic Carbon Target Formula
```
Carbon Target = (Grid_Intensity × Energy_Use × Sustainability_Weight) − Historical_Efficiency_Offset
```
The offset adapts based on actual emissions history, creating progressively tighter targets.

### 4. Multi-Method Deviation Detection
Three concurrent algorithms (CUSUM, Page-Hinkley, EWMA) vote on drift detection. A 2/3 consensus triggers alerts, reducing false positives while maintaining sensitivity.

### 5. Digital Twin Pre-Validation
Optimization recommendations are validated through Monte Carlo simulation in the digital twin before real-world application, quantifying risk and expected improvement.

### 6. Causal Root Cause Inference
The deviation detector maintains a pharmaceutical domain causal graph to trace parameter deviations back to upstream causes, enabling targeted corrective actions.

---

## Data

The system works with two data sources:

| File | Description |
|---|---|
| `_h_batch_process_data.xlsx` | Time-series sensor data (211 rows, 8 phases, 1 batch) |
| `_h_batch_production_data.xlsx` | Batch-level production data (60 batches, 15 features) |

The synthetic data generator creates 200+ additional batches with physics-based correlations for robust training.

---

## License

Made for IIT-H Aveva Hackathon 2026 by Team RISE
