import os
import json
import asyncio
from collections import defaultdict
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv
import base64
import requests

# Load environment variables
load_dotenv()

class ProcessingSettings:
    def __init__(
        self, 
        add_bullet_points: bool = False,
        add_headers: bool = False,
        expand: bool = False,
        summarize: bool = False,
        focus_topics: Optional[List[str]] = None,
        latex_style: str = "academic",
        font_preference: str = "Times New Roman",
        custom_specifications: Optional[str] = "",
        generate_flashcards: bool = False,
        flashcard_topics: Optional[List[str]] = None,
        flashcard_count: int = 0,
        max_flashcards_per_topic: int = 4,
        project_name: Optional[str] = None,
        latex_title: Optional[str] = None,
        include_nickname: bool = False,
        nickname: Optional[str] = None
    ):
        self.add_bullet_points = add_bullet_points
        self.add_headers = add_headers
        self.expand = expand
        self.summarize = summarize
        self.focus_topics = focus_topics or []
        self.latex_style = latex_style
        self.font_preference = font_preference
        self.custom_specifications = (custom_specifications or "").strip()
        self.generate_flashcards = generate_flashcards
        self.flashcard_topics = flashcard_topics or []
        self.flashcard_count = flashcard_count
        self.max_flashcards_per_topic = max(1, max_flashcards_per_topic or 4)
        self.project_name = project_name
        self.latex_title = latex_title
        self.include_nickname = include_nickname
        self.nickname = nickname

class ChatGPTService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.chunk_char_limit = int(os.getenv("OPENAI_CHUNK_CHAR_LIMIT", "3800"))
        self.max_parallel_requests = max(1, int(os.getenv("OPENAI_PARALLEL_REQUESTS", "3")))
        
        if not self.api_key:
            print("⚠️ Warning: OPENAI_API_KEY not found in environment variables")
            return
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            print("✅ OpenAI client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def _download_and_encode_image(self, image_source: str, use_dropbox_path: bool = False) -> str:
        """
        Download image and encode as base64 for GPT-4 Vision
        
        Args:
            image_source: Either a URL or Dropbox path
            use_dropbox_path: If True, image_source is a Dropbox path and we'll use dropbox_service
            
        Returns:
            Base64 encoded image data URL
        """
        try:
            if use_dropbox_path:
                # Download from Dropbox using the service
                from services.dropbox_service import dropbox_service
                print(f"  Downloading from Dropbox: {image_source}")
                image_content = dropbox_service.download_image_for_ocr(image_source)
            else:
                # Download from URL
                print(f"  Downloading from URL: {image_source}")
                response = requests.get(image_source, timeout=30)
                response.raise_for_status()
                image_content = response.content
            
            # Detect image type from content (magic bytes)
            if image_content.startswith(b'\x89PNG'):
                mime_type = 'image/png'
            elif image_content.startswith(b'\xff\xd8'):
                mime_type = 'image/jpeg'
            elif image_content.startswith(b'GIF'):
                mime_type = 'image/gif'
            else:
                # Check file extension from source
                if image_source.lower().endswith('.png'):
                    mime_type = 'image/png'
                else:
                    mime_type = 'image/jpeg'  # Default fallback
            
            print(f"  Detected mime type: {mime_type}, size: {len(image_content)} bytes")
            
            # Encode to base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            # Return as data URL
            return f"data:{mime_type};base64,{image_base64}"
            
        except Exception as e:
            print(f"❌ Error downloading/encoding image {image_source}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to download image: {str(e)}")
    
    async def process_images_with_gpt4_vision(
        self, 
        image_sources: List[str], 
        settings: ProcessingSettings,
        use_dropbox_path: bool = False
    ) -> str:
        """
        Process multiple images (up to 5) using GPT-4 Vision API for OCR, 
        spell checking, and content enhancement
        
        Args:
            image_sources: List of image URLs or Dropbox paths
            settings: Processing settings
            use_dropbox_path: If True, image_sources are Dropbox paths
        """
        if not self.client:
            print("⚠️ OpenAI client not available, using fallback")
            return "OpenAI client not available. Please configure OPENAI_API_KEY."
        
        if not image_sources or len(image_sources) > 5:
            raise ValueError("Please provide between 1 and 5 images")
        
        try:
            # Create message content with all images
            message_content = [
                {
                    "type": "text",
                    "text": self._generate_vision_prompt(settings, len(image_sources))
                }
            ]
            
            # Download and encode each image as base64
            print(f"Downloading and encoding {len(image_sources)} image(s)...")
            for idx, image_source in enumerate(image_sources):
                print(f"  Processing image {idx + 1}/{len(image_sources)}...")
                base64_image = self._download_and_encode_image(image_source, use_dropbox_path)
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": base64_image,
                        "detail": "high"  # Use high detail for better OCR
                    }
                })
            
            print(f"Sending {len(image_sources)} image(s) to GPT-4 Vision...")
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # GPT-4 Vision model
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at reading handwritten and typed notes from images. Your specialty is:
- Accurately transcribing handwritten text, including cursive and messy handwriting
- Understanding context and correcting spelling errors
- Organizing notes with proper structure and formatting
- Enhancing content with additional context and explanations
- Combining multiple pages of notes into a coherent document"""
                    },
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            print("✅ GPT-4 Vision processing successful")
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"❌ Error processing images with GPT-4 Vision: {str(e)}")
            raise Exception(f"Failed to process images: {str(e)}")
    
    def _generate_vision_prompt(self, settings: ProcessingSettings, num_images: int) -> str:
        """
        Generate prompt for GPT-4 Vision based on settings and number of images
        """
        base_prompt = f"""I have uploaded {num_images} image(s) of my handwritten/typed notes. Please:

