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
        self.client = None
        
        if not self.api_key:
            print("⚠️ Warning: OPENAI_API_KEY not found in environment variables")
            return
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            print("✅ OpenAI client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            self.client = None
    
    async def process_text_with_chatgpt(self, text: str, settings: ProcessingSettings) -> str:
        """
        Process text using ChatGPT API based on provided settings
        """
        if not self.client:
            print("⚠️ OpenAI client not available, using fallback enhancement")
            return self._create_fallback_enhanced_text(text, settings)
        
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
            print(f"❌ Error processing with ChatGPT: {str(e)}")
            print("🔄 Falling back to local enhancement")
            return self._create_fallback_enhanced_text(text, settings)
    
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
    
    def _create_fallback_enhanced_text(self, text: str, settings: ProcessingSettings) -> str:
        """
        Create enhanced text without AI when OpenAI is not available
        """
        enhanced_text = text
        
        # Add header if requested
        if settings.add_headers:
            enhanced_text = f"# 📝 Enhanced Notes\n\n═══════════════════════════════════════\n\n{enhanced_text}"
        
        # Add bullet points if requested
        if settings.add_bullet_points:
            lines = enhanced_text.split('\n')
            bullet_lines = []
            for line in lines:
                if line.strip() and not line.startswith('#') and not line.startswith('═'):
                    bullet_lines.append(f"• {line.strip()}")
                else:
                    bullet_lines.append(line)
            enhanced_text = '\n'.join(bullet_lines)
        
        # Expand content if requested
        if settings.expand:
            enhanced_text = f"{enhanced_text}\n\n**Additional Context:** This content has been locally enhanced with basic formatting. Full AI enhancement is temporarily unavailable due to API configuration issues.\n\n**Next Steps:** Please check your OpenAI API configuration for full functionality."
        
        # Add summary if requested
        if settings.summarize:
            summary = f"**Summary:** {text[:100]}..." if len(text) > 100 else f"**Summary:** {text}"
            enhanced_text = f"{summary}\n\n═══════════════════════════════════════\n\n{enhanced_text}"
        
        return enhanced_text

# Create a singleton instance
chatgpt_service = ChatGPTService()