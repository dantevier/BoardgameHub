from fastapi import APIRouter

# Import individual routers here (e.g., from .endpoints import games)

api_router = APIRouter()

# Include individual routers here
# api_router.include_router(games.router, prefix="/games", tags=["games"])

# Placeholder for future routes
@api_router.get("/ping")
def ping():
    return {"ping": "pong"}
