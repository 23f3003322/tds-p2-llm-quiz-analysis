"""
Media Transcriber - HF Spaces Free Tier Optimized
Audio-only support (no ffmpeg needed)
"""

import httpx
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MediaTranscriber:
    """
    Audio transcriber optimized for HF Spaces free tier
    - Supports audio files: .mp3, .wav, .m4a, .ogg, .flac
    - Video files return helpful error message
    - No ffmpeg dependency required
    """
    
    def __init__(self, timeout: int = 300):
        """Initialize media transcriber"""
        self.timeout = timeout
        self.temp_dir = tempfile.mkdtemp(prefix='audio_transcription_')
        
        self.download_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'audio/*,*/*;q=0.8'
        }
        
        self.faster_whisper_available = self._check_faster_whisper()
        self.aipipe_available = self._check_aipipe()
        
        logger.info(
            f"MediaTranscriber initialized (audio-only) | "
            f"faster-whisper: {'✓' if self.faster_whisper_available else '✗'} | "
            f"AIPipe: {'✓' if self.aipipe_available else '✗'}"
        )
    
    def _check_faster_whisper(self) -> bool:
        """Check if faster-whisper is available"""
        try:
            from faster_whisper import WhisperModel
            return True
        except ImportError:
            return False
    
    def _check_aipipe(self) -> bool:
        """Check if AIPipe is configured"""
        return settings.is_llm_configured()
    
    async def transcribe_audio(self, url: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio file
        Supports: .mp3, .wav, .m4a, .ogg, .flac, .aac
        """
        logger.info(f"🎤 Transcribing audio: {url}")
        
        try:
            # Check if it's actually an audio file
            if not self._is_audio_file(url):
                logger.warning(f"Not an audio file: {url}")
                return {
                    'url': url,
                    'transcription': (
                        f'[Only audio files supported. Got: {url}. '
                        f'Supported: .mp3, .wav, .m4a, .ogg, .flac, .aac]'
                    ),
                    'status': 'unsupported_format',
                    'method': 'none',
                    'language': 'unknown'
                }
            
            # Download audio
            audio_path = await self._download_audio(url)
            if not audio_path:
                raise Exception("Failed to download audio")
            
            # Transcribe
            if self.faster_whisper_available:
                result = await self._transcribe_with_faster_whisper(audio_path, language)
            elif self.aipipe_available:
                result = await self._transcribe_with_aipipe(audio_path, language)
            else:
                result = {
                    'transcription': f'[Transcription unavailable. Install faster-whisper or set AIPIPE_TOKEN]',
                    'language': 'unknown',
                    'method': 'none',
                    'status': 'unavailable'
                }
            
            result['url'] = url
            logger.info(f"✅ Transcription complete | Method: {result['method']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}", exc_info=True)
            return {
                'url': url,
                'transcription': f'[Transcription failed: {str(e)}]',
                'status': 'error',
                'method': 'none',  # ← ADD THIS
                'language': 'unknown',  # ← ADD THIS
                'error': str(e)
            }


    async def transcribe_video(self, url: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Video transcription not supported on HF Spaces free tier
        Returns helpful error message
        """
        logger.warning(f"⚠️  Video transcription not supported: {url}")
        
        return {
            'url': url,
            'transcription': (
                f'[Video transcription not supported on HF Spaces free tier. '
                f'Video URL: {url}. '
                f'To transcribe videos: '
                f'1) Extract audio locally and upload as .mp3, or '
                f'2) Use a service that provides direct audio URLs.]'
            ),
            'language': 'unknown',
            'method': 'none',
            'status': 'video_not_supported',
            'note': 'HF Spaces free tier limitation - no ffmpeg available'
        }
    
    def _is_audio_file(self, url: str) -> bool:
        """Check if URL is an audio file"""
        audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in audio_extensions)
    
    async def _download_audio(self, url: str) -> Optional[str]:
        """Download audio file"""
        try:
            logger.info(f"Downloading audio: {url}")
            
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.download_headers
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
            
            # Save to temp
            extension = Path(url.split('?')[0]).suffix or '.mp3'
            file_path = os.path.join(self.temp_dir, f"audio_{hash(url)}{extension}")
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Downloaded: {len(response.content) / (1024*1024):.2f} MB")
            return file_path
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    async def _transcribe_with_faster_whisper(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe with faster-whisper (local, no API key)"""
        from faster_whisper import WhisperModel
        
        if not hasattr(self, '_whisper_model'):
            logger.info("Loading faster-whisper model...")
            model_size = os.getenv('WHISPER_MODEL_SIZE', 'base')
            self._whisper_model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8"
            )
            logger.info(f"✓ Model '{model_size}' loaded")
        
        segments, info = self._whisper_model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True
        )
        
        transcription = ' '.join([s.text for s in segments]).strip()
        
        return {
            'transcription': transcription,
            'language': info.language if hasattr(info, 'language') else 'unknown',
            'duration': info.duration if hasattr(info, 'duration') else None,
            'method': 'faster_whisper',
            'status': 'success'
        }
    
    async def _transcribe_with_aipipe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe with AIPipe API"""
        logger.info("Transcribing with AIPipe...")
        
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        files = {'file': (os.path.basename(audio_path), audio_data, 'audio/mpeg')}
        data = {'model': 'gpt-4o-audio-preview'}
        
        if language:
            data['language'] = language
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{settings.AIPIPE_BASE_URL}/audio/transcriptions",
                headers={'Authorization': f'Bearer {settings.AIPIPE_TOKEN}'},
                files=files,
                data=data
            )
            response.raise_for_status()
            result = response.json()
        
        return {
            'transcription': result.get('text', ''),
            'language': result.get('language', 'unknown'),
            'duration': result.get('duration'),
            'method': 'aipipe',
            'status': 'success'
        }
    
    def cleanup(self):
        """Clean up temp files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
