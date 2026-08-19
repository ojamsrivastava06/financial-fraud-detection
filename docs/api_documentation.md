# REST API Documentation — Financial Fraud Detection Platform

## 1. Overview & Architecture
The Financial Fraud Detection REST API is built with **FastAPI** and **Pydantic v2**. It exposes endpoints for real-time transaction fraud inference, batch processing, data exploration, dynamic analytics, security alert incident response, and container health/readiness probes.

- **Base URL**: `http://localhost:8000`
- **Interactive OpenAPI Docs (Swagger UI)**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Diagnostic Response Header**: `X-Process-Time-Ms` (latency in milliseconds)

---

## 2. API Endpoints Specification

### 2.1 Health & Readiness Probes

#### `GET /health`
- **Summary**: Liveness probe returning application availability, database connectivity, and active ML model information.
- **HTTP Status Codes**: `200 OK`
- **Response Schema**:
```json
{
  "status": "healthy",
  "app_name": "Financial Fraud Detection Platform",
  "environment": "production",
  "database": "connected",
  "model_loaded": true,
  "model_name": "Logistic Regression",
  "model_version": "1.0.0",
  "timestamp": "2026-08-16T18:40:00.000000+00:00"
}
```

#### `GET /ready` (or `GET /health/ready`)
- **Summary**: Readiness probe verifying database connectivity, ML model binary artifact, preprocessing pipeline artifact, and metadata availability.
- **HTTP Status Codes**: `200 OK` (when all dependencies healthy), `503 Service Unavailable` (when any component fails).
- **Response Schema**:
```json
{
  "status": "ready",
  "app_name": "Financial Fraud Detection Platform",
  "environment": "production",
  "database": {
    "status": "healthy",
    "details": "Database connection pool verified."
  },
  "model_artifact": {
    "status": "healthy",
    "details": "Trained model artifact found at fraud_model.joblib"
  },
  "preprocessor_artifact": {
    "status": "healthy",
    "details": "Preprocessor artifact found at preprocessor.joblib"
  },
  "metadata_artifact": {
    "status": "healthy",
    "details": "Metadata found at model_metadata.json"
  },
  "timestamp": "2026-08-16T18:40:00.000000+00:00"
}
```

---

### 2.2 Transaction Explorer API

#### `GET /transactions`
- **Summary**: Retrieve paginated list of financial transactions with granular filtering.
- **Query Parameters**:
  - `skip` (int, default `0`, min `0`): Pagination offset.
  - `limit` (int, default `50`, min `1`, max `500`): Page size cap.
  - `search` (string, optional): Search query matching `transaction_id`, `customer_id`, or `location`.
  - `fraud_only` (bool, optional): Filter for predicted fraud (`1`) transactions only.
  - `risk_level` (string, optional): Filter by risk tier (`LOW`, `MEDIUM`, `HIGH`).
  - `merchant_category` (string, optional): Merchant business category (`Travel`, `Grocery`, etc.).
  - `payment_method` (string, optional): Payment instrument (`Credit Card`, `Debit Card`, etc.).
- **Response**: Array of transaction objects with model inference scores.

#### `GET /transactions/{transaction_id}`
- **Summary**: Retrieve single transaction details by unique transaction ID.
- **HTTP Status Codes**: `200 OK`, `404 Not Found`.

---

### 2.3 Machine Learning Fraud Prediction API

#### `POST /predictions/predict`
- **Summary**: Real-time fraud scoring for single transaction payload. Executes feature engineering, ColumnTransformer preprocessing, Logistic Regression inference, risk tier assignment, database persistence, and alert engine evaluation.
- **HTTP Status Codes**: `200 OK`, `400 Bad Request`, `422 Unprocessable Entity`, `503 Service Unavailable`.
- **Request Body**:
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
- **Response Schema**:
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

