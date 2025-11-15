# PDF Generation Feature

## Overview

The Note Embellisher now includes professional PDF generation using LaTeX! This feature transforms your processed notes into beautifully formatted academic PDFs with proper mathematical notation, section headers, and professional typesetting.

## How It Works

### 1. **Content Processing** (Existing)
   - User uploads notes (text or image)
   - ChatGPT enhances the content with better structure
   - Content is saved with improvements

### 2. **LaTeX Generation** (New!)
   - OpenAI GPT-4 converts enhanced content into LaTeX
   - Intelligently structures content with:
     - Section headers and hierarchy
     - Mathematical notation in proper LaTeX format
     - Theorem environments (theorems, lemmas, definitions)
     - Professional formatting and spacing
     - Table of contents for longer documents

### 3. **PDF Compilation** (New!)
   - Two compilation methods available:
     - **Local**: Uses `pdflatex` if installed (faster, better control)
     - **Cloud**: Uses the texlive.net `latexcgi` API (no local installation needed)
   - Automatically saves both `.tex` and `.pdf` files
   - Returns download URL to frontend

## API Endpoint

### Generate PDF from Note

**POST** `/notes/{note_id}/generate-pdf`

**Authentication**: Requires Firebase ID token

**Request**:
```http
POST /notes/123/generate-pdf
Authorization: Bearer <firebase_token>
```

**Response**:
```json
{
  "success": true,
  "note_id": 123,
  "pdf_path": "/path/to/generated_pdfs/note_123_abcd1234.pdf",
  "tex_path": "/path/to/generated_pdfs/note_123_abcd1234.tex",
  "pdf_url": "/generated_pdfs/note_123_abcd1234.pdf",
  "message": "PDF generated successfully"
}
```

**Error Responses**:
- `400`: Note hasn't been processed yet
- `404`: Note not found
- `503`: LaTeX/PDF services unavailable
- `500`: Compilation error

## Installation & Setup

### Option 1: Cloud Compilation (Recommended for deployment)
No additional installation needed! Uses LaTeX.Online API.

**Pros**:
- No local dependencies
- Works on any server
- Automatic updates

**Cons**:
- Requires internet connection
- Slightly slower (120s timeout)
- Relies on external service

> **Note:** texlive.net expects uploaded `.tex` files to use CRLF (Windows) line endings. The backend normalizes your LaTeX before uploading, but if you call the API manually be sure to convert `\n` to `\r\n`.

### Option 2: Local Compilation (Better for development)

**macOS**:
```bash
brew install --cask mactex-no-gui
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install texlive-latex-base texlive-latex-extra
```

**Windows**:
Download and install MiKTeX: https://miktex.org/download

**Verify Installation**:
```bash
pdflatex --version
```

**Pros**:
- Faster compilation (30s timeout)
- No external dependencies
- Better error messages
- Full control over LaTeX environment

**Cons**:
- Requires ~1-4GB installation
- Manual updates needed

## Architecture

### Files Created

1. **`latex_service.py`** - LaTeX generation service
   - Uses OpenAI GPT-4 for intelligent formatting
   - Converts markdown/plain text to LaTeX
   - Handles mathematical notation
   - Creates proper document structure

2. **`pdf_compiler.py`** - PDF compilation utility
   - Tries local `pdflatex` first
   - Falls back to cloud compilation
   - Manages temporary files
   - Returns PDF and .tex paths

3. **Updated `main.py`**:
   - Added `/notes/{note_id}/generate-pdf` endpoint
   - Integrated LaTeX and PDF services
   - Added error handling

### Document Structure

Generated PDFs include:

```latex
\documentclass[12pt,a4paper]{article}

% Packages for math, graphics, headers
\usepackage{amsmath,amssymb,amsthm}
\usepackage{graphicx,hyperref,fancyhdr}
\usepackage[margin=1in]{geometry}

% Custom header/footer with note metadata
\pagestyle{fancy}
\rhead{Subject Name}
\lhead{Note Title}

% Theorem environments
\newtheorem{theorem}{Theorem}
\newtheorem{definition}{Definition}

\begin{document}
\maketitle
\tableofcontents

% Your beautifully formatted content here

\end{document}
```

