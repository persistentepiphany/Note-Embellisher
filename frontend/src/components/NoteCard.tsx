import React from 'react';
import { Download, Trash2, Clock, FileText } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { FormattedContent } from './FormattedContent';
import { NoteResponse } from '../services/apiService';

interface NoteCardProps {
  note: NoteResponse;
  onDownload: (note: NoteResponse) => void;
  onExportPDF: (note: NoteResponse) => void;
  onDelete: (noteId: number) => void;
}

export const NoteCard: React.FC<NoteCardProps> = ({
  note,
  onDownload,
  onExportPDF,
  onDelete,
}) => {
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
              onClick={() => onDownload(note)}
              className="h-8 w-8 p-0"
              title="Download TXT"
            >
              <Download className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onExportPDF(note)}
              className="h-8 w-8 p-0"
              title="Generate LaTeX PDF (professional formatting)"
              disabled={note.status !== 'completed'}
            >
              <FileText className="h-4 w-4" />
            </Button>
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