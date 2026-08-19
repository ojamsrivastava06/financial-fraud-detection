import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings
from src.config.logging_config import setup_logging
from src.database.connection import init_db
from src.models.model_registry import ModelRegistry
from src.api.routes import (
    health_router,
    transactions_router,
    predictions_router,
    analytics_router,
    alerts_router,
)

logger = setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan context manager."""
    logger.info("Initializing Financial Fraud Detection REST API...")
    init_db()

    # Efficient Singleton Application-Level Model Loading
    registry = ModelRegistry()
    model, preprocessor, metadata = registry.load_active_model()

    app.state.model = model
    app.state.preprocessor = preprocessor
    app.state.metadata = metadata

    if model:
        logger.info(f"Loaded active model '{metadata.get('model_name')}' v{metadata.get('model_version')} into application state.")
    else:
        logger.warning("No active ML model found in registry on startup.")

    yield
    logger.info("Shutting down Financial Fraud Detection API.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Production-Grade Financial Fraud Detection & Risk Scoring API",
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
)

# Enable CORS for Streamlit frontend integration with defined origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_and_logging(request: Request, call_next):
    """Timing and access logging middleware."""
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled exception in middleware on {request.method} {request.url.path}: {type(exc).__name__} - {exc}", exc_info=True)
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred. Please contact system administrator.",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )
    process_time_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} [{process_time_ms:.2f}ms]")
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic payload validation errors with structured JSON response."""
    error_details = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", [])])
        msg = err.get("msg", "Invalid value")
        error_details.append(f"{field}: {msg}")

    detail_str = "; ".join(error_details) if error_details else "Invalid request payload schema."
    logger.warning(f"Request validation failure on {request.method} {request.url.path}: {detail_str}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": detail_str,
            "error_code": "VALIDATION_ERROR",
            "errors": exc.errors()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Structured handler for standard HTTPExceptions."""
    logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "status_code": exc.status_code
        },
        headers=exc.headers
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to hide internal stack traces from clients."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {type(exc).__name__} - {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please contact system administrator.",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )


# Include API Routers
app.include_router(health_router)
app.include_router(transactions_router)
app.include_router(predictions_router)
app.include_router(analytics_router)
app.include_router(alerts_router)


@app.get("/", tags=["Root"])
def read_root():
    """Root landing endpoint."""
    return {
        "title": settings.APP_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/health",
        "readiness_check": "/ready"
    }
