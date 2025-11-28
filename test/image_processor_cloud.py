"""
Test Image Processor with Cloud Vision
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

import asyncio
from app.orchestrator.actions.image_processor import ImageProcessor
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_ocr():
    """Test OCR functionality"""
    
    print("\n" + "=" * 60)
    print("Testing Image Processor (Cloud Vision)")
    print("=" * 60)
    
    processor = ImageProcessor()
    
    # Test images (using more reliable sources)
    test_images = [
        {
            'url': 'https://cdn.botpenguin.com/assets/website/Hugging_Face_1_e8ba23f378.webp',
            'description': 'Simple text placeholder'
        },
        {
            'url': 'https://picsum.photos/400/300',
            'description': 'Random photo (no text expected)'
        }
    ]
    
    for i, img in enumerate(test_images, 1):
        print(f"\n{'-' * 60}")
        print(f"Test {i}: {img['description']}")
        print(f"URL: {img['url']}")
        print(f"{'-' * 60}")
        
        # Test basic analysis first
        print(f"\nAnalyzing image properties...")
        try:
            analysis = await processor.analyze_image(img['url'])
            
            if analysis['status'] == 'success':
                print(f"✅ {analysis['description']}")
                props = analysis['properties']
                print(f"   Size: {props['width']}x{props['height']}")
                print(f"   Format: {props['format']}")
                print(f"   File size: {props['size_kb']} KB")
            elif analysis['status'] == 'download_failed':
                print(f"❌ {analysis['description']}")
                print(f"   Note: {analysis.get('note', '')}")
                continue  # Skip OCR if download failed
            else:
                print(f"❌ Analysis failed: {analysis.get('error', 'Unknown')}")
                continue
        
        except Exception as e:
            print(f"❌ Analysis exception: {e}")
            continue
        
        # Test OCR
        print(f"\nAttempting OCR...")
        try:
            result = await processor.extract_text_from_image(img['url'])
            
            print(f"Status: {result['status']}")
            print(f"Method: {result['method']}")
            
            if result['status'] == 'success':
                print(f"Confidence: {result['confidence']:.2f}")
                print(f"Text length: {len(result['extracted_text'])} chars")
                
                if result['extracted_text']:
                    preview = result['extracted_text'][:150]
                    print(f"Preview: {preview}...")
                else:
                    print("No text found in image")
            
            elif result['status'] == 'unavailable':
                print(f"Reason: {result.get('reason', 'Unknown')}")
                print("💡 Configure Cloud Vision API to enable OCR")
            
            elif result['status'] == 'error':
                print(f"Error: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"❌ OCR exception: {e}")
    
    # Cleanup
    processor.cleanup()
    
    print("\n" + "=" * 60)
    print("✅ Image Processor Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_ocr())
