from sqlalchemy import (Column, Integer, String, Text, DateTime, Boolean, ForeignKey)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

# Function to ensure timezone awareness
def nowtz():
    return datetime.datetime.now(datetime.timezone.utc)

class Game(Base):
    __tablename__ = "games"

    game_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    bgg_id = Column(Integer, nullable=True, unique=True) # From PRD schema
    cover_image_url = Column(String(512)) # From PRD schema
    # Using server_default for creation, onupdate for updates, ensuring timezone
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=nowtz, onupdate=nowtz)

    rulebooks = relationship("Rulebook", back_populates="game")
    chat_history = relationship("ChatHistory", back_populates="game")

class Rulebook(Base):
    __tablename__ = "rulebooks"

    rulebook_id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False)
    # Removed game_title, link via game_id
    original_filename = Column(String(255))
    storage_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), unique=True) # From PRD schema
    processing_status = Column(String(50), default='Processed') # From PRD schema
    # processed_date uses server_default with timezone
    processed_date = Column(DateTime(timezone=True), server_default=func.now())
    page_count = Column(Integer)

    game = relationship("Game", back_populates="rulebooks")

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255)) # Store appropriately hashed passwords
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submissions = relationship("GameSubmission", back_populates="submitted_by")
    chat_history = relationship("ChatHistory", back_populates="user")

class ChatHistory(Base):
    __tablename__ = "chat_history"

    message_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True) # Allow anonymous chat
    role = Column(String(50), nullable=False) # e.g., 'user', 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    citations = Column(Text) # Store citations as JSON string or similar?

    game = relationship("Game", back_populates="chat_history")
    user = relationship("User", back_populates="chat_history")

class GameSubmission(Base):
    __tablename__ = "game_submissions"

    submission_id = Column(Integer, primary_key=True, index=True)
    game_title = Column(String(255), nullable=False)
    user_description = Column(Text)
    submitted_rulebook_path = Column(String(512))
    submission_status = Column(String(50), default='Pending Review', index=True)
    submitted_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    admin_notes = Column(Text)

    submitted_by = relationship("User", back_populates="submissions")
