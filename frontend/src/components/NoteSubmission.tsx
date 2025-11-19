import React, { useState, useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { NoteUploadStep } from './NoteUploadStep';
import { NoteConfigStep } from './NoteConfigStep';
import { ProcessingResult } from './ProcessingResult';
import { ErrorDisplay } from './ErrorDisplay';
import { ProcessingConfig, defaultConfig } from '../types/config';
import { createNote, uploadImageNote, uploadMultipleImages, pollNoteStatus, NoteResponse } from '../services/apiService';
import { Button } from './ui/button';

type Step = 'upload' | 'config' | 'result';

export const NoteSubmission: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [notes, setNotes] = useState('');
  const [uploadMode, setUploadMode] = useState<'text' | 'image'>('image'); // Default to image
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [config, setConfig] = useState<ProcessingConfig>(defaultConfig);
  const [processedNotes, setProcessedNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<string>('');
  const [currentNote, setCurrentNote] = useState<NoteResponse | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<number | null>(null);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [remainingTime, setRemainingTime] = useState<number | null>(null);

  // Real-time countdown timer
  useEffect(() => {
    if (!isProcessing || !startTime || !estimatedTime) {
      setRemainingTime(null);
      return;
    }

    const updateRemainingTime = () => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const remaining = Math.max(0, estimatedTime - elapsed);
      setRemainingTime(remaining);
    };

    // Update immediately
    updateRemainingTime();

    // Update every second
    const interval = setInterval(updateRemainingTime, 1000);

    return () => clearInterval(interval);
  }, [isProcessing, startTime, estimatedTime]);

  const getStepProgress = () => {
    switch (currentStep) {
      case 'upload': return 33;
      case 'config': return 66;
      case 'result': return 100;
      default: return 0;
    }
  };

  const handleNext = () => {
    setCurrentStep('config');
  };

  const handleBack = () => {
    setCurrentStep('upload');
  };

  const handleSubmit = async () => {
    // Validate input based on upload mode
    if (uploadMode === 'text' && !notes.trim()) {
      setError('Please enter some text to process');
      return;
    }
    
    if (uploadMode === 'image' && selectedFiles.length === 0) {
      setError('Please select at least one image file to process');
      return;
    }

  let patienceTimer: ReturnType<typeof setTimeout> | null = null;

  try {
      setIsProcessing(true);
      setError(null);
      setStartTime(Date.now());

      // Estimate processing time based on content (more generous for large payloads)
      let computedEstimateSeconds: number;
      if (uploadMode === 'image') {
        const perImage = selectedFiles.length > 1 ? 70 : 55;
        computedEstimateSeconds = Math.min(300, Math.max(60, perImage * Math.max(1, selectedFiles.length)));
      } else {
        const wordCount = notes.trim().split(/\s+/).length;
        computedEstimateSeconds = Math.min(240, Math.max(45, Math.ceil(wordCount / 35)));
      }
      setEstimatedTime(computedEstimateSeconds);

      const pollTimeoutMs = uploadMode === 'image'
        ? Math.min(12 * 60 * 1000, (computedEstimateSeconds + selectedFiles.length * 90) * 1000)
        : Math.min(10 * 60 * 1000, (computedEstimateSeconds + 180) * 1000);

      patienceTimer = window.setTimeout(() => {
        setProcessingStatus((prev) =>
          prev && prev.toLowerCase().includes('still working')
            ? prev
            : 'Still working... large uploads may take a few minutes. Please keep this page open.'
        );
      }, Math.min(90_000, pollTimeoutMs * 0.3));
      
      let noteResponse: NoteResponse;
      
      if (uploadMode === 'image' && selectedFiles.length > 0) {
        if (selectedFiles.length === 1) {
          // Single image - use the original endpoint
          setProcessingStatus('Uploading image...');
          noteResponse = await uploadImageNote(selectedFiles[0], config);
          setProcessingStatus('Extracting text from image...');
        } else {
          // Multiple images - use the new endpoint
          setProcessingStatus(`Uploading ${selectedFiles.length} images...`);
          noteResponse = await uploadMultipleImages(selectedFiles, config);
          setProcessingStatus('Processing images with GPT-4 Vision...');
        }
        
      } else {
        setProcessingStatus('Creating note...');
        
        // Create text note
        noteResponse = await createNote({
          text: notes,
          settings: config
        });
        setProcessingStatus('Processing with ChatGPT...');
      }
      
      setCurrentNote(noteResponse);
      
      // Poll for completion
      const completedNote = await pollNoteStatus(
        noteResponse.id,
        (updatedNote) => {
          setCurrentNote(updatedNote);
          // Use progress_message from backend if available, otherwise fall back to default messages
          if (updatedNote.status === 'processing') {
            const message = updatedNote.progress_message || 
              (uploadMode === 'image' 
                ? selectedFiles.length > 1
                  ? 'Processing multiple images with GPT-4 Vision...'
                  : 'Processing with OCR and ChatGPT...'
                : 'Processing with ChatGPT...');
            setProcessingStatus(message);
          }
        },
        {
          timeoutMs: pollTimeoutMs,
          intervalMs: uploadMode === 'image' ? 1500 : 1100,
          onTimeout: () => {
            setProcessingStatus('Processing timed out before completion. Please try again or split the upload into smaller batches.');
          },
        }
      );
      
      if (completedNote.status === 'completed' && completedNote.processed_content) {
        setProcessedNotes(completedNote.processed_content);
        // For image notes, also update the extracted text
        if (uploadMode === 'image' && completedNote.text) {
          setNotes(completedNote.text);
        }
        setCurrentStep('result');
        setProcessingStatus('');
      } else if (completedNote.status === 'error') {
        throw new Error('Processing failed on the server');
      }
      
      if (patienceTimer) {
        clearTimeout(patienceTimer);
        patienceTimer = null;
      }
    } catch (error) {
      console.error('Error processing note:', error);
      setError(error instanceof Error ? error.message : 'An error occurred while processing your content');
      setProcessingStatus('');
      setEstimatedTime(null);
      setStartTime(null);

      if (patienceTimer) {
        clearTimeout(patienceTimer);
        patienceTimer = null;
      }
    } finally {
      if (patienceTimer) {
        clearTimeout(patienceTimer);
      }
      setIsProcessing(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    handleSubmit();
  };

  const handleStartOver = () => {
    setCurrentStep('upload');
    setNotes('');
    setUploadMode('image');
    setSelectedFiles([]);
    setConfig(defaultConfig);
    setProcessedNotes('');
    setError(null);
    setCurrentNote(null);
    setProcessingStatus('');
    setEstimatedTime(null);
    setStartTime(null);
    setRemainingTime(null);
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-rose-50 p-4">
      <div className="container mx-auto py-8 space-y-8 max-w-4xl">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={handleBackToDashboard}
              className="flex items-center text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </div>
          <div className="text-center space-y-4">
            <h1 className="text-3xl font-bold text-gray-900">Note Embellisher</h1>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Transform your notes with AI-powered enhancements. Upload images or enter text, 
              then choose how you want your notes organized and improved.
            </p>
          </div>
        </div>

        {/* Progress indicator */}
        <div className="max-w-md mx-auto space-y-2">
          <div className="flex justify-between text-sm font-medium">
            <span className={currentStep === 'upload' ? 'text-orange-700' : 'text-gray-400'}>
              Upload Notes
            </span>
            <span className={currentStep === 'config' ? 'text-orange-700' : 'text-gray-400'}>
              Configure
            </span>
            <span className={currentStep === 'result' ? 'text-orange-700' : 'text-gray-400'}>
              Results
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-orange-400 to-amber-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${getStepProgress()}%` }}
            ></div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6">
            <ErrorDisplay error={error} onRetry={handleRetry} />
          </div>
        )}

        {/* Processing Status with Progress Bar */}
        {isProcessing && processingStatus && (
          <div className="mb-6 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-lg p-6 shadow-sm">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="relative mr-3">
                    <div className="w-5 h-5 border-2 border-amber-300 border-t-amber-600 rounded-full animate-spin"></div>
                  </div>
                  <span className="text-amber-800 font-medium">{processingStatus}</span>
                </div>
                <div className="flex items-center gap-2">
                  {currentNote && (
                    <span className="text-sm text-amber-700 font-semibold">
                      {currentNote.progress || 0}%
                    </span>
                  )}
                  {remainingTime !== null && (
                    <span className="text-xs text-amber-600 bg-amber-100 px-2 py-1 rounded">
                      ~{remainingTime}s remaining
                    </span>
                  )}
                </div>
              </div>
              {/* Progress bar */}
              {currentNote && (
                <div className="w-full bg-amber-100 rounded-full h-3 overflow-hidden shadow-inner">
                  <div 
                    className="bg-gradient-to-r from-amber-400 via-orange-400 to-amber-500 h-3 rounded-full transition-all duration-500 ease-out shadow-sm"
                    style={{ width: `${currentNote.progress || 0}%` }}
                  >
                    <div className="w-full h-full animate-pulse opacity-30 bg-white"></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step content */}
        <div className="w-full">
          {currentStep === 'upload' && (
            <NoteUploadStep
              notes={notes}
              onNotesChange={setNotes}
              onNext={handleNext}
              uploadMode={uploadMode}
              onUploadModeChange={setUploadMode}
              onFilesSelect={setSelectedFiles}
            />
          )}

          {currentStep === 'config' && (
            <NoteConfigStep
              config={config}
              onConfigChange={setConfig}
              onBack={handleBack}
              onNext={handleSubmit}
              isProcessing={isProcessing}
              noteText={notes}
            />
          )}

          {currentStep === 'result' && (
            <ProcessingResult
              originalNotes={notes}
              processedNotes={processedNotes}
              noteId={currentNote?.id}
              initialPdfUrl={currentNote?.pdf_url || undefined}
              initialFlashcards={currentNote?.flashcards || []}
              onStartOver={handleStartOver}
            />
          )}
        </div>
      </div>
    </div>
  );
};
