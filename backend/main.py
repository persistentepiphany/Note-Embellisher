from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from fastapi.security import OAuth2PasswordBearer

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
    from database import get_db, Note
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Database not available: {e}")
    DATABASE_AVAILABLE = False

try:
    from schemas import NoteCreate, NoteResponse, NoteUpdate, ProcessingStatus, ProcessingSettingsSchema
    SCHEMAS_AVAILABLE = True
except ImportError as e:
    print(f"Schemas not available: {e}")
    SCHEMAS_AVAILABLE = False

try:
    from chatgpt_service import chatgpt_service, ProcessingSettings
    CHATGPT_AVAILABLE = True
except ImportError as e:
    print(f"ChatGPT service not available: {e}")
    CHATGPT_AVAILABLE = False

try:
    from dropbox_service import dropbox_service
    DROPBOX_AVAILABLE = True
except ImportError as e:
    print(f"Dropbox service not available: {e}")
    DROPBOX_AVAILABLE = False

# Optional OCR service - disable if not available
try:
    from ocr_service import ocr_service
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"OCR service not available: {e}")
    OCR_AVAILABLE = False
    ocr_service = None

# Optional Firebase SDK
try:
    import firebasesdk  # Initialize Firebase
    FIREBASE_SDK_AVAILABLE = True
except ImportError as e:
    print(f"Firebase SDK not available: {e}")
    FIREBASE_SDK_AVAILABLE = False

