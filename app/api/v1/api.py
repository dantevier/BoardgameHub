from fastapi import APIRouter

from app.api.v1.endpoints import rulebooks

api_router = APIRouter()
api_router.include_router(rulebooks.router, prefix="/rulebooks", tags=["rulebooks"])

# Add other v1 endpoint routers here in the future
# e.g., api_router.include_router(games.router, prefix="/games", tags=["games"])
