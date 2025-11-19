import React, { useState, useEffect, useRef } from 'react';
import { ProcessingConfig } from '../types/config';
import { previewTopics } from '../services/apiService';

interface NoteConfigStepProps {
  config: ProcessingConfig;
  onConfigChange: (config: ProcessingConfig) => void;
  onBack: () => void;
  onNext: () => void;
  isProcessing?: boolean;
  noteText?: string; // Text content for topic preview
}

export const NoteConfigStep: React.FC<NoteConfigStepProps> = ({ 
  config, 
  onConfigChange, 
  onBack, 
  onNext,
  isProcessing = false,
  noteText = ''
}) => {
  const [suggestedTopics, setSuggestedTopics] = useState<string[]>([]);
  const [loadingTopics, setLoadingTopics] = useState(false);
  const [topicError, setTopicError] = useState<string | null>(null);
  const [customTopic, setCustomTopic] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [flashcardTopicInput, setFlashcardTopicInput] = useState('');
  const lastTopicSeedRef = useRef<string | null>(null);

  const handleConfigChange = (key: keyof ProcessingConfig, value: boolean | string | string[]) => {
    onConfigChange({
      ...config,
      [key]: value,
    });
  };

  const hasProcessingOption = config.add_bullet_points || config.add_headers || config.expand || config.summarize;
  const flashcardTopics = config.flashcard_topics || [];
  const flashcardEnabled = !!config.generate_flashcards;

  const fetchTopicSuggestions = async (sourceText: string = noteText) => {
    if (!sourceText || sourceText.length < 50) {
      setTopicError('Please enter at least 50 characters to get topic suggestions');
      return;
    }

    try {
      setLoadingTopics(true);
      setTopicError(null);
      setSuggestedTopics([]); // Clear previous suggestions
      console.log('Fetching topic suggestions for text length:', sourceText.length);
      const response = await previewTopics(sourceText);
      console.log('Received topic suggestions:', response);
      setSuggestedTopics(response.topics || []);
      if (!response.topics || response.topics.length === 0) {
        setTopicError('No topics found. Try adding custom topics manually.');
      }
    } catch (error) {
      console.error('Error fetching topic suggestions:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setTopicError(`Failed to load topic suggestions: ${errorMessage}. You can still add topics manually.`);
    } finally {
      setLoadingTopics(false);
    }
  };

  // Auto-fetch topics whenever the note text changes and is long enough (debounced)
  useEffect(() => {
    if (!noteText || noteText.length < 50) {
      return;
    }
    if (lastTopicSeedRef.current === noteText) {
      return;
    }
    const handle = setTimeout(() => {
      lastTopicSeedRef.current = noteText;
      fetchTopicSuggestions(noteText);
    }, 600);
    return () => clearTimeout(handle);
  }, [noteText]);

  const toggleTopic = (topic: string) => {
    const currentTopics = config.focus_topics || [];
    const isSelected = currentTopics.includes(topic);
    
    if (isSelected) {
      handleConfigChange('focus_topics', currentTopics.filter(t => t !== topic));
    } else {
      handleConfigChange('focus_topics', [...currentTopics, topic]);
    }
  };

  const addCustomTopic = () => {
    const trimmed = customTopic.trim();
    if (!trimmed) return;
    
    const currentTopics = config.focus_topics || [];
    if (!currentTopics.includes(trimmed)) {
      handleConfigChange('focus_topics', [...currentTopics, trimmed]);
    }
    setCustomTopic('');
    setShowCustomInput(false);
  };

  const removeTopic = (topic: string) => {
    const currentTopics = config.focus_topics || [];
    handleConfigChange('focus_topics', currentTopics.filter(t => t !== topic));
  };
  
  const addFlashcardTopic = () => {
    const trimmed = flashcardTopicInput.trim();
    if (!trimmed) return;
    if (!flashcardTopics.includes(trimmed)) {
      handleConfigChange('flashcard_topics', [...flashcardTopics, trimmed]);
    }
    setFlashcardTopicInput('');
  };

  const removeFlashcardTopic = (topic: string) => {
    handleConfigChange('flashcard_topics', flashcardTopics.filter(t => t !== topic));
  };

  const copyTopicsToFlashcards = (topics: string[]) => {
    const unique = Array.from(new Set([...flashcardTopics, ...topics]));
    handleConfigChange('flashcard_topics', unique);
    if ((config.flashcard_count || 0) < unique.length) {
      handleConfigChange('flashcard_count', unique.length);
    }
  };

  const handleFlashcardCountChange = (value: number) => {
    const clamped = Math.max(flashcardTopics.length || 1, Math.min(50, value));
    handleConfigChange('flashcard_count', clamped);
  };

  return (
    <div className="w-full mx-auto bg-white/80 backdrop-blur-sm border-orange-200/50 border rounded-xl shadow-lg p-6">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.828 2.828A4 4 0 019.172 21H7l-4-4h2.828a4 4 0 001.414-.586l.828-.828A4 4 0 006.586 10H4l4-4z" />
          </svg>
          <h2 className="text-2xl font-bold text-gray-900">Configure Your Notes</h2>
        </div>
        <p className="text-gray-600">
          Customize how your notes are enhanced with AI
        </p>
      </div>
      
      <div className="space-y-8">
        {/* Content Focus Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Content Focus (Optional)
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {noteText && noteText.length >= 50 
                  ? 'Specify key topics to emphasize in your notes' 
                  : 'AI topic suggestions available after text is extracted from images'}
              </p>
            </div>
            {noteText && noteText.length >= 50 && !suggestedTopics.length && !loadingTopics && !topicError && (
              <button
                onClick={fetchTopicSuggestions}
                disabled={loadingTopics}
                className="text-sm px-4 py-2 bg-indigo-600 text-white border border-indigo-700 rounded-lg hover:bg-indigo-700 transition-colors font-medium shadow-sm"
              >
                Get AI Suggestions
              </button>
            )}
          </div>

          {/* Topic Suggestions */}
          {loadingTopics && (
            <div className="p-4 bg-indigo-50/50 border border-indigo-200 rounded-lg">
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-indigo-700">
                  <div className="w-4 h-4 border-2 border-indigo-400 border-t-indigo-700 rounded-full animate-spin"></div>
                  <span className="text-sm font-medium">Analyzing content with AI...</span>
                </div>
                <div className="text-xs text-indigo-600 space-y-1">
                  <p>✓ Reading your notes</p>
                  <p>✓ Identifying key concepts</p>
                  <p className="animate-pulse">⏳ Extracting main topics...</p>
                </div>
                <p className="text-xs text-indigo-500 italic">This may take 5-10 seconds</p>
              </div>
            </div>
          )}

          {topicError && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm text-amber-800">{topicError}</p>
            </div>
          )}

          {suggestedTopics.length > 0 && (
            <div className="p-4 bg-indigo-50/50 border border-indigo-200 rounded-lg space-y-3">
              <p className="text-sm font-medium text-indigo-900">AI-Suggested Topics:</p>
              <div className="flex flex-wrap gap-2">
                {suggestedTopics.map((topic, index) => {
                  const isSelected = (config.focus_topics || []).includes(topic);
                  return (
                    <button
                      key={index}
                      onClick={() => toggleTopic(topic)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                        isSelected
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'bg-white text-indigo-700 border border-indigo-300 hover:bg-indigo-50'
                      }`}
                    >
                      {isSelected && (
                        <svg className="w-3 h-3 inline mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                      {topic}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Selected Topics Display */}
          {(config.focus_topics && config.focus_topics.length > 0) && (
            <div className="p-4 bg-green-50/50 border border-green-200 rounded-lg space-y-2">
              <p className="text-sm font-medium text-green-900">Selected Topics ({config.focus_topics.length}):</p>
              <div className="flex flex-wrap gap-2">
                {config.focus_topics.map((topic, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1.5 px-3 py-1 bg-green-100 text-green-800 rounded-lg text-sm font-medium"
                  >
                    {topic}
                    <button
                      onClick={() => removeTopic(topic)}
                      className="hover:bg-green-200 rounded-full p-0.5 transition-colors"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Custom Topic Input */}
        {showCustomInput ? (
          <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg space-y-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customTopic}
                  onChange={(e) => setCustomTopic(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addCustomTopic()}
                  placeholder="Enter a custom topic..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  autoFocus
                />
                <button
                  onClick={addCustomTopic}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium"
                >
                  Add
                </button>
                <button
                  onClick={() => {
                    setShowCustomInput(false);
                    setCustomTopic('');
                  }}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowCustomInput(true)}
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add custom topic
            </button>
          )}
        
        {/* Custom Specifications */}
        <div className="space-y-2 border-t border-dashed pt-4 mt-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
              </svg>
              Custom Specifications
            </h3>
            <span className="text-xs text-gray-500">Conflicts yield to enhancement toggles automatically</span>
          </div>
          <textarea
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            rows={3}
            placeholder="Example: Keep tone casual, include callout boxes for formulas, emphasize color-coded sections..."
            value={config.custom_specifications || ''}
            onChange={(e) => handleConfigChange('custom_specifications', e.target.value)}
          />
        </div>

        {/* Project Metadata Section */}
        <div className="space-y-4 border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .672-3 1.5S10.343 11 12 11s3-.672 3-1.5S13.657 8 12 8zM5 21h14M8 21v-6m8 6v-6M3 9h18M6 3h12l3 6H3l3-6z" />
            </svg>
            Project Presentation
          </h3>
          <p className="text-sm text-gray-600">
            Choose how this project appears in your dashboard and within the LaTeX export.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700">Project Name</label>
              <input
                type="text"
                className="w-full border border-amber-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                placeholder="e.g., Biology Unit 3 Review"
                value={config.project_name || ''}
                onChange={(e) => handleConfigChange('project_name', e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700">LaTeX Title Override</label>
              <input
                type="text"
                className="w-full border border-amber-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                placeholder="Appears at the top of the PDF"
                value={config.latex_title || ''}
                onChange={(e) => handleConfigChange('latex_title', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <input
                  type="checkbox"
                  className="h-4 w-4 text-amber-600 rounded border-amber-300"
                  checked={!!config.include_nickname}
                  onChange={(e) => handleConfigChange('include_nickname', e.target.checked)}
                />
                Include my nickname as the author
              </label>
              <input
                type="text"
                className="w-full border border-amber-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 disabled:bg-gray-100"
                placeholder="Nickname to show in the PDF"
                value={config.nickname || ''}
                onChange={(e) => handleConfigChange('nickname', e.target.value)}
                disabled={!config.include_nickname}
              />
            </div>
          </div>
        </div>
      </div>

        {/* Flashcard Generation Section */}
        <div className="space-y-4 border-t pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Flashcard Generation
              </h3>
              <p className="text-sm text-gray-600">
                AI builds up to 50 double-sided cards directly from your notes. You can add extra topics or cards manually later.
              </p>
            </div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
              <span>{flashcardEnabled ? 'Enabled' : 'Disabled'}</span>
              <input
                type="checkbox"
                className="h-5 w-5 text-emerald-600 rounded border-emerald-300 focus:ring-emerald-500"
                checked={flashcardEnabled}
                onChange={(e) => {
                  handleConfigChange('generate_flashcards', e.target.checked);
                  if (e.target.checked) {
                    const preferred = Math.max(4, flashcardTopics.length || 1);
                    if (!config.flashcard_count || config.flashcard_count < preferred) {
                      handleConfigChange('flashcard_count', preferred);
                    }
                  }
                }}
              />
            </label>
          </div>

          {!flashcardEnabled && (
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
              Enable flashcards to have AI summarize each topic with concise definitions (≤ 50 words) pulled directly from your text.
            </div>
          )}

          {flashcardEnabled && (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => copyTopicsToFlashcards(config.focus_topics || [])}
                  className="px-3 py-1.5 text-sm border border-emerald-300 text-emerald-700 rounded-lg hover:bg-emerald-50"
                  disabled={!config.focus_topics || config.focus_topics.length === 0}
                >
                  Copy selected focus topics
                </button>
                <button
                  type="button"
                  onClick={() => copyTopicsToFlashcards(suggestedTopics)}
                  className="px-3 py-1.5 text-sm border border-indigo-300 text-indigo-700 rounded-lg hover:bg-indigo-50 disabled:opacity-40"
                  disabled={!suggestedTopics.length}
                >
                  Copy AI suggestions
                </button>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-800">
                  Flashcard Topics ({flashcardTopics.length})
                </p>
                {flashcardTopics.length === 0 && (
                  <p className="text-sm text-gray-500">
                    Add at least one topic or copy from the focus list so AI knows what to prioritize.
                  </p>
                )}
                <div className="flex flex-wrap gap-2">
                  {flashcardTopics.map((topic) => (
                    <span
                      key={topic}
                      className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full text-xs font-medium border border-emerald-200"
                    >
                      {topic}
                      <button onClick={() => removeFlashcardTopic(topic)} className="hover:text-emerald-900">
                        ×
                      </button>
                    </span>
                  ))}
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="Add a flashcard topic..."
                    value={flashcardTopicInput}
                    onChange={(e) => setFlashcardTopicInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addFlashcardTopic())}
                  />
                  <button
                    type="button"
                    onClick={addFlashcardTopic}
                    className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
                  >
                    Add
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">
                    Total flashcards (min topics, max 50)
                  </label>
                  <input
                    type="number"
                    min={Math.max(1, flashcardTopics.length || 1)}
                    max={50}
                    value={config.flashcard_count || Math.max(flashcardTopics.length || 1, 4)}
                    onChange={(e) => handleFlashcardCountChange(Number(e.target.value) || (flashcardTopics.length || 1))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">
                    Max flashcards per topic (up to 4)
                  </label>
                  <input
                    type="range"
                    min={1}
                    max={4}
                    value={config.max_flashcards_per_topic || 4}
                    onChange={(e) => handleConfigChange('max_flashcards_per_topic', Number(e.target.value))}
                    className="w-full accent-emerald-600"
                  />
                  <p className="text-xs text-gray-500">
                    Currently {config.max_flashcards_per_topic || 4} per topic
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Processing Options Section */}
        <div className="space-y-4 border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Enhancement Options
            <span className="text-sm text-red-600 font-normal">(choose at least one)</span>
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { 
                key: 'add_bullet_points', 
                label: 'Add Bullet Points', 
                description: 'Format content with bullet points for better readability',
                icon: (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v6a2 2 0 002 2h2m9-9h2a2 2 0 012 2v6a2 2 0 01-2 2h-2m-9-9V7a2 2 0 012-2h2m-2 9v2a2 2 0 002 2h2" />
                  </svg>
                )
              },
              { 
                key: 'add_headers', 
                label: 'Add Headers', 
                description: 'Organize content with clear headers and sections',
                icon: (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                  </svg>
                )
              },
              { 
                key: 'expand', 
                label: 'Expand Content', 
                description: 'Add more details, explanations, and context',
                icon: (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  </svg>
                )
              },
              { 
                key: 'summarize', 
                label: 'Summarize', 
                description: 'Create a concise summary of key points',
                icon: (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )
              }
            ].map((option) => (
              <div 
                key={option.key} 
                className="flex items-start space-x-3 p-4 border border-orange-200/50 rounded-lg bg-orange-50/30 hover:bg-orange-50/50 transition-all duration-200 cursor-pointer"
                onClick={() => handleConfigChange(option.key as keyof ProcessingConfig, !config[option.key as keyof ProcessingConfig])}
              >
                <input
                  id={option.key}
                  type="checkbox"
                  checked={config[option.key as keyof ProcessingConfig] as boolean}
                  onChange={(e) => handleConfigChange(option.key as keyof ProcessingConfig, e.target.checked)}
                  disabled={isProcessing}
                  className="h-4 w-4 text-orange-600 focus:ring-orange-500 border-orange-300 rounded disabled:opacity-50 mt-1 cursor-pointer"
                  onClick={(e) => e.stopPropagation()}
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
          </div>
          
          {!hasProcessingOption && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
              Please select at least one enhancement option
            </p>
          )}
        </div>

        {/* Style & Format Section */}
        <div className="space-y-4 border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
            </svg>
            PDF Style & Format (Optional)
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* LaTeX Style Selector */}
            <div className="space-y-2">
              <label htmlFor="latex-style" className="block text-sm font-medium text-gray-700">
                Document Style
              </label>
              <select
                id="latex-style"
                value={config.latex_style || 'academic'}
                onChange={(e) => handleConfigChange('latex_style', e.target.value)}
                className="w-full px-3 py-2 border border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white text-sm"
              >
                <option value="academic">Academic - Scholarly layout with refined spacing</option>
                <option value="personal">Personal - Friendly tone for study notes</option>
                <option value="minimalist">Minimalist - Clean and simple design</option>
              </select>
            </div>

            {/* Font Preference Selector */}
            <div className="space-y-2">
              <label htmlFor="font-preference" className="block text-sm font-medium text-gray-700">
                Font Preference
              </label>
              <select
                id="font-preference"
                value={config.font_preference || 'Times New Roman'}
                onChange={(e) => handleConfigChange('font_preference', e.target.value)}
                className="w-full px-3 py-2 border border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white text-sm"
              >
                <option value="Times New Roman">Times New Roman (Serif)</option>
                <option value="Helvetica">Helvetica (Sans-serif)</option>
                <option value="Arial">Arial (Sans-serif)</option>
                <option value="Palatino">Palatino (Serif)</option>
                <option value="Garamond">Garamond (Serif)</option>
                <option value="Monospace">Monospace (Code-friendly)</option>
              </select>
            </div>
          </div>

          <div className="p-3 bg-purple-50/50 border border-purple-200 rounded-lg">
            <p className="text-xs text-purple-800">
              <strong>Note:</strong> These settings will be applied when generating PDF documents from your notes.
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between pt-6 border-t mt-6">
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
