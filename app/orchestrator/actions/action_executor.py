"""
Action Executor
Executes actions identified by the classifier
Updated for HF Spaces free tier (audio-only, no video support)
"""

from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from app.orchestrator.models import ContentAnalysis
from app.orchestrator.actions import FileDownloader, MediaTranscriber, ImageProcessor
from app.services.task_fetcher import TaskFetcher
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError
from app.modules.scrapers.static_scraper import StaticScraper
from app.modules.scrapers.dynamic_scraper import DynamicScraper
from app.modules.clients.rest_client import RESTClient
from app.modules.processors.data_cleaner import DataCleaner
from app.modules.processors.data_transformer import DataTransformer
from app.modules.analyzers.data_analyzer import DataAnalyzer
from app.modules.visualizers.chart_generator import ChartGenerator
from app.modules.generators.report_generator import ReportGenerator


logger = get_logger(__name__)


class ActionExecutor:
    """
    Executes actions based on content analysis
    Handles downloads, transcription, navigation, OCR
    Optimized for HF Spaces free tier
    """
    
    def __init__(self):
        """Initialize action executor"""
        self.file_downloader = FileDownloader()
        self.media_transcriber = MediaTranscriber()
        self.image_processor = ImageProcessor()
        logger.debug("ActionExecutor initialized (HF Spaces optimized)")
    
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
        
        # Execute transcriptions (audio only)
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
                    # Text-based file with extracted content
                    results.append(
                        f"\n\n--- Downloaded file from {url} ---\n{file_info['content']}"
                    )
                else:
                    # Binary file
                    results.append(
                        f"\n\n[Downloaded {file_info['file_type']} file from {url} "
                        f"({file_info['size_bytes']} bytes)]"
                    )
                
            except Exception as e:
                logger.error(f"Failed to download {url}: {e}")
                results.append(f"\n\n[Failed to download file from {url}: {str(e)}]")
        
        return results
    
    async def _handle_transcriptions(self, urls: List[str]) -> List[str]:
        """
        Handle audio transcription (audio-only, no video support)
        Updated for HF Spaces free tier
        """
        logger.info(f"🎤 Processing transcription URLs")
        
        results = []
        
        for url in urls:
            try:
                # Check if it's audio or video
                if self._is_audio(url):
                    # Audio file - transcribe it
                    transcription = await self.media_transcriber.transcribe_audio(url)
                    
                    status = transcription.get('status', 'unknown')
                    
                    if status == 'success':
                        results.append(
                            f"\n\n--- Audio transcription from {url} ---\n"
                            f"{transcription['transcription']}"
                        )
                    elif status == 'unavailable':
                        results.append(
                            f"\n\n[Audio transcription unavailable for {url}. "
                            f"Install faster-whisper or configure AIPIPE_TOKEN]"
                        )
                    elif status == 'unsupported_format':
                        results.append(
                            f"\n\n[Unsupported audio format: {url}]"
                        )
                    else:
                        results.append(
                            f"\n\n[Audio transcription failed for {url}: "
                            f"{transcription.get('error', 'Unknown error')}]"
                        )
                    
                elif self._is_video(url):
                    # Video file - not supported on free tier
                    transcription = await self.media_transcriber.transcribe_video(url)
                    
                    # This will return 'video_not_supported' status
                    results.append(
                        f"\n\n[Video transcription not supported on HF Spaces free tier. "
                        f"Video URL: {url}. Extract audio locally and upload as .mp3]"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to transcribe {url}: {e}")
                results.append(f"\n\n[Transcription failed for {url}: {str(e)}]")
        
        return results
    
    async def _handle_ocr(self, urls: List[str]) -> List[str]:
        """Handle OCR on images"""
        logger.info(f"🖼️  Processing OCR URLs")
        
        results = []
        
        for url in urls:
            if not self._is_image(url):
                continue
            
            try:
                ocr_result = await self.image_processor.extract_text_from_image(url)
                
                status = ocr_result.get('status', 'unknown')
                
                if status == 'success':
                    extracted_text = ocr_result.get('extracted_text', '')
                    if extracted_text.strip():
                        results.append(
                            f"\n\n--- Text extracted from image {url} ---\n"
                            f"{extracted_text}"
                        )
                    else:
                        results.append(
                            f"\n\n[No text found in image: {url}]"
                        )
                
                elif status == 'no_text_found':
                    results.append(
                        f"\n\n[No text found in image: {url}]"
                    )
                
                elif status == 'unavailable':
                    results.append(
                        f"\n\n[OCR unavailable for {url}. "
                        f"Configure Google Cloud Vision API to enable OCR]"
                    )
                
                else:
                    results.append(
                        f"\n\n[OCR failed for {url}: "
                        f"{ocr_result.get('error', 'Unknown error')}]"
                    )
                
            except Exception as e:
                logger.error(f"Failed to OCR {url}: {e}")
                results.append(f"\n\n[OCR failed for {url}: {str(e)}]")
        
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
                    f"\n\n--- Content from {url} ---\n{task_info['task_description']}"
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
            combined = combined[:max_length] + "\n\n[...truncated for length]"
        
        return combined
    
    def _is_downloadable_file(self, url: str) -> bool:
        """Check if URL is a downloadable file"""
        extensions = ['.pdf', '.csv', '.xlsx', '.xls', '.zip', '.txt', '.json', '.xml', '.doc', '.docx']
        return any(url.lower().endswith(ext) for ext in extensions)
    
    def _is_audio(self, url: str) -> bool:
        """Check if URL is an audio file"""
        extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']
        return any(url.lower().endswith(ext) for ext in extensions)
    
    def _is_video(self, url: str) -> bool:
        """Check if URL is a video file"""
        extensions = ['.mp4', '.webm', '.avi', '.mov', '.mkv']
        url_lower = url.lower()
        return (any(url_lower.endswith(ext) for ext in extensions) or 
                'youtube.com' in url_lower or 
                'vimeo.com' in url_lower or
                'youtu.be' in url_lower)
    
    def _is_image(self, url: str) -> bool:
        """Check if URL is an image file"""
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        return any(url.lower().endswith(ext) for ext in extensions)
    
    def cleanup(self):
        """Clean up temporary resources"""
        try:
            self.file_downloader.cleanup()
            self.image_processor.cleanup()
            self.media_transcriber.cleanup()
            logger.debug("✓ Action executor cleanup complete")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
