"""
Task Fetcher Service - Enhanced Version
Fetches and extracts task descriptions from URLs with intelligent content detection
"""

import httpx
import json
import base64
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError

logger = get_logger(__name__)


class TaskFetcher:
    """
    Enhanced service for fetching and extracting task descriptions from URLs
    Handles multiple content types and detects special elements requiring processing
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize TaskFetcher
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client = None
        logger.debug("TaskFetcher initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    async def fetch_task(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract task description from URL with intelligent detection
        
        Args:
            url: URL to fetch task from
            
        Returns:
            Dict containing task information:
            {
                "task_description": str,
                "raw_content": str,
                "content_type": str,
                "url": str,
                "needs_llm_analysis": bool,
                "metadata": dict with special_elements, etc.
            }
            
        Raises:
            TaskProcessingError: If fetching or extraction fails
        """
        logger.info(f"📥 Fetching task from URL: {url}")
        
        # Validate URL
        if not self._is_valid_url(url):
            logger.error(f"❌ Invalid URL format: {url}")
            raise TaskProcessingError(f"Invalid URL format: {url}")
        
        try:
            # Fetch content
            response = await self._fetch_url(url)
            
            # Detect content type
            content_type = self._detect_content_type(response)
            logger.info(f"📄 Content type detected: {content_type}")
            
            # Extract task based on content type
            task_info = await self._extract_task(response, content_type, url)
            
            # Determine if LLM analysis is needed
            task_info['needs_llm_analysis'] = self._needs_llm_analysis(task_info)
            
            if task_info['needs_llm_analysis']:
                logger.warning("🤖 Content requires LLM analysis for complete extraction")
            
            logger.info(f"✅ Task fetched successfully")
            logger.debug(f"Task description length: {len(task_info['task_description'])} chars")
            
            return task_info
            
        except httpx.TimeoutException:
            logger.error(f"⏱️  Timeout fetching URL: {url}")
            raise TaskProcessingError(f"Request timeout for URL: {url}")
        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error {e.response.status_code}: {url}")
            raise TaskProcessingError(
                f"HTTP {e.response.status_code} error fetching URL: {url}"
            )
        
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching task: {str(e)}", exc_info=True)
            raise TaskProcessingError(f"Failed to fetch task from URL: {str(e)}")
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            result = urlparse(url)
            is_valid = all([result.scheme in ['http', 'https'], result.netloc])
            
            if not is_valid:
                logger.warning(f"Invalid URL structure: {url}")
            
            return is_valid
            
        except Exception as e:
            logger.warning(f"URL validation error: {str(e)}")
            return False
    
    async def _fetch_url(self, url: str) -> httpx.Response:
        """
        Fetch content from URL with retry logic
        
        Args:
            url: URL to fetch
            
        Returns:
            httpx.Response: HTTP response
            
        Raises:
            httpx.HTTPStatusError: If HTTP error occurs
            httpx.TimeoutException: If request times out
        """
        max_retries = settings.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries} to fetch URL")
                
                response = await self.client.get(url)
                response.raise_for_status()
                
                logger.debug(
                    f"✓ Fetch successful | Status: {response.status_code} | "
                    f"Size: {len(response.content)} bytes"
                )
                
                return response
                
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                if attempt == max_retries - 1:
                    # Last attempt, raise error
                    raise
                
                logger.warning(
                    f"⚠️  Attempt {attempt + 1} failed: {str(e)} | Retrying..."
                )
                continue
    
    def _detect_content_type(self, response: httpx.Response) -> str:
        """
        Detect content type from response
        
        Args:
            response: HTTP response
            
        Returns:
            str: Content type (json, html, text, pdf, csv, etc.)
        """
        content_type_header = response.headers.get('content-type', '').lower()
        
        # Check content-type header first
        if 'application/json' in content_type_header:
            return 'json'
        elif 'text/html' in content_type_header:
            return 'html'
        elif 'application/pdf' in content_type_header:
            return 'pdf'
        elif 'text/csv' in content_type_header or 'application/csv' in content_type_header:
            return 'csv'
        elif 'audio/' in content_type_header:
            return 'audio'
        elif 'video/' in content_type_header:
            return 'video'
        elif 'image/' in content_type_header:
            return 'image'
        
        # Try to detect from content
        try:
            json.loads(response.text)
            return 'json'
        except:
            if '<html' in response.text.lower()[:100]:
                return 'html'
            return 'text'
    
    async def _extract_task(
        self,
        response: httpx.Response,
        content_type: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Extract task description based on content type
        
        Args:
            response: HTTP response
            content_type: Detected content type
            url: Original URL
            
        Returns:
            Dict with task information
        """
        extractors = {
            'json': self._extract_from_json,
            'html': self._extract_from_html,
            'text': self._extract_from_text,
            'pdf': self._extract_from_binary,
            'csv': self._extract_from_binary,
            'audio': self._extract_from_binary,
            'video': self._extract_from_binary,
            'image': self._extract_from_binary,
        }
        
        extractor = extractors.get(content_type, self._extract_from_text)
        
        logger.debug(f"Using extractor: {extractor.__name__}")
        
        return await extractor(response, url)
    
    async def _extract_from_json(
        self,
        response: httpx.Response,
        url: str
    ) -> Dict[str, Any]:
        """
        Extract task from JSON response with base64 detection
        
        Args:
            response: HTTP response
            url: Original URL
            
        Returns:
            Dict with task information
        """
        logger.debug("Extracting task from JSON")
        
        try:
            data = response.json()
            
            # Try common field names for task description
            task_fields = [
                'task', 'task_description', 'description',
                'question', 'prompt', 'instruction',
                'task_text', 'content', 'message', 'text'
            ]
            
            task_description = None
            found_field = None
            
            # Search for task description in JSON
            for field in task_fields:
                if field in data:
                    task_description = str(data[field])
                    found_field = field
                    logger.debug(f"Found task in field: {field}")
                    break
            
            # If not found in root, try nested
            if not task_description:
                task_description = self._search_nested_json(data, task_fields)
                found_field = "nested"
            
            # Fallback: use entire JSON as string
            if not task_description:
                logger.warning("No task field found, using entire JSON")
                task_description = json.dumps(data, indent=2)
                found_field = "full_json"
            
            # Check for base64 encoding
            original_description = task_description
            task_description = self._detect_and_decode_base64(task_description)
            was_base64_decoded = (original_description != task_description)
            
            return {
                'task_description': task_description.strip(),
                'raw_content': response.text,
                'content_type': 'json',
                'url': url,
                'metadata': {
                    'json_structure': list(data.keys()) if isinstance(data, dict) else [],
                    'data_type': type(data).__name__,
                    'found_in_field': found_field,
                    'was_base64_decoded': was_base64_decoded,
                    'special_elements': {}  # No special elements in JSON
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            # Fallback to text extraction
            return await self._extract_from_text(response, url)
    
    def _search_nested_json(self, data: Any, fields: List[str], max_depth: int = 3) -> Optional[str]:
        """
        Recursively search for task description in nested JSON
        
        Args:
            data: JSON data to search
            fields: Field names to look for
            max_depth: Maximum recursion depth
            
        Returns:
            Task description if found, None otherwise
        """
        if max_depth <= 0:
            return None
        
        if isinstance(data, dict):
            for field in fields:
                if field in data:
                    return str(data[field])
            
            # Search nested dicts
            for value in data.values():
                result = self._search_nested_json(value, fields, max_depth - 1)
                if result:
                    return result
        
        elif isinstance(data, list) and len(data) > 0:
            # Search first item in list
            return self._search_nested_json(data[0], fields, max_depth - 1)
        
        return None
    
    async def _extract_from_html(
        self,
        response: httpx.Response,
        url: str
    ) -> Dict[str, Any]:
        """
        Extract task from HTML response with comprehensive element detection
        
        Args:
            response: HTTP response
            url: Original URL
            
        Returns:
            Dict with task information
        """
        logger.debug("Extracting task from HTML")
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # FIRST: Detect special elements
            special_elements = self._detect_special_elements(soup, url)
            has_special = any(special_elements.values())
            
            if has_special:
                detected_types = [k for k, v in special_elements.items() if v]
                logger.info(f"🔍 Detected special elements: {', '.join(detected_types)}")
            
            # Strategy 1: Look for common task containers
            task_selectors = [
                {'id': 'task'},
                {'id': 'question'},
                {'id': 'instruction'},
                {'id': 'quiz'},
                {'class_': 'task'},
                {'class_': 'question'},
                {'class_': 'instruction'},
                {'class_': 'task-description'},
                {'class_': 'quiz-question'},
                {'data-task': True}
            ]
            
            task_description = None
            extraction_method = None
            
            for selector in task_selectors:
                element = soup.find(**selector)
                if element:
                    task_description = element.get_text(strip=True, separator=' ')
                    extraction_method = f"selector_{list(selector.keys())[0]}"
                    logger.debug(f"Found task using selector: {selector}")
                    break
            
            # Strategy 2: Look for main content area
            if not task_description:
                main_content = (
                    soup.find('main') or
                    soup.find('article') or
                    soup.find('div', class_='content') or
                    soup.find('div', id='content') or
                    soup.find('section', class_='main')
                )
                
                if main_content:
                    task_description = main_content.get_text(strip=True, separator=' ')
                    extraction_method = "main_content"
                    logger.debug("Found task in main content area")
            
            # Strategy 3: Look for pre/code/textarea blocks (often contain base64 or instructions)
            if not task_description:
                code_blocks = soup.find_all(['pre', 'code', 'textarea'])
                if code_blocks:
                    task_description = '\n'.join(
                        block.get_text(strip=True) for block in code_blocks
                    )
                    extraction_method = "code_blocks"
                    logger.debug(f"Found task in {len(code_blocks)} code blocks")
            
            # Strategy 4: Use body text (last resort)
            if not task_description:
                # Remove script and style tags
                for script in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    script.decompose()
                
                task_description = soup.get_text(strip=True, separator=' ')
                extraction_method = "body_fallback"
                logger.warning("Using body text as task description")
            
            # Check for base64 encoding
            original_description = task_description
            task_description = self._detect_and_decode_base64(task_description)
            was_base64_decoded = (original_description != task_description)
            
            # Extract metadata
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ''
            
            # Check for meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_description = meta_desc.get('content', '') if meta_desc else ''
            
            return {
                'task_description': task_description.strip(),
                'raw_content': response.text,
                'content_type': 'html',
                'url': url,
                'metadata': {
                    'title': title_text,
                    'meta_description': meta_description,
                    'extraction_method': extraction_method,
                    'has_forms': bool(soup.find('form')),
                    'has_tables': bool(soup.find('table')),
                    'was_base64_decoded': was_base64_decoded,
                    'special_elements': special_elements,
                    'page_size_kb': len(response.content) / 1024
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to parse HTML: {str(e)}", exc_info=True)
            # Fallback to text extraction
            return await self._extract_from_text(response, url)
    
    def _detect_special_elements(self, soup: BeautifulSoup, base_url: str) -> Dict[str, List[str]]:
        """
        Detect special elements that might contain or lead to the task
        
        Args:
            soup: BeautifulSoup parsed HTML
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Dict of detected elements with absolute URLs
        """
        elements = {
            'audio_urls': [],
            'video_urls': [],
            'image_urls': [],
            'download_links': [],
            'iframe_sources': [],
            'external_links': [],
            'form_actions': [],
            'javascript_files': []
        }
        
        # Audio elements
        for audio in soup.find_all(['audio', 'source']):
            src = audio.get('src')
            if src:
                # Check for audio extensions or content type
                is_audio = any(ext in src.lower() for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'])
                audio_type = audio.get('type', '')
                if is_audio or 'audio/' in audio_type:
                    absolute_url = urljoin(base_url, src)
                    elements['audio_urls'].append(absolute_url)
                    logger.debug(f"Found audio: {absolute_url}")
        
        # Video elements
        for video in soup.find_all(['video', 'source']):
            src = video.get('src')
            if src:
                is_video = any(ext in src.lower() for ext in ['.mp4', '.webm', '.avi', '.mov', '.mkv'])
                video_type = video.get('type', '')
                if is_video or 'video/' in video_type:
                    absolute_url = urljoin(base_url, src)
                    elements['video_urls'].append(absolute_url)
                    logger.debug(f"Found video: {absolute_url}")
        
        # YouTube/Vimeo iframes
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if 'youtube.com' in src or 'vimeo.com' in src:
                elements['video_urls'].append(src)
                logger.debug(f"Found video iframe: {src}")
            elif src:
                absolute_url = urljoin(base_url, src)
                elements['iframe_sources'].append(absolute_url)
                logger.debug(f"Found iframe: {absolute_url}")
        
        # Image elements (might contain QR codes, screenshots with tasks, etc.)
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                absolute_url = urljoin(base_url, src)
                # Only include if it looks like it might contain data (not decorative)
                alt_text = img.get('alt', '').lower()
                if any(keyword in alt_text for keyword in ['task', 'question', 'instruction', 'qr', 'code']):
                    elements['image_urls'].append(absolute_url)
                    logger.debug(f"Found relevant image: {absolute_url}")
        
        # Download links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            link_text = link.get_text().strip().lower()
            
            # Check for downloadable files
            download_extensions = [
                '.pdf', '.csv', '.xlsx', '.xls', '.zip', '.txt',
                '.json', '.xml', '.doc', '.docx', '.tsv'
            ]
            
            is_download = any(ext in href.lower() for ext in download_extensions)
            
            # Check for text indicating download or external task
            download_keywords = ['download', 'get task', 'click here', 'task file', 'see task']
            has_download_text = any(keyword in link_text for keyword in download_keywords)
            
            if is_download:
                absolute_url = urljoin(base_url, href)
                elements['download_links'].append(absolute_url)
                logger.debug(f"Found download link: {absolute_url}")
            elif has_download_text:
                absolute_url = urljoin(base_url, href)
                elements['external_links'].append(absolute_url)
                logger.debug(f"Found external link: {absolute_url}")
        
        # Forms (might need to submit to get task)
        for form in soup.find_all('form'):
            action = form.get('action')
            if action:
                absolute_url = urljoin(base_url, action)
                elements['form_actions'].append(absolute_url)
                logger.debug(f"Found form action: {absolute_url}")
        
        # JavaScript files (might load task dynamically)
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and not any(cdn in src for cdn in ['google', 'cdn', 'jquery']):
                absolute_url = urljoin(base_url, src)
                elements['javascript_files'].append(absolute_url)
        
        # Remove duplicates
        for key in elements:
            elements[key] = list(set(elements[key]))
        
        return elements
    
    async def _extract_from_text(
        self,
        response: httpx.Response,
        url: str
    ) -> Dict[str, Any]:
        """
        Extract task from plain text response with base64 detection
        
        Args:
            response: HTTP response
            url: Original URL
            
        Returns:
            Dict with task information
        """
        logger.debug("Extracting task from plain text")
        
        text = response.text.strip()
        
        # Check for base64 encoding
        original_text = text
        text = self._detect_and_decode_base64(text)
        was_base64_decoded = (original_text != text)
        
        return {
            'task_description': text,
            'raw_content': response.text,
            'content_type': 'text',
            'url': url,
            'metadata': {
                'length': len(text),
                'lines': text.count('\n') + 1,
                'was_base64_decoded': was_base64_decoded,
                'special_elements': {}
            }
        }
    
    async def _extract_from_binary(
        self,
        response: httpx.Response,
        url: str
    ) -> Dict[str, Any]:
        """
        Handle binary content (PDF, audio, video, images, CSV)
        Returns info that LLM will need to process
        
        Args:
            response: HTTP response
            url: Original URL
            
        Returns:
            Dict with task information indicating processing needed
        """
        content_type = response.headers.get('content-type', 'unknown')
        
        logger.warning(f"⚠️  Binary content detected: {content_type}")
        
        task_description = f"Binary content detected. Type: {content_type}. URL: {url}. "
        
        if 'pdf' in content_type:
            task_description += "This is a PDF file that needs to be downloaded and parsed."
        elif 'audio' in content_type:
            task_description += "This is an audio file that needs to be transcribed."
        elif 'video' in content_type:
            task_description += "This is a video file that might need processing or transcription."
        elif 'image' in content_type:
            task_description += "This is an image that might need OCR or vision analysis."
        elif 'csv' in content_type:
            task_description += "This is a CSV file that needs to be downloaded and parsed."
        else:
            task_description += "This needs to be downloaded and processed."
        
        return {
            'task_description': task_description,
            'raw_content': '',  # Don't include binary in raw_content
            'content_type': content_type,
            'url': url,
            'metadata': {
                'is_binary': True,
                'content_length': len(response.content),
                'requires_download': True,
                'special_elements': {
                    'download_links': [url]
                }
            }
        }
    
    def _detect_and_decode_base64(self, text: str) -> str:
        """
        Detect and decode base64 content in text
        
        Args:
            text: Text that might contain base64
            
        Returns:
            Decoded text if base64 found, original text otherwise
        """
        # Pattern to detect base64 strings (at least 20 chars, typical base64 chars)
        # Must be fairly long to avoid false positives
        base64_pattern = r'([A-Za-z0-9+/]{40,}={0,2})'
        
        matches = re.findall(base64_pattern, text)
        
        if not matches:
            return text
        
        logger.debug(f"Found {len(matches)} potential base64 strings")
        
        decoded_parts = []
        
        for match in matches:
            try:
                # Try to decode
                decoded_bytes = base64.b64decode(match, validate=True)
                decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
                
                # Check if decoded text is readable (not binary)
                if self._is_readable_text(decoded_text):
                    logger.info(
                        f"✓ Decoded base64 string "
                        f"(length: {len(match)} → {len(decoded_text)} chars)"
                    )
                    decoded_parts.append(decoded_text)
                else:
                    logger.debug("Base64 decoded to binary/unreadable data")
                    
            except Exception as e:
                logger.debug(f"Not valid base64: {str(e)}")
                continue
        
        # If we successfully decoded anything, return the best candidate
        if decoded_parts:
            # Use the longest decoded string as it's likely the main content
            result = max(decoded_parts, key=len)
            logger.info(f"✅ Using decoded base64 content ({len(result)} chars)")
            return result
        
        return text
    
    def _is_readable_text(self, text: str, min_printable_ratio: float = 0.7) -> bool:
        """
        Check if decoded text is human-readable
        
        Args:
            text: Text to check
            min_printable_ratio: Minimum ratio of printable characters
            
        Returns:
            bool: True if text appears readable
        """
        if not text or len(text) < 10:
            return False
        
        # Count printable characters (letters, numbers, punctuation, spaces)
        printable_count = sum(c.isprintable() or c.isspace() for c in text)
        ratio = printable_count / len(text)
        
        # Also check for some common words to confirm it's text
        has_common_words = any(
            word in text.lower()
            for word in ['the', 'and', 'task', 'data', 'file', 'http']
        )
        
        return ratio >= min_printable_ratio and (ratio > 0.9 or has_common_words)
    
    def _needs_llm_analysis(self, task_info: Dict[str, Any]) -> bool:
        """
        Determine if fetched content needs LLM analysis to extract actual task
        
        Args:
            task_info: Fetched task information
            
        Returns:
            bool: True if LLM analysis needed
        """
        metadata = task_info.get('metadata', {})
        task_desc = task_info.get('task_description', '').lower()
        
        # Check 1: Binary content always needs LLM
        if metadata.get('is_binary'):
            logger.info("🤖 Binary content detected - LLM analysis required")
            return True
        
        # Check 2: Special elements present
        special_elements = metadata.get('special_elements', {})
        has_audio = bool(special_elements.get('audio_urls'))
        has_video = bool(special_elements.get('video_urls'))
        has_downloads = bool(special_elements.get('download_links'))
        has_iframes = bool(special_elements.get('iframe_sources'))
        has_images = bool(special_elements.get('image_urls'))
        has_forms = bool(special_elements.get('form_actions'))
        
        if any([has_audio, has_video, has_downloads, has_iframes, has_images, has_forms]):
            logger.info(
                f"🤖 Special elements detected - LLM analysis recommended "
                f"(audio:{has_audio}, video:{has_video}, downloads:{has_downloads}, "
                f"iframes:{has_iframes}, images:{has_images}, forms:{has_forms})"
            )
            return True
        
        # Check 3: Very short content (likely incomplete)
        if len(task_desc.strip()) < 30:
            logger.info("🤖 Very short content - LLM analysis recommended")
            return True
        
        # Check 4: Indirect language suggesting further action needed
        indirect_keywords = [
            'click here', 'download', 'visit', 'listen to',
            'watch', 'see attached', 'refer to', 'check the',
            'navigate to', 'go to', 'follow the link',
            'open the file', 'play the', 'view the'
        ]
        
        has_indirect_language = any(keyword in task_desc for keyword in indirect_keywords)
        
        if has_indirect_language:
            logger.info("🤖 Indirect language detected - LLM analysis recommended")
            return True
        
        # Check 5: Multiple URLs in content (might need to visit them)
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls_in_content = re.findall(url_pattern, task_desc)
        
        if len(urls_in_content) > 1:
            logger.info(f"🤖 Multiple URLs found ({len(urls_in_content)}) - LLM analysis recommended")
            return True
        
        # Content seems straightforward
        logger.info("✓ Content appears straightforward - LLM analysis not required")
        return False


# Convenience function for quick usage
async def fetch_task_from_url(url: str) -> Dict[str, Any]:
    """
    Convenience function to fetch task from URL
    
    Args:
        url: URL to fetch task from
        
    Returns:
        Dict with task information
        
    Raises:
        TaskProcessingError: If fetching fails
    """
    async with TaskFetcher() as fetcher:
        return await fetcher.fetch_task(url)
