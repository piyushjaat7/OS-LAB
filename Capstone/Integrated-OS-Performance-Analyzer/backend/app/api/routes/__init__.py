from app.api.routes.analysis import router as analysis_router
from app.api.routes.history import router as history_router
from app.api.routes.system import router as system_router

__all__ = ["analysis_router", "history_router", "system_router"]
