import React from 'react';
import { ProcessingConfig } from '../types/config';

interface NoteConfigStepProps {
  config: ProcessingConfig;
  onConfigChange: (config: ProcessingConfig) => void;
  onBack: () => void;
  onNext: () => void;
  isProcessing?: boolean;
}

export const NoteConfigStep: React.FC<NoteConfigStepProps> = ({ 
  config, 
  onConfigChange, 
  onBack, 
  onNext,
  isProcessing = false 
}) => {
  const handleConfigChange = (key: keyof ProcessingConfig, value: boolean) => {
    onConfigChange({
      ...config,
      [key]: value,
    });
  };

  const hasProcessingOption = Object.values(config).some(Boolean);

  return (
    <div className="w-full mx-auto bg-white/80 backdrop-blur-sm border-orange-200/50 border rounded-xl shadow-lg p-6">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.828 2.828A4 4 0 019.172 21H7l-4-4h2.828a4 4 0 001.414-.586l.828-.828A4 4 0 016.586 10H4l4-4z" />
          </svg>
          <h2 className="text-2xl font-bold text-gray-900">Configure Your Notes</h2>
        </div>
        <p className="text-gray-600">
          Choose how you want your notes enhanced
        </p>
      </div>
      
      <div className="space-y-4 mb-6">
        <p className="text-sm font-medium text-gray-700">Processing Options (choose at least one)</p>
        
        {[
          { 
            key: 'add_bullet_points', 
            label: 'Add Bullet Points', 
            description: 'Format content with bullet points for better readability and organization',
            icon: (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v6a2 2 0 002 2h2m9-9h2a2 2 0 012 2v6a2 2 0 01-2 2h-2m-9-9V7a2 2 0 012-2h2m-2 9v2a2 2 0 002 2h2" />
              </svg>
            )
          },
          { 
            key: 'add_headers', 
            label: 'Add Headers', 
            description: 'Add clear headers and subheaders to organize content into logical sections',
            icon: (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
              </svg>
            )
          },
          { 
            key: 'expand', 
            label: 'Expand Content', 
            description: 'Elaborate with more details, explanations, and context',
            icon: (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            )
          },
          { 
            key: 'summarize', 
            label: 'Summarize', 
            description: 'Provide a concise summary of main points while maintaining key information',
            icon: (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )
          }
        ].map((option) => (
          <div 
            key={option.key} 
            className="flex items-start space-x-3 p-4 border border-orange-200/50 rounded-lg bg-orange-50/30 hover:bg-orange-50/50 transition-all duration-200"
          >
            <input
              id={option.key}
              type="checkbox"
              checked={config[option.key as keyof ProcessingConfig]}
              onChange={(e) => handleConfigChange(option.key as keyof ProcessingConfig, e.target.checked)}
              disabled={isProcessing}
              className="h-4 w-4 text-orange-600 focus:ring-orange-500 border-orange-300 rounded disabled:opacity-50 mt-1"
            />
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <div className="text-orange-600">
                  {option.icon}
                </div>
                <label htmlFor={option.key} className="text-sm font-medium text-gray-900 cursor-pointer">
                  {option.label}
                </label>
              </div>
              <p className="text-xs text-gray-600">
                {option.description}
              </p>
            </div>
          </div>
        ))}
        
        {!hasProcessingOption && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
            Please select at least one processing option
          </p>
        )}
      </div>

      <div className="flex justify-between pt-4">
        <button
          onClick={onBack}
          disabled={isProcessing}
          className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-300 transition-colors duration-200 flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back</span>
        </button>
        
        <button
          onClick={onNext}
          disabled={isProcessing || !hasProcessingOption}
          className="px-8 py-2 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-lg hover:from-orange-600 hover:to-amber-600 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 font-medium transition-all duration-200 flex items-center space-x-2"
        >
          {isProcessing ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Processing...</span>
            </>
          ) : (
            <>
              <span>Enhance Notes</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.828 2.828A4 4 0 019.172 21H7l-4-4h2.828a4 4 0 001.414-.586l.828-.828A4 4 0 006.586 10H4l4-4z" />
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  );
};