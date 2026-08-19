# Financial Fraud Detection Platform & Interactive Dashboard

Production-grade, end-to-end Financial Fraud Detection and Risk Scoring system featuring automated schema validation, domain feature engineering, machine learning classification, high-concurrency SQLite ORM storage, FastAPI REST API with readiness probes, real-time alert incident response, performance benchmarking, containerized Docker deployment, CI/CD automation, and an interactive Streamlit dashboard.

---

## 📌 System Architecture

```
[Raw CSV / Ingestion Stream]
          ↓
[Data Validation & Schema Guard] (src/data/validation.py)
          ↓
[Domain Feature Engineering] (src/features/engineering.py)
          ↓
[ColumnTransformer Preprocessor Pipeline] (models/preprocessing/preprocessor.joblib)
          ↓
[Trained Machine Learning Model] (models/trained/fraud_model.joblib)
          ↓
[Risk Scoring & Tier Calibration] (src/models/risk_scoring.py)
          ↓
[High-Concurrency SQLAlchemy ORM Database] (database/fraud_detection.db)
          ↓
[Automated Security Alert Engine] (src/monitoring/alert_engine.py)
          ↓
[FastAPI Production REST API with Diagnostics] (src/api/main.py)
    ├── /health & /ready (Probes)
    ├── /predictions/predict & /predictions/batch
    ├── /transactions & /transactions/{id}
    ├── /analytics/summary & /analytics/time-series
    └── /alerts & /alerts/{id}
          ↓
[Streamlit Multi-Page Analytics Dashboard] (dashboard/app.py)
```

---

## 🎯 Key System Capabilities

1. **Pristine ML Model Engine**: Winning Logistic Regression classifier ($PR-AUC = 0.4135$, $ROC-AUC = 0.8904$, $100\%$ test fraud recall, zero data leakage).
2. **Data-Driven Operating Threshold**: Decision threshold calibrated at `0.65` with `LOW` ($< 0.35$), `MEDIUM` ($0.35 - 0.65$), and `HIGH` ($\ge 0.65$) risk tiers.
3. **High-Performance Database Layer**: SQLite database with Write-Ahead Logging (`WAL`), connection timeouts, and indexes on `transaction_id`, `customer_id`, `transaction_date`, `risk_level`, `fraud_prediction`, `status`, and `severity`.
4. **FastAPI Reliability & Hardening**: Request validation (Pydantic v2), batch size bounds (max 500), process timing header (`X-Process-Time-Ms`), CORS configuration, and sanitized 500 error responses.
5. **Health & Readiness Probes**: `/health` liveness probe and `/ready` readiness probe verifying database connectivity, ML model binary, preprocessing pipeline, and metadata availability.
6. **In-Memory ML Caching**: `ModelRegistry` caches serialized model artifacts in memory, achieving sub-millisecond inference latency without repetitive disk I/O.
7. **Security Alert Queue**: Automated alert trigger on high/critical risk transactions with investigative resolution workflows (`OPEN` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `RESOLVED` / `DISMISSED`).
8. **Docker & Docker Compose**: Multi-stage, production-ready `Dockerfile` (FastAPI) and `Dockerfile.dashboard` (Streamlit) orchestrated via `docker-compose.yml` with health checks and persistent volume mounts.
9. **CI/CD Pipeline**: GitHub Actions workflow (`.github/workflows/ci.yml`) automating linting (Ruff), dependency verification, artifact verification, pytest execution, and Docker build verification.
10. **Load & Performance Testing**: Built-in benchmark suite (`scripts/performance_test.py`) measuring RPS, average, median, p95, and p99 latency distributions across all endpoints.

---

## 🔬 Machine Learning Methodology & Metrics

### 1. Training & Cross-Validation Pipeline
- **Dataset**: 5,000 transaction records with ~3.6% fraud prevalence.
- **Split**: 80/20 Stratified train/test split (4,000 train / 1,000 test) preserving class balance.
- **Cross-Validation**: 5-Fold Stratified K-Fold.
- **Preprocessing**: `ColumnTransformer` with `StandardScaler` for continuous numerical features and `OneHotEncoder(handle_unknown='ignore')` for high-cardinality categorical attributes.

