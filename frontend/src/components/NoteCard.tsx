import React, { useEffect, useState } from 'react';
import { Download, Trash2, Clock, FileText, Loader2, Cloud, ExternalLink, Image as ImageIcon } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { FormattedContent } from './FormattedContent';
import { FlashcardDeck } from './FlashcardDeck';
import { FlashcardPayload, FolderSummary, NoteMetadataPayload, NoteResponse } from '../services/apiService';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

interface NoteCardProps {
  note: NoteResponse;
  apiBaseUrl: string;
  onDownloadPdf: (note: NoteResponse) => Promise<void>;
  onDownloadDocx: (note: NoteResponse) => Promise<void>;
  onDownloadTxt: (note: NoteResponse) => Promise<void>;
  onUploadToDrive: (note: NoteResponse, format: 'pdf' | 'docx' | 'txt') => Promise<void>;
  onDelete: (noteId: number) => void;
  onUpdateMetadata: (noteId: number, payload: NoteMetadataPayload) => Promise<void>;
  onAddFlashcard: (noteId: number, payload: FlashcardPayload) => Promise<void>;
  onDeleteFlashcard: (noteId: number, cardId: string) => Promise<void>;
  folders: FolderSummary[];
  actionStates: {
    pdf: boolean;
    docx: boolean;
    txt: boolean;
    drive: boolean;
    metadata?: boolean;
    flashcards?: boolean;
  };
}

