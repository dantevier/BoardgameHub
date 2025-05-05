from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load .env file from the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Settings(BaseSettings):
    PROJECT_NAME: str = "Boardgame RAG"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration (Example using environment variables)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db") # Use async sqlite driver
    
    # Vector DB Configuration (Example)
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "chroma")
    VECTOR_DB_PATH: str | None = os.getenv("VECTOR_DB_PATH", os.path.join(BASE_DIR, "vector_store"))
    
    # Embedding Model
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # File Uploads
    UPLOAD_FOLDER: str = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS: set[str] = {"pdf"}
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024 # 16MB
    
    # Secret Key for potential future use (e.g., JWT)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key")
    
    class Config:
        case_sensitive = True
        # If you have a .env file, uncomment the line below
        # env_file = ".env"

settings = Settings()
