import React from 'react';

interface FormattedContentProps {
  content: string;
  className?: string;
}

export const FormattedContent: React.FC<FormattedContentProps> = ({ content, className = '' }) => {
  // Function to process and format the content
  const formatContent = (text: string) => {
    return text
      // Replace headers with styled versions
      .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-gray-900 mb-4 mt-6 border-b-2 border-gray-200 pb-2">$1</h1>')
      .replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold text-gray-800 mb-3 mt-5">$1</h2>')
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-medium text-gray-700 mb-2 mt-4">$1</h3>')
      .replace(/^#### (.*$)/gim, '<h4 class="text-base font-medium text-gray-600 mb-2 mt-3">$1</h4>')
      
      // Replace bullet points with styled versions
      .replace(/^• (.*$)/gim, '<div class="flex items-start mb-2"><span class="text-green-600 mr-2 mt-1">•</span><span class="flex-1">$1</span></div>')
      .replace(/^◦ (.*$)/gim, '<div class="flex items-start mb-1 ml-4"><span class="text-green-500 mr-2 mt-1">◦</span><span class="flex-1">$1</span></div>')
      
      // Replace numbered lists
      .replace(/^(\d+)\. (.*$)/gim, '<div class="flex items-start mb-2"><span class="text-blue-600 font-medium mr-2 mt-0">$1.</span><span class="flex-1">$2</span></div>')
      
      // Replace decorative lines
      .replace(/^═+$/gim, '<hr class="border-0 h-0.5 bg-gradient-to-r from-transparent via-gray-300 to-transparent my-6" />')
      .replace(/^─+$/gim, '<hr class="border-0 h-px bg-gray-200 my-4" />')
      
      // Replace bold text
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
      
      // Replace italic text
      .replace(/\*(.*?)\*/g, '<em class="italic text-gray-700">$1</em>')
      
      // Replace code blocks or highlighted text
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-mono">$1</code>')
      
      // Handle paragraphs (double line breaks)
      .replace(/\n\n/g, '</p><p class="mb-4">')
      
      // Handle single line breaks
      .replace(/\n/g, '<br />')
      
      // Wrap in paragraph tags
      .replace(/^/, '<p class="mb-4">')
      .replace(/$/, '</p>');
  };

  return (
    <div 
      className={`formatted-content prose prose-sm max-w-none ${className}`}
      dangerouslySetInnerHTML={{ __html: formatContent(content) }}
      style={{
        lineHeight: '1.7',
        fontSize: '14px'
      }}
    />
  );
};