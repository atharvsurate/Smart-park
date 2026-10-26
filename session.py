from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Create SQLite engine with WAL mode and multi-thread support
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> dict:
    """Verifies that the SQLite database engine is reachable and writable."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            return {
                "status": "connected" if result == 1 else "unexpected_result",
                "engine": "sqlite",
                "database_url": settings.DATABASE_URL,
                "db_file_exists": settings.SQLITE_DB_PATH.exists()
            }
    except Exception as e:
        return {
            "status": "error",
            "engine": "sqlite",
            "error": str(e),
            "database_url": settings.DATABASE_URL
        }
