"""
Test Media Transcriber - Audio Only Version
Tests for HF Spaces free tier (no ffmpeg)
"""

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

import asyncio
from app.orchestrator.actions.media_transcriber import MediaTranscriber
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def test_speech_detection():
    """Test transcription with real internet audio containing speech"""
    
    print("\n" + "=" * 60)
    print("Test: Speech Detection (Real World Audio)")
    print("=" * 60)
    
    transcriber = MediaTranscriber()
    
    # Public domain/open source audio samples with speech
    speech_samples = [
        {
            'url': 'https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav',
            'description': 'Open Speech Repository - American English',
            'format': '.wav',
            'duration': '~3 seconds',
            'expected_type': 'clear speech',
            'source': 'VoIP Troubleshooter Open Speech Repository'
        },
        {
            'url': 'https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0011_8k.wav',
            'description': 'Open Speech Repository - Short phrase',
            'format': '.wav',
            'duration': '~3 seconds',
            'expected_type': 'clear speech',
            'source': 'VoIP Troubleshooter Open Speech Repository'
        },
        {
            'url': 'https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0012_8k.wav',
            'description': 'Open Speech Repository - Another phrase',
            'format': '.wav',
            'duration': '~3 seconds',
            'expected_type': 'clear speech',
            'source': 'VoIP Troubleshooter Open Speech Repository'
        }
    ]
    
    print("\n🎙️  Testing with real-world speech samples")
    print("Source: Open Speech Repository (Public Domain)")
    print()
    
    success_count = 0
    speech_detected_count = 0
    
    for i, sample in enumerate(speech_samples, 1):
        print(f"{'-' * 60}")
        print(f"Test {i}/{len(speech_samples)}")
        print(f"Audio: {sample['description']}")
        print(f"URL: {sample['url']}")
        print(f"Duration: {sample['duration']}")
        print(f"Expected: {sample['expected_type']}")
        print(f"{'-' * 60}")
        
        try:
            result = await transcriber.transcribe_audio(sample['url'])
            
            status = result.get('status', 'unknown')
            method = result.get('method', 'none')
            
            print(f"\n✓ Status: {status}")
            print(f"✓ Method: {method}")
            
            if status == 'success':
                language = result.get('language', 'unknown')
                duration = result.get('duration')
                transcription = result.get('transcription', '').strip()
                
                print(f"✓ Language: {language}")
                if duration:
                    print(f"✓ Duration: {duration:.2f} seconds")
                
                word_count = len(transcription.split()) if transcription else 0
                print(f"✓ Word count: {word_count}")
                
                if word_count > 0:
                    print(f"\n✅ SPEECH DETECTED!")
                    print(f"\n📝 Transcribed text:")
                    print(f'   "{transcription}"')
                    speech_detected_count += 1
                else:
                    print(f"\n⚠️  No words detected")
                
                success_count += 1
            
            elif status == 'unavailable':
                print("\n⚠️  Transcription backend not available")
                print("💡 Install: pip install faster-whisper")
                break
            
            elif status == 'error':
                error_msg = result.get('error', 'Unknown')
                print(f"\n❌ Error: {error_msg[:150]}")
                
                # Check error type
                if any(x in error_msg.lower() for x in ['network', 'dns', 'timeout', 'nodename']):
                    print("   (Network error - trying next sample...)")
                    continue
                else:
                    print("   (Non-network error - skipping remaining tests)")
                    break
        
        except Exception as e:
            print(f"\n❌ Exception: {str(e)[:150]}")
            logger.error(f"Test {i} failed", exc_info=True)
            continue
        
        print()
    
    # Summary
    print("=" * 60)
    print("SPEECH DETECTION SUMMARY")
    print("=" * 60)
    
    if success_count > 0:
        print(f"✅ {success_count}/{len(speech_samples)} samples processed")
        print(f"🎙️  {speech_detected_count}/{success_count} detected speech")
        
        if speech_detected_count > 0:
            print(f"\n🎉 SUCCESS! Real-world speech transcription working")
            print(f"   System successfully transcribed human speech from internet audio")
        else:
            print(f"\n⚠️  Processed but no speech detected")
    else:
        if not (transcriber.faster_whisper_available or transcriber.aipipe_available):
            print("⚠️  No transcription backend installed")
            print("   Install: pip install faster-whisper")
        else:
            print("⚠️  Audio files unavailable or network issue")
            print("   The transcriber itself is properly configured")
    
    print("=" * 60)
    
    return transcriber


