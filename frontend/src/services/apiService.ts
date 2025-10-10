import { getAuth } from "firebase/auth";

const API_BASE_URL = 'http://localhost:8000';

// ----- firebase-fix: Add authentication header helper -----
const getAuthHeaders = async () => {
  const auth = getAuth();
  const user = auth.currentUser;
  const headers: { [key: string]: string } = {
    'Content-Type': 'application/json',
  };

  if (user) {
    try {
      const token = await user.getIdToken();
      headers['Authorization'] = `Bearer ${token}`;
    } catch (error) {
      console.error("Error getting auth token:", error);
    }
  }
  return headers;
};
// ----------------------------------------------------

export interface ProcessingSettings {
  add_bullet_points: boolean;
  add_headers: boolean;
  expand: boolean;
  summarize: boolean;
}

export interface NoteRequest {
  text: string;
  settings: ProcessingSettings;
}

export interface NoteResponse {
  id: number;
  text: string;
  settings: ProcessingSettings;
  processed_content: string | null;
  status: 'pending' | 'processing' | 'completed' | 'error';
  created_at: string;
}

export const createNote = async (noteData: NoteRequest): Promise<NoteResponse> => {
  try {
    const headers = await getAuthHeaders(); // firebase-fix: Add auth header
    const response = await fetch(`${API_BASE_URL}/notes/`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(noteData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create note');
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating note:', error);
    throw error;
  }
};

export const getNoteById = async (noteId: number): Promise<NoteResponse> => {
  try {
    const headers = await getAuthHeaders(); // firebase-fix: Add auth header
    const response = await fetch(`${API_BASE_URL}/notes/${noteId}`, {
      headers: headers,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch note');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching note:', error);
    throw error;
  }
};

export const getAllNotes = async (): Promise<NoteResponse[]> => {
  try {
    const headers = await getAuthHeaders(); // firebase-fix: Add auth header
    const response = await fetch(`${API_BASE_URL}/notes/`, {
      headers: headers,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch notes');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching notes:', error);
    throw error;
  }
};

export const deleteNote = async (noteId: number): Promise<void> => {
  try {
    console.log('API: Attempting to delete note:', noteId);
    const headers = await getAuthHeaders(); // firebase-fix: Add auth header
    const response = await fetch(`${API_BASE_URL}/notes/${noteId}`, {
      method: 'DELETE',
      headers: headers,
    });

    console.log('API: Delete response status:', response.status);

    if (!response.ok) {
      const error = await response.json();
      console.error('API: Delete failed with error:', error);
      throw new Error(error.detail || 'Failed to delete note');
    }
    
    console.log('API: Note deleted successfully');
  } catch (error) {
    console.error('Error deleting note:', error);
    throw error;
  }
};

export const pollNoteStatus = async (
  noteId: number, 
  onUpdate: (note: NoteResponse) => void,
  maxAttempts: number = 30
): Promise<NoteResponse> => {
  let attempts = 0;
  
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const note = await getNoteById(noteId);
        onUpdate(note);
        
        if (note.status === 'completed' || note.status === 'error') {
          resolve(note);
          return;
        }
        
        attempts++;
        if (attempts >= maxAttempts) {
          reject(new Error('Polling timeout - processing took too long'));
          return;
        }
        
        // Poll every 2 seconds
        setTimeout(poll, 2000);
      } catch (error) {
        reject(error);
      }
    };
    
    poll();
  });
};