export const NoteCard: React.FC<NoteCardProps> = ({
  note,
  apiBaseUrl,
  onDownloadPdf,
  onDownloadDocx,
  onDownloadTxt,
  onUploadToDrive,
  onDelete,
  onUpdateMetadata,
  onAddFlashcard,
  onDeleteFlashcard,
  folders,
  actionStates,
}) => {
  const [driveFormat, setDriveFormat] = useState<'pdf' | 'docx' | 'txt'>('pdf');
  const [projectNameInput, setProjectNameInput] = useState(note.project_name || `Note #${note.id}`);
  const [editingProjectName, setEditingProjectName] = useState(false);
  const [metadataMessage, setMetadataMessage] = useState<string | null>(null);
  const [latexTitleInput, setLatexTitleInput] = useState(note.latex_title || '');
  const [nicknameInput, setNicknameInput] = useState(note.nickname || '');
  const [nicknameEnabled, setNicknameEnabled] = useState<boolean>(!!note.include_nickname);
  const [flashcardForm, setFlashcardForm] = useState<FlashcardPayload>({
    topic: '',
    term: '',
    definition: '',
  });
  const [flashcardError, setFlashcardError] = useState<string | null>(null);

  useEffect(() => {
    setProjectNameInput(note.project_name || `Note #${note.id}`);
    setLatexTitleInput(note.latex_title || '');
    setNicknameInput(note.nickname || '');
    setNicknameEnabled(!!note.include_nickname);
  }, [note.project_name, note.latex_title, note.nickname, note.include_nickname, note.id]);
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const truncateText = (text: string | null | undefined, maxLength: number = 150) => {
    if (!text) return '[No content available]';
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const isCompleted = note.status === 'completed';
  const pdfPreviewUrl = note.pdf_url ? `${apiBaseUrl}${note.pdf_url}` : null;
  const actionDisabled = (stateFlag: boolean) => !isCompleted || stateFlag;
  const metadataBusy = !!actionStates.metadata;
  const flashcardsBusy = !!actionStates.flashcards;
  const flashcards = note.flashcards || [];
  const projectDisplayName = note.project_name?.trim() || `Note #${note.id}`;
  const folderValue = note.folder?.id ? note.folder.id.toString() : 'none';

  const handleRenameSubmit = async () => {
    try {
      setMetadataMessage('Saving project name...');
      await onUpdateMetadata(note.id, { project_name: projectNameInput.trim() || null });
      setEditingProjectName(false);
      setTimeout(() => setMetadataMessage(null), 2000);
    } catch (error) {
      setMetadataMessage('Failed to update name');
      setTimeout(() => setMetadataMessage(null), 2000);
      alert(error instanceof Error ? error.message : 'Failed to update project name');
    }
  };

  const handleFolderChange = async (value: string) => {
    try {
      setMetadataMessage('Updating folder...');
      await onUpdateMetadata(note.id, { folder_id: value === 'none' ? null : Number(value) });
      setTimeout(() => setMetadataMessage(null), 2000);
    } catch (error) {
      setMetadataMessage('Failed to update folder');
      setTimeout(() => setMetadataMessage(null), 2000);
      alert(error instanceof Error ? error.message : 'Failed to update folder');
    }
  };

  const handlePresentationSave = async () => {
    try {
      setMetadataMessage('Saving display details...');
      await onUpdateMetadata(note.id, {
        latex_title: latexTitleInput.trim() || null,
        include_nickname: nicknameEnabled,
        nickname: nicknameEnabled ? (nicknameInput.trim() || null) : null,
      });
      setTimeout(() => setMetadataMessage(null), 2000);
    } catch (error) {
      setMetadataMessage('Failed to update display');
      setTimeout(() => setMetadataMessage(null), 2000);
      alert(error instanceof Error ? error.message : 'Failed to update display options');
    }
  };

  const handleFlashcardInputChange = (field: keyof FlashcardPayload, value: string) => {
    setFlashcardForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleFlashcardSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!flashcardForm.topic || !flashcardForm.term || !flashcardForm.definition) {
      setFlashcardError('Topic, term, and definition are required.');
      return;
    }
    try {
      setFlashcardError(null);
      await onAddFlashcard(note.id, flashcardForm);
      setFlashcardForm({ topic: '', term: '', definition: '' });
    } catch (error) {
      setFlashcardError(error instanceof Error ? error.message : 'Failed to add flashcard');
    }
  };

  const handleFlashcardDelete = async (cardId: string) => {
    try {
      await onDeleteFlashcard(note.id, cardId);
      setFlashcardError(null);
    } catch (error) {
      setFlashcardError(error instanceof Error ? error.message : 'Failed to remove flashcard');
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg">{projectDisplayName}</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setEditingProjectName((prev) => !prev)}
                title="Rename project"
              >
                <FileText className="w-4 h-4 text-gray-500" />
              </Button>
            </div>
            <CardDescription className="text-sm text-gray-500">
              Created {formatDate(note.created_at)}
            </CardDescription>
            {editingProjectName && (
              <div className="mt-2 flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  value={projectNameInput}
                  onChange={(e) => setProjectNameInput(e.target.value)}
                  disabled={metadataBusy}
                />
                <Button size="sm" onClick={handleRenameSubmit} disabled={metadataBusy}>
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setEditingProjectName(false);
                    setProjectNameInput(projectDisplayName);
                  }}
                  disabled={metadataBusy}
                >
                  Cancel
                </Button>
              </div>
            )}
            {metadataMessage && (
              <p className="text-xs text-amber-600 mt-1">{metadataMessage}</p>
            )}
            
            {/* Folder Organization */}
            <div className="mt-3 flex items-center gap-2">
              <label className="text-xs uppercase text-gray-500 whitespace-nowrap">Folder:</label>
              <Select
                value={folderValue}
                onValueChange={handleFolderChange}
                disabled={metadataBusy}
              >
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue placeholder="No folder" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No folder</SelectItem>
                  {folders.map((folder) => (
                    <SelectItem key={folder.id} value={folder.id.toString()}>
                      {folder.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge className={getStatusColor(note.status)}>
              {note.status === 'processing' && <Clock className="w-3 h-3 mr-1 animate-spin" />}
              {note.status}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (window.confirm(`Are you sure you want to delete ${projectDisplayName}? This action cannot be undone.`)) {
                  onDelete(note.id);
                }
              }}
              className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
              title="Delete Note"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-1">Original Text:</h4>
              <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
              {truncateText(note.text)}
            </p>
          </div>
          {note.processed_content && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-1">Enhanced Text:</h4>
              <div className="bg-green-50 p-3 rounded border border-green-200 max-h-32 overflow-y-auto">
                <FormattedContent 
                  content={truncateText(note.processed_content, 200)}
                  className="text-xs"
                />
              </div>
            </div>
          )}
          {note.status === 'processing' && (
            <div className="bg-yellow-50 p-2 rounded">
              <p className="text-sm text-yellow-700">Processing with AI...</p>
            </div>
          )}
          {note.status === 'error' && note.processed_content && (
            <div className="bg-red-50 p-3 rounded border border-red-200">
              <h4 className="text-sm font-medium text-red-700 mb-1">Error:</h4>
              <p className="text-sm text-red-600">{note.processed_content}</p>
            </div>
          )}
          {note.image_url && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <ImageIcon className="w-4 h-4" /> Original Upload
              </h4>
              <div className="bg-gray-50 border rounded p-2">
                {note.image_type === 'pdf' ? (
                  <p className="text-sm text-gray-600">
                    PDF uploaded. Use the button below to view the original file.
                  </p>
                ) : (
                  <img
                    src={note.image_url}
                    alt={`Note ${note.id} original upload`}
                    className="max-h-48 w-full object-cover rounded"
                  />
                )}
              </div>
              <Button
                variant="link"
                size="sm"
                className="px-0"
                onClick={() => window.open(note.image_url || '#', '_blank', 'noopener')}
              >
                <ExternalLink className="w-4 h-4 mr-1" /> View original file
              </Button>
            </div>
          )}
          {pdfPreviewUrl && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <FileText className="w-4 h-4" /> LaTeX PDF Preview
              </h4>
              <div className="border rounded overflow-hidden h-64">
                <iframe
                  src={`${pdfPreviewUrl}#view=FitH`}
                  title={`PDF preview for note ${note.id}`}
                  className="w-full h-full"
                />
              </div>
            </div>
          )}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Downloads</h4>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={actionDisabled(actionStates.pdf)}
                onClick={() => onDownloadPdf(note)}
              >
                {actionStates.pdf ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                PDF
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={actionDisabled(actionStates.docx)}
                onClick={() => onDownloadDocx(note)}
              >
                {actionStates.docx ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                Word
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={actionDisabled(actionStates.txt)}
                onClick={() => onDownloadTxt(note)}
              >
                {actionStates.txt ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                TXT
              </Button>
            </div>
          </div>
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Save to Google Drive</h4>
            <div className="flex flex-wrap items-center gap-3">
              <Select
                value={driveFormat}
                onValueChange={(value) => setDriveFormat(value as 'pdf' | 'docx' | 'txt')}
                disabled={!isCompleted || actionStates.drive}
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Format" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="docx">Word</SelectItem>
                  <SelectItem value="txt">TXT</SelectItem>
                </SelectContent>
              </Select>
              <Button
                size="sm"
                onClick={() => onUploadToDrive(note, driveFormat)}
                disabled={actionDisabled(actionStates.drive)}
              >
                {actionStates.drive ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Cloud className="w-4 h-4 mr-2" />}
                Add to Google Drive
              </Button>
            </div>
          </div>

          <div className="space-y-2 border-t pt-4">
            <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <svg className="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Flashcards
            </h4>
            {flashcardError && (
              <p className="text-xs text-red-600">{flashcardError}</p>
            )}
            <FlashcardDeck
              cards={flashcards}
              onDeleteCard={handleFlashcardDelete}
              compact
              emptyLabel="No flashcards yet. Generate them by enabling the option during customization or add manual ones below."
            />
            <form onSubmit={handleFlashcardSubmit} className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <input
                type="text"
                placeholder="Topic"
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                value={flashcardForm.topic}
                onChange={(e) => handleFlashcardInputChange('topic', e.target.value)}
                disabled={flashcardsBusy}
              />
              <input
                type="text"
                placeholder="Term"
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                value={flashcardForm.term}
                onChange={(e) => handleFlashcardInputChange('term', e.target.value)}
                disabled={flashcardsBusy}
              />
              <textarea
                placeholder="Definition"
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm sm:col-span-2"
                rows={2}
                value={flashcardForm.definition}
                onChange={(e) => handleFlashcardInputChange('definition', e.target.value)}
                disabled={flashcardsBusy}
              />
              <div className="flex items-end">
                <Button
                  type="submit"
                  size="sm"
                  className="w-full"
                  disabled={flashcardsBusy || !flashcardForm.topic || !flashcardForm.term || !flashcardForm.definition}
                >
                  Add Flashcard
                </Button>
              </div>
            </form>
          </div>
          <div className="flex flex-wrap gap-1">
            {note.settings.add_bullet_points && (
              <Badge variant="secondary" className="text-xs">Bullet Points</Badge>
            )}
            {note.settings.add_headers && (
              <Badge variant="secondary" className="text-xs">Headers</Badge>
            )}
            {note.settings.expand && (
              <Badge variant="secondary" className="text-xs">Expand</Badge>
            )}
            {note.settings.summarize && (
              <Badge variant="secondary" className="text-xs">Summarize</Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