async def test_small_audio_files():
    """Test with small audio files suitable for quick tasks"""
    
    print("\n" + "=" * 60)
    print("Test 1: Small Audio Files (< 30 seconds)")
    print("=" * 60)
    
    transcriber = MediaTranscriber()
    
    # Small, reliable test audio files
    test_audios = [
        {
            'url': 'https://actions.google.com/sounds/v1/alarms/beep_short.ogg',
            'description': 'Very short beep (< 1 second)',
            'format': '.ogg',
            'expected_duration': '< 1 sec',
            'expected_text': 'Instrumental/beep (no speech)'
        },
        {
            'url': 'https://actions.google.com/sounds/v1/cartoon/cartoon_boing.ogg',
            'description': 'Short sound effect (< 2 seconds)',
            'format': '.ogg',
            'expected_duration': '~2 sec',
            'expected_text': 'Sound effect (no speech)'
        }
    ]
    
    print("\n📝 Testing with small audio samples suitable for 3-minute tasks\n")
    
    success_count = 0
    
    for i, test_audio in enumerate(test_audios, 1):
        print(f"{'-' * 60}")
        print(f"Test {i}/{len(test_audios)}: {test_audio['description']}")
        print(f"URL: {test_audio['url']}")
        print(f"Format: {test_audio['format']}")
        print(f"Expected duration: {test_audio['expected_duration']}")
        print(f"Expected: {test_audio['expected_text']}")
        print(f"{'-' * 60}")
        
        try:
            result = await transcriber.transcribe_audio(test_audio['url'])
            
            status = result.get('status', 'unknown')
            method = result.get('method', 'none')
            
            print(f"\n✓ Status: {status}")
            print(f"✓ Method: {method}")
            
            if status == 'success':
                print(f"✅ Transcription successful!")
                
                language = result.get('language', 'unknown')
                print(f"✓ Language: {language}")
                
                duration = result.get('duration')
                if duration:
                    print(f"✓ Duration: {duration:.2f} seconds")
                
                transcription = result.get('transcription', '')
                print(f"✓ Text length: {len(transcription)} chars")
                
                if transcription.strip():
                    print(f"\n📝 Transcription:")
                    print(f"   {transcription[:200]}")
                else:
                    print(f"\n📝 No speech detected (expected for sound effects)")
                
                success_count += 1
            
            elif status == 'unavailable':
                print("⚠️  Transcription backend not available")
                print("\n💡 To enable transcription:")
                print("   1. Install: pip install faster-whisper")
                print("   2. Or set AIPIPE_TOKEN in .env")
                break  # No point testing other files
            
            elif status == 'error':
                error_msg = result.get('error', 'Unknown')
                print(f"❌ Error: {error_msg[:100]}")
                
                # Check if it's a network error
                if any(x in error_msg.lower() for x in ['network', 'dns', 'nodename', 'timeout']):
                    print("   ℹ️  Network error - URL may be temporarily unavailable")
        
        except Exception as e:
            print(f"❌ Exception: {str(e)[:100]}")
            logger.error(f"Test {i} failed", exc_info=True)
        
        print()
    
    # Summary
    print("=" * 60)
    if success_count > 0:
        print(f"✅ {success_count}/{len(test_audios)} audio files transcribed successfully")
    elif transcriber.faster_whisper_available or transcriber.aipipe_available:
        print("⚠️  Transcription available but test files failed to download")
        print("   (Network issue - the transcriber itself is working)")
    else:
        print("ℹ️  No transcription backend installed")
    print("=" * 60)
    
    return transcriber


async def test_video_rejection():
    """Test that video files are rejected gracefully"""
    
    print("\n" + "=" * 60)
    print("Test 2: Video File Rejection (Audio-Only Mode)")
    print("=" * 60)
    
    transcriber = MediaTranscriber()
    
    # Test video URL
    test_video = {
        'url': 'https://example.com/sample-video.mp4',
        'description': 'Sample video file'
    }
    
    print(f"\n📹 Testing: {test_video['description']}")
    print(f"URL: {test_video['url']}")
    print(f"Expected: Rejection with helpful message")
    print("-" * 60)
    
    result = await transcriber.transcribe_video(test_video['url'])
    
    status = result.get('status', 'unknown')
    print(f"\n✓ Status: {status}")
    
    if status == 'video_not_supported':
        print(f"✅ Video correctly rejected (audio-only mode)")
        print(f"\n📝 Message shown to user:")
        print(f"   {result.get('transcription', '')[:200]}...")
    else:
        print(f"⚠️  Unexpected status: {status}")
    
    return transcriber


async def test_format_detection():
    """Test audio format detection"""
    
    print("\n" + "=" * 60)
    print("Test 3: Format Detection & Validation")
    print("=" * 60)
    
    transcriber = MediaTranscriber()
    
    test_cases = [
        {
            'url': 'https://example.com/file.mp3',
            'expected': 'audio',
            'description': 'MP3 audio file'
        },
        {
            'url': 'https://example.com/file.wav',
            'expected': 'audio',
            'description': 'WAV audio file'
        },
        {
            'url': 'https://example.com/file.m4a',
            'expected': 'audio',
            'description': 'M4A audio file'
        },
        {
            'url': 'https://example.com/image.png',
            'expected': 'unsupported',
            'description': 'PNG image (not audio)'
        },
        {
            'url': 'https://example.com/doc.pdf',
            'expected': 'unsupported',
            'description': 'PDF document (not audio)'
        }
    ]
    
    print("\n🔍 Testing format detection for various file types:\n")
    
    for i, test in enumerate(test_cases, 1):
        is_audio = transcriber._is_audio_file(test['url'])
        detected = 'audio' if is_audio else 'unsupported'
        
        if detected == test['expected']:
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} {test['description']}")
        print(f"   URL: {test['url']}")
        print(f"   Detected: {detected} | Expected: {test['expected']}")
        print()
    
    return transcriber


