import pytest
from httpx import AsyncClient, ASGITransport

# Import the FastAPI app instance from your main application file
# Adjust the import path if your app instance is named differently or located elsewhere
from main import app 
from app.config import settings

@pytest.mark.asyncio
async def test_read_root():
    """Test the root endpoint '/'"""
    # Use ASGITransport to wrap the FastAPI app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": f"Welcome to {settings.PROJECT_NAME}"}

@pytest.mark.asyncio
async def test_ping_api():
    """Test the API ping endpoint '/api/v1/ping'"""
    # Use ASGITransport to wrap the FastAPI app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"{settings.API_V1_STR}/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}