# ----- firebase-fix: Add authentication dependency -----
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Verifies Firebase ID token and returns user data.
    """
    try:
        decoded_token = auth.verify_id_token(token)
        print(f"🔐 User authenticated - UID: {decoded_token.get('uid', 'No UID found')}")
        print(f"🔐 User email: {decoded_token.get('email', 'No email found')}")
        return decoded_token
    except auth.InvalidIdTokenError:
        print("❌ Authentication failed: Invalid ID token")
        raise HTTPException(status_code=401, detail="Invalid ID token")
    except auth.ExpiredIdTokenError:
        print("❌ Authentication failed: Expired ID token")
        raise HTTPException(status_code=401, detail="Expired ID token")
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")
# ----------------------------------------------------

app = FastAPI(title="Note Embellisher API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://note-embellisher-2.web.app", 
                   "https://note-embellisher-2.firebaseapp.com",
                   "http://localhost:3000",
                   "http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Note Embellisher API"}

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
    db_note = Note(
        user_id=user["uid"],  # firebase-fix: Link note to user
        text=note.text,
        settings_json=json.dumps({
            "add_bullet_points": note.settings.add_bullet_points,
            "add_headers": note.settings.add_headers,
            "expand": note.settings.expand,
            "summarize": note.settings.summarize
        }),
        status=ProcessingStatus.PROCESSING
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    # Add background task to process the note
    background_tasks.add_task(process_note_background, db_note.id, note.settings)
    
    # Return the created note
    return NoteResponse(
        id=db_note.id,
        text=db_note.text,
        settings=note.settings,
        processed_content=db_note.processed_content,
        status=db_note.status,
        image_url=db_note.image_url,
        image_filename=db_note.image_filename,
        image_type=db_note.image_type,
        input_type=db_note.input_type,
        created_at=db_note.created_at,
        updated_at=db_note.updated_at
    )

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
    db_note = db.query(Note).filter(Note.id == note_id, Note.user_id == user["uid"]).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return NoteResponse(
        id=db_note.id,
        text=db_note.text,
        settings=json.loads(db_note.settings_json),
        processed_content=db_note.processed_content,
        status=db_note.status,
        image_url=db_note.image_url,
        image_filename=db_note.image_filename,
        image_type=db_note.image_type,
        input_type=db_note.input_type,
        created_at=db_note.created_at,
        updated_at=db_note.updated_at
    )

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
    print(f"📋 Fetching notes for user: {user_id}")
    notes = db.query(Note).filter(Note.user_id == user_id).offset(skip).limit(limit).all()
    print(f"📋 Found {len(notes)} notes for user {user_id}")
    
    return [
        NoteResponse(
            id=note.id,
            text=note.text,
            settings=json.loads(note.settings_json),
            processed_content=note.processed_content,
            status=note.status,
            image_url=note.image_url,
            image_filename=note.image_filename,
            image_type=note.image_type,
            input_type=note.input_type,
            created_at=note.created_at,
            updated_at=note.updated_at
        )
        for note in notes
    ]

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
        db_note = Note(
            user_id=user["uid"],
            text=None,  # Will be populated after OCR
            settings_json=json.dumps({
                "add_bullet_points": processing_settings.add_bullet_points,
                "add_headers": processing_settings.add_headers,
                "expand": processing_settings.expand,
                "summarize": processing_settings.summarize
            }),
            status=ProcessingStatus.PROCESSING,
            input_type="image",
            image_url=shareable_url,
            image_path=dropbox_path,  # Store Dropbox path
            image_filename=file.filename,
            image_type=image_type
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        
        # Add background task to process the image with OCR
        background_tasks.add_task(
            process_image_note_background, 
            db_note.id, 
            dropbox_path, 
            processing_settings
        )
        
        # Return the created note
        return NoteResponse(
            id=db_note.id,
            text=db_note.text,
            settings=ProcessingSettingsSchema(
                add_bullet_points=processing_settings.add_bullet_points,
                add_headers=processing_settings.add_headers,
                expand=processing_settings.expand,
                summarize=processing_settings.summarize
            ),
            processed_content=db_note.processed_content,
            status=db_note.status,
            image_url=db_note.image_url,
            image_filename=db_note.image_filename,
            image_type=db_note.image_type,
            input_type=db_note.input_type,
            created_at=db_note.created_at,
            updated_at=db_note.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

async def process_note_background(note_id: int, settings):
    """
    Background task to process note with ChatGPT
    """
    from database import SessionLocal
    db = SessionLocal()
    db_note = None
    try:
        # Get the note from database
        db_note = db.query(Note).filter(Note.id == note_id).first()
        if not db_note:
            print(f"Note {note_id} not found")
            return
        
        # Convert settings to ProcessingSettings object
        processing_settings = ProcessingSettings(
            add_bullet_points=settings.add_bullet_points,
            add_headers=settings.add_headers,
            expand=settings.expand,
            summarize=settings.summarize
        )
        
        # Process with ChatGPT
        processed_content = await chatgpt_service.process_text_with_chatgpt(
            db_note.text, 
            processing_settings
        )
        
        # Update the note with processed content
        db_note.processed_content = processed_content
        db_note.status = ProcessingStatus.COMPLETED
        db.commit()
        print(f"Successfully processed note {note_id}")
        
    except Exception as e:
        # Update status to error
        print(f"Error processing note {note_id}: {str(e)}")
        if db_note:
            db_note.status = ProcessingStatus.ERROR
            db.commit()
    finally:
        db.close()

async def process_image_note_background(note_id: int, dropbox_path: str, settings):
    """
    Background task to process image note with OCR and ChatGPT
    """
    from database import SessionLocal
    db = SessionLocal()
    db_note = None
    try:
        # Get the note from database
        db_note = db.query(Note).filter(Note.id == note_id).first()
        if not db_note:
            print(f"Note {note_id} not found")
            return
        
        print(f"Starting OCR processing for note {note_id}")
        
        # Extract text from image using OCR
        if not OCR_AVAILABLE or ocr_service is None:
            extracted_text = "[OCR service is not available in this deployment. Please process text manually.]"
        else:
            extracted_text = ocr_service.extract_text_from_image_url(dropbox_path)
            
            if not extracted_text.strip():
                raise Exception("No text could be extracted from the image")
            
            # Check if OCR failed and returned a fallback message
            if "[OCR Processing Required]" in extracted_text:
                raise Exception("OCR processing failed: Tesseract OCR is not installed or not available")
        
        # Update note with extracted text
        db_note.text = extracted_text
        db.commit()
        
        print(f"OCR completed for note {note_id}, extracted text length: {len(extracted_text)}")
        
        # Convert settings to ProcessingSettings object
        processing_settings = ProcessingSettings(
            add_bullet_points=settings.add_bullet_points,
            add_headers=settings.add_headers,
            expand=settings.expand,
            summarize=settings.summarize
        )
        

        
        # Process with ChatGPT
        processed_content = await chatgpt_service.process_text_with_chatgpt(
            extracted_text, 
            processing_settings
        )
        
        # Update the note with processed content
        db_note.processed_content = processed_content
        db_note.status = ProcessingStatus.COMPLETED
        db.commit()
        print(f"Successfully processed image note {note_id}")
        
    except Exception as e:
        # Update status to error and provide detailed error message
        error_message = str(e)
        print(f"Error processing image note {note_id}: {error_message}")
        if db_note:
            db_note.status = ProcessingStatus.ERROR
            # Store the error message in processed_content so frontend can display it
            db_note.processed_content = f"❌ Processing failed: {error_message}"
            # Also ensure text field has content to prevent null issues
            if not db_note.text:
                db_note.text = "[Image processing failed - no text extracted]"
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)