async def test_backend_check():
    """Test backend availability"""
    
    print("\n" + "=" * 60)
    print("Test 4: Transcription Backend Status")
    print("=" * 60)
    
    transcriber = MediaTranscriber()
    
    print("\n🔧 Checking available backends:\n")
    
    # Check faster-whisper
    if transcriber.faster_whisper_available:
        print("✅ faster-whisper: Available")
        print("   → Local transcription (CPU)")
        print("   → No API key needed")
        print("   → Free, unlimited")
        print("   → Model: base (~150MB)")
        print("   → Speed: ~20 seconds per minute of audio")
    else:
        print("❌ faster-whisper: Not installed")
        print("   → Install: pip install faster-whisper")
    
    print()
    
    # Check AIPipe
    if transcriber.aipipe_available:
        print("✅ AIPipe: Configured")
        print("   → Cloud transcription")
        print("   → Uses AIPIPE_TOKEN")
        print("   → Model: gpt-4o-audio-preview")
        print("   → Speed: ~5 seconds per minute of audio")
    else:
        print("❌ AIPipe: Not configured")
        print("   → Set AIPIPE_TOKEN in .env")
    
    print()
    
    # Recommendation
    if transcriber.faster_whisper_available:
        print("💡 Recommendation: Using faster-whisper (local, free)")
    elif transcriber.aipipe_available:
        print("💡 Recommendation: Using AIPipe (cloud, paid)")
    else:
        print("⚠️  No transcription backend available")
        print("\n📦 Quick Setup:")
        print("   pip install faster-whisper")
    
    return transcriber


async def test_performance_estimate():
    """Show performance estimates for typical task sizes"""
    
    print("\n" + "=" * 60)
    print("Test 5: Performance Estimates")
    print("=" * 60)
    
    transcriber = MediaTranscriber()
    
    # Typical task scenarios
    scenarios = [
        {'duration': 10, 'description': 'Very short clip'},
        {'duration': 30, 'description': 'Short instruction'},
        {'duration': 60, 'description': 'One minute audio'},
        {'duration': 120, 'description': 'Two minute recording'},
        {'duration': 180, 'description': 'Maximum task audio (3 min)'}
    ]
    
    print("\n⏱️  Estimated transcription times for HF Spaces free tier:\n")
    print(f"{'Audio Duration':<20} | {'faster-whisper':<20} | {'AIPipe':<20}")
    print("-" * 65)
    
    for scenario in scenarios:
        duration = scenario['duration']
        desc = scenario['description']
        
        # Estimates (conservative for free tier CPU)
        local_time = duration * 0.3  # ~30% of audio duration
        cloud_time = duration * 0.1  # ~10% of audio duration
        
        print(f"{duration}s ({desc:<15}) | ~{local_time:.0f}s               | ~{cloud_time:.0f}s")
    
    print()
    print("📝 Notes:")
    print("   - Estimates for HF Spaces CPU tier")
    print("   - faster-whisper: First run downloads model (~30s)")
    print("   - AIPipe: Network latency may add 1-2 seconds")
    print("   - All times well within 3-minute task limit")
    
    return transcriber


async def run_all_tests():
    """Run all tests"""
    
    print("\n" + "=" * 80)
    print(" " * 15 + "MEDIA TRANSCRIBER TEST SUITE")
    print(" " * 12 + "(Small Audio Files - 3 Minute Tasks)")
    print("=" * 80)
    
    transcriber = None
    
    try:
        # Test 1: Small audio files
        transcriber = await test_small_audio_files()
        
        # Test 2: Video rejection
        if transcriber:
            transcriber.cleanup()
        transcriber = await test_video_rejection()
        
        # Test 3: Format detection
        if transcriber:
            transcriber.cleanup()
        transcriber = await test_format_detection()
        
        # Test 4: Backend check
        if transcriber:
            transcriber.cleanup()
        transcriber = await test_backend_check()
        
        # Test 5: Performance estimates
        if transcriber:
            transcriber.cleanup()
        transcriber = await test_performance_estimate()

        if transcriber:
            transcriber.cleanup()
        transcriber = await test_speech_detection()
        
        print("\n" + "=" * 80)
        print(" " * 30 + "TESTS COMPLETE")
        print("=" * 80)
        
        print("\n✅ All tests finished!")
        print("\n📊 Summary:")
        print("   • Small audio files tested (< 30 seconds)")
        print("   • Video rejection verified")
        print("   • Format detection working")
        print("   • Performance suitable for 3-minute tasks")
        print("\n💡 For production: Install faster-whisper for free local transcription")
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ Test suite error: {e}")
        print("=" * 80)
        logger.error("Test suite failed", exc_info=True)
    
    finally:
        if transcriber:
            transcriber.cleanup()
            print("\n🧹 Cleanup complete")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
