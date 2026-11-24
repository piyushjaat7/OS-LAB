from fastapi import HTTPException, status
from pymongo.database import Database

from app.collectors.system import SystemMetricsCollector
from app.database.mongodb import mongodb

_system_collector_instance: SystemMetricsCollector | None = None


def get_system_collector() -> SystemMetricsCollector:
    """Retrieve or initialize the persistent application-wide SystemMetricsCollector.

    Preserves collector state across HTTP requests so that CPU, network, and
    process sampling baselines remain continuous and accurate.
    Can be overridden in tests via FastAPI dependency_overrides.
    """
    global _system_collector_instance
    if _system_collector_instance is None:
        _system_collector_instance = SystemMetricsCollector()
    return _system_collector_instance


def reset_system_collector() -> None:
    """Reset the persistent collector instance (primarily for clean test isolation)."""
    global _system_collector_instance
    _system_collector_instance = None


def get_database() -> Database:
    """Retrieve the connected MongoDB database instance.

    Raises HTTPException 503 if the database is disconnected or uninitialized.
    Can be overridden in tests via FastAPI dependency_overrides.
    """
    if mongodb.database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is currently unavailable",
        )
    return mongodb.database
