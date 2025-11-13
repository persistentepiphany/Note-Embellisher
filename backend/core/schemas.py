from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class ProcessingSettingsSchema(BaseModel):
    add_bullet_points: bool = False
    add_headers: bool = False
    expand: bool = False
    summarize: bool = False

class NoteCreate(BaseModel):
    text: str
    settings: ProcessingSettingsSchema

class NoteResponse(BaseModel):
    id: int
    text: Optional[str] = None  # Made optional since image notes start without text
    settings: ProcessingSettingsSchema
    processed_content: Optional[str] = None
    status: ProcessingStatus
    # Image-related fields
    image_url: Optional[str] = None
    image_filename: Optional[str] = None
    image_type: Optional[str] = None
    input_type: str = "text"
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NoteUpdate(BaseModel):
    processed_content: str
    status: ProcessingStatus