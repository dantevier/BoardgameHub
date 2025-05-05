from fastapi import FastAPI
from app.api import api_router
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

# Add startup/shutdown events if needed
# @app.on_event("startup")
# async def startup_event():
#     pass

# @app.on_event("shutdown")
# async def shutdown_event():
#     pass
