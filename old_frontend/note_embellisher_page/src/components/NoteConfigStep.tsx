import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Checkbox } from './ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { CalendarDays, ArrowLeft, Sparkles } from 'lucide-react';

interface NoteConfigStepProps {
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
  onConfigChange: (config: any) => void;
  onBack: () => void;
  onSubmit: () => void;
}

const flairOptions = [
  'Study Notes', 'Meeting Notes', 'Research', 'Ideas', 'To-Do', 'Important', 
  'Draft', 'Personal', 'Work', 'School', 'Creative', 'Technical'
];

const subjects = [
  'Mathematics', 'Science', 'History', 'Literature', 'Computer Science',
  'Business', 'Art', 'Music', 'Language', 'Medicine', 'Law', 'Engineering',
  'Psychology', 'Philosophy', 'Other'
];

export function NoteConfigStep({ config, onConfigChange, onBack, onSubmit }: NoteConfigStepProps) {
  const updateConfig = (field: string, value: any) => {
    onConfigChange({
      ...config,
      [field]: value
    });
  };

  const updateProcessingOption = (option: string, checked: boolean) => {
    onConfigChange({
      ...config,
      processingOptions: {
        ...config.processingOptions,
        [option]: checked
      }
    });
  };

  const hasProcessingOption = Object.values(config.processingOptions).some(Boolean);
  const canSubmit = config.subject && config.title && config.description && hasProcessingOption;
  const descriptionLength = config.description.length;

  return (
    <Card className="w-full mx-auto bg-white/80 backdrop-blur-sm border-orange-200/50 shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          Configure Your Notes
        </CardTitle>
        <CardDescription>
          Add details and choose how you want your notes enhanced
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="subject">Subject</Label>
            <Select value={config.subject} onValueChange={(value) => updateConfig('subject', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select subject" />
              </SelectTrigger>
              <SelectContent>
                {subjects.map((subject) => (
                  <SelectItem key={subject} value={subject}>
                    {subject}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="date">Date</Label>
            <div className="relative">
              <Input
                id="date"
                type="date"
                value={config.date}
                onChange={(e) => updateConfig('date', e.target.value)}
              />
              <CalendarDays className="absolute right-3 top-3 w-4 h-4 text-muted-foreground pointer-events-none" />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label>Flair (for organization)</Label>
          <div className="flex flex-wrap gap-2">
            {flairOptions.map((flair) => (
              <Badge
                key={flair}
                variant={config.flair === flair ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => updateConfig('flair', flair)}
              >
                {flair}
              </Badge>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            placeholder="Give your notes a title"
            value={config.title}
            onChange={(e) => updateConfig('title', e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <div className="space-y-1">
            <Textarea
              id="description"
              placeholder="Brief description of your notes"
              value={config.description}
              onChange={(e) => updateConfig('description', e.target.value)}
              maxLength={50}
              className="resize-none"
            />
            <div className="text-right text-sm text-muted-foreground">
              {descriptionLength}/50 characters
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <Label>Processing Options (choose at least one)</Label>
          <div className="space-y-4">
            {[
              { key: 'summarize', label: 'Summarize', description: 'Create a concise summary' },
              { key: 'expand', label: 'Expand', description: 'Add more detail and context' },
              { key: 'addHeaders', label: 'Add Headers', description: 'Organize with section headers' },
              { key: 'addBulletPoints', label: 'Add Bullet Points', description: 'Format as bullet lists' }
            ].map((option) => (
              <div key={option.key} className="flex items-start space-x-3 p-4 border border-orange-200/50 rounded-lg bg-orange-50/30 hover:bg-orange-50/50 transition-colors">
                <Checkbox
                  id={option.key}
                  checked={config.processingOptions[option.key as keyof typeof config.processingOptions]}
                  onCheckedChange={(checked) => 
                    updateProcessingOption(option.key, checked as boolean)
                  }
                />
                <div className="space-y-1">
                  <Label htmlFor={option.key} className="cursor-pointer">
                    {option.label}
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    {option.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
          {!hasProcessingOption && (
            <p className="text-sm text-destructive">
              Please select at least one processing option
            </p>
          )}
        </div>

        <div className="flex justify-between pt-4">
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <Button 
            onClick={onSubmit} 
            disabled={!canSubmit}
            className="px-8"
          >
            Enhance Notes
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}