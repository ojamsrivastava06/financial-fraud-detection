# Data Dictionary — Financial Fraud Detection Platform

## Dataset Summary
- **Source File**: `data/raw/financial_fraud_detection_dataset.csv`
- **Processed File**: `data/processed/financial_fraud_processed.csv`
- **Total Records**: 5,000 transactions
- **Target Variable**: `Fraudulent` (0 = Legitimate, 1 = Fraudulent)
- **Missing Values**: 0 (0.0%)
- **Duplicate Records**: 0

---

## 📋 Comprehensive Column Specification

### 1. Raw Dataset Columns

| Column Name | Data Type | Role | Unique Values | Missing Count | Missing % | Example Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Transaction_ID` | `object` (String) | `identifier` | 5,000 | 0 | 0.0% | `T100000`, `T100001` | Unique transaction record identifier. |
| `Customer_ID` | `object` (String) | `identifier` | 3,847 | 0 | 0.0% | `CUST3252`, `CUST1630` | Unique customer account identifier. |
| `Transaction_Date` | `object` (Datetime String) | `datetime feature` | 4,980 | 0 | 0.0% | `04-10-2023 07:45` | Date and timestamp of transaction (`DD-MM-YYYY HH:MM`). |
| `Transaction_Amount` | `float64` | `numerical feature` | 4,302 | 0 | 0.0% | `37.54`, `240.81` | Transaction monetary value in USD ($0.00 to $653.80). |
| `Merchant_Category` | `object` | `categorical feature` | 8 | 0 | 0.0% | `Travel`, `Utilities` | Merchant business sector classification. |
| `Payment_Method` | `object` | `categorical feature` | 5 | 0 | 0.0% | `PayPal`, `Credit Card` | Payment instrument used for transaction. |
| `Device_Type` | `object` | `categorical feature` | 3 | 0 | 0.0% | `POS`, `Mobile`, `Desktop` | Client terminal/device platform used. |
| `Location` | `object` | `categorical feature` | 7 | 0 | 0.0% | `Bengaluru`, `Kolkata` | Geographic transaction origin city. |
| `Is_International` | `int64` | `boolean feature` | 2 | 0 | 0.0% | `0`, `1` | Cross-border transaction indicator (1 = International, 0 = Domestic). |
| `Previous_Transactions` | `int64` | `numerical feature` | 199 | 0 | 0.0% | `94`, `76` | Cumulative count of prior transactions executed by customer. |
| `Average_Spend` | `float64` | `numerical feature` | 4,753 | 0 | 0.0% | `417.40`, `335.47` | Historical average spend amount per customer ($10.01 to $499.99). |
| `Account_Age_Days` | `int64` | `numerical feature` | 1,827 | 0 | 0.0% | `1492`, `66` | Age of customer account in days (30 to 1,999 days). |
| `Suspicious_Keyword` | `object` | `categorical feature` | 2 | 0 | 0.0% | `No`, `Yes` | Flag indicating presence of suspicious keywords in metadata. |
| `Fraudulent` | `int64` | `target` | 2 | 0 | 0.0% | `0`, `1` | Ground truth label (0 = Legitimate, 1 = Fraudulent). |

> ℹ️ *Note*: Standard column meanings are derived directly from column names and value distributions. Semantic meaning requiring further context is confirmed via dataset profiling.

---

### 2. Engineered Features (`src/features/engineering.py`)

| Feature Name | Derived From | Data Type | Role | Description |
| :--- | :--- | :--- | :--- | :--- |
| `spend_to_avg_ratio` | `Transaction_Amount`, `Average_Spend` | `float64` | `numerical feature` | Ratio of current transaction amount to customer historical average spend (`Transaction_Amount / Average_Spend`). |
| `is_high_value_transaction` | `Transaction_Amount` | `int64` (Binary) | `boolean feature` | Flag (1) if transaction amount exceeds the 95th percentile threshold ($250+). |
| `transaction_hour` | `Transaction_Date` | `int64` | `numerical feature` | Hour of the day (0 to 23) extracted from `Transaction_Date`. |
| `transaction_day_of_week` | `Transaction_Date` | `int64` | `numerical feature` | Day of week (0 = Monday, 6 = Sunday) extracted from `Transaction_Date`. |
| `is_night_transaction` | `transaction_hour` | `int64` (Binary) | `boolean feature` | Flag (1) if transaction occurred during off-peak hours (00:00 - 05:59). |
| `is_weekend` | `transaction_day_of_week` | `int64` (Binary) | `boolean feature` | Flag (1) if transaction occurred on Saturday or Sunday. |
| `account_age_years` | `Account_Age_Days` | `float64` | `numerical feature` | Customer account age converted to years (`Account_Age_Days / 365.25`). |
| `suspicious_keyword_flag` | `Suspicious_Keyword` | `int64` (Binary) | `boolean feature` | Binary encoding of suspicious keyword flag (1 = 'Yes', 0 = 'No'). |
| `is_international_flag` | `Is_International` | `int64` (Binary) | `boolean feature` | Standardized integer binary flag for international status. |
