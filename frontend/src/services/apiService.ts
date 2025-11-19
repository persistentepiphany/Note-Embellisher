import { getAuth } from "firebase/auth";

// Use environment variable or default to localhost for development
const env = (import.meta as unknown as { env: Record<string, string | undefined> }).env;
export const API_BASE_URL = env.VITE_API_BASE_URL || 'http://localhost:8080';

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

export interface Flashcard {
  id: string;
  topic: string;
  term: string;
  definition: string;
  source: 'ai' | 'manual';
  created_at?: string | null;
}

export interface FolderSummary {
  id: number;
  name: string;
}

export interface ProcessingSettings {
  add_bullet_points: boolean;
  add_headers: boolean;
  expand: boolean;
  summarize: boolean;
  focus_topics?: string[];
  latex_style?: string;
  font_preference?: string;
  custom_specifications?: string;
  generate_flashcards?: boolean;
  flashcard_topics?: string[];
  flashcard_count?: number;
  max_flashcards_per_topic?: number;
  project_name?: string;
  latex_title?: string;
  include_nickname?: boolean;
  nickname?: string;
}

export interface TopicSuggestion {
  topics: string[];
}

export interface NoteRequest {
  text: string;
  settings: ProcessingSettings;
}

export interface NoteResponse {
  id: number;
  text: string | null;
  settings: ProcessingSettings;
  processed_content: string | null;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number; // 0-100
  progress_message: string | null;
  // Image-related fields
  image_url?: string | null;
  image_filename?: string | null;
  image_type?: string | null;
  input_type: string;
  pdf_url?: string | null;
  docx_url?: string | null;
  txt_url?: string | null;
  project_name?: string | null;
  latex_title?: string | null;
  include_nickname?: boolean;
  nickname?: string | null;
  flashcards?: Flashcard[];
  folder?: FolderSummary | null;
  created_at: string;
  updated_at?: string | null;
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

export const uploadImageNote = async (
  file: File,
  settings: ProcessingSettings
): Promise<NoteResponse> => {
  try {
    const auth = getAuth();
    const user = auth.currentUser;
    
    if (!user) {
      throw new Error('User not authenticated');
    }

    const token = await user.getIdToken();
    
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('file', file);
    formData.append('settings', JSON.stringify(settings));

    const response = await fetch(`${API_BASE_URL}/upload-image/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        // Don't set Content-Type header - let browser set it with boundary for FormData
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload image');
    }

    return await response.json();
  } catch (error) {
    console.error('Error uploading image:', error);
    throw error;
  }
};

export const uploadMultipleImages = async (
  files: File[],
  settings: ProcessingSettings
): Promise<NoteResponse> => {
  try {
    const auth = getAuth();
    const user = auth.currentUser;
    
    if (!user) {
      throw new Error('User not authenticated');
    }

    const token = await user.getIdToken();
    
    // Create FormData for multiple file upload
    const formData = new FormData();
    
    // Append each file with the same field name (FastAPI will collect them as a list)
    files.forEach(file => {
      formData.append('files', file);
    });
    
    formData.append('settings', JSON.stringify(settings));

    const response = await fetch(`${API_BASE_URL}/upload-multiple-images/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        // Don't set Content-Type header - let browser set it with boundary for FormData
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload images');
    }

    return await response.json();
  } catch (error) {
    console.error('Error uploading multiple images:', error);
    throw error;
  }
};

export const pollNoteStatus = async (
  noteId: number, 
  onUpdate: (note: NoteResponse) => void,
  maxAttempts: number = 60 // Increased for longer processing times
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
        
        // Poll every 1 second for better progress updates
        setTimeout(poll, 1000);
      } catch (error) {
        reject(error);
      }
    };
    
    poll();
  });
};

export interface GeneratePDFResponse {
  success: boolean;
  note_id: number;
  pdf_path: string;
  tex_path?: string;
  pdf_url: string;
  message: string;
}

export const generatePDF = async (noteId: number): Promise<GeneratePDFResponse> => {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/notes/${noteId}/generate-pdf`, {
      method: 'POST',
      headers: headers,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate PDF');
    }

    return await response.json();
  } catch (error) {
    console.error('Error generating PDF:', error);
    throw error;
  }
};

export interface GenerateDocxResponse {
  success: boolean;
  note_id: number;
  docx_path: string;
  docx_url: string;
}

export interface GenerateTxtResponse {
  success: boolean;
  note_id: number;
  txt_path: string;
  txt_url: string;
}

export const generateDocx = async (noteId: number): Promise<GenerateDocxResponse> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/notes/${noteId}/generate-docx`, {
    method: 'POST',
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate Word document');
  }

  return await response.json();
};

