import os
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ProcessingSettings:
    def __init__(
        self, 
        add_bullet_points: bool = False,
        add_headers: bool = False,
        expand: bool = False,
        summarize: bool = False
    ):
        self.add_bullet_points = add_bullet_points
        self.add_headers = add_headers
        self.expand = expand
        self.summarize = summarize

class ChatGPTService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please add OPENAI_API_KEY to your .env file.")
        
        logger.info(f"Initializing ChatGPT service with API key: {self.api_key[:10]}...")
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def process_text_with_chatgpt(self, text: str, settings: ProcessingSettings) -> str:
        """
        Process text using ChatGPT API based on provided settings
        """
        try:
            prompt = self._generate_prompt(text, settings)
            logger.info(f"Processing text with ChatGPT, length: {len(text)} chars")
            
            # Test if API key is valid by making a simple request first
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4 for better formatting and comprehension
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert content formatter, editor, and writer with exceptional skills in document design and presentation. Your specialty is transforming basic text into beautifully formatted, comprehensive, and engaging documents that are both visually appealing and highly informative. You excel at:

- Creating elegant visual hierarchies with proper spacing and formatting
- Expanding content with relevant details while maintaining accuracy
- Using sophisticated formatting techniques including symbols, lines, and visual elements
- Writing in a clear, professional, and engaging style
- Organizing information logically with smooth transitions between sections"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,  # Increased for longer, more comprehensive responses
                temperature=0.8   # Slightly higher for more creative formatting
            )
            
            result = response.choices[0].message.content
            logger.info(f"ChatGPT processing completed, result length: {len(result)} chars")
            return result or text  # Fallback to original text if no result
        
        except Exception as e:
            logger.error(f"Error processing with ChatGPT: {str(e)}")
            
            # Check for various API error types
            error_str = str(e).lower()
            if any(term in error_str for term in ["401", "invalid_api_key", "authentication", "unauthorized", "api key"]):
                logger.warning("Using fallback mock response due to API authentication issues")
                return self._generate_mock_response(text, settings)
            elif any(term in error_str for term in ["quota", "rate limit", "limit exceeded"]):
                logger.warning("Using fallback mock response due to API quota/rate limit")
                return self._generate_mock_response(text, settings)
            else:
                logger.warning(f"Using fallback mock response due to API error: {e}")
                return self._generate_mock_response(text, settings)
    
    def _generate_mock_response(self, text: str, settings: ProcessingSettings) -> str:
        """
        Generate a mock formatted response when OpenAI API is not available
        """
        formatted_text = f"""# Enhanced Note Processing Result

**Original Content:**
{text}

═══════════════════════════════════════

## Processed Content

"""
        
        if settings.add_headers:
            formatted_text += "### Overview\n\n"
        
        if settings.add_bullet_points:
            lines = text.split('\n')
            formatted_text += "**Key Points:**\n"
            for line in lines:
                if line.strip():
                    formatted_text += f"• {line.strip()}\n"
            formatted_text += "\n"
        
        if settings.expand:
            formatted_text += "**Expanded Details:**\n"
            formatted_text += f"This content has been enhanced with additional context and formatting. "
            formatted_text += f"The original text ({len(text)} characters) provides valuable information that can be further developed.\n\n"
        
        if settings.summarize:
            formatted_text += "**Summary:**\n"
            formatted_text += f"Key takeaways from the above content focus on the main themes and important details presented.\n\n"
        
        formatted_text += """
---
*Note: This is a demo response generated due to OpenAI API configuration issues. Please configure a valid API key for full functionality.*
"""
        
        return formatted_text
    
    def _generate_prompt(self, text: str, settings: ProcessingSettings) -> str:
        """
        Generate enhanced prompt for beautiful, comprehensive formatting
        """
        base_instructions = [
            "Transform this text into a beautifully formatted, comprehensive document",
            "Use rich formatting with proper spacing, visual hierarchy, and elegant organization",
            "Make the content substantially longer and more detailed while maintaining accuracy",
            "Add relevant context, explanations, and insights where appropriate"
        ]
        
        formatting_instructions = []
        
        if settings.add_bullet_points:
            formatting_instructions.extend([
                "Use elegant bullet points (•) and sub-bullets (◦) for lists and key points",
                "Create nested bullet structures for complex information",
                "Use numbered lists (1., 2., 3.) for sequential processes or priorities"
            ])
        
        if settings.add_headers:
            formatting_instructions.extend([
                "Create a clear hierarchical structure with descriptive headers",
                "Use various header levels to create visual flow and organization",
                "Add section dividers using decorative elements like ═══════════",
                "Include a brief introduction and conclusion sections"
            ])
        
        if settings.expand:
            formatting_instructions.extend([
                "Significantly expand the content with detailed explanations and examples",
                "Add background context and relevant supporting information",
                "Include practical applications, implications, or next steps",
                "Provide additional insights that enhance understanding"
            ])
        
        if settings.summarize:
            formatting_instructions.extend([
                "Begin with an executive summary highlighting the key takeaways",
                "End with a concise conclusion that reinforces main points",
                "Use callout boxes or highlighted sections for critical information"
            ])
        
        # Combine all instructions
        all_instructions = base_instructions + formatting_instructions
        
        prompt = f"""You are an expert content formatter and writer. Your task is to transform the provided text into a beautifully formatted, comprehensive, and engaging document.

FORMATTING GUIDELINES:
{chr(10).join(f"• {instruction}" for instruction in all_instructions)}

ADDITIONAL REQUIREMENTS:
• Use visual elements like lines, spacing, and symbols to create an elegant layout
• Ensure the final result is at least 2-3 times longer than the original
• Maintain factual accuracy while enhancing readability and engagement
• Create a professional, polished appearance suitable for presentation
• Use appropriate spacing and line breaks for visual appeal
• Include transitional phrases to improve flow between sections

ORIGINAL TEXT:
═══════════════════════════════════════
{text}
═══════════════════════════════════════

Please provide the enhanced, beautifully formatted version:"""
        
        return prompt

# Create a singleton instance
chatgpt_service = ChatGPTService()