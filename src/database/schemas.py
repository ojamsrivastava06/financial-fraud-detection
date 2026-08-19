"""
Pydantic schemas for request validation, API serialization, and analytics responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TransactionBase(BaseModel):
    """Base transaction payload schema matching raw dataset columns with validation constraints."""

    transaction_id: str = Field(..., min_length=1, max_length=64, description="Unique transaction ID e.g. T100000")
    customer_id: str = Field(..., min_length=1, max_length=64, description="Customer identifier e.g. CUST3252")
    transaction_date: str = Field(..., min_length=5, max_length=32, description="Timestamp string e.g. 04-10-2023 07:45")
    transaction_amount: float = Field(..., gt=0, le=10000000.0, description="Transaction monetary amount")
    merchant_category: str = Field(..., min_length=1, max_length=64, description="Merchant business category")
    payment_method: str = Field(..., min_length=1, max_length=64, description="Payment instrument")
    device_type: str = Field(..., min_length=1, max_length=64, description="Device used for transaction")
    location: str = Field(..., min_length=1, max_length=128, description="Geographic location")
    is_international: int = Field(0, ge=0, le=1, description="1 if international transaction, else 0")
    previous_transactions: int = Field(0, ge=0, le=100000, description="Prior customer transaction count")
    average_spend: float = Field(0.0, ge=0, le=10000000.0, description="Historical customer average spend")
    account_age_days: int = Field(0, ge=0, le=50000, description="Age of customer account in days")
    suspicious_keyword: str = Field("No", max_length=32, description="Presence of suspicious keyword")
    fraudulent: Optional[int] = Field(None, ge=0, le=1, description="Ground truth label (0 or 1)")


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction record."""
    pass


class TransactionResponse(TransactionBase):
    """Schema for returning detailed transaction records."""

    id: int
    fraud_probability: Optional[float] = None
    fraud_prediction: Optional[int] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    prediction_timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PredictionRequest(BaseModel):
    """Schema for single transaction prediction request."""

    transaction: TransactionBase


class PredictionResponse(BaseModel):
    """Schema for prediction response."""

    transaction_id: str
    fraud_probability: float
    fraud_percentage: float
    fraud_prediction: int
    risk_score: float
    risk_level: str
    action: str
    threshold_used: float
    model_name: str


class BatchPredictionRequest(BaseModel):
    """Schema for batch prediction request."""

    transactions: List[TransactionBase]


class BatchPredictionResponse(BaseModel):
    """Schema for batch prediction response."""

    total_submitted: int
    successful_predictions: int
    failed_predictions: int
    predictions: List[PredictionResponse]
    errors: List[Dict[str, Any]]


class AlertResponse(BaseModel):
    """Schema for security alerts."""

    id: int
    transaction_id: str
    alert_type: str
    severity: str
    fraud_probability: float
    risk_score: float
    status: str
    message: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AlertUpdate(BaseModel):
    """Schema for updating alert status."""

    status: str = Field(..., pattern="^(OPEN|INVESTIGATING|RESOLVED|DISMISSED|open|investigating|resolved|dismissed)$", description="Target status: OPEN, INVESTIGATING, RESOLVED, DISMISSED")
    resolution_notes: Optional[str] = Field(None, max_length=1000, description="Analyst review notes")


class AnalyticsSummary(BaseModel):
    """Aggregated financial fraud metrics summary."""

    total_transactions: int
    total_fraud_predictions: int
    total_legitimate_predictions: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    fraud_rate_pct: float
    total_transaction_value: float
    high_risk_value: float
    average_transaction_value: float


class TimeSeriesDataPoint(BaseModel):
    """Aggregated daily time-series data point."""

    date: str
    total_count: int
    fraud_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    total_amount: float
    fraud_amount: float


class TimeSeriesAnalytics(BaseModel):
    """Time-series analytics trend response."""

    period: str
    data_points: List[TimeSeriesDataPoint]


class ErrorResponse(BaseModel):
    """Structured error response schema."""

    detail: str
    error_code: Optional[str] = None
    timestamp: Optional[str] = None


class HealthResponse(BaseModel):
    """Structured health check response schema."""

    status: str
    app_name: str
    environment: str
    database: str
    model_loaded: bool
    model_name: str
    model_version: str
    timestamp: str


class ComponentHealth(BaseModel):
    """Component status detail."""

    status: str = Field(..., description="Status string: healthy, degraded, or unhealthy")
    details: Optional[str] = None


class ReadinessResponse(BaseModel):
    """Structured readiness probe response schema."""

    status: str = Field(..., description="Readiness status: ready or not_ready")
    app_name: str
    environment: str
    database: ComponentHealth
    model_artifact: ComponentHealth
    preprocessor_artifact: ComponentHealth
    metadata_artifact: ComponentHealth
    timestamp: str
