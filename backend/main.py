from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional, Union
import json
from fastapi.security import OAuth2PasswordBearer
import sys
import os
import secrets
from datetime import datetime, timezone
from pydantic import BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

print("=" * 50)
print("STARTING NOTE EMBELLISHER API")
print("=" * 50)
print(f"Python version: {sys.version}")
print(f"Working directory: {sys.path[0]}")

# Optional Firebase - disable if not available
try:
    from firebase_admin import auth
    FIREBASE_AVAILABLE = True
except ImportError as e:
    print(f"Firebase admin not available: {e}")
    FIREBASE_AVAILABLE = False
    auth = None

# Optional imports - make everything optional for minimal deployment
try:
    from core.database import get_db, Note, GoogleDriveToken, Folder
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Database not available: {e}")
    DATABASE_AVAILABLE = False

try:
    from core.schemas import (
        NoteCreate,
        NoteResponse,
        NoteUpdate,
        ProcessingStatus,
        ProcessingSettingsSchema,
        FlashcardCreate,
        FlashcardList,
        FolderCreate,
        FolderUpdate,
        NoteMetadataUpdate,
        FolderSchema
    )
    SCHEMAS_AVAILABLE = True
except ImportError as e:
    print(f"Schemas not available: {e}")
    SCHEMAS_AVAILABLE = False

try:
    from services.chatgpt_service import chatgpt_service, ProcessingSettings
    CHATGPT_AVAILABLE = True
except ImportError as e:
    print(f"ChatGPT service not available: {e}")
    CHATGPT_AVAILABLE = False

try:
    from services.dropbox_service import dropbox_service
    DROPBOX_AVAILABLE = True
except ImportError as e:
    print(f"Dropbox service not available: {e}")
    DROPBOX_AVAILABLE = False

try:
    from services.document_export_service import export_service, DOCX_AVAILABLE
    EXPORT_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"Document export service not available: {e}")
    export_service = None
    DOCX_AVAILABLE = False
    EXPORT_SERVICE_AVAILABLE = False

# Optional OCR service - disable if not available
try:
    from services.ocr_service import ocr_service
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"OCR service not available: {e}")
    OCR_AVAILABLE = False
    ocr_service = None

# Optional LaTeX and PDF services
try:
    from pdf_generation.latex_service import latex_service
    LATEX_AVAILABLE = True
except ImportError as e:
    print(f"LaTeX service not available: {e}")
    LATEX_AVAILABLE = False
    latex_service = None

try:
    from pdf_generation.pdf_compiler import pdf_compiler
    PDF_COMPILER_AVAILABLE = True
except ImportError as e:
    print(f"PDF compiler not available: {e}")
    PDF_COMPILER_AVAILABLE = False
    pdf_compiler = None

try:
    from services.google_drive_service import google_drive_service
    GOOGLE_DRIVE_SERVICE_AVAILABLE = google_drive_service.is_configured
except ImportError as e:
    print(f"Google Drive service not available: {e}")
    google_drive_service = None
    GOOGLE_DRIVE_SERVICE_AVAILABLE = False

# Optional Firebase SDK
firebase_init_module = None
try:
    # First try the safe, committable version
    import firebase_init as firebase_init_module
    FIREBASE_SDK_AVAILABLE = True
    print("Firebase init module imported")
except ImportError:
    try:
        # Fall back to the legacy version if it exists
        import firebasesdk as firebase_init_module
        FIREBASE_SDK_AVAILABLE = True
        print("Firebase SDK module imported (legacy)")
    except ImportError as e:
        print(f"Firebase SDK not available: {e}")
        FIREBASE_SDK_AVAILABLE = False
        firebase_init_module = None

# ----- firebase-fix: Add authentication dependency -----
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

BACKEND_DIR = os.path.dirname(__file__)
GENERATED_FILES_ROUTE = "/generated_pdfs"
DRIVE_STATE_TTL_SECONDS = 600
drive_auth_states: Dict[str, Dict[str, datetime]] = {}


def _cleanup_drive_states() -> None:
    cutoff = datetime.now(timezone.utc).timestamp() - DRIVE_STATE_TTL_SECONDS
    stale_keys = [state for state, data in drive_auth_states.items() if data["created_at"].timestamp() < cutoff]
    for key in stale_keys:
        drive_auth_states.pop(key, None)


def _remember_drive_state(state: str, user_id: str) -> None:
    _cleanup_drive_states()
    drive_auth_states[state] = {
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc)
    }


def _consume_drive_state(state: str) -> Optional[str]:
    data = drive_auth_states.pop(state, None)
    if not data:
        return None
    if (datetime.now(timezone.utc) - data["created_at"]).total_seconds() > DRIVE_STATE_TTL_SECONDS:
        return None
    return data["user_id"]


def absolute_export_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(BACKEND_DIR, path))


def export_file_exists(path: Optional[str]) -> bool:
    abs_path = absolute_export_path(path)
    return bool(abs_path and os.path.exists(abs_path))


def build_generated_file_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    filename = os.path.basename(path)
    if not filename:
        return None
    return f"{GENERATED_FILES_ROUTE}/{filename}"


def _note_export_slug(note: "Note") -> str:
    user_fragment = (note.user_id or "user")[:8].replace("-", "")
    return f"note_{note.id}_{user_fragment}"


def _generate_pdf_assets(note: "Note", author: str, slug: str) -> Dict[str, Optional[str]]:
    if not (LATEX_AVAILABLE and PDF_COMPILER_AVAILABLE and latex_service and pdf_compiler):
        raise RuntimeError("PDF generation services unavailable")

    settings_schema = settings_to_schema(note.settings_json)
    title_override = note.latex_title or note.project_name or f"Note {note.id}"
    author_override = author
    if note.include_nickname:
        author_override = note.nickname or author or "Student"
    latex_content = latex_service.generate_latex_document(
        content=note.processed_content,
        title=title_override,
        author=author_override,
        style=settings_schema.latex_style,
        font=settings_schema.font_preference
    )

    pdf_path, tex_path, error = pdf_compiler.compile_to_pdf(
        latex_content=latex_content,
        output_filename=slug,
        save_tex=True
    )

    if error or not pdf_path:
        raise RuntimeError(error or "Unknown PDF compilation error")

    pdf_path_abs = absolute_export_path(pdf_path)
    tex_path_abs = absolute_export_path(tex_path) if tex_path else None
    note.pdf_path = pdf_path_abs
    note.tex_path = tex_path_abs

    return {
        "pdf_path": pdf_path_abs,
        "tex_path": tex_path_abs,
        "pdf_url": build_generated_file_url(pdf_path_abs),
    }