## Frontend Integration

### Example React/TypeScript Usage

```typescript
const generatePDF = async (noteId: number) => {
  const token = await getFirebaseToken();
  
  const response = await fetch(`/api/notes/${noteId}/generate-pdf`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  if (data.success) {
    // Download the PDF
    window.open(data.pdf_url, '_blank');
  } else {
    console.error('PDF generation failed');
  }
};
```

### Add to Note Component

```tsx
<button 
  onClick={() => generatePDF(note.id)}
  disabled={note.status !== 'completed'}
>
  📄 Download PDF
</button>
```

## Customization

### Modify LaTeX Template

Edit `latex_service.py` to customize:
- Document class options
- Package includes
- Theorem environment names
- Header/footer design
- Margins and spacing
- Colors and fonts

### Adjust OpenAI Prompt

Modify `_create_latex_conversion_prompt()` to:
- Change formatting style
- Add specific instructions
- Include custom LaTeX commands
- Control section hierarchy

## Troubleshooting

### PDF Generation Fails

1. **Check service availability**:
```bash
curl http://localhost:8000/
# Should show "latex": true, "pdf_compiler": true
```

2. **Verify note is processed**:
```bash
curl http://localhost:8000/notes/123
# Check that processed_content is not null
```

3. **Check compilation logs**:
   - Server will print detailed error messages
   - Look for LaTeX syntax errors
   - Check timeout issues

### LaTeX Errors

Common issues:
- **Special characters**: Automatically escaped by fallback mode
- **Math mode errors**: GPT-4 usually handles correctly
- **Missing packages**: Template includes common ones
- **Timeout**: Increase timeout in `pdf_compiler.py`

## Future Enhancements

- [ ] Upload PDFs to Firebase Storage
- [ ] Custom templates selection
- [ ] Bibliography support
- [ ] Image embedding from notes
- [ ] Multiple export formats (HTML, DOCX)
- [ ] Real-time preview
- [ ] Custom styling options in UI
- [ ] Batch PDF generation

## Dependencies

Already included in `requirements.txt`:
- `openai>=1.12.0` - For LaTeX content formatting
- `requests>=2.32.0` - For cloud compilation API
- `python-dotenv>=1.0.0` - For environment variables

Optional local tools:
- `pdflatex` - Part of TeX Live or MiKTeX installation

## Testing

### Test Locally

```bash
# Start the backend
cd backend
python main.py

# Test the endpoint
curl -X POST http://localhost:8000/notes/1/generate-pdf \
  -H "Authorization: Bearer test-token"
```

### Test LaTeX Service Directly

```python
from latex_service import latex_service

latex_content = latex_service.generate_latex_document(
    title="Test Note",
    content="This is a test with $E=mc^2$",
    subject="Physics",
    author="Test User"
)

print(latex_content)
```

### Test PDF Compilation

```python
from pdf_compiler import pdf_compiler

latex = r"\documentclass{article}\begin{document}Hello World\end{document}"
pdf_path, tex_path, error = pdf_compiler.compile_to_pdf(
    latex, 
    "test_document"
)

print(f"PDF: {pdf_path}, Error: {error}")
```

## Production Deployment

### Railway/Render Configuration

No special configuration needed! Cloud compilation works out of the box.

### Environment Variables

Ensure these are set:
- `OPENAI_API_KEY` - For LaTeX generation
- Firebase credentials - For authentication

### File Storage

Update `pdf_compiler.get_pdf_url()` to:
1. Upload PDFs to Firebase Storage
2. Return public download URL
3. Clean up local files

Example:
```python
def get_pdf_url(self, pdf_path: str) -> str:
    # Upload to Firebase Storage
    blob = bucket.blob(f"pdfs/{Path(pdf_path).name}")
    blob.upload_from_filename(pdf_path)
    
    # Return public URL
    return blob.public_url
```

## License

Part of the Note Embellisher project.