1. **Extract and Transcribe**: Carefully read ALL the text from {"each image" if num_images > 1 else "the image"}, including handwritten text. Transcribe everything accurately.

2. **Spell Check**: Fix any spelling errors you notice in the transcribed text.

3. **Enhance and Format**: Transform the notes into a well-organized, comprehensive document.
"""
        
        formatting_instructions = []
        
        if settings.add_bullet_points:
            formatting_instructions.append(
                "- Use bullet points (•) and numbered lists to organize information clearly"
            )
        
        if settings.add_headers:
            formatting_instructions.append(
                "- Add descriptive section headers to create a clear structure"
            )
            formatting_instructions.append(
                "- Use visual dividers (═══) between major sections"
            )
        
        if settings.expand:
            formatting_instructions.append(
                "- Expand the content with additional context and explanations"
            )
            formatting_instructions.append(
                "- Add relevant examples or practical applications"
            )
        
        if settings.summarize:
            formatting_instructions.append(
                "- Include a summary section at the beginning highlighting key points"
            )
            formatting_instructions.append(
                "- End with a conclusion that reinforces main ideas"
            )
        
        if formatting_instructions:
            base_prompt += "\n**Formatting Requirements:**\n" + "\n".join(formatting_instructions)

        if settings.focus_topics:
            focus_text = ", ".join(settings.focus_topics)
            base_prompt += f"\n\n**Priority Concepts:** Highlight and elaborate on the following focus topics: {focus_text}."
        
        if num_images > 1:
            base_prompt += f"""

**Multi-Page Notes**: You have {num_images} pages. Please:
- Read them in order and combine the content into a single coherent document
- Maintain the logical flow between pages
- Note any connections or continuations between pages"""
        
        base_prompt += """

