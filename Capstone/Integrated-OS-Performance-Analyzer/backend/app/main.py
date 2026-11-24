from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from app.api.routes import analysis_router, history_router, system_router
from app.core.config import get_settings
from app.database.mongodb import mongodb
from app.services.metrics_persistence import get_metrics_persistence_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(mongodb.connect)
    persistence_service = get_metrics_persistence_service()
    await persistence_service.start()
    try:
        yield
    finally:
        await persistence_service.stop()
        await run_in_threadpool(mongodb.disconnect)


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Cross-platform operating system performance analyzer",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
)

app.include_router(system_router)
app.include_router(history_router)
app.include_router(analysis_router)


@app.get("/")
def root():
    return {
        "application": settings.app_name,
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    connected = await run_in_threadpool(mongodb.ping)

    if not connected:
        raise HTTPException(
            status_code=503,
            detail="MongoDB connection unavailable",
        )

    return {
        "status": "healthy",
        "database": "connected",
    }
