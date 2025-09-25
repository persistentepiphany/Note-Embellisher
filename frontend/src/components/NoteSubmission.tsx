import React, { useState } from 'react';
import { NoteUploadStep } from './NoteUploadStep';
import { NoteConfigStep } from './NoteConfigStep';
import { ProcessingResult } from './ProcessingResult';
import { ErrorDisplay } from './ErrorDisplay';
import { ProcessingConfig, defaultConfig } from '../types/config';
import { createNote, pollNoteStatus, NoteResponse } from '../services/apiService';

type Step = 'upload' | 'config' | 'result';

export const NoteSubmission: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [notes, setNotes] = useState('');
  const [uploadMode, setUploadMode] = useState<'text' | 'image'>('text');
  const [config, setConfig] = useState<ProcessingConfig>(defaultConfig);
  const [processedNotes, setProcessedNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<string>('');
  const [currentNote, setCurrentNote] = useState<NoteResponse | null>(null);

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
    if (!notes.trim()) {
      setError('Please enter some text to process');
      return;
    }

    try {
      setIsProcessing(true);
      setError(null);
      setProcessingStatus('Creating note...');
      
      // Create note with backend
      const noteResponse = await createNote({
        text: notes,
        settings: config
      });
      
      setCurrentNote(noteResponse);
      setProcessingStatus('Processing with ChatGPT...');
      
      // Poll for completion
      const completedNote = await pollNoteStatus(
        noteResponse.id,
        (updatedNote) => {
          setCurrentNote(updatedNote);
          if (updatedNote.status === 'processing') {
            setProcessingStatus('Processing with ChatGPT...');
          }
        }
      );
      
      if (completedNote.status === 'completed' && completedNote.processed_content) {
        setProcessedNotes(completedNote.processed_content);
        setCurrentStep('result');
        setProcessingStatus('');
      } else if (completedNote.status === 'error') {
        throw new Error('Processing failed on the server');
      }
      
    } catch (error) {
      console.error('Error processing note:', error);
      setError(error instanceof Error ? error.message : 'An error occurred while processing your text');
      setProcessingStatus('');
    } finally {
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
    setUploadMode('text');
    setConfig(defaultConfig);
    setProcessedNotes('');
    setError(null);
    setCurrentNote(null);
    setProcessingStatus('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-rose-50 p-4">
      <div className="container mx-auto py-8 space-y-8 max-w-4xl">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-3xl font-bold text-gray-900">Note Embellisher</h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Transform your notes with AI-powered enhancements. Upload images or enter text, 
            then choose how you want your notes organized and improved.
          </p>
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

        {/* Processing Status */}
        {isProcessing && processingStatus && (
          <div className="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="relative">
                <div className="w-5 h-5 border-2 border-amber-200 border-t-amber-500 rounded-full animate-spin mr-3"></div>
              </div>
              <span className="text-amber-700">{processingStatus}</span>
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
            />
          )}

          {currentStep === 'config' && (
            <NoteConfigStep
              config={config}
              onConfigChange={setConfig}
              onBack={handleBack}
              onNext={handleSubmit}
              isProcessing={isProcessing}
            />
          )}

          {currentStep === 'result' && (
            <ProcessingResult
              originalNotes={notes}
              processedNotes={processedNotes}
              onStartOver={handleStartOver}
            />
          )}
        </div>
      </div>
    </div>
  );
};