Please provide the enhanced, spell-checked, and beautifully formatted version of the notes."""
        
        return base_prompt
    
    def _split_text_into_chunks(self, text: str, max_chars: Optional[int] = None) -> List[str]:
        """Split long text into balanced chunks that fit within model limits."""
        limit = max_chars or self.chunk_char_limit
        if len(text) <= limit:
            return [text]

        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for para in paragraphs:
            para_with_break = para + "\n\n"
            para_length = len(para_with_break)
            if current_length + para_length > limit and current_chunk:
                chunks.append("".join(current_chunk).strip())
                current_chunk = [para_with_break]
                current_length = para_length
            else:
                current_chunk.append(para_with_break)
                current_length += para_length

        if current_chunk:
            chunks.append("".join(current_chunk).strip())

        return [chunk for chunk in chunks if chunk]

    async def _process_chunk_async(
        self,
        chunk_text: str,
        settings: ProcessingSettings,
        chunk_index: int,
        total_chunks: int,
        semaphore: Optional[asyncio.Semaphore] = None
    ) -> str:
        """Send a single chunk to OpenAI without blocking the event loop."""
        import concurrent.futures
        
        async def _run() -> str:
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return await loop.run_in_executor(
                    pool,
                    self._call_openai_for_chunk,
                    chunk_text,
                    settings,
                    chunk_index,
                    total_chunks
                )

        if semaphore:
            async with semaphore:
                return await _run()
        return await _run()

    def _call_openai_for_chunk(
        self,
        chunk_text: str,
        settings: ProcessingSettings,
        chunk_index: int,
        total_chunks: int
    ) -> str:
        prompt = self._generate_prompt(
            chunk_text,
            settings,
            chunk_index=chunk_index,
            total_chunks=total_chunks
        )

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert content formatter, editor, and writer with exceptional skills in document design and presentation. Your specialty is transforming basic text into beautifully formatted, comprehensive, and engaging documents that are both visually appealing and highly informative."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=4000,
            temperature=0.8
        )

        return response.choices[0].message.content

    def _merge_chunk_responses(self, chunk_responses: List[str]) -> str:
        cleaned = [chunk.strip() for chunk in chunk_responses if chunk and chunk.strip()]
        return "\n\n".join(cleaned)
    
    async def process_text_with_chatgpt(self, text: str, settings: ProcessingSettings) -> str:
        """
        Process text using ChatGPT API based on provided settings
        """
        if not self.client:
            print("⚠️ OpenAI client not available, using fallback enhancement")
            return self._create_fallback_enhanced_text(text, settings)
        
        try:
            cleaned_text = text.strip()
            if not cleaned_text:
                return ""

            chunks = self._split_text_into_chunks(cleaned_text)
            total_chunks = len(chunks)

            if total_chunks == 1:
                return await self._process_chunk_async(chunks[0], settings, 1, 1)

            print(f"Processing text in {total_chunks} parallel chunks (limit {self.max_parallel_requests})")
            semaphore = asyncio.Semaphore(self.max_parallel_requests)
            tasks = [
                self._process_chunk_async(chunk, settings, idx + 1, total_chunks, semaphore)
                for idx, chunk in enumerate(chunks)
            ]

            chunk_results = await asyncio.gather(*tasks)
            return self._merge_chunk_responses(chunk_results)
        
        except Exception as e:
            print(f"❌ Error processing with ChatGPT: {str(e)}")
            print("🔄 Falling back to local enhancement")
            return self._create_fallback_enhanced_text(text, settings)
    
    def _generate_prompt(
        self,
        text: str,
        settings: ProcessingSettings,
        chunk_index: Optional[int] = None,
        total_chunks: Optional[int] = None
    ) -> str:
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

        if settings.focus_topics:
            topics_text = ", ".join(settings.focus_topics)
            formatting_instructions.append(
                f"Prioritize covering the following focus topics in depth: {topics_text}"
            )
        
        if settings.custom_specifications:
            formatting_instructions.append(
                "Custom instructions from the user (follow these only when they do not conflict with the selected enhancement options): "
                f"{settings.custom_specifications}"
            )
            formatting_instructions.append(
                "If any part of the custom instructions contradicts the selected enhancement options above, obey the selected options exactly and gracefully ignore the conflicting requests."
            )
        
        # Combine all instructions
        all_instructions = base_instructions + formatting_instructions
        
        chunk_context = ""
        if total_chunks and total_chunks > 1:
            chunk_context = f"""

