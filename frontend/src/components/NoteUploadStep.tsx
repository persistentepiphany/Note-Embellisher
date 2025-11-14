import React, { useState } from 'react';

interface NoteUploadStepProps {
  notes: string;
  onNotesChange: (notes: string) => void;
  onNext: () => void;
  uploadMode: 'text' | 'image';
  onUploadModeChange: (mode: 'text' | 'image') => void;
  onFilesSelect?: (files: File[]) => void;
}

interface FileValidationResult {
  isValid: boolean;
  error?: string;
}

export const NoteUploadStep: React.FC<NoteUploadStepProps> = ({ 
  notes, 
  onNotesChange, 
  onNext,
  uploadMode,
  onUploadModeChange,
  onFilesSelect
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  const MAX_FILES = 5;

  const validateFile = (file: File): FileValidationResult => {
    // Check file size (10MB max)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
      return { isValid: false, error: 'File size must be less than 10MB' };
    }

    // Check file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
      return { isValid: false, error: 'Only PNG, JPG, JPEG, and PDF files are allowed' };
    }

    // Check file extension as additional validation
    const allowedExtensions = ['.png', '.jpg', '.jpeg', '.pdf'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedExtensions.includes(fileExtension)) {
      return { isValid: false, error: 'Only PNG, JPG, JPEG, and PDF files are allowed' };
    }

    return { isValid: true };
  };

  const handleFileSelection = (files: FileList) => {
    const fileArray = Array.from(files);
    
    // Check if adding these files would exceed the limit
    if (selectedFiles.length + fileArray.length > MAX_FILES) {
      setFileError(`You can only upload up to ${MAX_FILES} images at once`);
      return;
    }

    // Validate all files
    const validFiles: File[] = [];
    for (const file of fileArray) {
      const validation = validateFile(file);
      if (!validation.isValid) {
        setFileError(validation.error || 'Invalid file');
        return;
      }
      validFiles.push(file);
    }

    // Add to selected files
    const newFiles = [...selectedFiles, ...validFiles];
    setFileError(null);
    setSelectedFiles(newFiles);
    
    // Update notes display
    const totalSize = newFiles.reduce((sum, f) => sum + f.size, 0);
    onNotesChange(
      `Selected ${newFiles.length} file(s): ${newFiles.map(f => f.name).join(', ')} (Total: ${(totalSize / 1024 / 1024).toFixed(2)} MB)`
    );
    
    // Notify parent component about file selection
    if (onFilesSelect) {
      onFilesSelect(newFiles);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      handleFileSelection(files);
    }
    // Reset input so same file can be selected again
    event.target.value = '';
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelection(files);
    }
  };

  const removeFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
    
    if (newFiles.length === 0) {
      onNotesChange('');
      if (onFilesSelect) {
        onFilesSelect([]);
      }
    } else {
      const totalSize = newFiles.reduce((sum, f) => sum + f.size, 0);
      onNotesChange(
        `Selected ${newFiles.length} file(s): ${newFiles.map(f => f.name).join(', ')} (Total: ${(totalSize / 1024 / 1024).toFixed(2)} MB)`
      );
      if (onFilesSelect) {
        onFilesSelect(newFiles);
      }
    }
    setFileError(null);
  };

  const clearAllFiles = () => {
    setSelectedFiles([]);
    onNotesChange('');
    setFileError(null);
    if (onFilesSelect) {
      onFilesSelect([]);
    }
  };

  const canProceed = uploadMode === 'text' ? notes.trim().length > 0 : selectedFiles.length > 0;

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
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700">
                Upload images of your notes (up to {MAX_FILES})
              </label>
              {selectedFiles.length > 0 && (
                <span className="text-sm text-orange-600 font-medium">
                  {selectedFiles.length} / {MAX_FILES} files
                </span>
              )}
            </div>
            
            <div 
              className={`border-2 border-dashed rounded-lg p-8 text-center relative transition-all duration-200 ${
                isDragOver 
                  ? 'border-orange-400 bg-orange-100/50' 
                  : selectedFiles.length > 0
                    ? 'border-green-300 bg-green-50/30'
                    : 'border-orange-200 bg-orange-50/30 hover:bg-orange-50/50'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {selectedFiles.length > 0 ? (
                <div className="space-y-3">
                  <svg className="w-12 h-12 mx-auto text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="space-y-1">
                    <p className="text-green-700 font-medium">
                      {selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} selected
                    </p>
                    <p className="text-sm text-green-600">
                      {(selectedFiles.reduce((sum, f) => sum + f.size, 0) / 1024 / 1024).toFixed(2)} MB total • Ready to process
                    </p>
                  </div>
                  <div className="flex gap-2 justify-center">
                    {selectedFiles.length < MAX_FILES && (
                      <label className="text-sm text-orange-600 hover:text-orange-700 underline cursor-pointer">
                        Add more files
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/jpg,application/pdf"
                          onChange={handleFileUpload}
                          multiple
                          className="hidden"
                        />
                      </label>
                    )}
                    <button
                      onClick={clearAllFiles}
                      className="text-sm text-red-600 hover:text-red-700 underline"
                    >
                      Clear all
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <svg className="w-12 h-12 mx-auto mb-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <div className="space-y-2">
                    <p className="text-gray-600">
                      {isDragOver ? 'Drop your files here' : 'Click to upload or drag and drop'}
                    </p>
                    <p className="text-sm text-gray-500">
                      PNG, JPG, JPEG, or PDF up to 10MB each
                    </p>
                    <p className="text-xs text-gray-400">
                      Upload up to {MAX_FILES} images at once
                    </p>
                  </div>
                </>
              )}
              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg,application/pdf"
                onChange={handleFileUpload}
                multiple
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>
            
            {fileError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{fileError}</p>
              </div>
            )}
            
            {selectedFiles.length > 0 && (
              <div className="space-y-3">
                <div className="p-4 bg-amber-50/70 rounded-lg border border-amber-200">
                  <label className="block text-sm font-medium text-amber-800 mb-2">
                    Selected files ({selectedFiles.length}):
                  </label>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {selectedFiles.map((file, index) => (
                      <div 
                        key={index}
                        className="flex items-center justify-between p-2 bg-white/70 rounded border border-amber-200"
                      >
                        <div className="flex items-center space-x-2 flex-1 min-w-0">
                          <svg className="w-4 h-4 text-amber-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-amber-900 truncate">{file.name}</p>
                            <p className="text-xs text-amber-600">
                              {(file.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => removeFile(index)}
                          className="ml-2 p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded flex-shrink-0"
                          title="Remove file"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-amber-600 mt-3">
                    {selectedFiles.length > 1 
                      ? 'All images will be processed together using GPT-4 Vision for accurate handwriting recognition and enhancement'
                      : 'Image will be processed using GPT-4 Vision for handwriting recognition and enhancement'
                    }
                  </p>
                </div>
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