"""
OCR Service using EasyOCR with OpenCV preprocessing
====================================================

This service handles:
1. Image download from Dropbox
2. Image preprocessing using OpenCV for better OCR accuracy
3. Text extraction using EasyOCR (no system dependencies required)
4. Spelling and grammar correction using OpenAI API
5. Integration with ChatGPT service for note embellishment

Complete Flow:
-------------
User uploads image → main.py → OCR Service → ChatGPT Service → Database

Detailed Steps:
1. User uploads image via frontend
2. main.py: Stores image in Dropbox, creates DB record
3. main.py: Calls process_image_note_background() as background task
4. OCR Service (this file):
   a. Downloads image from Dropbox
   b. Preprocesses with OpenCV (grayscale, blur, threshold, morphology)
   c. Extracts text with EasyOCR
   d. Corrects spelling/OCR errors with OpenAI GPT-3.5
   e. Returns clean text
5. main.py: Receives clean text, updates note.text field
6. ChatGPT Service (chatgpt_service.py):
   a. Takes clean text
   b. Applies user settings (headers, bullets, expand, summarize)
   c. Embellishes with GPT-4 mini
   d. Returns beautifully formatted content
7. main.py: Updates note.processed_content field, marks as COMPLETED
8. Frontend: Displays embellished notes to user

Technology Stack:
-----------------
• EasyOCR: Text extraction (Python-based, no Tesseract dependency)
• OpenCV (cv2): Image preprocessing for better accuracy
• OpenAI GPT-3.5: Spelling/OCR error correction
• OpenAI GPT-4 mini: Full text embellishment (in chatgpt_service.py)
• Dropbox API: Image storage
• SQLite: Metadata and text storage

Key Features:
-------------
✅ No system dependencies (EasyOCR is pure Python)
✅ Advanced image preprocessing with OpenCV
✅ Two-stage AI processing (correction + embellishment)
✅ Lazy loading of EasyOCR (faster startup)
✅ Comprehensive error handling and logging
✅ Supports both images and PDFs
"""

