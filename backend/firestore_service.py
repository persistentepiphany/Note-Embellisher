from firebase_admin import firestore
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from schemas import ProcessingStatus

logger = logging.getLogger(__name__)

class FirestoreService:
    def __init__(self):
        self.db = firestore.client()
        self.notes_collection = 'notes'
    
    async def create_note(self, user_id: str, text: str, settings: Dict[str, Any]) -> str:
        """
        Create a new note in Firestore
        Returns the document ID
        """
        try:
            note_data = {
                'user_id': user_id,
                'text': text,
                'settings': settings,
                'processed_content': None,
                'status': ProcessingStatus.PROCESSING.value,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection(self.notes_collection).document()
            doc_ref.set(note_data)
            
            logger.info(f"Created note {doc_ref.id} for user {user_id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            raise e
    
    async def get_note(self, note_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific note by ID for a specific user
        """
        try:
            doc_ref = self.db.collection(self.notes_collection).document(note_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            note_data = doc.to_dict()
            
            # Check if the note belongs to the requesting user
            if note_data.get('user_id') != user_id:
                logger.warning(f"User {user_id} attempted to access note {note_id} owned by {note_data.get('user_id')}")
                return None
            
            # Add the document ID to the data
            note_data['id'] = doc.id
            
            # Convert Firestore timestamps to datetime objects
            if note_data.get('created_at'):
                note_data['created_at'] = note_data['created_at'].replace(tzinfo=None) if hasattr(note_data['created_at'], 'replace') else note_data['created_at']
            if note_data.get('updated_at'):
                note_data['updated_at'] = note_data['updated_at'].replace(tzinfo=None) if hasattr(note_data['updated_at'], 'replace') else note_data['updated_at']
            
            return note_data
            
        except Exception as e:
            logger.error(f"Error getting note {note_id}: {str(e)}")
            raise e
    
    async def get_user_notes(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all notes for a specific user
        """
        try:
            logger.info(f"Getting notes for user {user_id}")
            
            # First, let's check if there are ANY notes in the collection
            all_notes_query = self.db.collection(self.notes_collection).limit(5)
            all_docs = list(all_notes_query.stream())
            logger.info(f"Total notes in database: {len(all_docs)}")
            
            if all_docs:
                for doc in all_docs:
                    data = doc.to_dict()
                    logger.info(f"Sample note - ID: {doc.id}, user_id: {data.get('user_id')}, text preview: {data.get('text', '')[:50]}...")
            
            # Now use the actual query with the index
            query = (self.db.collection(self.notes_collection)
                    .where('user_id', '==', user_id)
                    .order_by('created_at', direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            docs = query.stream()
            notes = []
            
            for doc in docs:
                try:
                    note_data = doc.to_dict()
                    note_data['id'] = doc.id
                    
                    # Convert Firestore timestamps to datetime objects
                    if note_data.get('created_at'):
                        if hasattr(note_data['created_at'], 'timestamp'):
                            # Convert Firestore timestamp to datetime
                            note_data['created_at'] = datetime.fromtimestamp(note_data['created_at'].timestamp())
                        elif hasattr(note_data['created_at'], 'replace'):
                            note_data['created_at'] = note_data['created_at'].replace(tzinfo=None)
                            
                    if note_data.get('updated_at'):
                        if hasattr(note_data['updated_at'], 'timestamp'):
                            # Convert Firestore timestamp to datetime
                            note_data['updated_at'] = datetime.fromtimestamp(note_data['updated_at'].timestamp())
                        elif hasattr(note_data['updated_at'], 'replace'):
                            note_data['updated_at'] = note_data['updated_at'].replace(tzinfo=None)
                    
                    # Ensure settings is a valid dict
                    if not isinstance(note_data.get('settings'), dict):
                        logger.warning(f"Note {doc.id} has invalid settings: {note_data.get('settings')}")
                        note_data['settings'] = {
                            'add_bullet_points': False,
                            'add_headers': False,
                            'expand': False,
                            'summarize': False
                        }
                    
                    notes.append(note_data)
                except Exception as e:
                    logger.error(f"Error processing note {doc.id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully retrieved {len(notes)} notes for user {user_id}")
            return notes
            
        except Exception as e:
            logger.error(f"Error getting notes for user {user_id}: {str(e)}")
            raise e
    
    async def update_note(self, note_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a note with new data
        """
        try:
            doc_ref = self.db.collection(self.notes_collection).document(note_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            note_data = doc.to_dict()
            
            # Check if the note belongs to the requesting user
            if note_data.get('user_id') != user_id:
                logger.warning(f"User {user_id} attempted to update note {note_id} owned by {note_data.get('user_id')}")
                return False
            
            # Add updated timestamp
            updates['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref.update(updates)
            logger.info(f"Updated note {note_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating note {note_id}: {str(e)}")
            raise e
    
    async def delete_note(self, note_id: str, user_id: str) -> bool:
        """
        Delete a note
        """
        try:
            doc_ref = self.db.collection(self.notes_collection).document(note_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            note_data = doc.to_dict()
            
            # Check if the note belongs to the requesting user
            if note_data.get('user_id') != user_id:
                logger.warning(f"User {user_id} attempted to delete note {note_id} owned by {note_data.get('user_id')}")
                return False
            
            doc_ref.delete()
            logger.info(f"Deleted note {note_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting note {note_id}: {str(e)}")
            raise e

# Create a singleton instance
firestore_service = FirestoreService()