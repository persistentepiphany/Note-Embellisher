from pydantic import BaseModel, Field
from typing import Optional, List
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
    focus_topics: List[str] = Field(default_factory=list)
    latex_style: str = "academic"
    font_preference: str = "Times New Roman"

class NoteCreate(BaseModel):
    text: str
    settings: ProcessingSettingsSchema

class NoteResponse(BaseModel):
    id: int
    text: Optional[str] = None  # Made optional since image notes start without text
    settings: ProcessingSettingsSchema
    processed_content: Optional[str] = None
    status: ProcessingStatus
    progress: Optional[int] = None
    progress_message: Optional[str] = None
    # Image-related fields
    image_url: Optional[str] = None
    image_filename: Optional[str] = None
    image_type: Optional[str] = None
    input_type: str = "text"
    pdf_url: Optional[str] = None
    docx_url: Optional[str] = None
    txt_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NoteUpdate(BaseModel):
    processed_content: str
    status: ProcessingStatus