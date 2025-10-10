import pytesseract
import tempfile
import os
from typing import Optional, List
from PIL import Image, ImageEnhance, ImageFilter
import fitz  # PyMuPDF for PDF processing
from dropbox_service import dropbox_service
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OCRService:
    def __init__(self):
        """Initialize OCR service with pytesseract"""
        # Set tesseract path if needed (uncomment and modify if tesseract is not in PATH)
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'
        
        # Initialize OpenAI client for text correction
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def extract_text_from_image_url(self, dropbox_path: str) -> str:
        """
        Extract text from an image stored in Dropbox
        
        Args:
            dropbox_path: Dropbox path for downloading
            
        Returns:
            Extracted and corrected text
        """
        temp_file_path = None
        try:
            # Download image from Dropbox
            file_content = dropbox_service.download_image_for_ocr(dropbox_path)
            
            # Create a temporary file to store the content
            file_extension = os.path.splitext(dropbox_path)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Extract text using OCR
            raw_text = self._extract_text_from_file(temp_file_path)
            
            # Correct spelling and improve formatting using OpenAI
            corrected_text = self._correct_text_with_ai(raw_text)
            
            return corrected_text
        
        except Exception as e:
            print(f"Error extracting text from image: {str(e)}")
            raise Exception(f"OCR processing failed: {str(e)}")
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
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
        Extract text from an image file using pytesseract
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Raw extracted text
        """
        try:
            # Try to use pytesseract if available
            try:
                # Preprocess image for better OCR results
                processed_image_path = self._preprocess_image(image_path)
                
                # Use pytesseract to extract text
                with Image.open(processed_image_path) as img:
                    # Configure pytesseract for better results
                    custom_config = r'--oem 3 --psm 6'
                    extracted_text = pytesseract.image_to_string(img, config=custom_config)
                
                # Clean up processed image if it's different from original
                if processed_image_path != image_path and os.path.exists(processed_image_path):
                    os.unlink(processed_image_path)
                
                return extracted_text.strip()
                
            except Exception as ocr_error:
                print(f"OCR not available or failed: {str(ocr_error)}")
                # Fallback: return a placeholder message indicating OCR is needed
                return f"[OCR Processing Required] Image uploaded successfully. Please install Tesseract OCR to extract text from images. File: {os.path.basename(image_path)}"
        
        except Exception as e:
            print(f"Error in image OCR: {str(e)}")
            raise Exception(f"Image OCR failed: {str(e)}")
    
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
    
    def _preprocess_image(self, image_path: str) -> str:
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image_path: Path to the original image
            
        Returns:
            Path to processed image (may be the same as input)
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to grayscale for better OCR performance
                img = img.convert('L')
                
                # Enhance contrast and sharpness
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(2.0)
                
                # Get image size
                width, height = img.size
                
                # If image is very large, resize it to improve processing speed
                max_dimension = 2000
                if max(width, height) > max_dimension:
                    ratio = max_dimension / max(width, height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # If image is too small, resize it up
                if max(width, height) < 300:
                    scale_factor = 300 / max(width, height)
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save processed image
                processed_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
                img.save(processed_path, 'PNG')
                return processed_path
        
        except Exception as e:
            print(f"Error preprocessing image: {str(e)}")
            return image_path  # Return original path if preprocessing fails
    
    def _correct_text_with_ai(self, raw_text: str) -> str:
        """
        Use OpenAI to correct spelling errors and improve formatting
        
        Args:
            raw_text: Raw text from OCR
            
        Returns:
            Corrected and formatted text
        """
        if not raw_text.strip():
            return raw_text
        
        try:
            prompt = f"""
            Please correct the spelling errors and improve the formatting of this text that was extracted from an image using OCR. 
            Keep the original meaning and structure, but fix any obvious OCR errors, spelling mistakes, and improve readability.
            
            Text to correct:
            {raw_text}
            
            Please return only the corrected text without any additional commentary.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that corrects OCR text while preserving the original meaning and structure."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            corrected_text = response.choices[0].message.content.strip()
            return corrected_text
        
        except Exception as e:
            print(f"Error correcting text with AI: {str(e)}")
            # Return original text if AI correction fails
            return raw_text

# Create a global instance
ocr_service = OCRService()
