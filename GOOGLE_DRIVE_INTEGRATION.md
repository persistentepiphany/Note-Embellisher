# Google Drive Integration & Multi-Format Export

This document explains the new Google Drive integration and multi-format export features added to Note Embellisher.

## Features

### 1. **Auto-Generated PDF/DOCX/TXT Exports**
After processing, notes automatically generate:
- **PDF** - Professional LaTeX-formatted documents with proper typography
- **DOCX** - Microsoft Word-compatible documents
- **TXT** - Plain text exports

### 2. **Google Drive Integration**
Users can:
- Connect their Google Drive account via OAuth 2.0
- Upload processed notes directly to Drive in any format (PDF/DOCX/TXT)
- Maintain persistent authorization (refresh tokens stored securely)

### 3. **Enhanced Dashboard**
- PDF preview embedded in note cards
- Download buttons for all export formats
- Google Drive upload interface with format selection
- View original uploaded images alongside processed content

---

## Backend Setup

### Environment Variables

Add these to your `.env` file:

```bash
# Google Drive OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_DRIVE_REDIRECT_URI=http://localhost:8000/google-drive/callback
GOOGLE_DRIVE_SUCCESS_REDIRECT=http://localhost:5173/dashboard
GOOGLE_DRIVE_FOLDER_ID=optional-default-folder-id
```

### Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google Drive API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized redirect URIs:
   - `http://localhost:8000/google-drive/callback` (development)
   - `https://your-domain.com/google-drive/callback` (production)
7. Copy **Client ID** and **Client Secret** to `.env`

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `google-auth>=2.35.0`
- `google-auth-oauthlib>=1.2.0`
- `google-auth-httplib2>=0.2.0`
- `google-api-python-client>=2.149.0`
- `python-docx>=1.1.2`

---

## API Endpoints

### Google Drive

#### Get Connection Status
```http
GET /google-drive/status
Authorization: Bearer {firebase-token}
```

**Response:**
```json
{
  "connected": true,
  "expires_at": "2025-11-16T12:00:00Z",
  "has_refresh_token": true
}
```

#### Start OAuth Flow
```http
GET /google-drive/auth-url
Authorization: Bearer {firebase-token}
```

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "random-state-token"
}
```

#### OAuth Callback (handled automatically)
```http
GET /google-drive/callback?code={auth-code}&state={state}
```

#### Upload to Drive
```http
POST /notes/{note_id}/upload-to-drive?file_format=pdf
Authorization: Bearer {firebase-token}
```

**Response:**
```json
{
  "success": true,
  "note_id": 123,
  "format": "pdf",
  "drive_file": {
    "id": "1abc...",
    "name": "note_123_user1234.pdf",
    "webViewLink": "https://drive.google.com/file/d/...",
    "webContentLink": "https://drive.google.com/uc?id=..."
  }
}
```

### Export Generation

#### Generate PDF
```http
POST /notes/{note_id}/generate-pdf
Authorization: Bearer {firebase-token}
```

#### Generate DOCX
```http
POST /notes/{note_id}/generate-docx
Authorization: Bearer {firebase-token}
```

#### Generate TXT
```http
POST /notes/{note_id}/generate-txt
Authorization: Bearer {firebase-token}
```

---

## Frontend Usage

### Connect Google Drive

```typescript
import { getGoogleDriveAuthUrl, getGoogleDriveStatus } from './services/apiService';

// Check connection status
const status = await getGoogleDriveStatus();
console.log(status.connected); // true/false

// Start OAuth flow
const { auth_url } = await getGoogleDriveAuthUrl();
const popup = window.open(auth_url, 'drive-auth', 'width=520,height=720');

// Poll for completion
// (Dashboard.tsx handles this automatically)
```

### Download Exports

```typescript
import { generatePDF, generateDocx, generateTxt, API_BASE_URL } from './services/apiService';

// Generate and download PDF
const result = await generatePDF(noteId);
const pdfUrl = `${API_BASE_URL}${result.pdf_url}`;
window.open(pdfUrl, '_blank');

