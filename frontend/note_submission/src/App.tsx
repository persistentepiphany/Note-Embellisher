import React, { useState } from 'react';
import { NoteUploadStep } from './components/NoteUploadStep';
import { NoteConfigStep } from './components/NoteConfigStep';
import { ProcessingResult } from './components/ProcessingResult';
import { Progress } from './components/ui/progress';

type Step = 'upload' | 'config' | 'result';

interface NoteConfig {
  subject: string;
  date: string;
  flair: string;
  title: string;
  description: string;
  processingOptions: {
    summarize: boolean;
    expand: boolean;
    addHeaders: boolean;
    addBulletPoints: boolean;
  };
}

export default function App() {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [notes, setNotes] = useState('');
  const [uploadMode, setUploadMode] = useState<'text' | 'image'>('text');
  const [config, setConfig] = useState<NoteConfig>({
    subject: '',
    date: new Date().toISOString().split('T')[0],
    flair: '',
    title: '',
    description: '',
    processingOptions: {
      summarize: false,
      expand: false,
      addHeaders: false,
      addBulletPoints: false,
    },
  });

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

  const handleSubmit = () => {
    // In a real app, this would send data to backend for processing
    setCurrentStep('result');
  };

  const handleStartOver = () => {
    setCurrentStep('upload');
    setNotes('');
    setConfig({
      subject: '',
      date: new Date().toISOString().split('T')[0],
      flair: '',
      title: '',
      description: '',
      processingOptions: {
        summarize: false,
        expand: false,
        addHeaders: false,
        addBulletPoints: false,
      },
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="container mx-auto py-8 space-y-8">
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
            <span className={currentStep === 'upload' ? 'text-primary' : 'text-muted-foreground'}>
              Upload Notes
            </span>
            <span className={currentStep === 'config' ? 'text-primary' : 'text-muted-foreground'}>
              Configure
            </span>
            <span className={currentStep === 'result' ? 'text-primary' : 'text-muted-foreground'}>
              Results
            </span>
          </div>
          <Progress value={getStepProgress()} className="h-2" />
        </div>

        {/* Step content */}
        <div className="flex justify-center">
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
              onSubmit={handleSubmit}
            />
          )}

          {currentStep === 'result' && (
            <ProcessingResult
              config={config}
              originalNotes={notes}
              onStartOver={handleStartOver}
            />
          )}
        </div>
      </div>
    </div>
  );
}