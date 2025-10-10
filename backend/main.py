from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import json

from database import get_db, Note
from schemas import NoteCreate, NoteResponse, NoteUpdate, ProcessingStatus
from chatgpt_service import chatgpt_service, ProcessingSettings
import firebasesdk  # Initialize Firebase

app = FastAPI(title="Note Embellisher API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Note Embellisher API"}

@app.post("/notes/", response_model=NoteResponse)
async def create_note(
    note: NoteCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new note and start processing it in the background
    """
    # Create note in database
    db_note = Note(
        text=note.text,
        settings_json=json.dumps(note.settings.dict()),
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
        created_at=db_note.created_at,
        updated_at=db_note.updated_at
    )

@app.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, db: Session = Depends(get_db)):
    """
    Get a specific note by ID
    """
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return NoteResponse(
        id=db_note.id,
        text=db_note.text,
        settings=json.loads(db_note.settings_json),
        processed_content=db_note.processed_content,
        status=db_note.status,
        created_at=db_note.created_at,
        updated_at=db_note.updated_at
    )

@app.get("/notes/", response_model=List[NoteResponse])
async def get_notes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all notes with pagination
    """
    notes = db.query(Note).offset(skip).limit(limit).all()
    
    return [
        NoteResponse(
            id=note.id,
            text=note.text,
            settings=json.loads(note.settings_json),
            processed_content=note.processed_content,
            status=note.status,
            created_at=note.created_at,
            updated_at=note.updated_at
        )
        for note in notes
    ]

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific note by ID
    """
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(db_note)
    db.commit()
    
    return {"message": "Note deleted successfully"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)