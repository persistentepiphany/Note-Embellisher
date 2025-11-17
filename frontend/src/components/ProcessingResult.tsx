import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { exportToWord, downloadTextFile } from '../utils/exportUtils';
import { FormattedContent } from './FormattedContent';
import { generatePDF } from '../services/apiService';

interface ProcessingResultProps {
  originalNotes: string;
  processedNotes: string;
  noteId?: number; // Optional note ID for PDF generation
  onStartOver: () => void;
}

export const ProcessingResult: React.FC<ProcessingResultProps> = ({
  originalNotes,
  processedNotes,
  noteId,
  onStartOver,
}) => {
  const navigate = useNavigate();
  const [showContent, setShowContent] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  const apiBaseUrl = useMemo(() => {
    const metaEnv = (import.meta as unknown as { env: Record<string, string | undefined> }).env;
    return metaEnv.VITE_API_BASE_URL || 'http://localhost:8080';
  }, []);

  useEffect(() => {
    // Trigger the fade-in animation
    const timer = setTimeout(() => setShowContent(true), 300);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!noteId || pdfUrl) {
      return;
    }

    let active = true;
    const generate = async () => {
      setPdfLoading(true);
      setPdfError(null);
      try {
        const result = await generatePDF(noteId);
        if (!active) return;
        if (!result?.pdf_url) {
          throw new Error('PDF generation succeeded but no file URL was returned.');
        }
        setPdfUrl(`${apiBaseUrl}${result.pdf_url}`);
      } catch (error) {
        if (!active) return;
        console.error('Error generating PDF preview:', error);
        setPdfError(error instanceof Error ? error.message : 'Failed to generate PDF preview.');
      } finally {
        if (active) {
          setPdfLoading(false);
        }
      }
    };

    generate();

    return () => {
      active = false;
    };
  }, [noteId, pdfUrl, apiBaseUrl]);

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const handleExportPDF = async () => {
    try {
      setPdfError(null);
      
      if (!noteId) {
        setPdfError('Note ID is required to generate PDF. Please save your note first.');
        return;
      }
      
      // Call backend to generate LaTeX PDF
      console.log(`Generating LaTeX PDF for note ${noteId}...`);
      const result = await generatePDF(noteId);
      
      // Open the PDF in a new tab
      const pdfUrl = `${apiBaseUrl}${result.pdf_url}`;
      window.open(pdfUrl, '_blank');
      
      console.log('PDF generated successfully:', result);
    } catch (error) {
      console.error('Error generating PDF:', error);
      setPdfError(error instanceof Error ? error.message : 'Failed to generate PDF. Please try again.');
    }
  };

  const handleExportWord = () => {
    try {
      exportToWord(processedNotes, 'Enhanced Notes');
    } catch (error) {
      alert(`Error exporting Word document: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleDownloadText = () => {
    try {
      downloadTextFile(processedNotes, 'enhanced_notes.txt');
    } catch (error) {
      alert(`Error downloading file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleDownloadAll = () => {
    try {
      const combinedContent = `ORIGINAL NOTES:\n\n${originalNotes}\n\n${'='.repeat(50)}\n\nENHANCED NOTES:\n\n${processedNotes}`;
      downloadTextFile(combinedContent, 'all_notes.txt');
    } catch (error) {
      alert(`Error downloading file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleConnectGoogleDrive = () => {
    // Mock Google Drive connection
    alert('Connecting to Google Drive... (This would integrate with Google Drive API)');
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
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
            className={`p-6 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg max-h-96 overflow-y-auto border border-green-200 transition-all duration-1000 ${
              showContent 
                ? 'opacity-100 blur-none transform translate-y-0' 
                : 'opacity-0 blur-sm transform translate-y-2'
            }`}
          >
            <FormattedContent 
              content={processedNotes} 
              className="text-green-800"
            />
          </div>
        </div>
      </div>

      {/* Export Options */}
      <div className="space-y-4 mb-6">
        <h4 className="text-lg font-medium text-slate-700">Export & Share Options</h4>
        
        {/* PDF Error Display */}
        {pdfError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-sm text-red-700">{pdfError}</p>
          </div>
        )}
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button 
            onClick={handleDownloadText} 
            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Download TXT</span>
          </button>
          <button 
            onClick={handleExportPDF}
            disabled={!noteId}
            className={`${
              noteId 
                ? 'bg-red-500 hover:bg-red-600' 
                : 'bg-gray-300 cursor-not-allowed'
            } text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2`}
            title={noteId ? 'Generate professional LaTeX PDF' : 'Save note first to generate PDF'}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Generate LaTeX PDF</span>
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

      {/* PDF Preview */}
      <div className="space-y-3 mb-6">
        <div className="flex items-center justify-between">
          <h4 className="text-lg font-medium text-slate-700">LaTeX PDF Preview</h4>
          {pdfLoading && (
            <span className="text-sm text-amber-600">Generating preview...</span>
          )}
        </div>
        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
          {pdfUrl ? (
            <iframe
              src={pdfUrl}
              className="w-full h-[600px]"
              title="Note PDF Preview"
              loading="lazy"
            />
          ) : (
            <div className="p-6 text-center text-slate-500 text-sm">
              {pdfLoading
                ? 'Compiling LaTeX and generating PDF preview...'
                : pdfError
                  ? `Preview unavailable: ${pdfError}`
                  : 'PDF preview will appear here once generated.'}
            </div>
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3 pt-4 border-t border-green-200 justify-between">
        <div className="flex gap-3">
          <button 
            onClick={handleDownloadAll}
            className="border border-orange-200 text-orange-700 hover:bg-orange-50 px-4 py-2 rounded-lg transition-colors duration-200 flex items-center space-x-2"
          >
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
        <div className="flex gap-3">
          <button 
            onClick={handleBackToDashboard}
            className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-2 rounded-lg transition-colors duration-200 flex items-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 0V3" />
            </svg>
            <span>Back to Dashboard</span>
          </button>
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
    </div>
  );
};