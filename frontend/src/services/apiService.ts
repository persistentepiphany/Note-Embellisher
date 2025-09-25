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
  id: number;
  text: string;
  settings: ProcessingSettings;
  processed_content: string | null;
  status: 'pending' | 'processing' | 'completed' | 'error';
  created_at: string;
}

export const createNote = async (noteData: NoteRequest): Promise<NoteResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/notes/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
    const response = await fetch(`${API_BASE_URL}/notes/${noteId}`);
    
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