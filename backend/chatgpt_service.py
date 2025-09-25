import os
from typing import Dict, Any, Optional
import openai
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
        
        openai.api_key = self.api_key
    
    async def process_text_with_chatgpt(self, text: str, settings: ProcessingSettings) -> str:
        """
        Process text using ChatGPT API based on provided settings
        """
        try:
            prompt = self._generate_prompt(text, settings)
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that improves and formats text according to specific instructions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error processing with ChatGPT: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _generate_prompt(self, text: str, settings: ProcessingSettings) -> str:
        """
        Generate prompt based on processing settings
        """
        instructions = []
        
        if settings.add_bullet_points:
            instructions.append("Format the content using bullet points where appropriate for better readability and organization")
        
        if settings.add_headers:
            instructions.append("Add clear headers and subheaders to organize the content into logical sections")
        
        if settings.expand:
            instructions.append("Expand and elaborate on the content with more details, explanations, and context")
        
        if settings.summarize:
            instructions.append("Provide a concise summary of the main points while maintaining key information")
        
        if not instructions:
            instructions.append("Improve the clarity and readability of the text")
        
        prompt = f"""
Please process the following text according to these instructions:
{chr(10).join(f"- {instruction}" for instruction in instructions)}

Original text:
\"\"\"
{text}
\"\"\"

Please provide the improved version:"""
        
        return prompt

# Create a singleton instance
chatgpt_service = ChatGPTService()