// Generate DOCX
const docxResult = await generateDocx(noteId);
window.open(`${API_BASE_URL}${docxResult.docx_url}`, '_blank');

// Generate TXT
const txtResult = await generateTxt(noteId);
window.open(`${API_BASE_URL}${txtResult.txt_url}`, '_blank');
```

### Upload to Drive

```typescript
import { uploadNoteToDrive } from './services/apiService';

// Upload as PDF
await uploadNoteToDrive(noteId, 'pdf');

// Upload as DOCX
await uploadNoteToDrive(noteId, 'docx');

// Upload as TXT
await uploadNoteToDrive(noteId, 'txt');
```

---

## Database Schema Updates

### New Table: `google_drive_tokens`

```sql
CREATE TABLE google_drive_tokens (
    id INTEGER PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    token_expiry TIMESTAMP,
    token_scope TEXT,
    token_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Updated `notes` Table

New columns:
```sql
ALTER TABLE notes ADD COLUMN pdf_path TEXT;
ALTER TABLE notes ADD COLUMN tex_path TEXT;
ALTER TABLE notes ADD COLUMN docx_path TEXT;
ALTER TABLE notes ADD COLUMN txt_path TEXT;
```

These migrations are applied automatically on startup.

---

## File Storage

All generated exports are stored in:
```
backend/generated_pdfs/
├── note_123_user1234.pdf
├── note_123_user1234.tex
├── note_123_user1234.docx
└── note_123_user1234.txt
```

Files are served via static file mounting:
```
GET http://localhost:8000/generated_pdfs/note_123_user1234.pdf
```

---

## Security Considerations

1. **OAuth Tokens** - Stored in database with refresh tokens for long-term access
2. **State Parameter** - CSRF protection with 10-minute TTL
3. **User Isolation** - All exports filtered by `user_id`
4. **Token Refresh** - Automatic refresh on expired access tokens
5. **Scopes** - Minimal scope: `https://www.googleapis.com/auth/drive.file` (user-created files only)

---

## Troubleshooting

### "Google Drive integration is not configured"
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
- Ensure `GOOGLE_DRIVE_REDIRECT_URI` matches Google Cloud Console

### "python-docx dependency missing"
```bash
pip install python-docx==1.1.2
```

### "PDF generation services unavailable"
- Verify LaTeX service is running
- Check `OPENAI_API_KEY` is set for LaTeX generation
- Install `pdflatex` for local compilation (optional)

### OAuth callback shows "state expired"
- State tokens expire after 10 minutes
- Close popup and try again

---

## Production Deployment

### Update Environment Variables
```bash
GOOGLE_DRIVE_REDIRECT_URI=https://your-api-domain.com/google-drive/callback
GOOGLE_DRIVE_SUCCESS_REDIRECT=https://your-frontend-domain.com/dashboard
```

### Update Google Cloud Console
Add production redirect URI to authorized list

### File Storage
Consider migrating to cloud storage (S3, Google Cloud Storage) for production:
```python
# Example: Upload to S3 instead of local filesystem
def upload_to_s3(local_path: str) -> str:
    # ... S3 upload logic
    return s3_url
```

---

## Example Workflow

1. **User uploads note** → Image/text processed via ChatGPT
2. **Auto-export** → PDF/DOCX/TXT generated automatically
3. **Dashboard preview** → PDF embedded in note card
4. **Download** → Click PDF/Word/TXT buttons
5. **Google Drive** → Click "Connect Drive" once
6. **Upload** → Select format, click "Add to Google Drive"
7. **Access** → File appears in user's Google Drive immediately

---

## Future Enhancements

- [ ] Batch export multiple notes
- [ ] Custom folder selection in Drive
- [ ] Shareable Drive links
- [ ] Export history tracking
- [ ] Dropbox integration
- [ ] OneDrive integration

---

## Questions?

Check the main README or open an issue on GitHub.