CHUNK CONTEXT:
• This is section {chunk_index} of {total_chunks}.
• Maintain continuity between sections and avoid repeating introductions.
• Only include a final summary if this is the last section.
• Use neutral transitions so the sections merge seamlessly."""

        prompt = f"""You are an expert content formatter and writer. Your task is to transform the provided text into a beautifully formatted, comprehensive, and engaging document.{chunk_context}

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

    async def generate_flashcards(
        self,
        text: str,
        topics: List[str],
        total_cards: int,
        max_per_topic: int = 4
    ) -> List[Dict[str, str]]:
        """Generate flashcards constrained to the provided notes."""
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            return []
        if not self.client:
            print("⚠️ OpenAI client unavailable, cannot generate flashcards")
            return []

        prepared_topics = [topic.strip() for topic in topics if topic and topic.strip()]
        if not prepared_topics:
            return []

        max_cards = min(50, max(total_cards, len(prepared_topics)))
        per_topic_limit = max(1, max_per_topic)

        prompt = f"""
You are an academic studying coach that prepares concise study flashcards strictly from provided notes.

NOTES:
{text}

TOPICS TO COVER: {", ".join(prepared_topics)}

REQUIREMENTS:
- Use ONLY the information found in the notes above. Do not invent facts.
- Provide at most {per_topic_limit} flashcards per topic and no more than {max_cards} flashcards total.
- Definitions must be full sentences with proper punctuation and must not exceed 50 words.
- Format the response as valid JSON: a list where each item contains "topic", "term", and "definition".
- If the notes lack enough information for a topic, skip that topic gracefully.
- The definition text should help a student recall the {per_topic_limit <= 2 and "term" or "term/concept"}.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You create flashcards using only the supplied notes and respond in JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=1200
            )
            raw = response.choices[0].message.content.strip()
            return self._parse_flashcard_response(raw, max_cards, per_topic_limit)
        except Exception as e:
            print(f"Flashcard generation failed: {e}")
            return []

    def _parse_flashcard_response(
        self,
        raw_response: str,
        total_cards: int,
        per_topic_limit: int
    ) -> List[Dict[str, str]]:
        try:
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                cleaned = "\n".join(
                    line for line in cleaned.splitlines()
                    if not line.strip().startswith("```")
                )
            parsed = json.loads(cleaned)
        except Exception as e:
            print(f"Failed to parse flashcard JSON: {e}")
            return []

        cards: List[Dict[str, str]] = []
        topic_counts = defaultdict(int)

        for entry in parsed if isinstance(parsed, list) else []:
            topic = str(entry.get("topic", "")).strip()
            term = str(entry.get("term", "")).strip()
            definition = str(entry.get("definition", "")).strip()

            if not topic or not term or not definition:
                continue

            if topic_counts[topic] >= per_topic_limit:
                continue

            limited_definition = self._limit_definition(definition)
            if not limited_definition:
                continue

            cards.append({
                "topic": topic,
                "term": term,
                "definition": limited_definition
            })
            topic_counts[topic] += 1

            if len(cards) >= total_cards:
                break

        return cards

    def _limit_definition(self, definition: str) -> str:
        words = definition.split()
        if not words:
            return ""
        if len(words) <= 50:
            return " ".join(words)
        trimmed = " ".join(words[:50]).rstrip(",;:")
        if not trimmed.endswith((".", "?", "!")):
            trimmed += "."
        return trimmed

    async def extract_topics_from_text(self, text: str, max_topics: int = 6) -> List[str]:
        """Use OpenAI to extract the most important topics from raw text."""
        cleaned_text = text.strip()
        if not cleaned_text:
            print("No text provided for topic extraction")
            return []
        if not self.client:
            print("No OpenAI client available, using fallback")
            return self._fallback_topic_extraction(cleaned_text, max_topics)

        try:
            print(f"Calling OpenAI for topic extraction with {len(cleaned_text)} chars, max_topics={max_topics}")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You extract key topics from study notes. Return JSON only."
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Identify the top concepts or topics in the following notes. "
                            f"Limit to {max_topics} concise topics. Respond with a JSON array of strings.\n\n"
                            f"NOTES:\n{cleaned_text}"
                        )
                    }
                ],
                temperature=0.2,
                max_tokens=400
            )
            raw = response.choices[0].message.content.strip()
            print(f"OpenAI raw response: {raw}")
            topics = self._parse_topics_response(raw, max_topics)
            print(f"Parsed topics: {topics}")
            return topics
        except Exception as e:
            print(f"Topic extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_topic_extraction(cleaned_text, max_topics)

    async def extract_topics_from_images(
        self,
        image_contents: List[bytes],
        filenames: Optional[List[str]] = None,
        max_topics: int = 6
    ) -> List[str]:
        """Use GPT-4 Vision to extract topics from raw image bytes."""
        if not image_contents:
            return []
        if not self.client:
            return []

        try:
            message_content: List[Dict[str, Any]] = [
                {
                    "type": "text",
                    "text": (
                        "Analyze these note images and identify the most important concepts. "
                        f"Return up to {max_topics} concise topic names as a JSON array."
                    )
                }
            ]

            for idx, content in enumerate(image_contents):
                if content.startswith(b'\x89PNG'):
                    mime_type = 'image/png'
                elif content.startswith(b'\xff\xd8'):
                    mime_type = 'image/jpeg'
                elif content[:4] == b'%PDF':
                    mime_type = 'application/pdf'
                else:
                    mime_type = 'image/jpeg'
                data_url = f"data:{mime_type};base64,{base64.b64encode(content).decode('utf-8')}"
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data_url,
                        "detail": "high"
                    }
                })

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You analyze handwritten note images and output concise topic lists as JSON."
                    },
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
                temperature=0.2,
                max_tokens=400
            )

            raw = response.choices[0].message.content.strip()
            return self._parse_topics_response(raw, max_topics)
        except Exception as e:
            print(f"Image topic extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _parse_topics_response(self, raw_response: str, max_topics: int) -> List[str]:
        print(f"Parsing topics response: {raw_response[:200]}")
        try:
            # Some models wrap JSON in markdown fences
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                print("Removing markdown code fences")
                lines = cleaned.splitlines()
                # Remove first line if it's a code fence (e.g., ```json or ```)
                if lines and lines[0].strip().startswith("```"):
                    lines = lines[1:]
                # Remove last line if it's a closing code fence
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            
            print(f"Cleaned response: {cleaned[:200]}")
            parsed = json.loads(cleaned)
            print(f"Parsed JSON: {parsed}")
            if isinstance(parsed, list):
                topics = [str(item).strip() for item in parsed if str(item).strip()]
                print(f"Extracted topics: {topics}")
                return topics[:max_topics]
        except Exception as e:
            print(f"Failed to parse topics JSON: {e}")
            import traceback
            traceback.print_exc()
        print("Using fallback extraction")
        return self._fallback_topic_extraction(raw_response, max_topics)

    def _fallback_topic_extraction(self, text: str, max_topics: int) -> List[str]:
        from collections import Counter
        import re
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9-]+", text.lower())
        stopwords = {"the", "and", "or", "of", "in", "to", "a", "for", "is", "are", "on", "with"}
        filtered = [t for t in tokens if t not in stopwords and len(t) > 3]
        most_common = Counter(filtered).most_common(max_topics)
        return [word.title() for word, _ in most_common]
    
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
