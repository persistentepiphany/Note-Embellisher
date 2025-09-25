import os
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        
        self.client = OpenAI(api_key=self.api_key)
    
    async def process_text_with_chatgpt(self, text: str, settings: ProcessingSettings) -> str:
        """
        Process text using ChatGPT API based on provided settings
        """
        try:
            prompt = self._generate_prompt(text, settings)
            
            response = self.client.chat.completions.create(
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
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error processing with ChatGPT: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")
    
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