def ensure_note_exports(
    note: "Note",
    author_email: Optional[str] = None,
    force: bool = False,
    formats: Optional[List[str]] = None,
) -> Dict[str, Optional[str]]:
    """Ensure PDF/DOCX/TXT exports exist for the note."""

    if not note or not note.processed_content:
        return {}

    exports: Dict[str, Optional[str]] = {}
    slug = _note_export_slug(note)
    author = author_email or note.user_id or "Student"
    requested_formats = set(formats or ["pdf", "docx", "txt"])

    wants_pdf = "pdf" in requested_formats
    wants_docx = "docx" in requested_formats
    wants_txt = "txt" in requested_formats

    need_pdf = wants_pdf and (force or not export_file_exists(note.pdf_path))
    if need_pdf:
        try:
            pdf_result = _generate_pdf_assets(note, author, slug)
            exports.update(pdf_result)
        except Exception as e:
            print(f"PDF export failed for note {note.id}: {e}")

    if export_service:
        need_docx = wants_docx and (force or not export_file_exists(note.docx_path))
        if need_docx and DOCX_AVAILABLE:
            try:
                docx_path = export_service.generate_docx(
                    note.processed_content,
                    f"Note {note.id}",
                    slug
                )
                docx_abs = absolute_export_path(docx_path)
                note.docx_path = docx_abs
                exports["docx_url"] = build_generated_file_url(docx_abs)
            except Exception as e:
                print(f"DOCX export failed for note {note.id}: {e}")

        need_txt = wants_txt and (force or not export_file_exists(note.txt_path))
        if need_txt:
            try:
                txt_path = export_service.generate_txt(note.processed_content, slug)
                txt_abs = absolute_export_path(txt_path)
                note.txt_path = txt_abs
                exports["txt_url"] = build_generated_file_url(txt_abs)
            except Exception as e:
                print(f"TXT export failed for note {note.id}: {e}")

    return exports


def _get_drive_token(db: Session, user_id: str) -> Optional["GoogleDriveToken"]:
    if not DATABASE_AVAILABLE:
        return None
    return db.query(GoogleDriveToken).filter(GoogleDriveToken.user_id == user_id).first()


def _update_drive_token_from_credentials(token: "GoogleDriveToken", credentials: Any) -> None:
    token.access_token = getattr(credentials, "token", None)
    refresh_token = getattr(credentials, "refresh_token", None)
    if refresh_token:
        token.refresh_token = refresh_token
    token.token_expiry = getattr(credentials, "expiry", None)
    scopes = getattr(credentials, "scopes", None)
    if scopes:
        token.token_scope = " ".join(scopes)
    token.token_type = getattr(credentials, "token_type", "Bearer")

def ensure_processing_settings(settings_payload: Union[ProcessingSettings, ProcessingSettingsSchema, dict, str, None]) -> ProcessingSettings:
    """Normalize any incoming settings payload into a ProcessingSettings instance."""
    if isinstance(settings_payload, ProcessingSettings):
        return settings_payload
    if isinstance(settings_payload, ProcessingSettingsSchema):
        data = settings_payload.model_dump()
    elif isinstance(settings_payload, str):
        try:
            data = json.loads(settings_payload)
        except json.JSONDecodeError:
            data = {}
    elif isinstance(settings_payload, dict):
        data = settings_payload
    elif settings_payload is None:
        data = {}
    else:
        data = getattr(settings_payload, "__dict__", {})
    return ProcessingSettings(**data)

def settings_to_schema(settings_payload: Union[ProcessingSettings, ProcessingSettingsSchema, dict, str]) -> ProcessingSettingsSchema:
    if isinstance(settings_payload, ProcessingSettingsSchema):
        return settings_payload
    if isinstance(settings_payload, ProcessingSettings):
        return ProcessingSettingsSchema(**settings_payload.__dict__)
    if isinstance(settings_payload, str):
        return ProcessingSettingsSchema(**json.loads(settings_payload))
    if isinstance(settings_payload, dict):
        return ProcessingSettingsSchema(**settings_payload)
    raise ValueError("Unsupported settings payload")

def apply_note_metadata_from_settings(note: "Note", settings: ProcessingSettings) -> None:
    note.project_name = settings.project_name or note.project_name
    note.latex_title = settings.latex_title or note.latex_title
    note.include_nickname = bool(settings.include_nickname)
    if settings.nickname:
        note.nickname = settings.nickname

def serialize_flashcards(note: "Note") -> List[Dict[str, Any]]:
    flashcards: List[Dict[str, Any]] = []
    for entry in note.flashcards:
        flashcards.append({
            "id": entry.get("id") or str(uuid.uuid4()),
            "topic": entry.get("topic", ""),
            "term": entry.get("term", ""),
            "definition": entry.get("definition", ""),
            "source": entry.get("source", "ai"),
            "created_at": entry.get("created_at")
        })
    return flashcards

async def maybe_generate_flashcards_for_note(
    db: Session,
    note: "Note",
    text: Optional[str],
    settings: ProcessingSettings
) -> None:
    if not text or not text.strip():
        return
    if not settings.generate_flashcards:
        return
    if not CHATGPT_AVAILABLE or chatgpt_service is None:
        return

    topics = settings.flashcard_topics or settings.focus_topics or []
    topics = [topic.strip() for topic in topics if topic and topic.strip()]
    if not topics:
        return

    desired_count = settings.flashcard_count or len(topics)
    per_topic_min = max(
        1,
        getattr(settings, "min_flashcards_per_topic", None)
        or getattr(settings, "max_flashcards_per_topic", None)
        or 1
    )
    total_cards = max(len(topics) * per_topic_min, desired_count)
    total_cards = min(total_cards, 50)

    try:
        cards = await chatgpt_service.generate_flashcards(
            text=text,
            topics=topics,
            total_cards=total_cards,
            min_per_topic=per_topic_min
        )
    except Exception as e:
        print(f"Flashcard generation failed for note {note.id}: {e}")
        return

    if not cards:
        return

    timestamp = datetime.now(timezone.utc).isoformat()
    existing_manual = [
        card for card in note.flashcards
        if card.get("source") == "manual"
    ]
    ai_cards = [
        {
            "id": card.get("id") or str(uuid.uuid4()),
            "topic": card.get("topic", ""),
            "term": card.get("term", ""),
            "definition": card.get("definition", ""),
            "source": "ai",
            "created_at": timestamp
        }
        for card in cards
        if card.get("term") and card.get("definition")
    ]

    note.flashcards = existing_manual + ai_cards
    db.commit()
    db.refresh(note)

