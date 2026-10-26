import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "SmartPark - Smart Parking Queue & Slot Allocation"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # SQLite Database configuration
    SQLITE_DB_PATH: Path = DATA_DIR / "smartpark.db"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{SQLITE_DB_PATH.as_posix()}"
    )

    # Hourly rates for parking calculation
    BASE_HOURLY_RATE: float = 20.0  # ₹20 / hour
    GRACE_PERIOD_MINUTES: int = 15

    # CORS configuration
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # JWT & Authentication configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "smartpark-super-secure-jwt-secret-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

settings = Settings()
