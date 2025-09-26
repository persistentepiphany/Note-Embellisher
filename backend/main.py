from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Firebase configuration
try:
    import admin_config
    logger.info("Firebase admin config loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Firebase admin config: {e}")
    raise

from auth_middleware import CurrentUser
from firestore_service import firestore_service
from schemas import NoteCreate, NoteResponse, NoteUpdate, ProcessingStatus
from chatgpt_service import chatgpt_service, ProcessingSettings

app = FastAPI(title="Note Embellisher API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],  # Specific origins for development
    allow_credentials=True,  # Allow credentials for authentication
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

logger.info("FastAPI app initialized with CORS middleware")

@app.get("/")
async def root():
    return {"message": "Note Embellisher API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify services are working"""
    try:
        # Test ChatGPT service
        from chatgpt_service import ProcessingSettings
        settings = ProcessingSettings(add_bullet_points=True)
        test_result = await chatgpt_service.process_text_with_chatgpt("Test text", settings)
        
        return {
            "status": "success",
            "chatgpt_working": bool(test_result),
            "firebase_initialized": True,
            "message": "All services operational"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "firebase_initialized": True,
            "chatgpt_working": False
        }

@app.get("/auth-test")
async def auth_test_endpoint(current_user: CurrentUser = Depends()):
    """Test endpoint to verify authentication is working"""
    try:
        return {
            "status": "success",
            "message": "Authentication working",
            "user_id": current_user.uid,
            "user_email": current_user.email
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Authentication failed"
        }

@app.post("/notes/", response_model=NoteResponse)
async def create_note(
    note: NoteCreate, 
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends()
):
    """
    Create a new note and start processing it in the background
    """
    try:
        # Create note in Firestore
        note_id = await firestore_service.create_note(
            user_id=current_user.uid,
            text=note.text,
            settings=note.settings.dict()
        )
        
        # Add background task to process the note
        background_tasks.add_task(process_note_background, note_id, current_user.uid, note.settings)
        
        # Return the created note
        return NoteResponse(
            id=note_id,
            text=note.text,
            settings=note.settings,
            processed_content=None,
            status=ProcessingStatus.PROCESSING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logging.error(f"Error creating note: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create note")

@app.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str, current_user: CurrentUser = Depends()):
    """
    Get a specific note by ID
    """
    try:
        note_data = await firestore_service.get_note(note_id, current_user.uid)
        if not note_data:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return NoteResponse(
            id=note_data['id'],
            text=note_data['text'],
            settings=note_data['settings'],
            processed_content=note_data.get('processed_content'),
            status=note_data['status'],
            created_at=note_data['created_at'] or datetime.utcnow(),
            updated_at=note_data.get('updated_at') or datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get note")

@app.get("/notes/", response_model=List[NoteResponse])
async def get_notes(limit: int = 100, current_user: CurrentUser = Depends()):
    """
    Get all notes for the authenticated user
    """
    try:
        logging.info(f"Getting notes for user {current_user.uid}")
        notes_data = await firestore_service.get_user_notes(current_user.uid, limit)
        logging.info(f"Retrieved {len(notes_data)} notes for user {current_user.uid}")
        
        response_notes = []
        for note in notes_data:
            try:
                # Ensure settings is properly formatted
                settings = note.get('settings', {})
                if not isinstance(settings, dict):
                    settings = {
                        'add_bullet_points': False,
                        'add_headers': False,
                        'expand': False,
                        'summarize': False
                    }
                
                # Ensure required fields exist
                response_note = NoteResponse(
                    id=note['id'],
                    text=note.get('text', ''),
                    settings=settings,
                    processed_content=note.get('processed_content'),
                    status=note.get('status', 'pending'),
                    created_at=note.get('created_at') or datetime.utcnow(),
                    updated_at=note.get('updated_at') or datetime.utcnow()
                )
                response_notes.append(response_note)
            except Exception as note_error:
                logging.error(f"Error processing note {note.get('id', 'unknown')}: {str(note_error)}")
                continue
        
        logging.info(f"Successfully processed {len(response_notes)} notes for response")
        return response_notes
        
    except Exception as e:
        logging.error(f"Error getting notes for user {current_user.uid}: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        # Return empty list instead of raising exception to prevent frontend crashes
        return []

@app.delete("/notes/{note_id}")
async def delete_note(note_id: str, current_user: CurrentUser = Depends()):
    """
    Delete a specific note by ID
    """
    try:
        success = await firestore_service.delete_note(note_id, current_user.uid)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {"message": "Note deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete note")

async def process_note_background(note_id: str, user_id: str, settings):
    """
    Background task to process note with ChatGPT
    """
    try:
        logging.info(f"Starting background processing for note {note_id}, user {user_id}")
        
        # Get the note from Firestore
        note_data = await firestore_service.get_note(note_id, user_id)
        if not note_data:
            logging.error(f"Note {note_id} not found for user {user_id}")
            return
        
        # Convert settings to ProcessingSettings object
        if hasattr(settings, 'add_bullet_points'):
            # It's already a ProcessingSettingsSchema object
            processing_settings = ProcessingSettings(
                add_bullet_points=settings.add_bullet_points,
                add_headers=settings.add_headers,
                expand=settings.expand,
                summarize=settings.summarize
            )
        else:
            # It's a dict
            processing_settings = ProcessingSettings(
                add_bullet_points=settings.get('add_bullet_points', False),
                add_headers=settings.get('add_headers', False),
                expand=settings.get('expand', False),
                summarize=settings.get('summarize', False)
            )
        
        logging.info(f"Processing settings: {processing_settings.__dict__}")
        
        # Process with ChatGPT
        logging.info(f"Calling ChatGPT service for note {note_id}")
        processed_content = await chatgpt_service.process_text_with_chatgpt(
            note_data['text'], 
            processing_settings
        )
        
        if not processed_content:
            # Fallback to original text if processing fails
            logging.warning(f"ChatGPT service returned empty content for note {note_id}, using original text")
            processed_content = note_data['text']
        
        # Update the note with processed content
        logging.info(f"Updating note {note_id} with processed content")
        await firestore_service.update_note(
            note_id, 
            user_id, 
            {
                'processed_content': processed_content,
                'status': ProcessingStatus.COMPLETED.value,
                'updated_at': datetime.utcnow()
            }
        )
        logging.info(f"Successfully processed note {note_id} for user {user_id}")
        
    except Exception as e:
        # Update status to error but provide fallback content
        logging.error(f"Error processing note {note_id}: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        
        try:
            # Get original text as fallback
            note_data = await firestore_service.get_note(note_id, user_id)
            fallback_content = note_data.get('text', 'Error: Could not retrieve original content') if note_data else 'Error: Note not found'
            
            await firestore_service.update_note(
                note_id, 
                user_id, 
                {
                    'processed_content': f"Processing failed. Original content:\n\n{fallback_content}",
                    'status': ProcessingStatus.COMPLETED.value,  # Mark as completed with fallback
                    'error': str(e),
                    'updated_at': datetime.utcnow()
                }
            )
            logging.info(f"Updated note {note_id} with fallback content due to processing error")
        except Exception as update_error:
            logging.error(f"Failed to update note {note_id} with error status: {str(update_error)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)