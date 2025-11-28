"""
Image Processor - Production Ready for HF Spaces Free Tier
Skips local OCR models, uses Cloud Vision API only if configured
"""

import httpx
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image
from io import BytesIO

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError

logger = get_logger(__name__)


class ImageProcessor:
    """
    Image processor optimized for HF Spaces free tier
    - No heavy local models (saves memory and CPU)
    - Cloud Vision API only (if configured)
    - Graceful fallback with helpful messages
    """
    
    def __init__(self, timeout: int = 60):
        """
        Initialize image processor
        
        Args:
            timeout: HTTP timeout for downloading images
        """
        self.timeout = timeout
        self.temp_dir = tempfile.mkdtemp(prefix='image_processing_')
        
        # HTTP headers for image downloads
        self.download_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'DNT': '1'
        }
        
        # Check if Cloud Vision is available
        self.cloud_vision_available = self._check_cloud_vision()
        
        logger.info(
            f"ImageProcessor initialized | "
            f"Cloud Vision API: {'✓ Available' if self.cloud_vision_available else '✗ Not configured'} | "
            f"Mode: Production (HF Spaces Free Tier)"
        )
        
        if not self.cloud_vision_available:
            logger.warning(
                "⚠️  Google Cloud Vision API not configured. "
                "OCR will return placeholders. "
                "Set GOOGLE_CREDENTIALS_BASE64 to enable OCR."
            )
    
    def _check_cloud_vision(self) -> bool:
        """
        Check if Google Cloud Vision API is configured and available
        
        Returns:
            bool: True if Cloud Vision can be used
        """
        # Check if credentials are configured
        if not settings.is_cloud_logging_enabled():
            return False
        
        # Try to import the library
        try:
            from google.cloud import vision
            return True
        except ImportError:
            logger.warning("google-cloud-vision not installed")
            return False
        except Exception as e:
            logger.warning(f"Cloud Vision check failed: {e}")
            return False
    
    async def extract_text_from_image(self, url: str) -> Dict[str, Any]:
        """
        Extract text from image using OCR
        
        Strategy:
        1. If Cloud Vision available → Use it
        2. Otherwise → Return helpful placeholder
        
        Args:
            url: URL to image file
            
        Returns:
            Dict with OCR result
        """
        logger.info(f"🖼️  OCR request for image: {url}")
        
        # Try Cloud Vision if available
        if self.cloud_vision_available:
            try:
                logger.info("Using Google Cloud Vision API for OCR")
                result = await self._ocr_with_cloud_vision(url)
                
                logger.info(
                    f"✅ Cloud Vision OCR complete | "
                    f"Text length: {len(result['extracted_text'])} chars | "
                    f"Confidence: {result['confidence']:.2f}"
                )
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Cloud Vision OCR failed: {str(e)}", exc_info=True)
                
                # Return error result
                return {
                    'url': url,
                    'extracted_text': f'[OCR failed: {str(e)}]',
                    'confidence': 0.0,
                    'method': 'cloud_vision',
                    'status': 'error',
                    'error': str(e)
                }
        
        # OCR not available - return informative placeholder
        logger.warning(
            f"⚠️  OCR unavailable for image: {url}. "
            f"Cloud Vision API not configured."
        )
        
        return {
            'url': url,
            'extracted_text': (
                f'[OCR unavailable. Image URL: {url}. '
                f'To enable OCR, configure Google Cloud Vision API '
                f'by setting GOOGLE_CREDENTIALS_BASE64 in environment.]'
            ),
            'confidence': 0.0,
            'method': 'none',
            'status': 'unavailable',
            'reason': 'Cloud Vision API not configured'
        }
    
    async def _ocr_with_cloud_vision(self, image_url: str) -> Dict[str, Any]:
        """
        Extract text using Google Cloud Vision API
        Tries URL first, falls back to downloading and sending bytes
        
        Args:
            image_url: URL to image
            
        Returns:
            Dict with extracted text and metadata
        """
        from google.cloud import vision
        
        # Initialize client
        client = vision.ImageAnnotatorClient()
        
        # Strategy 1: Try using URL directly (faster, but doesn't work for all URLs)
        try:
            logger.debug("Attempting Cloud Vision OCR with URL...")
            image = vision.Image()
            image.source.image_uri = image_url
            
            response = client.text_detection(image=image)
            
            # Check if URL-based request worked
            if not response.error.message:
                logger.debug("✓ URL-based OCR succeeded")
                return self._parse_cloud_vision_response(response, image_url)
            else:
                logger.debug(f"URL-based OCR blocked: {response.error.message}")
                # Fall through to Strategy 2
        
        except Exception as e:
            logger.debug(f"URL-based OCR error: {e}")
            # Fall through to Strategy 2
        
        # Strategy 2: Download image and send bytes (works for all URLs)
        logger.debug("Downloading image for Cloud Vision OCR...")
        
        try:
            # Download image
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.download_headers
            ) as http_client:
                response_http = await http_client.get(image_url)
                response_http.raise_for_status()
            
            logger.debug(f"Downloaded {len(response_http.content)} bytes")
            
            # Create image from content bytes
            image = vision.Image(content=response_http.content)
            
            # Perform text detection
            response = client.text_detection(image=image)
            
            # Check for errors
            if response.error.message:
                raise Exception(f"Cloud Vision API error: {response.error.message}")
            
            logger.debug("✓ Bytes-based OCR succeeded")
            return self._parse_cloud_vision_response(response, image_url)
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to download image for OCR: {e}")
            raise Exception(f"Could not download image: {e}")
        
        except Exception as e:
            logger.error(f"Cloud Vision OCR with bytes failed: {e}")
            raise
    
    def _parse_cloud_vision_response(
        self,
        response,
        image_url: str
    ) -> Dict[str, Any]:
        """
        Parse Cloud Vision API response
        
        Args:
            response: Cloud Vision API response
            image_url: Original image URL
            
        Returns:
            Dict with extracted text and metadata
        """
        # Extract text annotations
        texts = response.text_annotations
        
        if not texts:
            # No text found in image
            logger.info("Cloud Vision found no text in image")
            return {
                'url': image_url,
                'extracted_text': '',
                'confidence': 0.0,
                'method': 'cloud_vision',
                'language': 'none',
                'status': 'no_text_found'
            }
        
        # First annotation contains all detected text
        full_text = texts[0].description
        
        # Cloud Vision doesn't provide overall confidence
        # Use presence of text as indicator
        confidence = 0.95 if full_text.strip() else 0.0
        
        # Try to detect language from response
        language = 'auto-detected'
        if hasattr(texts[0], 'locale') and texts[0].locale:
            language = texts[0].locale
        
        return {
            'url': image_url,
            'extracted_text': full_text,
            'confidence': confidence,
            'method': 'cloud_vision',
            'language': language,
            'status': 'success',
            'word_count': len(full_text.split())
        }
    
    async def analyze_image(self, url: str) -> Dict[str, Any]:
        """
        Analyze image and extract basic properties
        Uses lightweight PIL analysis (no Cloud Vision needed)
        
        Args:
            url: URL to image file
            
        Returns:
            Dict with image analysis
        """
        logger.info(f"🔍 Analyzing image: {url}")
        
        try:
            # Download image with proper headers
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.download_headers
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
            
            # Load image with PIL
            image = Image.open(BytesIO(response.content))
            
            # Extract properties
            width, height = image.size
            mode = image.mode
            format_name = image.format or 'unknown'
            file_size_kb = len(response.content) / 1024
            
            # Calculate aspect ratio
            aspect_ratio = width / height if height > 0 else 0
            
            # Determine orientation
            if width > height:
                orientation = 'landscape'
            elif height > width:
                orientation = 'portrait'
            else:
                orientation = 'square'
            
            description = (
                f"{width}x{height} {format_name} image "
                f"({file_size_kb:.1f} KB, {orientation})"
            )
            
            logger.info(f"✅ Image analyzed: {description}")
            
            return {
                'url': url,
                'description': description,
                'properties': {
                    'width': width,
                    'height': height,
                    'format': format_name,
                    'mode': mode,
                    'size_kb': round(file_size_kb, 2),
                    'aspect_ratio': round(aspect_ratio, 2),
                    'orientation': orientation
                },
                'status': 'success',
                'method': 'pil'
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error downloading image: {e.response.status_code}")
            return {
                'url': url,
                'description': f'Image download failed (HTTP {e.response.status_code})',
                'status': 'download_failed',
                'error': f"HTTP {e.response.status_code}",
                'note': 'Image may be protected or require authentication'
            }
        
        except Exception as e:
            logger.error(f"❌ Image analysis failed: {str(e)}", exc_info=True)
            return {
                'url': url,
                'description': '',
                'status': 'failed',
                'error': str(e)
            }
    
    async def download_image(self, url: str) -> Optional[str]:
        """
        Download image and save to temp directory
        
        Args:
            url: URL to image
            
        Returns:
            str: Path to downloaded image, or None if failed
        """
        try:
            logger.debug(f"Downloading image: {url}")
            
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.download_headers
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '').lower()
            extension = self._get_image_extension(url, content_type)
            
            # Save to temp file
            file_name = f"image_{hash(url)}{extension}"
            file_path = os.path.join(self.temp_dir, file_name)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.debug(f"Image saved to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None
    
    def _get_image_extension(self, url: str, content_type: str) -> str:
        """Determine image file extension from URL or content type"""
        # Try to get from URL
        path = Path(url.split('?')[0])
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']
        
        if path.suffix.lower() in valid_extensions:
            return path.suffix.lower()
        
        # Map content type to extension
        content_type_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/webp': '.webp',
            'image/tiff': '.tiff'
        }
        
        for ct, ext in content_type_map.items():
            if ct in content_type:
                return ext
        
        # Default to .jpg
        return '.jpg'
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.debug(f"✓ Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")
