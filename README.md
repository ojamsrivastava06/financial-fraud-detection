# Financial Fraud Detection Platform

An end-to-end Machine Learning Financial Fraud Detection and Risk Scoring system featuring automated schema validation, domain feature engineering, class-weighted ML classification, calibrated risk tiers, high-concurrency SQLite storage, and an interactive multipage Streamlit analytics dashboard.

---

## 1. Project Overview

Financial transaction fraud poses severe monetary and operational risks to banking infrastructure. This project provides a production-grade ML classification and analytics platform designed to detect fraudulent transactions in real time, evaluate multi-tier risk boundaries, and provide compliance officers with interactive investigation queues.

The platform is designed to be **100% self-contained**, allowing seamless zero-setup deployment on **Streamlit Community Cloud** while maintaining full local execution support.

---

## 2. Key Features

- **Pristine ML Classification Engine**: Class-weighted Logistic Regression optimized for fraud detection on imbalanced financial datasets (Test Fraud Recall: **100%**, ROC-AUC: **0.8904**, PR-AUC: **0.4135**).
- **Calibrated Three-Tier Risk Scoring**: Dynamic risk scoring with domain-calibrated thresholds: `LOW` (< 0.35), `MEDIUM` (0.35 - 0.65), and `HIGH` (>= 0.65).
- **Self-Contained SQLite Database**: Fast, zero-configuration database with WAL journal mode storing 5,000 clean transactions, 5,000 predictions, and 1,722 security alerts.
- **Multipage Interactive Dashboard**: Native Streamlit `st.navigation` interface spanning 6 dedicated analytical and operational pages.
- **Interactive Security Alert Queue**: Analyst workflow allowing investigators to review flagged transactions and transition alert statuses (`OPEN` -> `INVESTIGATING` -> `RESOLVED` / `DISMISSED`) with persistent database commits.

---

## 3. Technology Stack

- **Dashboard & UI**: Streamlit 1.32+, Plotly Express, Plotly Graph Objects
- **Machine Learning & Pipeline**: Scikit-Learn, Joblib, NumPy, Pandas, Pillow
- **Database & ORM**: SQLite 3 (WAL Mode), SQLAlchemy 2.0 ORM
- **Configuration & Validation**: Pydantic v2, Pydantic-Settings, Python-Dotenv
- **Language**: Python 3.11 / 3.13

---

## 4. System Architecture

```
[Master Dataset / Database] (database/fraud_detection.db)
          ↓
[Data Ingestion & Feature Extraction] (src/database/repository.py)
          ↓
[ColumnTransformer Preprocessing Pipeline] (models/preprocessing/preprocessor.joblib)
          ↓
[Trained Logistic Regression Model] (models/trained/fraud_model.joblib)
          ↓
[Risk Scoring Engine & Threshold Calibration] (src/models/risk_scoring.py)
          ↓
[Streamlit Multipage Analytics Dashboard] (dashboard/app.py)
    ├── 1. Overview (KPIs, time-series volume, risk tier donut)
    ├── 2. Transactions (search, multi-criteria filters, detail inspector)
    ├── 3. Fraud Analysis (merchant, payment method, device, geography)
    ├── 4. Risk Analysis (score distributions, threshold sensitivity)
    ├── 5. Alerts (security review queue, live status transitions)
    └── 6. Model Performance (ROC curves, PR curves, confusion matrix, feature ranking)
```

---

## 5. Final Repository Structure

```text
financial-fraud-detection/
├── dashboard/                              # Streamlit Frontend Application
│   ├── app.py                              # Multipage entrypoint (st.navigation)
│   ├── assets/styles/style.css             # Glassmorphism dark UI stylesheet
│   ├── components/                         # Shared UI components (sidebar, KPI cards, tables)
│   └── pages/                              # 6 analytical view pages
├── data/                                   # Data Layer
│   ├── data_dictionary.json                # Statistical metadata dictionary
│   ├── raw/
│   │   └── financial_fraud_detection_dataset.csv
│   └── processed/
│       └── financial_fraud_processed.csv
├── database/                               # Database Layer
│   └── fraud_detection.db                  # Seeded SQLite database (5,000 records)
├── models/                                 # Machine Learning Artifacts
│   ├── metadata/model_metadata.json        # Hyperparameters, threshold (0.65), metrics
│   ├── preprocessing/preprocessor.joblib   # Fitted ColumnTransformer (34 features)
│   └── trained/fraud_model.joblib          # Active LogisticRegression model
├── reports/                                # Pre-generated Evaluation Figures & CSV Reports
│   ├── figures/                            # ROC/PR curves, confusion matrix, feature ranking
│   └── model_reports/                      # Benchmark comparison & threshold sensitivity tables
├── src/                                    # Core Backend & Business Logic
│   ├── config/settings.py                  # Pydantic v2 settings & path resolution
│   ├── database/                           # Connection, ORM models, repositories, schemas
│   ├── models/                             # Model registry, inference, risk scoring
│   └── utils/                              # Structured logging & metrics
├── .env.example                            # Configuration environment template
├── .gitignore                              # Production Git exclusion rules
├── LICENSE                                 # MIT License
├── README.md                               # Project documentation & quickstart
├── requirements.txt                        # Pinned dependencies for Streamlit Cloud
└── VIVA_PROJECT_MAP.md                     # Concept-to-code viva presentation map
```

