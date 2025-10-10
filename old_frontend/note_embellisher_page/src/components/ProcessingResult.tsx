import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { CheckCircle, Download, Share, RotateCcw, FileText, Cloud, Loader2 } from 'lucide-react';

interface ProcessingResultProps {
  config: {
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
  };
  originalNotes: string;
  onStartOver: () => void;
}

export function ProcessingResult({ config, originalNotes, onStartOver }: ProcessingResultProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [processedContent, setProcessedContent] = useState('');
  const [showContent, setShowContent] = useState(false);

  // Mock processed content based on selected options
  const generateProcessedContent = () => {
    let content = originalNotes;
    
    if (config.processingOptions.addHeaders) {
      content = `# ${config.title}\n\n## Overview\n${content}\n\n## Key Points\n\n## Summary`;
    }
    
    if (config.processingOptions.addBulletPoints) {
      const sentences = content.split('.').filter(s => s.trim());
      content = sentences.map(sentence => `• ${sentence.trim()}`).join('\n');
    }
    
    if (config.processingOptions.summarize) {
      content += '\n\n**Summary:** This appears to be comprehensive notes that have been organized and structured for better readability and understanding.';
    }
    
    if (config.processingOptions.expand) {
      content += '\n\n**Additional Context:** These notes have been expanded with relevant context and supporting information to provide a more complete understanding of the topic.';
    }
    
    return content;
  };

  useEffect(() => {
    // Simulate processing time
    const timer = setTimeout(() => {
      setProcessedContent(generateProcessedContent());
      setIsLoading(false);
      // Trigger the fade-in animation
      setTimeout(() => setShowContent(true), 100);
    }, 2500);

    return () => clearTimeout(timer);
  }, []);

  const selectedOptions = Object.entries(config.processingOptions)
    .filter(([_, value]) => value)
    .map(([key, _]) => key);

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
    <Card className="w-full mx-auto bg-white/80 backdrop-blur-sm border-green-200/50 shadow-lg">
      <CardHeader>
        <div className="flex items-center gap-2 mb-2">
          {isLoading ? (
            <Loader2 className="w-5 h-5 text-amber-500 animate-spin" />
          ) : (
            <CheckCircle className="w-5 h-5 text-green-500" />
          )}
          <CardTitle>
            {isLoading ? 'Enhancing Your Notes...' : 'Notes Enhanced Successfully!'}
          </CardTitle>
        </div>
        <CardDescription>
          {isLoading 
            ? 'AI is processing your notes with the selected enhancements' 
            : 'Your notes have been processed with the selected enhancements'
          }
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Note metadata */}
        <div className="p-4 bg-green-50/70 rounded-lg space-y-3 border border-green-200/30">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="bg-amber-100 text-amber-800 border-amber-200">
              {config.subject}
            </Badge>
            <Badge variant="outline" className="border-green-300 text-green-700">
              {config.flair}
            </Badge>
            {config.date && (
              <Badge variant="outline" className="border-orange-300 text-orange-700">
                {new Date(config.date).toLocaleDateString()}
              </Badge>
            )}
          </div>
          <div>
            <h3 className="font-medium text-green-800">{config.title}</h3>
            <p className="text-sm text-green-600">{config.description}</p>
          </div>
          <div className="flex flex-wrap gap-1">
            <span className="text-sm text-green-600">Applied:</span>
            {selectedOptions.map((option) => (
              <Badge key={option} variant="outline" className="text-xs border-green-300 text-green-700">
                {option.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
              </Badge>
            ))}
          </div>
        </div>

        {/* Loading or Content Display */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-amber-200 border-t-amber-500 rounded-full animate-spin"></div>
              <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-orange-300 rounded-full animate-pulse"></div>
            </div>
            <p className="text-amber-700 animate-pulse">Processing your notes...</p>
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-rose-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        ) : (
          <>
            {/* Original vs Enhanced */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-3">
                <h4 className="font-medium text-slate-700">Original Notes</h4>
                <div className="p-4 bg-slate-50 rounded-lg max-h-80 overflow-y-auto border border-slate-200">
                  <pre className="whitespace-pre-wrap text-sm text-slate-600">{originalNotes}</pre>
                </div>
              </div>
              <div className="space-y-3">
                <h4 className="font-medium text-green-800">Enhanced Notes</h4>
                <div 
                  className={`p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg max-h-80 overflow-y-auto border border-green-200 transition-all duration-1000 ${
                    showContent 
                      ? 'opacity-100 blur-none transform translate-y-0' 
                      : 'opacity-0 blur-sm transform translate-y-2'
                  }`}
                >
                  <pre className="whitespace-pre-wrap text-sm text-green-800">{processedContent}</pre>
                </div>
              </div>
            </div>

            {/* Export Options */}
            <div className="space-y-4">
              <h4 className="font-medium text-slate-700">Export & Share Options</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <Button 
                  onClick={handleExportPDF} 
                  className="bg-red-500 hover:bg-red-600 text-white"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Export to PDF
                </Button>
                <Button 
                  onClick={handleExportWord}
                  className="bg-blue-500 hover:bg-blue-600 text-white"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Export to Word
                </Button>
                <Button 
                  onClick={handleConnectGoogleDrive}
                  className="bg-green-500 hover:bg-green-600 text-white"
                >
                  <Cloud className="w-4 h-4 mr-2" />
                  Save to Drive
                </Button>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex flex-wrap gap-3 pt-4 border-t border-green-200">
              <Button variant="outline" className="border-orange-200 text-orange-700 hover:bg-orange-50">
                <Download className="w-4 h-4 mr-2" />
                Download All
              </Button>
              <Button variant="outline" className="border-amber-200 text-amber-700 hover:bg-amber-50">
                <Share className="w-4 h-4 mr-2" />
                Share Link
              </Button>
              <Button 
                variant="outline" 
                onClick={onStartOver}
                className="border-slate-200 text-slate-700 hover:bg-slate-50"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Start Over
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}