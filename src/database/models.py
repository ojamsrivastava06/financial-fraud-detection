"""
SQLAlchemy ORM Database models for transactions, prediction events, and security alerts.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from src.database.connection import Base


def utc_now():
    """Helper for timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class TransactionModel(Base):
    """SQLAlchemy model representing financial transactions."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=False)
    transaction_date = Column(String(64), index=True, nullable=False)
    transaction_amount = Column(Float, nullable=False)
    merchant_category = Column(String(64), index=True, nullable=False)
    payment_method = Column(String(64), index=True, nullable=False)
    device_type = Column(String(64), nullable=False)
    location = Column(String(64), nullable=False)
    is_international = Column(Integer, default=0)
    previous_transactions = Column(Integer, default=0)
    average_spend = Column(Float, default=0.0)
    account_age_days = Column(Integer, default=0)
    suspicious_keyword = Column(String(16), default="No")
    fraudulent = Column(Integer, nullable=True)  # Ground truth label if available (0 or 1)

    # Model inference outputs
    fraud_probability = Column(Float, nullable=True)
    fraud_prediction = Column(Integer, index=True, nullable=True)  # 0 or 1
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(32), index=True, nullable=True)  # LOW, MEDIUM, HIGH
    prediction_timestamp = Column(DateTime, default=utc_now)

    # Relationships
    predictions = relationship("PredictionModel", back_populates="transaction", cascade="all, delete-orphan")
    alerts = relationship("AlertModel", back_populates="transaction", cascade="all, delete-orphan")


class PredictionModel(Base):
    """SQLAlchemy model for storing model inference log events."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    model_name = Column(String(64), nullable=False)
    model_version = Column(String(32), nullable=False)
    fraud_probability = Column(Float, nullable=False)
    fraud_prediction = Column(Integer, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(32), nullable=False)
    threshold_used = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now, index=True)

    transaction = relationship("TransactionModel", back_populates="predictions")


class AlertModel(Base):
    """SQLAlchemy model for security alert management."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    alert_type = Column(String(64), default="FRAUD_RISK_FLAG")
    severity = Column(String(32), nullable=False, index=True)  # MEDIUM, HIGH, CRITICAL
    fraud_probability = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    status = Column(String(32), default="OPEN", index=True)  # OPEN, INVESTIGATING, RESOLVED, DISMISSED
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    transaction = relationship("TransactionModel", back_populates="alerts")


# Composite indexes for query performance
Index("idx_tx_date_risk", TransactionModel.transaction_date, TransactionModel.risk_level)
Index("idx_tx_fraud_pred", TransactionModel.fraud_prediction, TransactionModel.risk_level)
Index("idx_tx_cust_date", TransactionModel.customer_id, TransactionModel.transaction_date)
Index("idx_alert_status_sev", AlertModel.status, AlertModel.severity)
