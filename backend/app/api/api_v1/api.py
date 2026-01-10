from fastapi import APIRouter
from app.api.api_v1.endpoints import login, pipelines, jobs, utils, auth, ops

api_router = APIRouter()

# Legacy login (for backward compatibility)
api_router.include_router(login.router, tags=["login"])

# New auth endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Ops endpoints (admin only)
api_router.include_router(ops.router, prefix="/ops", tags=["ops"])

# Core endpoints
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
