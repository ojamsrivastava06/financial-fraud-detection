# Complete Deployment & Repository File Audit

**Project**: `financial-fraud-detection`  
**Audit Purpose**: Identify lifecycle, runtime necessity, deployment requirements, and viva presentation utility for every file and folder in the repository.

---

## 1. File Classification & Deployment Audit Matrix

| File / Folder Path | Required for Runtime | Required for Deployment | Useful for Viva | Safe to Exclude from Git | Reason & Lifecycle Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `src/api/` | **YES** | **YES** | **YES** | **NO** | Core FastAPI REST API application shell, routes, middleware, and exception handlers. |
| `src/config/` | **YES** | **YES** | **YES** | **NO** | Pydantic v2 settings management (`settings.py`), logging setup, and cross-platform path resolution. |
| `src/data/` | **YES** | **YES** | **YES** | **NO** | Data validation (`validation.py`), cleaning (`cleaning.py`), and ingestion (`ingestion.py`) modules. |
| `src/database/` | **YES** | **YES** | **YES** | **NO** | SQLAlchemy 2.0 connection pool (`connection.py`), ORM models (`models.py`), schemas (`schemas.py`), repositories (`repository.py`). |
| `src/features/` | **YES** | **YES** | **YES** | **NO** | Feature engineering pipeline (`engineering.py`, `encoding.py`, `feature_pipeline.py`) generating 9 domain features. |
| `src/models/` | **YES** | **YES** | **YES** | **NO** | Model training (`train.py`), evaluation (`evaluate.py`), inference registry (`model_registry.py`), scoring (`risk_scoring.py`, `predict.py`). |
| `src/monitoring/` | **YES** | **YES** | **YES** | **NO** | Live transaction streaming (`transaction_stream.py`), alert engine (`alert_engine.py`), and fraud monitor (`fraud_monitor.py`). |
| `src/utils/` | **YES** | **YES** | **YES** | **NO** | Logging configuration, evaluation metrics, and helper utilities. |
| `dashboard/app.py` | **YES** | **YES** | **YES** | **NO** | Streamlit main entrypoint utilizing native `st.navigation` for seamless multipage routing. |
| `dashboard/pages/` | **YES** | **YES** | **YES** | **NO** | 6 complete view pages: Overview, Transactions, Fraud Analysis, Risk Analysis, Alerts, Model Performance. |
| `dashboard/components/` | **YES** | **YES** | **YES** | **NO** | Shared UI components: dynamic sidebar status (`sidebar.py`), KPI cards, filter controls, data tables. |
| `dashboard/assets/styles/style.css` | **YES** | **YES** | **YES** | **NO** | Modern dark glassmorphic CSS theme styling injected into Streamlit frontend. |
| `data/raw/financial_fraud_detection_dataset.csv` | **YES** | **YES** | **YES** | **NO** | Master raw dataset (5,000 transactions, 14 features, 0 nulls, 0 duplicates). Essential for viva & seeding. |
| `data/processed/financial_fraud_processed.csv` | **YES** | **YES** | **YES** | **NO** | Fully cleaned and preprocessed dataset used for model training and benchmark reproduction. |
| `data/data_dictionary.json` | NO | NO | **YES** | **NO** | Comprehensive schema definition and statistical metadata dictionary. Highly valuable for viva examiner questions. |
| `database/fraud_detection.db` | **YES** | **YES** | **YES** | **NO** | Seeded SQLite database with 5,000 transactions, 5,000 predictions, and 1,722 alerts. Enables zero-setup demo. |
| `database/schema.sql` | NO | NO | **YES** | **NO** | Reference DDL SQL schema showing tables, indices, foreign keys, and constraints for database viva review. |
| `models/trained/fraud_model.joblib` | **YES** | **YES** | **YES** | **NO** | Active serialized class-weighted `LogisticRegression` model artifact (1.1 KB). Loaded on API/UI startup. |
| `models/preprocessing/preprocessor.joblib` | **YES** | **YES** | **YES** | **NO** | Active serialized fitted `ColumnTransformer` pipeline (5.6 KB). Applied during real-time inference. |
| `models/metadata/model_metadata.json` | **YES** | **YES** | **YES** | **NO** | Full model hyperparameters, optimal decision threshold (0.65), feature names, and test metrics. |
| `requirements.txt` | **YES** | **YES** | **YES** | **NO** | Pinned Python package dependencies for pip, Docker, Streamlit Cloud, and cloud deployments. |
| `pyproject.toml` | **YES** | **YES** | **YES** | **NO** | Build system definition, project metadata, ruff/black lint configs, and pytest options. |
| `Dockerfile` | NO | **YES** | **YES** | **NO** | Multi-stage production container build for FastAPI backend server with healthchecks. |
| `Dockerfile.dashboard` | NO | **YES** | **YES** | **NO** | Multi-stage production container build for Streamlit dashboard with healthchecks. |
| `docker-compose.yml` | NO | **YES** | **YES** | **NO** | Full multi-container orchestration spec linking backend API and frontend dashboard. |
| `.env.example` | NO | **YES** | **YES** | **NO** | Environment variables template for cloud and local deployments. |
| `.env` | NO | NO | NO | **YES** | Local environment file containing local overrides. Must NEVER be committed to GitHub. |
| `.gitignore` | NO | **YES** | **YES** | **NO** | Git exclusion rules preventing commits of caches, virtual environments, logs, and secrets. |
| `.github/workflows/ci.yml` | NO | **YES** | **YES** | **NO** | GitHub Actions CI/CD workflow executing linting, artifact validation, pytest, and Docker builds on push. |
| `tests/test_*.py` | NO | NO | **YES** | **NO** | Complete 53-test automated test suite covering API, data integrity, database, features, models, hardening. |
| `tests/conftest.py` | NO | NO | **YES** | **NO** | Pytest session fixture automatically cleaning up test records to preserve 5,000 DB records. |
| `scripts/seed_database.py` | NO | **YES** | **YES** | **NO** | High-performance database seeding script processing dataset and executing batch inference. |
| `scripts/train_model.py` | NO | **YES** | **YES** | **NO** | End-to-end ML model training and evaluation script. |
| `scripts/run_pipeline.py` | NO | **YES** | **YES** | **NO** | One-command orchestration script executing data cleaning, training, and database seeding. |
| `scripts/cleanup_database.py` | NO | NO | **YES** | **NO** | Test isolation database cleaner removing transient test transactions. |
| `scripts/verify_*.py` | NO | NO | **YES** | **NO** | Verification audit scripts for live servers, API endpoints, database integrity, and artifacts. |
| `reports/figures/*.png` | **YES** | **YES** | **YES** | **NO** | ROC curves, PR curves, Confusion Matrices, and Feature Importance rankings displayed in Streamlit dashboard. |
| `reports/model_reports/*.csv` | **YES** | **YES** | **YES** | **NO** | Candidate model comparisons and threshold sensitivity tables displayed in Streamlit dashboard. |
| `notebooks/*.ipynb` | NO | NO | **YES** | **NO** | Jupyter research notebooks for EDA, feature engineering, and model experimentation for viva viva. |
| `docs/*.md` | NO | NO | **YES** | **NO** | Comprehensive system architecture, API specification, model card, runbook, and data pipeline documentation. |
| `README.md` | NO | **YES** | **YES** | **NO** | Main repository landing page, architecture overview, installation guide, and quickstart documentation. |
| `FINAL_*.md` | NO | NO | **YES** | **NO** | Historical audit and submission readiness milestone documents. |
| `.venv/` | NO | NO | NO | **YES** | Local virtual environment folder. Must be excluded from Git via `.gitignore`. |
| `**/__pycache__/` | NO | NO | NO | **YES** | Python bytecode caches. Regenerated automatically at runtime. |
| `.pytest_cache/` | NO | NO | NO | **YES** | Pytest runtime cache directory. Excluded from Git. |
| `uvicorn*.log` | NO | NO | NO | **YES** | Local temporary server log files. Excluded from Git. |

---

## 2. Key Audit Takeaways

1. **All core source files (`src/`, `dashboard/`, `data/`, `database/`, `models/`, `reports/`) are required either for live runtime or interactive dashboard visualizations.**
2. **The SQLite database (`database/fraud_detection.db`) is lightweight (2 MB), self-contained, and essential for instant clone-and-run viva demonstrations and Streamlit Cloud deployment.**
3. **No source, documentation, test, model, or dataset file needs to be deleted.**
4. **Only local artifacts (`.venv/`, `__pycache__/`, `.pytest_cache/`, `uvicorn*.log`, `.env`) are excluded via `.gitignore`.**
