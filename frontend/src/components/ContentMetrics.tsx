import React from 'react';

interface ContentMetricsProps {
  text: string;
}

export const ContentMetrics: React.FC<ContentMetricsProps> = ({ text }) => {
  const characterCount = text.length;
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const readingTimeMinutes = Math.ceil(wordCount / 200); // Average reading speed: 200 words/minute

  if (!text.trim()) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
      <div className="flex items-center space-x-2">
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span className="text-sm font-medium text-blue-800">
          {characterCount.toLocaleString()} characters
        </span>
      </div>
      <div className="flex items-center space-x-2">
        <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
        <span className="text-sm font-medium text-indigo-800">
          {wordCount.toLocaleString()} words
        </span>
      </div>
      <div className="flex items-center space-x-2">
        <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-sm font-medium text-purple-800">
          ~{readingTimeMinutes} min read
        </span>
      </div>
    </div>
  );
};