def note_to_response(note: "Note", progress_override: Optional[int] = None, progress_message: Optional[str] = None) -> NoteResponse:
    settings_schema = settings_to_schema(note.settings_json)
    stored_progress = getattr(note, "progress", None)
    if progress_override is not None:
        progress = progress_override
    elif stored_progress is not None:
        progress = stored_progress
    else:
        progress = 100 if note.status == ProcessingStatus.COMPLETED else 0
    stored_message = progress_message if progress_message is not None else getattr(note, "progress_message", None)
    folder = None
    if getattr(note, "folder", None):
        folder = {
            "id": note.folder.id,
            "name": note.folder.name
        }

    return NoteResponse(
        id=note.id,
        text=note.text,
        settings=settings_schema,
        processed_content=note.processed_content,
        status=note.status,
        progress=progress,
        progress_message=stored_message,
        image_url=note.image_url,
        image_filename=note.image_filename,
        image_type=note.image_type,
        input_type=note.input_type,
        pdf_url=build_generated_file_url(note.pdf_path),
        docx_url=build_generated_file_url(note.docx_path),
        txt_url=build_generated_file_url(note.txt_path),
        project_name=note.project_name,
        latex_title=note.latex_title,
        include_nickname=bool(note.include_nickname),
        nickname=note.nickname,
        flashcards=serialize_flashcards(note),
        folder=folder,
        created_at=note.created_at,
        updated_at=note.updated_at
    )

def _get_user_note(db: Session, note_id: int, user_id: str) -> "Note":
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

def update_note_progress(db: Session, note: "Note", progress: int, message: Optional[str] = None, status: Optional[ProcessingStatus] = None) -> None:
    """Persist progress updates for long-running tasks so the UI can render truthful progress."""
    if getattr(note, "status", None) == ProcessingStatus.CANCELLED and status is None:
        return
    capped_progress = max(0, min(100, progress))
    note.progress = capped_progress
    if message is not None:
        note.progress_message = message
    if status is not None:
        note.status = status
    db.commit()
    db.refresh(note)


def _refresh_note_and_check_cancelled(db: Session, note: "Note") -> bool:
    try:
        db.refresh(note)
    except Exception:
        return False
    if getattr(note, "status", None) == ProcessingStatus.CANCELLED:
        print(f"Cancellation detected for note {note.id}, aborting background work")
        return True
    return False


