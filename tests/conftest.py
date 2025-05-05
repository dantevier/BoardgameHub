import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Adjust the import based on your actual app structure
# If main.py is in the root, and app instance is 'app'
from main import app

@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncClient:
    """Provides an asynchronous client for testing the FastAPI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

# You can add other shared fixtures here, like database session fixtures if needed
# Example (if you weren't already handling this in test_db_setup.py):
# from app.db.session import TestingSessionLocal, engine
# from app.db.models import Base
#
# @pytest.fixture(scope="session", autouse=True)
# def setup_test_db():
#     Base.metadata.create_all(bind=engine)
#     yield
#     Base.metadata.drop_all(bind=engine)
#
# @pytest_asyncio.fixture(scope="function")
# async def db_session():
#     async with TestingSessionLocal() as session:
#         yield session
#         await session.rollback() # Ensure clean state after each test
