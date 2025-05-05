from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import shutil
from pathlib import Path

router = APIRouter()

# Define a temporary directory for uploads (you might want to configure this)
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload", status_code=201)
async def upload_rulebook(file: UploadFile = File(...)):
    """
    Accepts a PDF file upload, saves it temporarily, and returns confirmation.
    
    Later, this will trigger the RAG processing pipeline.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are accepted.")

    try:
        # Create a safe filename (or generate a unique one)
        # For now, just use the original filename, but consider sanitizing it
        file_path = UPLOAD_DIR / file.filename

        # Save the uploaded file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    except Exception as e:
        # Clean up the file object
        await file.close()
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        # Always close the file
        await file.close()

    return {"filename": file.filename, "detail": "File uploaded successfully. Processing pending."}