export const generateTxt = async (noteId: number): Promise<GenerateTxtResponse> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/notes/${noteId}/generate-txt`, {
    method: 'POST',
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate TXT file');
  }

  return await response.json();
};

export interface GoogleDriveStatusResponse {
  connected: boolean;
  expires_at?: string | null;
  has_refresh_token: boolean;
}

export const getGoogleDriveStatus = async (): Promise<GoogleDriveStatusResponse> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/google-drive/status`, {
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch Google Drive status');
  }

  return await response.json();
};

export interface GoogleDriveAuthUrlResponse {
  auth_url: string;
  state: string;
}

export const getGoogleDriveAuthUrl = async (): Promise<GoogleDriveAuthUrlResponse> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/google-drive/auth-url`, {
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start Google Drive authorization');
  }

  return await response.json();
};

export interface UploadDriveResponse {
  success: boolean;
  note_id: number;
  format: 'pdf' | 'docx' | 'txt';
  drive_file: {
    id: string;
    name: string;
    webViewLink?: string;
    webContentLink?: string;
  };
}

export const uploadNoteToDrive = async (
  noteId: number,
  format: 'pdf' | 'docx' | 'txt' = 'pdf'
): Promise<UploadDriveResponse> => {
  const headers = await getAuthHeaders();
  const response = await fetch(
    `${API_BASE_URL}/notes/${noteId}/upload-to-drive?file_format=${format}`,
    {
      method: 'POST',
      headers,
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to upload file to Google Drive');
  }

  return response.json();
};

export const previewTopics = async (text: string): Promise<TopicSuggestion> => {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/preview-topics`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({ text }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get topic suggestions');
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting topic suggestions:', error);
    throw error;
  }
};

interface FlashcardListResponse {
  flashcards: Flashcard[];
}

export interface FlashcardPayload {
  topic: string;
  term: string;
  definition: string;
}

export const fetchFlashcards = async (noteId: number): Promise<Flashcard[]> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/notes/${noteId}/flashcards`, {
    headers,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to load flashcards');
  }
  const data: FlashcardListResponse = await response.json();
  return data.flashcards;
};

export const addFlashcard = async (noteId: number, payload: FlashcardPayload): Promise<Flashcard[]> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/notes/${noteId}/flashcards`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to add flashcard');
  }
  const data: FlashcardListResponse = await response.json();
  return data.flashcards;
};

export const updateFlashcard = async (noteId: number, cardId: string, payload: FlashcardPayload): Promise<Flashcard[]> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/notes/${noteId}/flashcards/${cardId}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update flashcard');
  }
  const data: FlashcardListResponse = await response.json();
  return data.flashcards;
};

export const deleteFlashcard = async (noteId: number, cardId: string): Promise<Flashcard[]> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/notes/${noteId}/flashcards/${cardId}`, {
    method: 'DELETE',
    headers,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete flashcard');
  }
  const data: FlashcardListResponse = await response.json();
  return data.flashcards;
};

export interface NoteMetadataPayload {
  project_name?: string | null;
  latex_title?: string | null;
  include_nickname?: boolean;
  nickname?: string | null;
  folder_id?: number | null;
}

export const updateNoteMetadata = async (noteId: number, payload: NoteMetadataPayload): Promise<NoteResponse> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/notes/${noteId}/metadata`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update project settings');
  }
  return await response.json();
};

export const fetchFolders = async (): Promise<FolderSummary[]> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/folders`, {
    headers,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch folders');
  }
  return await response.json();
};

export const createFolder = async (name: string): Promise<FolderSummary> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/folders`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create folder');
  }
  return await response.json();
};

export const renameFolder = async (folderId: number, name: string): Promise<FolderSummary> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/folders/${folderId}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to rename folder');
  }
  return await response.json();
};

export const deleteFolder = async (folderId: number): Promise<void> => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/folders/${folderId}`, {
    method: 'DELETE',
    headers,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete folder');
  }
};