class TopicsFromTextRequest(BaseModel):
    text: str
    max_topics: Optional[int] = 6

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Verifies Firebase ID token and returns user data.
    Falls back to test user if Firebase is not available.
    """
    # If Firebase is not available, return a test user for development
    if not FIREBASE_AVAILABLE or auth is None:
        print("WARNING: Firebase not available - using test user")
        return {"uid": "test-user-id", "email": "test@example.com"}
    
    # If no token provided, return test user (for development)
    if not token:
        print("WARNING: No token provided - using test user")
        return {"uid": "test-user-id", "email": "test@example.com"}
    
    try:
        decoded_token = auth.verify_id_token(token)
        print(f"User authenticated - UID: {decoded_token.get('uid', 'No UID found')}")
        print(f"User email: {decoded_token.get('email', 'No email found')}")
        return decoded_token
    except Exception as e:
        print(f"Authentication failed: {str(e)} - using test user")
        # Instead of raising error, return test user for development
        return {"uid": "test-user-id", "email": "test@example.com"}
# ----------------------------------------------------

print("Creating FastAPI app...")
app = FastAPI(title="Note Embellisher API", version="1.0.0")
print("FastAPI app created successfully")

# Add CORS middleware
print("Adding CORS middleware...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://note-embellisher-2.web.app", 
                   "https://note-embellisher-2.firebaseapp.com",
                   "http://localhost:3000",
                   "http://localhost:3001", 
                   "http://localhost:5173",  # Vite dev server
                   "https://*.vercel.app",   # Vercel deployments
                   "*"],  # Allow all origins for Railway testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("CORS middleware configured")

# Mount static files directory for serving generated PDFs
print("Mounting static files for PDF serving...")
generated_pdfs_dir = os.path.join(os.path.dirname(__file__), "generated_pdfs")
os.makedirs(generated_pdfs_dir, exist_ok=True)
app.mount("/generated_pdfs", StaticFiles(directory=generated_pdfs_dir), name="generated_pdfs")
print(f"Static files mounted: {generated_pdfs_dir}")

print("API is ready to accept requests")
print("=" * 50)

@app.on_event("startup")
async def startup_event():
    """Initialize services after app startup to avoid blocking"""
    print("Running startup tasks...")
    
    # Initialize Firebase in background (non-blocking)
    # Only initialize if explicitly enabled or credentials are available
    if FIREBASE_SDK_AVAILABLE and firebase_init_module:
        try:
            print("Attempting Firebase initialization...")
            result = firebase_init_module.initialize_firebase()
            if result:
                print("Firebase initialized successfully")
            else:
                print("WARNING: Firebase initialization skipped (no credentials)")
        except Exception as e:
            print(f"WARNING: Firebase initialization failed (non-fatal): {e}")
            import traceback
            traceback.print_exc()
    else:
        print("INFO: Firebase module not available - skipping initialization")
    
    print("Startup tasks completed")

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Note Embellisher API",
        "services": {
            "database": DATABASE_AVAILABLE,
            "firebase": FIREBASE_AVAILABLE,
            "chatgpt": CHATGPT_AVAILABLE,
            "dropbox": DROPBOX_AVAILABLE,
            "ocr": OCR_AVAILABLE,
            "latex": LATEX_AVAILABLE,
            "pdf_compiler": PDF_COMPILER_AVAILABLE,
            "google_drive": GOOGLE_DRIVE_SERVICE_AVAILABLE,
            "exports": EXPORT_SERVICE_AVAILABLE
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-10-26"}


@app.get("/google-drive/status")
async def google_drive_status(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    token = _get_drive_token(db, user["uid"])
    return {
        "connected": bool(token and token.refresh_token),
        "expires_at": token.token_expiry if token else None,
        "has_refresh_token": bool(token and token.refresh_token)
    }


@app.get("/google-drive/auth-url")
async def google_drive_auth_url(
    user: dict = Depends(get_current_user)
):
    if not (GOOGLE_DRIVE_SERVICE_AVAILABLE and google_drive_service and google_drive_service.is_configured):
        raise HTTPException(status_code=503, detail="Google Drive integration is not configured")

    state = google_drive_service.generate_state()
    _remember_drive_state(state, user["uid"])
    auth_url, _ = google_drive_service.generate_auth_url(state)
    return {"auth_url": auth_url, "state": state}


@app.get("/google-drive/callback")
async def google_drive_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if not (GOOGLE_DRIVE_SERVICE_AVAILABLE and google_drive_service and google_drive_service.is_configured):
        return HTMLResponse("Google Drive integration is not available", status_code=503)

    if error:
        return HTMLResponse(f"Authorization failed: {error}", status_code=400)

    if not code or not state:
        return HTMLResponse("Missing authorization code or state", status_code=400)

    user_id = _consume_drive_state(state)
    if not user_id:
        return HTMLResponse("Authorization state expired. Please try again.", status_code=400)

    try:
        credentials = google_drive_service.exchange_code_for_credentials(code)
    except Exception as e:
        return HTMLResponse(f"Failed to exchange code: {e}", status_code=400)

    token = _get_drive_token(db, user_id)
    if not token:
        token = GoogleDriveToken(user_id=user_id)
        db.add(token)

    _update_drive_token_from_credentials(token, credentials)
    db.commit()

    success_redirect = getattr(google_drive_service, "success_redirect", None)
    if success_redirect:
        return RedirectResponse(f"{success_redirect}?connected=true", status_code=302)

    return HTMLResponse("Google Drive connected successfully. You can close this window.")

@app.get("/debug/all-notes")
async def debug_all_notes(db: Session = Depends(get_db)):
    """
    Debug endpoint to see all notes in database (no authentication)
    """
    if not DATABASE_AVAILABLE:
        return {"error": "Database not available"}
    
    notes = db.query(Note).all()
    return {
        "total_notes": len(notes),
        "notes": [
            {
                "id": note.id,
                "user_id": note.user_id,
                "text_preview": note.text[:50] if note.text else "No text",
                "status": note.status,
                "created_at": str(note.created_at)
            }
            for note in notes
        ]
    }

class TopicPreviewRequest(BaseModel):
    text: str

class TopicPreviewResponse(BaseModel):
    topics: List[str]

@app.post("/preview-topics", response_model=TopicPreviewResponse)
async def preview_topics(
    request: TopicPreviewRequest,
    user: dict = Depends(get_current_user)
):
    """
    Extract key topics from text content using AI
    """
    if not CHATGPT_AVAILABLE:
        raise HTTPException(status_code=503, detail="ChatGPT service not available")
    
    if not request.text or len(request.text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text must be at least 50 characters")
    
    try:
        print(f"Extracting topics from text ({len(request.text)} chars)")
        topics = await chatgpt_service.extract_topics_from_text(request.text, max_topics=6)
        print(f"Extracted {len(topics)} topics: {topics}")
        return TopicPreviewResponse(topics=topics)
    except Exception as e:
        print(f"Error extracting topics: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to extract topics: {str(e)}")

@app.post("/notes/", response_model=NoteResponse)
async def create_note(
    note: NoteCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)  # firebase-fix: Protect endpoint
):
    """
    Create a new note and start processing it in the background
    """
    # Create note in database
    processing_settings = ensure_processing_settings(note.settings)
    settings_dict = ProcessingSettingsSchema(**processing_settings.__dict__).model_dump()
    db_note = Note(
        user_id=user["uid"],  # firebase-fix: Link note to user
        text=note.text,
        settings_json=json.dumps(settings_dict),
        status=ProcessingStatus.PROCESSING,
        progress=0,
        progress_message="Queued for processing"
    )
    apply_note_metadata_from_settings(db_note, processing_settings)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    # Add background task to process the note
    background_tasks.add_task(process_note_background, db_note.id, processing_settings)
    
    # Return the created note
    return note_to_response(db_note, progress_override=0, progress_message="Queued for processing")

@app.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int, 
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)  # firebase-fix: Protect endpoint
):
    """
    Get a specific note by ID
    """
    # firebase-fix: Filter by user_id
    try:
        db_note = db.query(Note).filter(Note.id == note_id, Note.user_id == user["uid"]).first()
    except Exception as e:
        if "no such column" in str(e):
            try:
                from core.database import _ensure_note_columns
                _ensure_note_columns()
            except Exception:
                pass
            db_note = db.query(Note).filter(Note.id == note_id, Note.user_id == user["uid"]).first()
        else:
            raise
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return note_to_response(db_note)

@app.get("/notes/{note_id}/flashcards", response_model=FlashcardList)
async def get_note_flashcards(
    note_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    note = _get_user_note(db, note_id, user["uid"])
    return FlashcardList(flashcards=serialize_flashcards(note))

@app.post("/notes/{note_id}/flashcards", response_model=FlashcardList)
async def add_manual_flashcard(
    note_id: int,
    flashcard: FlashcardCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    note = _get_user_note(db, note_id, user["uid"])
    new_card = {
        "id": str(uuid.uuid4()),
        "topic": flashcard.topic.strip(),
        "term": flashcard.term.strip(),
        "definition": flashcard.definition.strip(),
        "source": "manual",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    cards = [card for card in note.flashcards]
    cards.append(new_card)
    note.flashcards = cards
    db.commit()
    db.refresh(note)
    return FlashcardList(flashcards=serialize_flashcards(note))

@app.put("/notes/{note_id}/flashcards/{card_id}", response_model=FlashcardList)
async def update_manual_flashcard(
    note_id: int,
    card_id: str,
    flashcard: FlashcardCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    note = _get_user_note(db, note_id, user["uid"])
    updated = False
    cards = []
    for card in note.flashcards:
        if card.get("id") == card_id:
            cards.append({
                "id": card_id,
                "topic": flashcard.topic.strip(),
                "term": flashcard.term.strip(),
                "definition": flashcard.definition.strip(),
                "source": card.get("source", "manual"),
                "created_at": card.get("created_at") or datetime.now(timezone.utc).isoformat()
            })
            updated = True
        else:
            cards.append(card)
    if not updated:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    note.flashcards = cards
    db.commit()
    db.refresh(note)
    return FlashcardList(flashcards=serialize_flashcards(note))

@app.delete("/notes/{note_id}/flashcards/{card_id}", response_model=FlashcardList)
async def delete_flashcard(
    note_id: int,
    card_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    note = _get_user_note(db, note_id, user["uid"])
    cards = [card for card in note.flashcards if card.get("id") != card_id]
    note.flashcards = cards
    db.commit()
    db.refresh(note)
    return FlashcardList(flashcards=serialize_flashcards(note))


@app.post("/notes/{note_id}/cancel", response_model=NoteResponse)
async def cancel_note_processing(
    note_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    note = _get_user_note(db, note_id, user["uid"])
    if note.status in {ProcessingStatus.COMPLETED, ProcessingStatus.CANCELLED}:
        raise HTTPException(status_code=400, detail="Note processing is already finished")
    if note.status == ProcessingStatus.ERROR:
        raise HTTPException(status_code=400, detail="Note failed previously and cannot be cancelled")

    note.status = ProcessingStatus.CANCELLED
    note.progress = 0
    note.progress_message = "Processing cancelled by user"
    db.commit()
    db.refresh(note)
    return note_to_response(note)

@app.get("/notes/", response_model=List[NoteResponse])
async def get_notes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)  # firebase-fix: Protect endpoint
):
    """
    Get all notes with pagination
    """
    # firebase-fix: Filter by user_id
    user_id = user["uid"]
    print(f"Fetching notes for user: {user_id}")
    try:
        notes = db.query(Note).filter(Note.user_id == user_id).offset(skip).limit(limit).all()
    except Exception as e:
        if "no such column" in str(e):
            try:
                from core.database import _ensure_note_columns
                _ensure_note_columns()
            except Exception:
                pass
            notes = db.query(Note).filter(Note.user_id == user_id).offset(skip).limit(limit).all()
        else:
            raise
    print(f"Found {len(notes)} notes for user {user_id}")
    
    return [note_to_response(note) for note in notes]

@app.get("/folders", response_model=List[FolderSchema])
async def list_folders(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    folders = db.query(Folder).filter(Folder.user_id == user["uid"]).order_by(Folder.created_at.desc()).all()
    return folders

@app.post("/folders", response_model=FolderSchema)
async def create_folder(
    folder: FolderCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    name = folder.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")
    new_folder = Folder(user_id=user["uid"], name=name)
    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)
    return new_folder

@app.put("/folders/{folder_id}", response_model=FolderSchema)
async def rename_folder(
    folder_id: int,
    folder: FolderUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    db_folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user["uid"]).first()
    if not db_folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    new_name = folder.name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")
    db_folder.name = new_name
    db.commit()
    db.refresh(db_folder)
    return db_folder

@app.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    db_folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user["uid"]).first()
    if not db_folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    # Detach notes from folder
    db.query(Note).filter(Note.folder_id == folder_id, Note.user_id == user["uid"]).update({"folder_id": None})
    db.delete(db_folder)
    db.commit()
    return {"success": True}

@app.delete("/notes/{note_id}")
async def delete_note(
    note_id: int, 
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)  # firebase-fix: Protect endpoint
):
    """
    Delete a specific note by ID
    """
    # firebase-fix: Filter by user_id
    db_note = db.query(Note).filter(Note.id == note_id, Note.user_id == user["uid"]).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Delete image from Dropbox if it exists
    if db_note.image_path:
        try:
            dropbox_service.delete_image(db_note.image_path)
        except Exception as e:
            print(f"Warning: Failed to delete image from Dropbox: {e}")
    
    db.delete(db_note)
    db.commit()
    
    return {"message": "Note deleted successfully"}

@app.patch("/notes/{note_id}/metadata", response_model=NoteResponse)
async def update_note_metadata(
    note_id: int,
    metadata: NoteMetadataUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    note = _get_user_note(db, note_id, user["uid"])
    payload = metadata.model_dump(exclude_unset=True)

    if "project_name" in payload:
        value = (payload["project_name"] or "").strip()
        note.project_name = value or None
    if "latex_title" in payload:
        value = (payload["latex_title"] or "").strip()
        note.latex_title = value or None
    if "include_nickname" in payload:
        note.include_nickname = bool(payload["include_nickname"])
    if "nickname" in payload:
        value = (payload["nickname"] or "").strip()
        note.nickname = value or None
    if "folder_id" in payload:
        folder_id = payload["folder_id"]
        if folder_id is None:
            note.folder_id = None
        else:
            folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user["uid"]).first()
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")
            note.folder_id = folder.id

    db.commit()
    db.refresh(note)
    return note_to_response(note)

@app.post("/upload-image/", response_model=NoteResponse)
async def upload_image_note(
    file: UploadFile = File(...),
    settings: str = Form(...),  # JSON string of ProcessingSettings
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Upload an image file, store it in Dropbox, and create a note with OCR processing
    """
    try:
        # Validate file type
        if not dropbox_service.validate_file_type(file.filename, file.content_type):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only PNG, JPG, JPEG, and PDF files are allowed."
            )
        
        # Check file size (limit to 10MB)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB in bytes
            raise HTTPException(status_code=400, detail="File size too large. Maximum size is 10MB.")
        
        # Parse settings
        try:
            settings_dict = json.loads(settings)
            processing_settings = ProcessingSettings(**settings_dict)
        except (json.JSONDecodeError, TypeError) as e:
            raise HTTPException(status_code=400, detail="Invalid settings format")
        
        # Upload image to Dropbox
        shareable_url, dropbox_path = dropbox_service.upload_image(
            file_content, file.filename, user["uid"]
        )
        
        # Determine file type
        file_extension = file.filename.lower().split('.')[-1]
        image_type = "pdf" if file_extension == "pdf" else "image"
        
        # Create note in database
        normalized_settings = ProcessingSettingsSchema(**processing_settings.__dict__).model_dump()
        db_note = Note(
            user_id=user["uid"],
            text=None,  # Will be populated after OCR
            settings_json=json.dumps(normalized_settings),
            status=ProcessingStatus.PROCESSING,
            progress=0,
            progress_message="Uploading media...",
            input_type="image",
            image_url=shareable_url,
            image_path=dropbox_path,  # Store Dropbox path
            image_filename=file.filename,
            image_type=image_type
        )
        apply_note_metadata_from_settings(db_note, processing_settings)
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        
        # Route PDFs through the OCR pipeline since GPT-4 Vision does not accept them
        if image_type == "pdf":
            background_tasks.add_task(
                process_image_note_background,
                db_note.id,
                dropbox_path,
                processing_settings
            )
        else:
            # Use GPT-4 Vision for better handwriting recognition on image inputs
            background_tasks.add_task(
                process_multiple_images_background,
                db_note.id,
                [shareable_url],  # Pass as a list with single image
                processing_settings
            )
        
        # Return the created note
        return note_to_response(db_note, progress_override=0, progress_message="Uploading media...")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@app.post("/upload-multiple-images/", response_model=NoteResponse)
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    settings: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Upload multiple images (up to 5), store in Dropbox, and process with GPT-4 Vision
    """
    try:
        # Validate number of files
        if len(files) < 1 or len(files) > 5:
            raise HTTPException(
                status_code=400,
                detail="Please upload between 1 and 5 images"
            )
        
        # Parse settings
        try:
            settings_dict = json.loads(settings)
            processing_settings = ProcessingSettings(**settings_dict)
        except (json.JSONDecodeError, TypeError) as e:
            raise HTTPException(status_code=400, detail="Invalid settings format")
        
        # Validate and upload all files
        image_urls = []
        image_paths = []
        filenames = []
        
        for idx, file in enumerate(files):
            # Validate file type
            if not dropbox_service.validate_file_type(file.filename, file.content_type):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {file.filename}. Only PNG, JPG, JPEG, and PDF files are allowed."
                )
            # GPT-4 Vision currently cannot consume PDFs. Require users to upload them individually
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension == ".pdf":
                raise HTTPException(
                    status_code=400,
                    detail=f"{file.filename} is a PDF. Please upload PDFs one at a time so we can run the OCR pipeline."
                )
            
            # Check file size (limit to 10MB per file)
            file_content = await file.read()
            if len(file_content) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is too large. Maximum size is 10MB per file."
                )
            
            # Upload to Dropbox
            shareable_url, dropbox_path = dropbox_service.upload_image(
                file_content, file.filename, user["uid"]
            )
            
            image_urls.append(shareable_url)
            image_paths.append(dropbox_path)
            filenames.append(file.filename)
        
        # Create note in database
        normalized_settings = ProcessingSettingsSchema(**processing_settings.__dict__).model_dump()
        db_note = Note(
            user_id=user["uid"],
            text=None,  # Will be populated after GPT-4 Vision processing
            settings_json=json.dumps(normalized_settings),
            status=ProcessingStatus.PROCESSING,
            progress=0,
            progress_message="Uploading images...",
            input_type="images",  # Note the plural
            image_url=image_urls[0],  # Store first image URL
            image_path=json.dumps(image_paths),  # Store all paths as JSON
            image_filename=", ".join(filenames),
            image_type="multiple_images"
        )
        apply_note_metadata_from_settings(db_note, processing_settings)
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        
        # Add background task to process images with GPT-4 Vision
        background_tasks.add_task(
            process_multiple_images_background,
            db_note.id,
            image_urls,
            processing_settings
        )
        
        # Return the created note
        return note_to_response(db_note, progress_override=0, progress_message="Uploading images...")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading multiple images: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upload images: {str(e)}")


@app.post("/preview/topics-from-text")
async def preview_topics_from_text(
    request: TopicsFromTextRequest,
    user: dict = Depends(get_current_user)
):
    if not CHATGPT_AVAILABLE or chatgpt_service is None:
        raise HTTPException(status_code=503, detail="ChatGPT service is not available")
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text content is required")
    max_topics = max(1, min(request.max_topics or 6, 10))
    try:
        suggestions = await chatgpt_service.extract_topics_from_text(request.text, max_topics)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract topics: {str(e)}")


@app.post("/preview/topics-from-images")
async def preview_topics_from_images(
    files: List[UploadFile] = File(...),
    max_topics: int = Form(6),
    user: dict = Depends(get_current_user)
):
    if not CHATGPT_AVAILABLE or chatgpt_service is None:
        raise HTTPException(status_code=503, detail="ChatGPT service is not available")
    if len(files) < 1 or len(files) > 5:
        raise HTTPException(status_code=400, detail="Please upload between 1 and 5 files")
    max_topics = max(1, min(max_topics, 10))

    image_buffers: List[bytes] = []
    image_names: List[str] = []
    aggregated_text_parts: List[str] = []

    for file in files:
        if not dropbox_service.validate_file_type(file.filename, file.content_type):
            raise HTTPException(status_code=400, detail=f"Invalid file type for {file.filename}")
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"{file.filename} exceeds 10MB limit")

        extension = os.path.splitext(file.filename)[1].lower()
        if extension == ".pdf" or file.content_type == "application/pdf":
            try:
                import fitz
                doc = fitz.open(stream=content, filetype="pdf")
                pdf_text = []
                for page in doc:
                    pdf_text.append(page.get_text())
                doc.close()
                aggregated_text_parts.append("\n".join(pdf_text))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to read PDF {file.filename}: {str(e)}")
        else:
            image_buffers.append(content)
            image_names.append(file.filename)

    suggestions: List[str] = []

    if aggregated_text_parts:
        text_blob = "\n".join(aggregated_text_parts)
        suggestions.extend(await chatgpt_service.extract_topics_from_text(text_blob, max_topics))

    if image_buffers:
        suggestions.extend(
            await chatgpt_service.extract_topics_from_images(image_buffers, image_names, max_topics)
        )

    # Deduplicate while preserving order
    unique_topics = []
    seen = set()
    for topic in suggestions:
        normalized = topic.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_topics.append(topic.strip())

    return {"suggestions": unique_topics[:max_topics]}

@app.post("/notes/{note_id}/generate-pdf")
async def generate_pdf(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a professional PDF from a note's processed content.
    OpenAI converts the content to LaTeX, then compiles to PDF.
    Works with any subject matter - math, science, humanities, etc.
    """
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    if not LATEX_AVAILABLE or not PDF_COMPILER_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="PDF generation services not available"
        )
    
    # Get the note
    db_note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user["uid"]
    ).first()
    
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if note has been processed
    if not db_note.processed_content:
        raise HTTPException(
            status_code=400, 
            detail="Note must be processed before generating PDF"
        )
    
    pdf_result: Dict[str, Optional[str]] = {}
    try:
        pdf_result = ensure_note_exports(
            db_note,
            author_email=current_user.get("email"),
            force=True,
            formats=["pdf"]
        )
        if pdf_result.get("pdf_path"):
            db_note.pdf_path = absolute_export_path(pdf_result["pdf_path"])
        if pdf_result.get("tex_path"):
            db_note.tex_path = absolute_export_path(pdf_result["tex_path"])
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error generating PDF for note {note_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

    tex_content_preview = None
    tex_path_abs = absolute_export_path(db_note.tex_path or pdf_result.get("tex_path"))
    if tex_path_abs and os.path.exists(tex_path_abs):
        try:
            with open(tex_path_abs, 'r', encoding='utf-8') as f:
                tex_full = f.read()
                tex_content_preview = {
                    "length": len(tex_full),
                    "first_500": tex_full[:500],
                    "last_500": tex_full[-500:],
                    "has_end_document": "\\end{document}" in tex_full
                }
        except Exception as e:
            print(f"Could not read .tex file for preview: {e}")

    return {
        "success": True,
        "note_id": note_id,
        "pdf_path": db_note.pdf_path or pdf_result.get("pdf_path"),
        "tex_path": db_note.tex_path or pdf_result.get("tex_path"),
        "pdf_url": pdf_result.get("pdf_url") or build_generated_file_url(db_note.pdf_path),
        "message": "PDF generated successfully",
        "tex_preview": tex_content_preview
    }


@app.post("/notes/{note_id}/generate-docx")
async def generate_docx(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    if not export_service:
        raise HTTPException(status_code=503, detail="Document export service unavailable")
    if not DOCX_AVAILABLE:
        raise HTTPException(status_code=503, detail="python-docx dependency missing")

    db_note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user["uid"]
    ).first()

    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not db_note.processed_content:
        raise HTTPException(status_code=400, detail="Note must be processed before exporting")

    try:
        ensure_note_exports(
            db_note,
            author_email=current_user.get("email"),
            force=True,
            formats=["docx"]
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate DOCX: {str(e)}")

    docx_url = build_generated_file_url(db_note.docx_path)
    if not docx_url:
        raise HTTPException(status_code=500, detail="DOCX file not available")

    return {
        "success": True,
        "note_id": note_id,
        "docx_path": db_note.docx_path,
        "docx_url": docx_url
    }


@app.post("/notes/{note_id}/generate-txt")
async def generate_txt(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    if not export_service:
        raise HTTPException(status_code=503, detail="Document export service unavailable")

    db_note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user["uid"]
    ).first()

    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not db_note.processed_content:
        raise HTTPException(status_code=400, detail="Note must be processed before exporting")

    try:
        ensure_note_exports(
            db_note,
            author_email=current_user.get("email"),
            force=True,
            formats=["txt"]
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate TXT: {str(e)}")

    txt_url = build_generated_file_url(db_note.txt_path)
    if not txt_url:
        raise HTTPException(status_code=500, detail="TXT file not available")

    return {
        "success": True,
        "note_id": note_id,
        "txt_path": db_note.txt_path,
        "txt_url": txt_url
    }


@app.post("/notes/{note_id}/upload-to-drive")
async def upload_note_to_drive(
    note_id: int,
    file_format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not (GOOGLE_DRIVE_SERVICE_AVAILABLE and google_drive_service and google_drive_service.is_configured):
        raise HTTPException(status_code=503, detail="Google Drive integration is not configured")
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    allowed_formats = {"pdf", "docx", "txt"}
    normalized_format = file_format.lower()
    if normalized_format not in allowed_formats:
        raise HTTPException(status_code=400, detail="Invalid file format")

    db_note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user["uid"]
    ).first()

    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not db_note.processed_content:
        raise HTTPException(status_code=400, detail="Note must be processed before uploading")

    try:
        ensure_note_exports(
            db_note,
            author_email=current_user.get("email"),
            force=False,
            formats=[normalized_format]
        )
        db.commit()
    except Exception as export_error:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to prepare file: {str(export_error)}")

    path_lookup = {
        "pdf": db_note.pdf_path,
        "docx": db_note.docx_path,
        "txt": db_note.txt_path
    }
    mime_lookup = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain"
    }

    local_path = absolute_export_path(path_lookup[normalized_format])
    if not local_path or not os.path.exists(local_path):
        raise HTTPException(status_code=500, detail="Exported file not found on server")

    token = _get_drive_token(db, current_user["uid"])
    if not token or not token.refresh_token:
        raise HTTPException(status_code=401, detail="Google Drive account not connected")

    credentials = google_drive_service.build_credentials_from_record(token)
    if not credentials:
        raise HTTPException(status_code=401, detail="Stored Google Drive credentials are invalid")

    try:
        upload_result = google_drive_service.upload_file(
            credentials,
            file_path=local_path,
            mime_type=mime_lookup[normalized_format],
            drive_filename=os.path.basename(local_path),
            description=f"Note Embellisher {normalized_format.upper()} export"
        )
    except Exception as upload_error:
        raise HTTPException(status_code=500, detail=f"Google Drive upload failed: {str(upload_error)}")

    # Persist any refreshed tokens
    _update_drive_token_from_credentials(token, credentials)
    db.commit()

    return {
        "success": True,
        "note_id": note_id,
        "format": normalized_format,
        "drive_file": upload_result
    }

# Thread pool for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)

def generate_pdf_sync_wrapper(note_id: int, current_user_email: Optional[str]) -> bool:
    """
    Synchronous wrapper for PDF generation (for thread pool)
    """
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        db_note = db.query(Note).filter(Note.id == note_id).first()
        if not db_note:
            return False
        
        pdf_exports = ensure_note_exports(
            db_note,
            author_email=current_user_email,
            force=True,
            formats=["pdf"]
        )
        
        if pdf_exports.get("pdf_path"):
            db_note.pdf_path = absolute_export_path(pdf_exports["pdf_path"])
        if pdf_exports.get("tex_path"):
            db_note.tex_path = absolute_export_path(pdf_exports["tex_path"])
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"PDF generation failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

async def process_note_background(note_id: int, settings):
    """
    Background task to process note with ChatGPT - now with synchronous PDF generation
    """
    from core.database import SessionLocal
    db = SessionLocal()
    db_note = None
    try:
        # Get the note from database
        db_note = db.query(Note).filter(Note.id == note_id).first()
        if not db_note:
            print(f"Note {note_id} not found")
            return
        
        # Convert settings to ProcessingSettings object
        processing_settings = ensure_processing_settings(settings)
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        update_note_progress(db, db_note, 5, "Starting note enhancement...")
        
        # Process with ChatGPT
        update_note_progress(db, db_note, 25, "Enhancing content with ChatGPT...")
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        processed_content = await chatgpt_service.process_text_with_chatgpt(
            db_note.text, 
            processing_settings
        )
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Update the note with processed content
        db_note.processed_content = processed_content
        db.commit()
        db.refresh(db_note)
        if _refresh_note_and_check_cancelled(db, db_note):
            return

        await maybe_generate_flashcards_for_note(
            db,
            db_note,
            processed_content,
            processing_settings
        )
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        update_note_progress(db, db_note, 50, "Converting to LaTeX format...")
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Generate PDF BEFORE marking as complete
        update_note_progress(db, db_note, 70, "Compiling LaTeX PDF...")
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Run PDF generation in thread pool (CPU-bound operation)
        loop = asyncio.get_event_loop()
        pdf_success = await loop.run_in_executor(
            executor,
            lambda: generate_pdf_sync_wrapper(db_note.id, None)
        )
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        if pdf_success:
            # Refresh note to get updated PDF paths
            db.refresh(db_note)
            final_message = "Completed"
        else:
            final_message = "Enhanced notes ready (PDF export unavailable)"
        
        # NOW mark as complete with PDF already generated
        update_note_progress(db, db_note, 100, final_message, ProcessingStatus.COMPLETED)
        print(f"Successfully processed note {note_id}")
        
    except Exception as e:
        # Update status to error
        print(f"Error processing note {note_id}: {str(e)}")
        if db_note and getattr(db_note, "status", None) != ProcessingStatus.CANCELLED:
            db_note.status = ProcessingStatus.ERROR
            db_note.progress_message = f"Processing failed: {e}"
            db_note.progress = 0
            db.commit()
    finally:
        db.close()

async def process_image_note_background(note_id: int, dropbox_path: str, settings):
    """
    Background task to process image note with OCR and ChatGPT
    """
    from core.database import SessionLocal
    db = SessionLocal()
    db_note = None
    try:
        # Get the note from database
        db_note = db.query(Note).filter(Note.id == note_id).first()
        if not db_note:
            print(f"Note {note_id} not found")
            return
        
        print(f"Starting OCR processing for note {note_id}")
        update_note_progress(db, db_note, 10, "Running OCR on uploaded files...")
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Extract text from image using OCR
        if not OCR_AVAILABLE or ocr_service is None:
            extracted_text = "[OCR service is not available in this deployment. Please process text manually.]"
        else:
            # Run OCR in thread pool
            loop = asyncio.get_event_loop()
            extracted_text = await loop.run_in_executor(
                executor,
                ocr_service.extract_text_from_image_url,
                dropbox_path
            )
            
            if not extracted_text.strip():
                raise Exception("No text could be extracted from the image")
            
            # Check if OCR failed and returned a fallback message
            if "[OCR Processing Required]" in extracted_text:
                raise Exception("OCR processing failed: Tesseract OCR is not installed or not available")
        
        # Update note with extracted text
        db_note.text = extracted_text
        db.commit()
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        update_note_progress(db, db_note, 45, "Enhancing extracted notes with GPT-4...")
        
        print(f"OCR completed for note {note_id}, extracted text length: {len(extracted_text)}")
        
        # Convert settings to ProcessingSettings object
        processing_settings = ensure_processing_settings(settings)
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Process with ChatGPT
        processed_content = await chatgpt_service.process_text_with_chatgpt(
            extracted_text, 
            processing_settings
        )
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Update the note with processed content
        db_note.processed_content = processed_content
        db.commit()
        db.refresh(db_note)
        if _refresh_note_and_check_cancelled(db, db_note):
            return

        await maybe_generate_flashcards_for_note(
            db,
            db_note,
            processed_content,
            processing_settings
        )
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        update_note_progress(db, db_note, 65, "Converting to LaTeX format...")
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Generate PDF BEFORE marking as complete
        update_note_progress(db, db_note, 80, "Compiling LaTeX PDF...")
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        loop = asyncio.get_event_loop()
        pdf_success = await loop.run_in_executor(
            executor,
            lambda: generate_pdf_sync_wrapper(db_note.id, None)
        )
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        if pdf_success:
            db.refresh(db_note)
            final_message = "Completed"
        else:
            final_message = "Enhanced notes ready (PDF export unavailable)"
            
        update_note_progress(db, db_note, 100, final_message, ProcessingStatus.COMPLETED)
        print(f"Successfully processed image note {note_id}")
        
    except Exception as e:
        # Update status to error and provide detailed error message
        error_message = str(e)
        print(f"Error processing image note {note_id}: {error_message}")
        if db_note and getattr(db_note, "status", None) != ProcessingStatus.CANCELLED:
            db_note.status = ProcessingStatus.ERROR
            db_note.progress = 0
            db_note.progress_message = f"Processing failed: {error_message}"
            # Store the error message in processed_content so frontend can display it
            db_note.processed_content = f"Processing failed: {error_message}"
            # Also ensure text field has content to prevent null issues
            if not db_note.text:
                db_note.text = "[Image processing failed - no text extracted]"
            db.commit()
    finally:
        db.close()

async def process_multiple_images_background(note_id: int, image_urls: List[str], settings):
    """
    Background task to process multiple images with GPT-4 Vision
    """
    from core.database import SessionLocal
    db = SessionLocal()
    db_note = None
    try:
        # Get the note from database
        db_note = db.query(Note).filter(Note.id == note_id).first()
        if not db_note:
            print(f"Note {note_id} not found")
            return

        if db_note.image_type == "pdf":
            print(f"Note {note_id} is a PDF. Delegating to OCR pipeline instead of GPT-4 Vision.")
            return await process_image_note_background(
                note_id,
                db_note.image_path,
                settings
            )
        
        print(f"Starting GPT-4 Vision processing for note {note_id} with {len(image_urls)} images")
        update_note_progress(db, db_note, 10, "Preparing images for GPT-4 Vision...")
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Check if ChatGPT service is available
        if not CHATGPT_AVAILABLE or chatgpt_service is None:
            raise Exception("ChatGPT service is not available in this deployment")
        
        # Convert settings to ProcessingSettings object
        processing_settings = ensure_processing_settings(settings)
        update_note_progress(db, db_note, 35, "Analyzing handwriting with GPT-4 Vision...")
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Get the actual Dropbox paths from the note
        # For single images, image_path is a string. For multiple, it's JSON array
        try:
            dropbox_paths = json.loads(db_note.image_path) if db_note.image_type == "multiple_images" else [db_note.image_path]
        except:
            dropbox_paths = [db_note.image_path]
        
        print(f"Dropbox paths: {dropbox_paths}")
        
        # Process images with GPT-4 Vision, passing Dropbox paths instead of URLs
        processed_content = await chatgpt_service.process_images_with_gpt4_vision(
            dropbox_paths,
            processing_settings,
            use_dropbox_path=True  # Flag to indicate these are Dropbox paths
        )
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        print(f"GPT-4 Vision processing completed for note {note_id}")
        update_note_progress(db, db_note, 60, "Converting to LaTeX format...")
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Update the note with processed content
        # For multi-image notes, we store the enhanced content directly
        db_note.text = f"Processed {len(image_urls)} images with GPT-4 Vision"
        db_note.processed_content = processed_content
        db.commit()
        db.refresh(db_note)
        if _refresh_note_and_check_cancelled(db, db_note):
            return

        await maybe_generate_flashcards_for_note(
            db,
            db_note,
            processed_content,
            processing_settings
        )
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        # Generate PDF BEFORE marking as complete
        update_note_progress(db, db_note, 80, "Compiling LaTeX PDF...")
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        loop = asyncio.get_event_loop()
        pdf_success = await loop.run_in_executor(
            executor,
            lambda: generate_pdf_sync_wrapper(db_note.id, None)
        )
        if _refresh_note_and_check_cancelled(db, db_note):
            return
        
        if pdf_success:
            db.refresh(db_note)
            final_message = "Completed"
        else:
            final_message = "Enhanced notes ready (PDF export unavailable)"
            
        update_note_progress(db, db_note, 100, final_message, ProcessingStatus.COMPLETED)
        print(f"Successfully processed multiple images for note {note_id}")
        
    except Exception as e:
        # Update status to error and provide detailed error message
        error_message = str(e)
        print(f"Error processing multiple images for note {note_id}: {error_message}")
        import traceback
        traceback.print_exc()
        
        if db_note and getattr(db_note, "status", None) != ProcessingStatus.CANCELLED:
            db_note.status = ProcessingStatus.ERROR
            db_note.progress = 0
            db_note.progress_message = f"Processing failed: {error_message}"
            db_note.processed_content = f"Processing failed: {error_message}"
            if not db_note.text:
                db_note.text = "[Multiple image processing failed]"
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get PORT from environment variable (for Railway/Render)
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on host=0.0.0.0 port={port}")
    
    # Bind to 0.0.0.0 to accept external connections
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
