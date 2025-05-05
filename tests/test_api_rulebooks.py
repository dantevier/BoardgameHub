import pytest
from httpx import AsyncClient
from fastapi import UploadFile
from pathlib import Path
import os
import shutil
from io import BytesIO

# Assuming your FastAPI app instance is accessible for testing
# If main.py is in the root, and app instance is 'app'
from main import app # Adjust the import based on your actual app structure

UPLOAD_DIR_TEST = Path("temp_uploads_test")

# Fixture to create and clean up the test upload directory
@pytest.fixture(scope="module", autouse=True)
def setup_test_upload_dir():
    UPLOAD_DIR_TEST.mkdir(exist_ok=True)
    yield
    shutil.rmtree(UPLOAD_DIR_TEST)

# Fixture to override the UPLOAD_DIR in the endpoint for testing
@pytest.fixture(autouse=True)
def override_upload_dir(monkeypatch):
    # Need to know the exact module where UPLOAD_DIR is defined
    # Assuming it's in app.api.v1.endpoints.rulebooks
    from app.api.v1.endpoints import rulebooks
    monkeypatch.setattr(rulebooks, 'UPLOAD_DIR', UPLOAD_DIR_TEST)

@pytest.mark.asyncio
async def test_upload_pdf_success(async_client: AsyncClient):
    """Test successful upload of a PDF file."""
    # Create a dummy PDF-like content
    dummy_pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n120\n%%EOF"
    file_content = BytesIO(dummy_pdf_content)
    test_filename = "test_rulebook.pdf"
    files = {'file': (test_filename, file_content, 'application/pdf')}

    response = await async_client.post("/api/v1/rulebooks/upload", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == test_filename
    assert "uploaded successfully" in data["detail"]

    # Check if file was actually saved in the test directory
    saved_file_path = UPLOAD_DIR_TEST / test_filename
    assert saved_file_path.exists()
    assert saved_file_path.is_file()
    # Optional: Check content length or a hash if needed
    assert saved_file_path.read_bytes() == dummy_pdf_content

    # Clean up the created file
    os.remove(saved_file_path)

@pytest.mark.asyncio
async def test_upload_invalid_file_type(async_client: AsyncClient):
    """Test uploading a non-PDF file."""
    dummy_text_content = b"This is not a PDF."
    file_content = BytesIO(dummy_text_content)
    test_filename = "not_a_pdf.txt"
    files = {'file': (test_filename, file_content, 'text/plain')}

    response = await async_client.post("/api/v1/rulebooks/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "Invalid file type" in data["detail"]

    # Check that the file was NOT saved
    saved_file_path = UPLOAD_DIR_TEST / test_filename
    assert not saved_file_path.exists()

# Add more tests: e.g., file save error, large files, concurrent uploads etc.