### 2. Model Performance Summary
| Model Algorithm | 5-Fold CV PR-AUC | Test PR-AUC | Test ROC-AUC | Test Recall | Test Precision | Test F1-Score | Selected |
|---|---|---|---|---|---|---|---|
| **Logistic Regression (Class-Weighted)** | **0.4315** | **0.4135** | **0.8904** | **1.0000** | 0.2712 | 0.4267 | **WINNER (Active)** |
| **XGBoost (scale_pos_weight=26.8)** | 0.3842 | 0.3621 | 0.8654 | 0.8889 | 0.2540 | 0.3951 | Candidate |

### 3. Decision Boundary Calibration
- **Operating Threshold**: `0.65` (optimizing fraud capture while controlling false positives).
- **Risk Tiers**:
  - `LOW`: Fraud Probability $< 0.35$ (Action: `APPROVE`)
  - `MEDIUM`: Fraud Probability $0.35 \le p < 0.65$ (Action: `MONITOR`)
  - `HIGH`: Fraud Probability $\ge 0.65$ (Action: `FLAG_FOR_REVIEW`)

---

## 📊 Streamlit Dashboard Guide

The interactive Streamlit UI is organized across 6 dedicated pages:
1. **Overview**: Executive KPI metrics (total volume, fraud rate %, active alerts), time-series trend analysis, and risk distribution breakdown.
2. **Transaction Explorer**: Granular transaction table with filters for risk level, merchant category, payment method, fraud status, and real-time search.
3. **Fraud Analysis**: Visual distributions comparing fraud rates across merchant categories, payment instruments, client device platforms, and domestic vs. international transactions.
4. **Risk Analysis**: Probability density histograms, amount vs. risk scatter plots, and operating threshold sensitivity tables.
5. **Alert Management Queue**: Operational security incident queue allowing investigators to transition alerts (`OPEN` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `RESOLVED` / `DISMISSED`) and attach resolution notes.
6. **Model Performance**: Comprehensive evaluation suite presenting ROC curve, Precision-Recall curve, Confusion Matrix, and top feature importances.

---

## 🛠️ Technology Stack

- **Language & Runtime**: Python 3.11+
- **Machine Learning & Pipeline**: Scikit-Learn, XGBoost, Joblib, NumPy, Pandas
- **Web Backend & REST API**: FastAPI, Uvicorn, Pydantic v2, Pydantic-Settings, Python-Dotenv
- **Database & ORM**: SQLite (WAL mode), SQLAlchemy 2.0 ORM
- **Interactive UI Dashboard**: Streamlit, Plotly Express & Graph Objects
- **Containerization**: Docker, Docker Compose
- **CI/CD Automation**: GitHub Actions
- **Testing & Benchmarking**: Pytest, Concurrent ThreadPool Benchmark Engine

---

## ⚙️ Prerequisites & Environment Setup

### 1. Prerequisites
- Python 3.11 or higher
- Git
- Docker & Docker Compose (optional, for containerized execution)

### 2. Local Virtual Environment Installation
```bash
# Clone repository
git clone <repository_url>
cd financial-fraud-detection

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Centralized Environment Configuration
Create a `.env` file from the provided `.env.example`:
```bash
cp .env.example .env
```

Key environment variables supported:
| Variable | Default Value | Description |
|---|---|---|
| `APP_NAME` | `Financial Fraud Detection Platform` | Application title |
| `APP_ENV` | `production` | Deployment environment (`production` / `development`) |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `DATABASE_URL` | `sqlite:///./database/fraud_detection.db` | SQLAlchemy database connection string |
| `API_HOST` | `0.0.0.0` | FastAPI host binding |
| `API_PORT` | `8000` | FastAPI port binding |
| `DASHBOARD_PORT` | `8501` | Streamlit port binding |
| `API_URL` | `http://localhost:8000` | Backend API URL for frontend integration |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated or `*`) |
| `MAX_BATCH_SIZE` | `500` | Maximum transactions per batch inference request |
| `HIGH_RISK_THRESHOLD` | `0.65` | Probability threshold for HIGH risk categorization |
| `MEDIUM_RISK_THRESHOLD` | `0.35` | Probability threshold for MEDIUM risk categorization |