import tempfile
import os
from typing import Optional, List
import numpy as np
import cv2  # OpenCV for advanced image preprocessing
from PIL import Image
import fitz  # PyMuPDF for PDF processing
from services.dropbox_service import dropbox_service
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OCRService:
    def __init__(self):
        """
        Initialize OCR service with EasyOCR
        
        Features:
        - EasyOCR: Python-based OCR engine (no system dependencies)
        - OpenCV: Advanced image preprocessing for accuracy improvement
        - OpenAI: Spelling and grammar correction
        """
        self.reader = None  # EasyOCR reader (lazy-loaded)
        
        # Initialize OpenAI client for text correction
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        print("✅ OCR Service initialized (EasyOCR will load on first use)")
    
    def extract_text_from_image_url(self, dropbox_path: str) -> str:
        """
        Complete OCR pipeline: Extract and correct text from an image stored in Dropbox
        
        Args:
            dropbox_path: Dropbox path for downloading the image
            
        Returns:
            Extracted and corrected text (ready for ChatGPT embellishment)
            
        Process Flow:
        1. Download image from Dropbox → temporary file
        2. Preprocess image with OpenCV → enhanced image
        3. Extract text with EasyOCR → raw text
        4. Correct text with OpenAI → clean text
        5. Return clean text → ready for chatgpt_service.py to embellish
        
        Note: This function only handles OCR and basic correction.
        The full note embellishment (headers, bullet points, expansion)
        is done by the ChatGPT service in main.py after this returns.
        """
        temp_file_path = None
        try:
            print(f"📥 Starting OCR pipeline for: {dropbox_path}")
            
            # Step 1: Download image from Dropbox
            print(f"🔄 Downloading image from Dropbox...")
            file_content = dropbox_service.download_image_for_ocr(dropbox_path)
            
            # Create a temporary file to store the downloaded content
            file_extension = os.path.splitext(dropbox_path)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            print(f"✅ Image downloaded to temporary file: {temp_file_path}")
            
            # Step 2: Extract text using OCR (with OpenCV preprocessing inside)
            print(f"🔄 Extracting text with EasyOCR...")
            raw_text = self._extract_text_from_file(temp_file_path)
            
            if not raw_text.strip():
                raise Exception("No text could be extracted from the image")
            
            print(f"✅ Raw text extracted: {len(raw_text)} characters")
            
            # Step 3: Correct spelling and improve formatting using OpenAI
            print(f"🔄 Correcting OCR errors with OpenAI...")
            corrected_text = self._correct_text_with_ai(raw_text)
            
            print(f"✅ OCR pipeline completed successfully!")
            print(f"📊 Final text length: {len(corrected_text)} characters")
            print(f"🎯 Text is now ready for ChatGPT embellishment in main.py")
            
            return corrected_text
        
        except Exception as e:
            error_msg = f"OCR processing failed: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                print(f"🧹 Cleaned up temporary file")
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text from a local file (image or PDF)
        
        Args:
            file_path: Path to the local file
            
        Returns:
            Raw extracted text
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self._extract_text_from_pdf(file_path)
        else:
            return self._extract_text_from_image_file(file_path)
    
    def _extract_text_from_image_file(self, image_path: str) -> str:
        """
        Extract text from an image file using EasyOCR
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Raw extracted text
            
        Process:
        1. Load EasyOCR reader (lazy initialization on first use)
        2. Try multiple preprocessing approaches (for handwriting support)
        3. Extract text using EasyOCR with handwriting-friendly settings
        4. Return the extracted text
        """
        try:
            # Lazy-load EasyOCR reader on first use (to avoid slow startup)
            if self.reader is None:
                print("🔄 Loading EasyOCR reader (this may take a moment on first use)...")
                import easyocr
                # Initialize reader for English (can add more languages if needed)
                self.reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if CUDA is available
                print("✅ EasyOCR reader loaded successfully")
            
            # Try multiple preprocessing approaches
            print("🔄 Attempting OCR with different preprocessing methods...")
            
            # Approach 1: Try with standard preprocessing (best for printed text)
            processed_image_path = self._preprocess_image_with_opencv(image_path)
            
            # Use EasyOCR to extract text with settings optimized for handwriting
            # readtext returns a list of tuples: (bbox, text, confidence)
            # Lower confidence threshold for handwriting (default is 0.7)
            results = self.reader.readtext(
                processed_image_path,
                paragraph=False,  # Don't merge text into paragraphs
                detail=1,  # Return detailed info including confidence
                text_threshold=0.4,  # Lower threshold for handwriting (default 0.7)
                low_text=0.3,  # Lower threshold for text detection
                link_threshold=0.3,  # Lower threshold for linking text
                canvas_size=2560,  # Larger canvas for better quality
                mag_ratio=1.5  # Magnification ratio for better recognition
            )
            
            print(f"📊 Found {len(results)} text regions with standard preprocessing")
            
            # If we got poor results, try with minimal preprocessing (better for handwriting)
            if len(results) < 3 or (results and sum(r[2] for r in results) / len(results) < 0.5):
                print("🔄 Trying with minimal preprocessing (better for handwriting)...")
                
                # Clean up first processed image
                if os.path.exists(processed_image_path) and processed_image_path != image_path:
                    os.unlink(processed_image_path)
                
                # Try with just grayscale conversion (no aggressive processing)
                minimal_processed = self._minimal_preprocess(image_path)
                
                results_minimal = self.reader.readtext(
                    minimal_processed,
                    paragraph=False,
                    detail=1,
                    text_threshold=0.4,
                    low_text=0.3,
                    link_threshold=0.3,
                    canvas_size=2560,
                    mag_ratio=1.5
                )
                
                print(f"📊 Found {len(results_minimal)} text regions with minimal preprocessing")
                
                # Use whichever approach found more text
                if len(results_minimal) > len(results):
                    results = results_minimal
                    processed_image_path = minimal_processed
                    print("✅ Using minimal preprocessing results")
                else:
                    if os.path.exists(minimal_processed) and minimal_processed != image_path:
                        os.unlink(minimal_processed)
                    print("✅ Using standard preprocessing results")
            
            # Extract text from results, sorted by vertical position (top to bottom)
            # Sort by y-coordinate of bounding box
            sorted_results = sorted(results, key=lambda x: x[0][0][1])  # x[0][0][1] is top-left y
            
            # Join text with spaces, preserving confidence info
            text_parts = []
            for bbox, text, confidence in sorted_results:
                if confidence > 0.3:  # Only include text with some confidence
                    text_parts.append(text)
                    print(f"  📝 Detected: '{text}' (confidence: {confidence:.2f})")
            
            extracted_text = ' '.join(text_parts)
            
            # Clean up processed image if it's different from original
            if processed_image_path != image_path and os.path.exists(processed_image_path):
                os.unlink(processed_image_path)
            
            if not extracted_text.strip():
                raise Exception("No text could be extracted from the image. This may be due to: 1) Handwriting that is too unclear, 2) Very low image quality, 3) Non-standard fonts")
            
            print(f"✅ Successfully extracted {len(extracted_text)} characters from image")
            return extracted_text.strip()
            
        except ImportError:
            # EasyOCR not installed yet
            error_msg = "EasyOCR is not installed. Please wait for the installation to complete."
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"Image OCR failed: {str(e)}"
            print(f"❌ Error in image OCR: {error_msg}")
            raise Exception(error_msg)
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using PyMuPDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Raw extracted text
        """
        try:
            doc = fitz.open(pdf_path)
            text_content = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # If text extraction returns empty, try OCR on the page
                if not text.strip():
                    # Convert page to image and OCR it
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    
                    # Save to temporary file for OCR
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
                        temp_img.write(img_data)
                        temp_img_path = temp_img.name
                    
                    try:
                        ocr_text = self._extract_text_from_image_file(temp_img_path)
                        text_content.append(ocr_text)
                    finally:
                        os.unlink(temp_img_path)
                else:
                    text_content.append(text)
            
            doc.close()
            return '\n'.join(text_content)
        
        except Exception as e:
            print(f"Error in PDF OCR: {str(e)}")
            raise Exception(f"PDF OCR failed: {str(e)}")
    
    def _preprocess_image_with_opencv(self, image_path: str) -> str:
        """
        Preprocess image using OpenCV to improve OCR accuracy
        
        Args:
            image_path: Path to the original image
            
        Returns:
            Path to processed image
            
        OpenCV Preprocessing Steps:
        1. Convert to grayscale (reduces noise, improves text contrast)
        2. Apply Gaussian blur (removes small noise)
        3. Apply adaptive thresholding (binarizes text for better recognition)
        4. Apply morphological operations (removes small artifacts)
        5. Resize if needed (optimal size for OCR)
        """
        try:
            # Read image using OpenCV
            img = cv2.imread(image_path)
            
            if img is None:
                print(f"⚠️ Could not load image with OpenCV, using original: {image_path}")
                return image_path
            
            # Get original dimensions
            height, width = img.shape[:2]
            print(f"📐 Original image size: {width}x{height}")
            
            # Step 1: Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Step 2: Apply Gaussian blur to reduce noise
            # Kernel size (5,5) works well for most text images
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Step 3: Apply adaptive thresholding for better text extraction
            # This works better than simple thresholding for images with varying lighting
            thresh = cv2.adaptiveThreshold(
                blurred, 
                255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                11,  # Block size
                2    # Constant subtracted from mean
            )
            
            # Step 4: Apply morphological operations to remove small noise
            # Create a kernel for morphological operations
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
            
            # Step 5: Resize if image is too large or too small
            # Optimal size for OCR is around 2000-3000 pixels on the longer side
            max_dimension = 3000
            min_dimension = 500
            
            if max(width, height) > max_dimension:
                # Image is too large, resize down
                scale = max_dimension / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                processed = cv2.resize(processed, (new_width, new_height), interpolation=cv2.INTER_AREA)
                print(f"📉 Resized large image to: {new_width}x{new_height}")
            
            elif max(width, height) < min_dimension:
                # Image is too small, resize up
                scale = min_dimension / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                processed = cv2.resize(processed, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                print(f"📈 Resized small image to: {new_width}x{new_height}")
            
            # Save processed image to a temporary file
            processed_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
            cv2.imwrite(processed_path, processed)
            
            print(f"✅ Image preprocessed successfully with OpenCV")
            return processed_path
            
        except Exception as e:
            print(f"⚠️ Error preprocessing image with OpenCV: {str(e)}")
            print(f"🔄 Falling back to original image")
            return image_path  # Return original path if preprocessing fails
    
    def _minimal_preprocess(self, image_path: str) -> str:
        """
        Minimal preprocessing for handwritten text (gentler approach)
        
        Args:
            image_path: Path to the original image
            
        Returns:
            Path to minimally processed image
            
        This approach is better for handwritten text because:
        - No aggressive thresholding that can break up handwriting
        - Preserves natural stroke variations
        - Only does basic grayscale conversion and resizing
        """
        try:
            # Read image using OpenCV
            img = cv2.imread(image_path)
            
            if img is None:
                print(f"⚠️ Could not load image, using original: {image_path}")
                return image_path
            
            # Get original dimensions
            height, width = img.shape[:2]
            
            # Step 1: Convert to grayscale only (no thresholding for handwriting)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Step 2: Apply very gentle denoising (preserves handwriting details)
            denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
            
            # Step 3: Slight contrast enhancement (helps with faint handwriting)
            # Using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Step 4: Resize if needed (same as standard preprocessing)
            max_dimension = 3000
            min_dimension = 500
            
            if max(width, height) > max_dimension:
                scale = max_dimension / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                enhanced = cv2.resize(enhanced, (new_width, new_height), interpolation=cv2.INTER_AREA)
                print(f"📉 Resized large image to: {new_width}x{new_height}")
            
            elif max(width, height) < min_dimension:
                scale = min_dimension / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                enhanced = cv2.resize(enhanced, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                print(f"📈 Resized small image to: {new_width}x{new_height}")
            
            # Save minimally processed image
            processed_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
            cv2.imwrite(processed_path, enhanced)
            
            print(f"✅ Image preprocessed with minimal processing (handwriting mode)")
            return processed_path
            
        except Exception as e:
            print(f"⚠️ Error in minimal preprocessing: {str(e)}")
            return image_path
    
    def _correct_text_with_ai(self, raw_text: str) -> str:
        """
        Use OpenAI to correct spelling errors and improve formatting
        
        Args:
            raw_text: Raw text from OCR (may contain spelling errors)
            
        Returns:
            Corrected and formatted text
            
        This function:
        1. Takes the raw OCR output (which often has errors)
        2. Uses OpenAI API to fix spelling mistakes
        3. Improves basic formatting
        4. Returns clean text ready for ChatGPT embellishment
        
        Note: This is different from the main ChatGPT embellishment service.
        This only does basic corrections, not full note enhancement.
        """
        if not raw_text.strip():
            print("⚠️ No text to correct")
            return raw_text
        
        try:
            print(f"🔄 Correcting OCR text with OpenAI ({len(raw_text)} characters)...")
            
            # Create a focused prompt for OCR error correction only
            prompt = f"""You are an OCR text correction specialist. Your job is to fix spelling errors and OCR mistakes in the following text that was extracted from an image.

INSTRUCTIONS:
• Fix obvious OCR errors (e.g., "teh" → "the", "c0mputer" → "computer")
• Correct spelling mistakes
• Preserve the original structure and meaning
• Do NOT add new content or embellish
• Do NOT add formatting like headers or bullet points
• Keep line breaks and paragraph structure
• Return ONLY the corrected text

TEXT TO CORRECT:
{raw_text}

Corrected text:"""
            
            # Call OpenAI API for correction
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using GPT-3.5 for cost-effective correction
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a text correction specialist focused on fixing OCR errors and spelling mistakes while preserving the original content structure."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.1  # Low temperature for consistent corrections
            )
            
            corrected_text = response.choices[0].message.content.strip()
            print(f"✅ Text corrected successfully ({len(corrected_text)} characters)")
            
            return corrected_text
        
        except Exception as e:
            print(f"⚠️ Error correcting text with AI: {str(e)}")
            print(f"🔄 Returning original text without corrections")
            # Return original text if AI correction fails
            return raw_text

# Create a global instance
ocr_service = OCRService()
