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
    custom_specifications: Optional[str] = None
    generate_flashcards: bool = False
    flashcard_topics: List[str] = Field(default_factory=list)
    flashcard_count: int = 0
    max_flashcards_per_topic: int = 4
    project_name: Optional[str] = None
    latex_title: Optional[str] = None
    include_nickname: bool = False
    nickname: Optional[str] = None

class FlashcardSchema(BaseModel):
    id: str
    topic: str
    term: str
    definition: str
    source: str
    created_at: Optional[str] = None

class FolderSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

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
    project_name: Optional[str] = None
    latex_title: Optional[str] = None
    include_nickname: bool = False
    nickname: Optional[str] = None
    flashcards: List[FlashcardSchema] = Field(default_factory=list)
    folder: Optional[FolderSchema] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NoteUpdate(BaseModel):
    processed_content: str
    status: ProcessingStatus

class FlashcardCreate(BaseModel):
    topic: str
    term: str
    definition: str

class FlashcardList(BaseModel):
    flashcards: List[FlashcardSchema]

class FolderCreate(BaseModel):
    name: str

class FolderUpdate(BaseModel):
    name: str

class NoteMetadataUpdate(BaseModel):
    project_name: Optional[str] = None
    latex_title: Optional[str] = None
    include_nickname: Optional[bool] = None
    nickname: Optional[str] = None
    folder_id: Optional[int] = None
