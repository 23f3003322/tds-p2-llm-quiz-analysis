"""
File Downloader
Handles downloading files (PDF, CSV, ZIP, etc.)
"""

import httpx
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError

logger = get_logger(__name__)


class FileDownloader:
    """
    Downloads files from URLs and extracts content
    """
    
    def __init__(self, timeout: int = 60):
        """
        Initialize file downloader
        
        Args:
            timeout: Download timeout in seconds
        """
        self.timeout = timeout
        self.temp_dir = tempfile.mkdtemp(prefix='task_downloads_')
        logger.debug(f"FileDownloader initialized | Temp dir: {self.temp_dir}")
    
    async def download_file(self, url: str) -> Dict[str, Any]:
        """
        Download a file from URL
        
        Args:
            url: URL to download from
            
        Returns:
            Dict with file info and content:
            {
                'url': str,
                'file_path': str,
                'file_type': str,
                'content': str (if text-based),
                'size_bytes': int
            }
        """
        logger.info(f"📥 Downloading file from: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
            
            # Determine file type from content-type or URL
            content_type = response.headers.get('content-type', '').lower()
            file_extension = self._get_file_extension(url, content_type)
            
            # Save to temp file
            file_name = f"download_{hash(url)}{file_extension}"
            file_path = os.path.join(self.temp_dir, file_name)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            
            logger.info(
                f"✅ File downloaded | Type: {file_extension} | "
                f"Size: {file_size / 1024:.2f} KB"
            )
            
            result = {
                'url': url,
                'file_path': file_path,
                'file_type': file_extension.lstrip('.'),
                'size_bytes': file_size,
                'content_type': content_type
            }
            
            # Extract text content if it's a text-based file
            if file_extension in ['.txt', '.csv', '.json', '.xml', '.html']:
                content = await self._extract_text_content(file_path, file_extension)
                result['content'] = content
            elif file_extension == '.pdf':
                content = await self._extract_pdf_content(file_path)
                result['content'] = content
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error downloading file: {e.response.status_code}")
            raise TaskProcessingError(f"Failed to download file: HTTP {e.response.status_code}")
        
        except Exception as e:
            logger.error(f"❌ Failed to download file: {str(e)}", exc_info=True)
            raise TaskProcessingError(f"Failed to download file: {str(e)}")
    
    def _get_file_extension(self, url: str, content_type: str) -> str:
        """Determine file extension from URL or content type"""
        # Try to get from URL
        path = Path(url.split('?')[0])  # Remove query params
        if path.suffix:
            return path.suffix.lower()
        
        # Try from content type
        content_type_map = {
            'application/pdf': '.pdf',
            'text/csv': '.csv',
            'application/csv': '.csv',
            'application/json': '.json',
            'text/plain': '.txt',
            'text/html': '.html',
            'application/xml': '.xml',
            'application/zip': '.zip',
            'application/x-zip-compressed': '.zip'
        }
        
        for ct, ext in content_type_map.items():
            if ct in content_type:
                return ext
        
        return '.bin'  # Unknown type
    
    async def _extract_text_content(self, file_path: str, file_type: str) -> str:
        """Extract text from text-based files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            logger.debug(f"Extracted text content: {len(content)} chars")
            return content
            
        except Exception as e:
            logger.warning(f"Failed to extract text content: {e}")
            return ""
    
    async def _extract_pdf_content(self, file_path: str) -> str:
        """Extract text from PDF files"""
        try:
            # Try to use PyPDF2 if available
            try:
                import PyPDF2
                
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text_parts = []
                    
                    for page in pdf_reader.pages:
                        text_parts.append(page.extract_text())
                    
                    content = '\n'.join(text_parts)
                    logger.debug(f"Extracted PDF content: {len(content)} chars")
                    return content
                    
            except ImportError:
                logger.warning("PyPDF2 not installed, PDF content extraction skipped")
                return f"[PDF file downloaded but text extraction requires PyPDF2: {file_path}]"
            
        except Exception as e:
            logger.warning(f"Failed to extract PDF content: {e}")
            return f"[PDF file downloaded but text extraction failed: {file_path}]"
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")