### 4. Seed Database
Populate the SQLite database with 5,000 real dataset transactions, inference scores, and alerts:
```bash
python scripts/seed_database.py
```

---

## 🚀 Running the System

### Option A: Local Execution

#### 1. Start FastAPI REST Backend
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- **API Root**: `http://localhost:8000/`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Liveness Probe**: `http://localhost:8000/health`
- **Readiness Probe**: `http://localhost:8000/ready`
- **Full API Documentation**: See [docs/api_documentation.md](docs/api_documentation.md)

#### 2. Start Streamlit Interactive Dashboard
In a separate terminal:
```bash
streamlit run dashboard/app.py --server.port 8501
```
- **Dashboard UI**: `http://localhost:8501`

---

### Option B: Containerized Execution via Docker Compose

```bash
# Build and start all services in detached mode
docker-compose up --build -d

# Check service logs
docker-compose logs -f

# Check container status & health
docker-compose ps

# Stop all containers
docker-compose down
```

---

## 🧪 Testing & Quality Assurance

### Run Unit, Integration & Hardening Tests
Execute the complete test suite (53 tests covering data validation, features, database, models, streaming, and API hardening):
```bash
python -m pytest -v
```

### Run Performance & Load Benchmark Suite
Run concurrent API performance tests across health, transactions, analytics, and single/batch predictions:
```bash
python scripts/performance_test.py
```
Benchmark outputs are saved to:
- `reports/performance_test_results.json`
- `reports/performance_test_report.md`

---

## 📡 Sample Prediction Example

### Request (`POST /predictions/predict`)
```json
{
  "transaction": {
    "transaction_id": "T99999",
    "customer_id": "CUST1234",
    "transaction_date": "14-08-2026 14:30",
    "transaction_amount": 550.0,
    "merchant_category": "Travel",
    "payment_method": "Credit Card",
    "device_type": "POS",
    "location": "Bengaluru",
    "is_international": 1,
    "previous_transactions": 5,
    "average_spend": 40.0,
    "account_age_days": 45,
    "suspicious_keyword": "Yes"
  }
}
```

### Response (`200 OK`)
```json
{
  "transaction_id": "T99999",
  "fraud_probability": 0.8735,
  "fraud_percentage": 87.35,
  "fraud_prediction": 1,
  "risk_score": 87.4,
  "risk_level": "HIGH",
  "action": "FLAG_FOR_REVIEW",
  "threshold_used": 0.65,
  "model_name": "Logistic Regression"
}
```

---

## 🔒 Security & Reliability Controls

- **Zero Hardcoded Secrets**: Fully environment-variable driven configuration.
- **SQL Injection Defense**: SQLAlchemy ORM parameterization on all dynamic filters.
- **Path Traversal Protection**: Registry artifact loading strictly sanitizes filenames via `Path.name` and `.resolve()`.
- **Sanitized Exception Responses**: Global exception handler prevents internal traceback or filesystem exposure.
- **Pagination Safeguards**: Hard caps on `limit` ($\le 500$) and `skip` ($\ge 0$).
- **Batch Size Rate Limiting**: Batches strictly capped at 500 items per request.

---

## ⚠️ Known Limitations & Scope

1. **Database Engine**: Defaults to SQLite with WAL mode for local and single-node deployments. For multi-node distributed enterprise scale, update `DATABASE_URL` in `.env` to PostgreSQL.
2. **Real-time Streaming Simulation**: The streaming module (`src/monitoring/transaction_stream.py`) is a synthetic generator designed for demonstration, stress-testing, and analytics simulation rather than live SWIFT/ACH banking rails.
3. **Authentication Scope**: As per Phase 1-4 architectural requirements, the core system focuses on model inference, latency optimization, and reliability hardening without adding unnecessary auth wrappers.
