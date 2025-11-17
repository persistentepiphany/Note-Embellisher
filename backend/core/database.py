from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    @property
    def settings(self):
        """Parse settings from JSON string"""
        return json.loads(self.settings_json) if self.settings_json else {}
    
    @settings.setter
    def settings(self, value):
        """Store settings as JSON string"""
        self.settings_json = json.dumps(value)


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
            "txt_path": "TEXT"
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