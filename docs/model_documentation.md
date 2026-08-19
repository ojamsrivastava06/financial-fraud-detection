# Machine Learning Model Documentation — Financial Fraud Detection

## 1. Problem Definition
The objective is to detect binary financial fraud transactions in real time:
- **`Fraudulent = 1`**: Fraudulent Transaction
- **`Fraudulent = 0`**: Legitimate Transaction

---

## 2. Target Variable & Class Imbalance Strategy
- **Ground Truth Target**: `Fraudulent`
- **Total Records**: 5,000 transactions
- **Class Distribution**:
  - Genuine (0): 4,518 (90.36%)
  - Fraudulent (1): 482 (9.64%)
- **Imbalance Handling**:
  - Class-weighted cost sensitivity (`class_weight='balanced'` in Logistic Regression & Random Forest).
  - `scale_pos_weight = 9.37` in XGBoost.
  - Primary evaluation metric: **PR-AUC (Average Precision)** rather than accuracy.
  - Data-driven operating threshold optimization.

---

## 3. Dataset Split & Leakage Prevention
- **Train/Test Split**: 80% Training (4,000 samples) / 20% Testing (1,000 samples).
- **Stratification**: `stratify=y` to preserve the 9.64% minority fraud ratio in both splits.
- **Random Seed**: `random_state = 42`.
- **Leakage Prevention**:
  - Identifiers (`Transaction_ID`, `Customer_ID`) are strictly excluded from predictors.
  - All preprocessing transformations (imputation, scaling, one-hot encoding) are fitted **only on the training split** inside a scikit-learn `ColumnTransformer` pipeline.

---

## 4. Feature Space Definition

### Included Predictor Features (17 Raw / 34 Transformed)
- **Numerical Features**: `Transaction_Amount`, `Previous_Transactions`, `Average_Spend`, `Account_Age_Days`, `spend_to_avg_ratio`, `account_age_years`.
- **Categorical Features**: `Merchant_Category` (8 categories), `Payment_Method` (5 categories), `Device_Type` (3 categories), `Location` (7 categories).
- **Binary Flags**: `is_high_value_transaction`, `is_night_transaction`, `is_weekend`, `suspicious_keyword_flag`, `is_international_flag`.

### Excluded Features
- `Transaction_ID` (Unique key, prevents memorization leakage).
- `Customer_ID` (Identifier string).

---

## 5. Candidate Models & Cross-Validation

### Cross-Validation Strategy
- **Method**: 5-Fold `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.
- **Primary Optimization Metric**: `PR-AUC (Average Precision)`.

### Evaluated Model Algorithms
1. **Logistic Regression**: Hyperparameter grid search over `C` values `[0.01, 0.1, 1.0, 10.0, 100.0]` with `class_weight='balanced'`.
2. **Random Forest Classifier**: Randomized search over `n_estimators`, `max_depth`, `min_samples_split`, `min_samples_leaf` with `class_weight='balanced'`.
3. **XGBoost Classifier**: Randomized search over `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`, `scale_pos_weight=9.37`.

---

## 6. Model Comparison & Measured Results

Evaluating on the 20% untouched test set (1,000 transactions):

| Model Name | CV PR-AUC | Test PR-AUC | Test ROC-AUC | Test Precision | Test Recall | Test F1 | Test Accuracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression** | **0.4315** | **0.4135** | **0.8904** | 0.2712 | **1.0000** | **0.4267** | 74.20% |
| **Random Forest** | 0.3878 | 0.3400 | 0.8588 | 0.2584 | 0.8854 | 0.4000 | 74.50% |
| **XGBoost** | 0.3675 | 0.3413 | 0.8683 | **0.2750** | 0.6875 | 0.3929 | **79.60%** |

---

## 7. Model Selection Rationale

🏆 **Winning Model Selected**: **Logistic Regression**

### Why Logistic Regression was Selected:
1. **Highest PR-AUC**: Achieved top CV PR-AUC (0.4315) and Test PR-AUC (0.4135).
2. **Highest ROC-AUC**: Achieved 0.8904 ROC-AUC on the test set.
3. **100% Fraud Recall**: Caught **100% of all fraudulent transactions** in the test set (96 out of 96 fraud samples detected).
4. **Explainability & Low Latency**: Linear log-odds coefficients allow direct auditability required for financial compliance.

---

## 8. Threshold Optimization & Decision Boundaries
- **Default Threshold (0.50)**: High recall, moderate false positive rate.
- **Selected Operating Threshold**: `0.65`
  - Optimizes Precision-Recall balance for deployment.

---

## 9. Risk Tier Framework (`src/models/risk_scoring.py`)

| Risk Tier | Probability Range | Action | Operational Logic |
| :--- | :--- | :--- | :--- |
| **LOW** | $0.00 \le P < 0.35$ | `APPROVE` | Transaction proceeds automatically. |
| **MEDIUM** | $0.35 \le P < 0.65$ | `MONITOR` | Step-up authentication / Step-2 verification. |
| **HIGH** | $P \ge 0.65$ | `FLAG_FOR_REVIEW` | Held for manual analyst review queue. |

---

## 10. Top Predictive Features
1. `suspicious_keyword_flag` (Weight: +4.83)
2. `is_international_flag` (Weight: +4.61)
3. `is_night_transaction` (Weight: +4.43)
4. `account_age_years` / `Account_Age_Days` (Weight: +1.05)
5. `Device_Type_Mobile` (Weight: +0.81)

---

## 11. Artifact Serializations & Model Registry
- **Trained Model**: `models/trained/fraud_model.joblib`
- **Preprocessor Pipeline**: `models/preprocessing/preprocessor.joblib`
- **Metadata Configuration**: `models/metadata/model_metadata.json`

---

## 12. Reproducibility Instructions
To reproduce exact training results:
```bash
python scripts/train_model.py
```
Random seed fixed at `random_state = 42`.
