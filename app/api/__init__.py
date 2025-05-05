from fastapi import APIRouter

# Import the V1 router
from app.api.v1.api import api_router as api_v1_router

api_router = APIRouter()

# Include the V1 router (prefix is handled in main.py)
api_router.include_router(api_v1_router)

# Include other top-level or version-agnostic routers here if needed

# Placeholder for future routes
@api_router.get("/ping")
def ping():
    return {"ping": "pong"}
