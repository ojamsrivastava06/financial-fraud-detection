"""
Application configuration settings module using Pydantic settings.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global system configuration settings."""

    # Application settings
    APP_NAME: str = "Financial Fraud Detection Platform"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_PATH: Path = Field(
        default=Path("data/raw/financial_fraud_detection_dataset.csv"),
        description="Path to primary raw dataset"
    )
    INTERIM_DATA_PATH: Path = Path("data/interim")
    PROCESSED_DATA_PATH: Path = Path("data/processed")
    MODEL_PATH: Path = Path("models/trained/fraud_model.joblib")
    PREPROCESSOR_PATH: Path = Path("models/preprocessing/preprocessor.joblib")
    METADATA_PATH: Path = Path("models/metadata")

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./database/fraud_detection.db"

    # Server settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    PORT: Optional[int] = None
    DASHBOARD_PORT: int = 8501
    API_URL: str = "http://localhost:8000"

    # Fraud Risk Scoring Thresholds
    HIGH_RISK_THRESHOLD: float = 0.65
    MEDIUM_RISK_THRESHOLD: float = 0.35
    RISK_THRESHOLD: float = 0.65

    # Security & CORS settings
    APP_DEBUG: bool = False
    CORS_ORIGINS: str = "*"
    MAX_BATCH_SIZE: int = 500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS into list for CORSMiddleware."""
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