---

## 6. Machine Learning Model & Metrics

### 1. Training & Preprocessing Pipeline
- **Dataset**: 5,000 financial transactions with 9.64% positive fraud prevalence.
- **Data Splitting**: 80/20 Stratified train/test split (4,000 train / 1,000 test) preserving class distributions.
- **Preprocessing Pipeline**: `ColumnTransformer` with `RobustScaler` on numerical features and `OneHotEncoder(handle_unknown='ignore')` on categorical attributes, yielding 34 standardized feature inputs.
- **Class Imbalance Strategy**: Loss-weighted penalization (`class_weight='balanced'`).

### 2. Verified Test Evaluation Metrics
| Metric | Value | Interpretation |
| :--- | :---: | :--- |
| **Test Fraud Recall** | **1.0000 (100%)** | 100% of actual fraudulent transactions are successfully captured |
| **Test ROC-AUC** | **0.8904** | High discriminatory capability across positive/negative classes |
| **5-Fold CV PR-AUC** | **0.4315** | Cross-validated precision-recall area under curve |
| **Test PR-AUC** | **0.4135** | Sustained PR performance on unseen test split |
| **Test Precision** | **0.2712** | Controlled false positive rate on rare fraud class |
| **Test F1-Score** | **0.4267** | Balanced harmonic mean under extreme recall prioritization |
| **Test Accuracy** | **74.20%** | Overall classification accuracy |

### 3. Decision Boundary Calibration
- **Operating Decision Threshold**: `0.65`
- **Risk Tiers**:
  - `LOW`: Fraud Probability < 0.35 (Action: `APPROVE`)
  - `MEDIUM`: Fraud Probability 0.35 <= p < 0.65 (Action: `AUTHENTICATE_2FA`)
  - `HIGH`: Fraud Probability >= 0.65 (Action: `FLAG_FOR_REVIEW`)

---

## 7. Streamlit Dashboard Pages

1. **Overview**: Top-level KPI cards ($399k transaction volume, 1,367 model-flagged transactions, $121k value at risk), volume trends, and risk tier donut chart.
2. **Transactions**: Multi-criteria search and filter bar (by Customer ID, Transaction ID, Risk Tier, Merchant Category), paginated transaction data table, and single-transaction detail inspector.
3. **Fraud Analysis**: Visual distributions comparing fraud across 8 merchant categories, 5 payment methods, 3 device platforms, and 7 metro locations.
4. **Risk Analysis**: Probability density histograms by risk tier, amount vs risk scatter plots, and operating threshold sensitivity analysis.
5. **Alerts**: Real-time security incident review queue with interactive status update actions (`Mark Investigating`, `Mark Resolved`, `Mark Dismissed`) committing directly to SQLite.
6. **Model Performance**: Evaluation report presenting active model metrics, candidate benchmark comparisons, high-resolution ROC curves, Precision-Recall curves, Confusion Matrix, and Feature Importance rankings.

---

## 8. Database Architecture

- **Engine**: SQLite 3 via SQLAlchemy 2.0 ORM with Write-Ahead Logging (`WAL`) mode for concurrent reads.
- **Location**: `database/fraud_detection.db`
- **Verified Record Counts**:
  - **Transactions**: `5,000`
  - **Predictions**: `5,000`
  - **Security Alerts**: `1,722`

---

## 9. Local Setup & Execution

### 1. Clone Repository & Setup Environment
```bash
# Clone the repository
git clone https://github.com/ojamsrivastava06/financial-fraud-detection.git
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

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Streamlit Dashboard
```bash
python -m streamlit run dashboard/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 10. Streamlit Community Cloud Deployment

This repository is pre-configured for one-click deployment on Streamlit Community Cloud:

1. Push this repository to GitHub on branch `main`.
2. Navigate to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **"New app"**.
4. Configure the settings:
   - **Repository**: `ojamsrivastava06/financial-fraud-detection`
   - **Branch**: `main`
   - **Main file path**: `dashboard/app.py`
5. Click **"Deploy!"**.

> **Note**: The dashboard directly accesses the bundled SQLite database (`database/fraud_detection.db`) and serialized model artifacts. No external database or separately running backend server is required.

---

## 11. Project & Viva Highlights

- **Data Leakage Defense**: The `ColumnTransformer` is fitted strictly on the 4,000 training rows and applied (`transform()`) to test and runtime records.
- **Domain Feature Engineering**: Generates 9 financial risk features including `spend_to_avg_ratio`, `is_high_value_transaction`, nocturnal hour indicators, and account age normalizations.
- **Model Explainability**: Logistic Regression provides transparent, inspectable linear weights for every feature and category, satisfying financial auditability requirements.
- **Zero-Setup Portability**: Uses cross-platform relative path resolution (`Path(__file__).resolve().parent.parent`), guaranteeing flawless operation on Windows, Linux, and macOS.

---

## 12. Important Limitations

1. **Synthetic Stream Generation**: For academic demonstration, real-time transaction streams are simulated from the master dataset rather than live banking core switch protocols (ISO 8583 / ISO 20022).
2. **Single-Node Storage**: The included SQLite database is tailored for single-instance dashboard hosting. For multi-node distributed enterprise scaling, the database URL can be updated to PostgreSQL.

---

## 13. License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
