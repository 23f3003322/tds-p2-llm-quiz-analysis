"""
Action Executor
Executes actions identified by the classifier
"""

from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from app.orchestrator.models import ContentAnalysis
from app.orchestrator.actions import FileDownloader, MediaTranscriber, ImageProcessor
from app.services.task_fetcher import TaskFetcher
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError

logger = get_logger(__name__)


class ActionExecutor:
    """
    Executes actions based on content analysis
    Handles downloads, transcription, navigation, OCR
    """
    
    def __init__(self):
        """Initialize action executor"""
        self.file_downloader = FileDownloader()
        self.media_transcriber = MediaTranscriber()
        self.image_processor = ImageProcessor()
        logger.debug("ActionExecutor initialized")
    
    async def execute_actions(
        self,
        content_analysis: ContentAnalysis,
        original_task_description: str
    ) -> str:
        """
        Execute all required actions and return final task description
        
        Args:
            content_analysis: Analysis from classifier
            original_task_description: Original task description
            
        Returns:
            str: Final task description after executing actions
        """
        logger.info("🔄 Executing identified actions")
        
        if content_analysis.is_direct_task:
            logger.info("✅ Task is direct, no actions needed")
            return content_analysis.task_description or original_task_description
        
        logger.info(
            f"Actions required: "
            f"download={content_analysis.requires_download}, "
            f"transcription={content_analysis.requires_transcription}, "
            f"OCR={content_analysis.requires_ocr}, "
            f"navigation={content_analysis.requires_navigation}"
        )
        
        task_parts = [original_task_description]
        
        # Execute downloads
        if content_analysis.requires_download:
            download_results = await self._handle_downloads(
                content_analysis.action_urls
            )
            task_parts.extend(download_results)
        
        # Execute transcriptions
        if content_analysis.requires_transcription:
            transcription_results = await self._handle_transcriptions(
                content_analysis.action_urls
            )
            task_parts.extend(transcription_results)
        
        # Execute OCR
        if content_analysis.requires_ocr:
            ocr_results = await self._handle_ocr(
                content_analysis.action_urls
            )
            task_parts.extend(ocr_results)
        
        # Navigate to additional URLs
        if content_analysis.requires_navigation:
            navigation_results = await self._handle_navigation(
                content_analysis.action_urls
            )
            task_parts.extend(navigation_results)
        
        # Combine all parts into final task description
        final_task = self._combine_results(task_parts)
        
        logger.info(f"✅ Actions executed | Final task length: {len(final_task)} chars")
        
        return final_task
    
    async def _handle_downloads(self, urls: List[str]) -> List[str]:
        """Handle file downloads"""
        logger.info(f"📥 Processing {len(urls)} download URLs")
        
        results = []
        
        for url in urls:
            if not self._is_downloadable_file(url):
                continue
            
            try:
                file_info = await self.file_downloader.download_file(url)
                
                if 'content' in file_info:
                    results.append(
                        f"\n\nDownloaded file from {url}:\n{file_info['content']}"
                    )
                else:
                    results.append(
                        f"\n\nDownloaded {file_info['file_type']} file from {url} "
                        f"({file_info['size_bytes']} bytes)"
                    )
                
            except Exception as e:
                logger.error(f"Failed to download {url}: {e}")
                results.append(f"\n\n[Failed to download file from {url}: {str(e)}]")
        
        return results
    
    async def _handle_transcriptions(self, urls: List[str]) -> List[str]:
        """Handle audio/video transcription"""
        logger.info(f"🎤 Processing transcription URLs")
        
        results = []
        
        for url in urls:
            try:
                if self._is_audio(url):
                    transcription = await self.media_transcriber.transcribe_audio(url)
                    results.append(
                        f"\n\nAudio transcription from {url}:\n{transcription['transcription']}"
                    )
                    
                elif self._is_video(url):
                    transcription = await self.media_transcriber.transcribe_video(url)
                    results.append(
                        f"\n\nVideo transcription from {url}:\n{transcription['transcription']}"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to transcribe {url}: {e}")
                results.append(f"\n\n[Failed to transcribe {url}: {str(e)}]")
        
        return results
    
    async def _handle_ocr(self, urls: List[str]) -> List[str]:
        results = []
        
        for url in urls:
            ocr_result = await self.image_processor.extract_text_from_image(url)
            
            if ocr_result['status'] == 'success':
                results.append(f"\nText from {url}:\n{ocr_result['extracted_text']}")
            elif ocr_result['status'] == 'unavailable':
                results.append(f"\n[Image at {url} - OCR not configured]")
            else:
                results.append(f"\n[OCR failed for {url}]")
        
        return results


    async def _handle_navigation(self, urls: List[str]) -> List[str]:
        """Handle navigation to additional URLs"""
        logger.info(f"🌐 Processing navigation URLs")
        
        results = []
        
        for url in urls:
            # Skip URLs that are for files/media
            if (self._is_downloadable_file(url) or 
                self._is_audio(url) or 
                self._is_video(url) or 
                self._is_image(url)):
                continue
            
            try:
                async with TaskFetcher() as fetcher:
                    task_info = await fetcher.fetch_task(url)
                
                results.append(
                    f"\n\nContent from {url}:\n{task_info['task_description']}"
                )
                
            except Exception as e:
                logger.error(f"Failed to navigate to {url}: {e}")
                results.append(f"\n\n[Failed to fetch content from {url}: {str(e)}]")
        
        return results
    
    def _combine_results(self, parts: List[str]) -> str:
        """Combine all result parts into final task description"""
        # Remove empty parts
        parts = [p.strip() for p in parts if p and p.strip()]
        
        # Combine with proper spacing
        combined = '\n\n'.join(parts)
        
        # Limit total length to avoid extremely long descriptions
        max_length = 10000
        if len(combined) > max_length:
            logger.warning(f"Combined task description too long ({len(combined)} chars), truncating")
            combined = combined[:max_length] + "\n\n[...truncated]"
        
        return combined
    
    def _is_downloadable_file(self, url: str) -> bool:
        """Check if URL is a downloadable file"""
        extensions = ['.pdf', '.csv', '.xlsx', '.xls', '.zip', '.txt', '.json', '.xml', '.doc', '.docx']
        return any(url.lower().endswith(ext) for ext in extensions)
    
    def _is_audio(self, url: str) -> bool:
        """Check if URL is an audio file"""
        extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac']
        return any(url.lower().endswith(ext) for ext in extensions)
    
    def _is_video(self, url: str) -> bool:
        """Check if URL is a video file"""
        extensions = ['.mp4', '.webm', '.avi', '.mov', '.mkv']
        return any(url.lower().endswith(ext) for ext in extensions) or 'youtube.com' in url or 'vimeo.com' in url
    
    def _is_image(self, url: str) -> bool:
        """Check if URL is an image file"""
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        return any(url.lower().endswith(ext) for ext in extensions)
    
    def cleanup(self):
        """Clean up temporary resources"""
        try:
            self.file_downloader.cleanup()
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
