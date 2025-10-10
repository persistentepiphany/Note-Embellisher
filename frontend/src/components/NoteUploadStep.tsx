import React from 'react';

interface NoteUploadStepProps {
  notes: string;
  onNotesChange: (notes: string) => void;
  onNext: () => void;
  uploadMode: 'text' | 'image';
  onUploadModeChange: (mode: 'text' | 'image') => void;
}

export const NoteUploadStep: React.FC<NoteUploadStepProps> = ({ 
  notes, 
  onNotesChange, 
  onNext,
  uploadMode,
  onUploadModeChange
}) => {
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // In a real app, this would process the image and extract text
      onNotesChange(`[Image uploaded: ${file.name}] - Text will be extracted automatically`);
    }
  };

  const canProceed = notes.trim().length > 0;

  return (
    <div className="w-full mx-auto bg-white/80 backdrop-blur-sm border-orange-200/50 border rounded-xl shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Your Notes</h2>
        <p className="text-gray-600">
          Start by uploading an image of your notes or entering them manually
        </p>
      </div>

      <div className="space-y-6">
        {/* Mode Selection */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            onClick={() => onUploadModeChange('text')}
            className={`h-12 px-4 rounded-lg border-2 font-medium transition-all duration-200 flex items-center justify-center space-x-2 ${
              uploadMode === 'text' 
                ? 'bg-orange-100 border-orange-300 text-orange-700' 
                : 'bg-white border-orange-200 text-gray-600 hover:border-orange-300 hover:bg-orange-50'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Manual Entry</span>
          </button>
          <button
            onClick={() => onUploadModeChange('image')}
            className={`h-12 px-4 rounded-lg border-2 font-medium transition-all duration-200 flex items-center justify-center space-x-2 ${
              uploadMode === 'image' 
                ? 'bg-orange-100 border-orange-300 text-orange-700' 
                : 'bg-white border-orange-200 text-gray-600 hover:border-orange-300 hover:bg-orange-50'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span>Upload Image</span>
          </button>
        </div>

        {uploadMode === 'text' ? (
          <div className="space-y-2">
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
              Enter your notes
            </label>
            <textarea
              id="notes"
              placeholder="Type or paste your notes here..."
              value={notes}
              onChange={(e) => onNotesChange(e.target.value)}
              className="w-full min-h-[200px] p-3 border border-orange-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 resize-none bg-white/70 backdrop-blur-sm"
            />
          </div>
        ) : (
          <div className="space-y-4">
            <label className="block text-sm font-medium text-gray-700">
              Upload image of your notes
            </label>
            <div className="border-2 border-dashed border-orange-200 rounded-lg p-8 text-center bg-orange-50/30 relative hover:bg-orange-50/50 transition-colors">
              <svg className="w-12 h-12 mx-auto mb-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <div className="space-y-2">
                <p className="text-gray-600">Click to upload or drag and drop</p>
                <p className="text-sm text-gray-500">
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
              <div className="p-4 bg-amber-50/70 rounded-lg border border-amber-200">
                <label className="block text-sm font-medium text-amber-800 mb-2">Extracted text preview:</label>
                <p className="text-sm text-amber-700">{notes}</p>
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end">
          <button 
            onClick={onNext} 
            disabled={!canProceed}
            className="px-8 py-2 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-lg hover:from-orange-600 hover:to-amber-600 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 font-medium transition-all duration-200"
          >
            Next Step
          </button>
        </div>
      </div>
    </div>
  );
};