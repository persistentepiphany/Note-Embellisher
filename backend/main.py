from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from fastapi.security import OAuth2PasswordBearer
import sys
import os

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
    from core.database import get_db, Note
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Database not available: {e}")
    DATABASE_AVAILABLE = False

try:
    from core.schemas import NoteCreate, NoteResponse, NoteUpdate, ProcessingStatus, ProcessingSettingsSchema
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
            "pdf_compiler": PDF_COMPILER_AVAILABLE
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-10-26"}

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
    print(f"Fetching notes for user: {user_id}")
    notes = db.query(Note).filter(Note.user_id == user_id).offset(skip).limit(limit).all()
    print(f"Found {len(notes)} notes for user {user_id}")
    
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
        db_note = Note(
            user_id=user["uid"],
            text=None,  # Will be populated after GPT-4 Vision processing
            settings_json=json.dumps({
                "add_bullet_points": processing_settings.add_bullet_points,
                "add_headers": processing_settings.add_headers,
                "expand": processing_settings.expand,
                "summarize": processing_settings.summarize
            }),
            status=ProcessingStatus.PROCESSING,
            input_type="images",  # Note the plural
            image_url=image_urls[0],  # Store first image URL
            image_path=json.dumps(image_paths),  # Store all paths as JSON
            image_filename=", ".join(filenames),
            image_type="multiple_images"
        )
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
        print(f"Error uploading multiple images: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upload images: {str(e)}")

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
    
    try:
        # Simple metadata
        title = f"Note {note_id}"
        author = current_user.get("email", "Student")
        
        # Use the processed content (already enhanced by ChatGPT)
        content = db_note.processed_content
        
        print(f"Generating LaTeX document for note {note_id}")
        print(f"Content length to convert: {len(content)} characters")
        
        # Let OpenAI handle ALL formatting - it will determine subject, structure, math, etc.
        latex_content = latex_service.generate_latex_document(
            content=content,
            title=title,
            author=author
        )
        
        print(f"LaTeX generation complete. Length: {len(latex_content)} characters")
        print(f"Compiling PDF for note {note_id}")
        
        # Compile to PDF
        pdf_path, tex_path, error = pdf_compiler.compile_to_pdf(
            latex_content=latex_content,
            output_filename=f"note_{note_id}_{current_user['uid'][:8]}",
            save_tex=True
        )
        
        if error or not pdf_path:
            raise HTTPException(
                status_code=500,
                detail=f"PDF compilation failed: {error}"
            )
        
        print(f"PDF generated successfully: {pdf_path}")
        
        # Read the .tex file to include in response for debugging
        tex_content_preview = None
        if tex_path and os.path.exists(tex_path):
            try:
                with open(tex_path, 'r', encoding='utf-8') as f:
                    tex_full = f.read()
                    tex_content_preview = {
                        "length": len(tex_full),
                        "first_500": tex_full[:500],
                        "last_500": tex_full[-500:],
                        "has_end_document": "\\end{document}" in tex_full
                    }
            except Exception as e:
                print(f"Could not read .tex file for preview: {e}")
        
        # Return PDF information
        return {
            "success": True,
            "note_id": note_id,
            "pdf_path": pdf_path,
            "tex_path": tex_path,
            "pdf_url": pdf_compiler.get_pdf_url(pdf_path),
            "message": "PDF generated successfully",
            "tex_preview": tex_content_preview  # For debugging
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating PDF for note {note_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )

async def process_note_background(note_id: int, settings):
    """
    Background task to process note with ChatGPT
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
        
        # Check if ChatGPT service is available
        if not CHATGPT_AVAILABLE or chatgpt_service is None:
            raise Exception("ChatGPT service is not available in this deployment")
        
        # Convert settings to ProcessingSettings object
        processing_settings = ProcessingSettings(
            add_bullet_points=settings.add_bullet_points,
            add_headers=settings.add_headers,
            expand=settings.expand,
            summarize=settings.summarize
        )
        
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
        
        print(f"GPT-4 Vision processing completed for note {note_id}")
        
        # Update the note with processed content
        # For multi-image notes, we store the enhanced content directly
        db_note.text = f"Processed {len(image_urls)} images with GPT-4 Vision"
        db_note.processed_content = processed_content
        db_note.status = ProcessingStatus.COMPLETED
        db.commit()
        print(f"Successfully processed multiple images for note {note_id}")
        
    except Exception as e:
        # Update status to error and provide detailed error message
        error_message = str(e)
        print(f"Error processing multiple images for note {note_id}: {error_message}")
        import traceback
        traceback.print_exc()
        
        if db_note:
            db_note.status = ProcessingStatus.ERROR
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