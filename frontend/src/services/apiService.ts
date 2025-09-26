import { auth } from '../firebase';

const API_BASE_URL = 'http://localhost:8000';

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
  id: string; // Changed from number to string for Firestore document IDs
  text: string;
  settings: ProcessingSettings;
  processed_content: string | null;
  status: 'pending' | 'processing' | 'completed' | 'error';
  created_at: string;
}

// Helper function to get authentication headers
const getAuthHeaders = async (): Promise<HeadersInit> => {
  const user = auth.currentUser;
  console.log('Getting auth headers, current user:', user?.email);
  if (!user) {
    console.error('User not authenticated in getAuthHeaders');
    throw new Error('User not authenticated');
  }
  
  try {
    // Force refresh token to ensure it's valid
    const token = await user.getIdToken(true); // Force refresh
    console.log('Got ID token, length:', token.length);
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  } catch (error) {
    console.error('Error getting ID token:', error);
    throw new Error('Failed to get authentication token');
  }
};

export const createNote = async (noteData: NoteRequest): Promise<NoteResponse> => {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/notes/`, {
      method: 'POST',
      headers,
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

export const getNoteById = async (noteId: string): Promise<NoteResponse> => {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/notes/${noteId}`, {
      headers,
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
    console.log('API: Starting getAllNotes request');
    
    // Add retry logic for authentication
    let retryCount = 0;
    const maxRetries = 3;
    
    while (retryCount < maxRetries) {
      try {
        const headers = await getAuthHeaders();
        console.log('API: Got auth headers, making request to:', `${API_BASE_URL}/notes/`);
        
        const response = await fetch(`${API_BASE_URL}/notes/`, {
          method: 'GET',
          headers,
          mode: 'cors',
        });
        
        console.log('API: Response status:', response.status);
        
        if (response.status === 401 && retryCount < maxRetries - 1) {
          console.log('API: Authentication failed, retrying...');
          retryCount++;
          // Wait a bit before retrying
          await new Promise(resolve => setTimeout(resolve, 1000));
          continue;
        }
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('API: Error response text:', errorText);
          try {
            const error = JSON.parse(errorText);
            throw new Error(error.detail || `Failed to fetch notes: ${response.status}`);
          } catch (parseError) {
            throw new Error(`HTTP ${response.status}: ${errorText || 'Unknown error'}`);
          }
        }

        const data = await response.json();
        console.log('API: Successfully fetched notes:', data);
        return Array.isArray(data) ? data : [];
      } catch (fetchError) {
        if (retryCount === maxRetries - 1) {
          throw fetchError;
        }
        retryCount++;
        console.log(`API: Retry ${retryCount}/${maxRetries} after error:`, fetchError);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    throw new Error('Max retries exceeded');
  } catch (error) {
    console.error('Error fetching notes:', error);
    throw error;
  }
};

export const deleteNote = async (noteId: string): Promise<void> => {
  try {
    console.log('API: Attempting to delete note:', noteId);
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/notes/${noteId}`, {
      method: 'DELETE',
      headers,
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
  noteId: string, 
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