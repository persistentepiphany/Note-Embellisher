import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { CheckCircle, Download, Share, RotateCcw } from 'lucide-react';

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

  const processedContent = generateProcessedContent();
  const selectedOptions = Object.entries(config.processingOptions)
    .filter(([_, value]) => value)
    .map(([key, _]) => key);

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle className="w-5 h-5 text-green-500" />
          <CardTitle>Notes Enhanced Successfully!</CardTitle>
        </div>
        <CardDescription>
          Your notes have been processed with the selected enhancements
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Note metadata */}
        <div className="p-4 bg-muted rounded-lg space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{config.subject}</Badge>
            <Badge variant="outline">{config.flair}</Badge>
            {config.date && <Badge variant="outline">{new Date(config.date).toLocaleDateString()}</Badge>}
          </div>
          <div>
            <h3 className="font-medium">{config.title}</h3>
            <p className="text-sm text-muted-foreground">{config.description}</p>
          </div>
          <div className="flex flex-wrap gap-1">
            <span className="text-sm text-muted-foreground">Applied:</span>
            {selectedOptions.map((option) => (
              <Badge key={option} variant="outline" className="text-xs">
                {option.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
              </Badge>
            ))}
          </div>
        </div>

        {/* Original vs Enhanced */}
        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <h4 className="font-medium">Original Notes</h4>
            <div className="p-4 bg-gray-50 rounded-lg max-h-64 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm">{originalNotes}</pre>
            </div>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">Enhanced Notes</h4>
            <div className="p-4 bg-green-50 rounded-lg max-h-64 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm">{processedContent}</pre>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-3 pt-4">
          <Button>
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
          <Button variant="outline">
            <Share className="w-4 h-4 mr-2" />
            Share
          </Button>
          <Button variant="outline" onClick={onStartOver}>
            <RotateCcw className="w-4 h-4 mr-2" />
            Start Over
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}