"""
Health check and Readiness probe REST route endpoints.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.config.settings import settings
from src.database.connection import get_db
from src.database.schemas import HealthResponse, ReadinessResponse, ComponentHealth
from src.models.model_registry import ModelRegistry

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="System Health & Liveness Status")
def check_health(db: Session = Depends(get_db)):
    """
    Liveness probe returning application availability, database connectivity, and active model info.
    """
    db_connected = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_connected = False

    registry = ModelRegistry()
    model, _, metadata = registry.load_active_model()
    model_loaded = model is not None
    model_name = metadata.get("model_name", "None") if metadata else "None"
    model_version = metadata.get("model_version", "None") if metadata else "None"

    status_str = "healthy" if (db_connected and model_loaded) else "degraded"

    return HealthResponse(
        status=status_str,
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        database="connected" if db_connected else "disconnected",
        model_loaded=model_loaded,
        model_name=model_name,
        model_version=model_version,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@router.get("/ready", response_model=ReadinessResponse, summary="System Readiness Probe")
@router.get("/health/ready", response_model=ReadinessResponse, summary="System Readiness Probe (Alias)")
def check_readiness(response: Response, db: Session = Depends(get_db)):
    """
    Readiness probe verifying database connectivity, ML model binary artifact,
    preprocessing pipeline artifact, and model metadata availability.
    Returns HTTP 200 when all dependencies are ready; HTTP 503 when any dependency is unavailable.
    """
    # 1. Check Database Connectivity
    db_status = "healthy"
    db_details = "Database connection pool verified."
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        db_details = f"Database connectivity error: {type(e).__name__}"

    # 2. Check Model Artifacts
    registry = ModelRegistry()
    model_path = registry.trained_dir / "fraud_model.joblib"
    preproc_path = registry.preprocessing_dir / "preprocessor.joblib"
    meta_path = registry.metadata_dir / "model_metadata.json"

    model_status = "healthy" if model_path.exists() else "unhealthy"
    model_details = f"Trained model artifact found at {model_path.name}" if model_path.exists() else "Model artifact missing"

    preproc_status = "healthy" if preproc_path.exists() else "unhealthy"
    preproc_details = f"Preprocessor artifact found at {preproc_path.name}" if preproc_path.exists() else "Preprocessor artifact missing"

    meta_status = "healthy" if meta_path.exists() else "unhealthy"
    meta_details = f"Metadata found at {meta_path.name}" if meta_path.exists() else "Metadata artifact missing"

    all_healthy = (
        db_status == "healthy"
        and model_status == "healthy"
        and preproc_status == "healthy"
        and meta_status == "healthy"
    )

    readiness_status = "ready" if all_healthy else "not_ready"

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status=readiness_status,
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        database=ComponentHealth(status=db_status, details=db_details),
        model_artifact=ComponentHealth(status=model_status, details=model_details),
        preprocessor_artifact=ComponentHealth(status=preproc_status, details=preproc_details),
        metadata_artifact=ComponentHealth(status=meta_status, details=meta_details),
        timestamp=datetime.now(timezone.utc).isoformat()
    )
