import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Upload, Type } from 'lucide-react';

interface NoteUploadStepProps {
  notes: string;
  onNotesChange: (notes: string) => void;
  onNext: () => void;
  uploadMode: 'text' | 'image';
  onUploadModeChange: (mode: 'text' | 'image') => void;
}

export function NoteUploadStep({ 
  notes, 
  onNotesChange, 
  onNext, 
  uploadMode, 
  onUploadModeChange 
}: NoteUploadStepProps) {
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // In a real app, this would process the image and extract text
      onNotesChange(`[Image uploaded: ${file.name}] - Text will be extracted automatically`);
    }
  };

  const canProceed = notes.trim().length > 0;

  return (
    <Card className="w-full mx-auto bg-white/80 backdrop-blur-sm border-orange-200/50 shadow-lg">
      <CardHeader>
        <CardTitle>Upload Your Notes</CardTitle>
        <CardDescription>
          Start by uploading an image of your notes or entering them manually
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Button
            variant={uploadMode === 'text' ? 'default' : 'outline'}
            onClick={() => onUploadModeChange('text')}
            className="h-12"
          >
            <Type className="w-4 h-4 mr-2" />
            Manual Entry
          </Button>
          <Button
            variant={uploadMode === 'image' ? 'default' : 'outline'}
            onClick={() => onUploadModeChange('image')}
            className="h-12"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Image
          </Button>
        </div>

        {uploadMode === 'text' ? (
          <div className="space-y-2">
            <Label htmlFor="notes">Enter your notes</Label>
            <Textarea
              id="notes"
              placeholder="Type or paste your notes here..."
              value={notes}
              onChange={(e) => onNotesChange(e.target.value)}
              className="min-h-[200px] resize-none"
            />
          </div>
        ) : (
          <div className="space-y-4">
            <Label>Upload image of your notes</Label>
            <div className="border-2 border-dashed border-orange-200 rounded-lg p-8 text-center bg-orange-50/30">
              <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <div className="space-y-2">
                <p>Click to upload or drag and drop</p>
                <p className="text-sm text-muted-foreground">
                  PNG, JPG, or PDF up to 10MB
                </p>
              </div>
              <input
                type="file"
                accept="image/*,.pdf"
                onChange={handleFileUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>
            {notes && (
              <div className="p-4 bg-muted rounded-lg">
                <Label>Extracted text preview:</Label>
                <p className="mt-2 text-sm">{notes}</p>
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end">
          <Button 
            onClick={onNext} 
            disabled={!canProceed}
            className="px-8"
          >
            Next Step
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}