#### `POST /predictions/batch`
- **Summary**: Batch transaction prediction endpoint. Processes list of transactions (max 500 per batch), returning individual predictions for valid items and isolating errors without crashing the batch.
- **HTTP Status Codes**: `200 OK`, `400 Bad Request` (empty batch), `413 Request Entity Too Large` (>500 items), `422 Unprocessable Entity`.
- **Request Body**:
```json
{
  "transactions": [
    {
      "transaction_id": "T88881",
      "customer_id": "CUST881",
      "transaction_date": "14-08-2026 10:00",
      "transaction_amount": 30.0,
      "merchant_category": "Grocery",
      "payment_method": "Debit Card",
      "device_type": "Mobile",
      "location": "Mumbai",
      "is_international": 0,
      "previous_transactions": 100,
      "average_spend": 35.0,
      "account_age_days": 500,
      "suspicious_keyword": "No"
    }
  ]
}
```
- **Response Schema**:
```json
{
  "total_submitted": 1,
  "successful_predictions": 1,
  "failed_predictions": 0,
  "predictions": [
    {
      "transaction_id": "T88881",
      "fraud_probability": 0.0245,
      "fraud_percentage": 2.45,
      "fraud_prediction": 0,
      "risk_score": 2.5,
      "risk_level": "LOW",
      "action": "APPROVE",
      "threshold_used": 0.65,
      "model_name": "Logistic Regression"
    }
  ],
  "errors": []
}
```

---

### 2.4 Analytics API

#### `GET /analytics/summary`
- **Summary**: Dynamically calculated fraud detection aggregates across stored database transactions.
- **Response Schema**:
```json
{
  "total_transactions": 5000,
  "total_fraud_predictions": 178,
  "total_legitimate_predictions": 4822,
  "high_risk_count": 178,
  "medium_risk_count": 312,
  "low_risk_count": 4510,
  "fraud_rate_pct": 3.56,
  "total_transaction_value": 754320.5,
  "high_risk_value": 89450.0,
  "average_transaction_value": 150.86
}
```

#### `GET /analytics/time-series`
- **Summary**: Daily aggregated transaction volume, fraud count, risk tiers, and total monetary volume.

---

### 2.5 Security Alerts Management API

#### `GET /alerts`
- **Summary**: Paginated list of security alerts with filtering.
- **Query Parameters**:
  - `status` (optional): `OPEN`, `INVESTIGATING`, `RESOLVED`, `DISMISSED`
  - `severity` (optional): `MEDIUM`, `HIGH`, `CRITICAL`
  - `skip` (default `0`, min `0`)
  - `limit` (default `50`, min `1`, max `500`)

#### `GET /alerts/{alert_id}`
- **Summary**: Retrieve alert details by primary alert ID.

#### `PATCH /alerts/{alert_id}`
- **Summary**: Update security alert status and record investigative resolution notes.
- **Request Body**:
```json
{
  "status": "RESOLVED",
  "resolution_notes": "Verified with cardholder via two-factor SMS. Transaction authorized."
}
```
- **Response Schema**: Updated alert object with `resolved_at` timestamp.

---

## 3. Error Handling & Status Codes

The API returns consistent JSON error envelopes:
```json
{
  "detail": "Descriptive error message",
  "error_code": "VALIDATION_ERROR",
  "status_code": 422
}
```

| HTTP Status | Error Code | Description |
|---|---|---|
| `400 Bad Request` | `HTTP_400` / `BAD_REQUEST` | Malformed parameter or empty batch payload. |
| `404 Not Found` | `HTTP_404` / `NOT_FOUND` | Resource ID not found in database. |
| `413 Payload Too Large` | `HTTP_413` | Batch size exceeds max limit (500 items). |
| `422 Unprocessable` | `VALIDATION_ERROR` | Request payload failed Pydantic schema validation. |
| `500 Server Error` | `INTERNAL_SERVER_ERROR` | Internal server error (stack traces hidden from response). |
| `503 Unavailable` | `SERVICE_UNAVAILABLE` | Dependency (model artifact or database) unavailable. |
