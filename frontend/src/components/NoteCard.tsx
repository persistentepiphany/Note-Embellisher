import React, { useState } from 'react';
import { Download, Trash2, Clock, FileText, Loader2, Cloud, ExternalLink, Image as ImageIcon } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { FormattedContent } from './FormattedContent';
import { NoteResponse } from '../services/apiService';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

interface NoteCardProps {
  note: NoteResponse;
  apiBaseUrl: string;
  onDownloadPdf: (note: NoteResponse) => Promise<void>;
  onDownloadDocx: (note: NoteResponse) => Promise<void>;
  onDownloadTxt: (note: NoteResponse) => Promise<void>;
  onUploadToDrive: (note: NoteResponse, format: 'pdf' | 'docx' | 'txt') => Promise<void>;
  onDelete: (noteId: number) => void;
  actionStates: {
    pdf: boolean;
    docx: boolean;
    txt: boolean;
    drive: boolean;
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
  actionStates,
}) => {
  const [driveFormat, setDriveFormat] = useState<'pdf' | 'docx' | 'txt'>('pdf');
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

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Note #{note.id}</CardTitle>
          <div className="flex items-center space-x-2">
            <Badge className={getStatusColor(note.status)}>
              {note.status === 'processing' && <Clock className="w-3 h-3 mr-1 animate-spin" />}
              {note.status}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (window.confirm(`Are you sure you want to delete Note #${note.id}? This action cannot be undone.`)) {
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
        <CardDescription className="text-sm text-gray-500">
          Created {formatDate(note.created_at)}
        </CardDescription>
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