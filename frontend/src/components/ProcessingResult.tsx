import React, { useState, useEffect } from 'react';

interface ProcessingResultProps {
  originalNotes: string;
  processedNotes: string;
  onStartOver: () => void;
}

export const ProcessingResult: React.FC<ProcessingResultProps> = ({
  originalNotes,
  processedNotes,
  onStartOver,
}) => {
  const [showContent, setShowContent] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  useEffect(() => {
    // Trigger the fade-in animation
    const timer = setTimeout(() => setShowContent(true), 300);
    return () => clearTimeout(timer);
  }, []);

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const handleExportPDF = () => {
    // Mock PDF export
    alert('Exporting to PDF... (This would integrate with a PDF generation service)');
  };

  const handleExportWord = () => {
    // Mock Word export
    alert('Exporting to Word... (This would generate a .docx file)');
  };

  const handleConnectGoogleDrive = () => {
    // Mock Google Drive connection
    alert('Connecting to Google Drive... (This would integrate with Google Drive API)');
  };

  return (
    <div className="w-full mx-auto bg-white/80 backdrop-blur-sm border-green-200/50 border rounded-xl shadow-lg p-6">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
          </svg>
          <h2 className="text-2xl font-bold text-gray-900">Notes Enhanced Successfully!</h2>
        </div>
        <p className="text-gray-600">
          Your notes have been processed with the selected enhancements
        </p>
      </div>

      {/* Original vs Enhanced */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="space-y-3">
          <h3 className="text-lg font-medium text-slate-700">Original Notes</h3>
          <div className="p-4 bg-slate-50 rounded-lg max-h-80 overflow-y-auto border border-slate-200">
            <pre className="whitespace-pre-wrap text-sm text-slate-600">{originalNotes}</pre>
          </div>
        </div>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-green-800">Enhanced Notes</h3>
            <button
              onClick={() => copyToClipboard(processedNotes)}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-all duration-200 ${
                copySuccess 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-orange-100 text-orange-700 hover:bg-orange-200'
              }`}
            >
              {copySuccess ? '✓ Copied!' : 'Copy'}
            </button>
          </div>
          <div 
            className={`p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg max-h-80 overflow-y-auto border border-green-200 transition-all duration-1000 ${
              showContent 
                ? 'opacity-100 blur-none transform translate-y-0' 
                : 'opacity-0 blur-sm transform translate-y-2'
            }`}
          >
            <pre className="whitespace-pre-wrap text-sm text-green-800">{processedNotes}</pre>
          </div>
        </div>
      </div>

      {/* Export Options */}
      <div className="space-y-4 mb-6">
        <h4 className="text-lg font-medium text-slate-700">Export & Share Options</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <button 
            onClick={handleExportPDF} 
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Export to PDF</span>
          </button>
          <button 
            onClick={handleExportWord}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Export to Word</span>
          </button>
          <button 
            onClick={handleConnectGoogleDrive}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 12l2 2 4-4" />
            </svg>
            <span>Save to Drive</span>
          </button>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3 pt-4 border-t border-green-200 justify-between">
        <div className="flex gap-3">
          <button className="border border-orange-200 text-orange-700 hover:bg-orange-50 px-4 py-2 rounded-lg transition-colors duration-200 flex items-center space-x-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span>Download All</span>
          </button>
          <button className="border border-amber-200 text-amber-700 hover:bg-amber-50 px-4 py-2 rounded-lg transition-colors duration-200 flex items-center space-x-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
            </svg>
            <span>Share Link</span>
          </button>
        </div>
        <button 
          onClick={onStartOver}
          className="border border-slate-200 text-slate-700 hover:bg-slate-50 px-6 py-2 rounded-lg transition-colors duration-200 flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Start Over</span>
        </button>
      </div>
    </div>
  );
};