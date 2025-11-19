from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import json
from datetime import datetime

# Database URL - Using SQLite for development
DATABASE_URL = "sqlite:///./notes.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    # ----- firebase-fix: Add user_id to link notes to users -----
    user_id = Column(String, index=True, nullable=False)
    # ----------------------------------------------------------
    text = Column(Text, nullable=True)  # Made nullable since we might have image-only notes
    settings_json = Column(Text, nullable=False)  # Store settings as JSON string
    processed_content = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0, server_default="0")
    progress_message = Column(Text, nullable=True)
    # Image-related fields
    image_url = Column(String, nullable=True)  # Dropbox shareable URL
    image_path = Column(String, nullable=True)  # Dropbox file path for internal operations
    image_filename = Column(String, nullable=True)  # Original filename
    image_type = Column(String(10), nullable=True)  # 'image' or 'pdf'
    input_type = Column(String(10), default="text")  # 'text' or 'image'
    # Export-related fields
    pdf_path = Column(String, nullable=True)
    tex_path = Column(String, nullable=True)
    docx_path = Column(String, nullable=True)
    txt_path = Column(String, nullable=True)
    project_name = Column(String, nullable=True)
    latex_title = Column(String, nullable=True)
    include_nickname = Column(Boolean, default=False, server_default="0")
    nickname = Column(String, nullable=True)
    flashcards_json = Column(Text, nullable=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    folder = relationship("Folder", back_populates="notes")
    
    @property
    def settings(self):
        """Parse settings from JSON string"""
        return json.loads(self.settings_json) if self.settings_json else {}
    
    @settings.setter
    def settings(self, value):
        """Store settings as JSON string"""
        self.settings_json = json.dumps(value)

    @property
    def flashcards(self):
        if not self.flashcards_json:
            return []
        try:
            return json.loads(self.flashcards_json)
        except json.JSONDecodeError:
            return []

    @flashcards.setter
    def flashcards(self, value):
        self.flashcards_json = json.dumps(value or [])


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    notes = relationship("Note", back_populates="folder")


class GoogleDriveToken(Base):
    __tablename__ = "google_drive_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    token_scope = Column(Text, nullable=True)
    token_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Create tables
Base.metadata.create_all(bind=engine)


def _ensure_note_columns():
    """Add new export-related columns to the notes table if they are missing."""
    try:
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("notes")}
        required_columns = {
            "pdf_path": "TEXT",
            "tex_path": "TEXT",
            "docx_path": "TEXT",
            "txt_path": "TEXT",
            "progress": "INTEGER DEFAULT 0",
            "progress_message": "TEXT",
            "project_name": "TEXT",
            "latex_title": "TEXT",
            "include_nickname": "BOOLEAN DEFAULT 0",
            "nickname": "TEXT",
            "flashcards_json": "TEXT",
            "folder_id": "INTEGER"
        }
        missing = [name for name in required_columns if name not in columns]
        if not missing:
            return
        with engine.connect() as conn:
            for name in missing:
                ddl = required_columns[name]
                conn.execute(text(f"ALTER TABLE notes ADD COLUMN {name} {ddl}"))
            conn.commit()
            print(f"Added missing note columns: {missing}")
    except Exception as e:
        print(f"Could not verify note columns: {e}")


_ensure_note_columns()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
