"""
Test Dynamic Web Scraper
Comprehensive tests for Playwright scraper
"""
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
import pytest
pytest_plugins = ('pytest_asyncio',)
"""
Test Dynamic Web Scraper
Comprehensive tests for Playwright-based scraper
"""
"""
Test Dynamic Web Scraper
Comprehensive tests for Playwright scraper
No skipping - all tests must pass
"""

import asyncio
import sys
from app.modules.scrapers.dynamic_scraper import DynamicScraper
from app.modules.scrapers.browser_config import BrowserConfig, BrowserPresets, get_browser_config
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_playwright_installation():
    """Test if Playwright is properly installed"""
    print("\n" + "=" * 60)
    print("Test 0: Playwright Installation Check")
    print("=" * 60)
    
    try:
        from playwright.async_api import async_playwright
        print("✓ Playwright Python package: Installed")
        
        # Try to start playwright
        async with async_playwright() as p:
            print("✓ Playwright started successfully")
            
            # Check browser availability
            try:
                browser = await p.chromium.launch(headless=True)
                print("✓ Chromium browser: Available")
                await browser.close()
            except Exception as e:
                print(f"❌ Chromium browser: Not installed")
                print(f"   Error: {e}")
                print("\n🔧 Fix: Run 'playwright install chromium'")
                raise
        
        print("\n✅ Playwright setup verified")
        return True
        
    except ImportError as e:
        print(f"❌ Playwright not installed: {e}")
        print("\n🔧 Fix: Run 'pip install playwright'")
        raise
    except Exception as e:
        print(f"❌ Playwright setup error: {e}")
        raise


async def test_scraper_initialization():
    """Test scraper initialization"""
    print("\n" + "=" * 60)
    print("Test 1: Scraper Initialization")
    print("=" * 60)
    
    scraper = DynamicScraper(use_pool=False)
    
    print(f"  Name: {scraper.name}")
    print(f"  Config: {scraper.config is not None}")
    print(f"  Headless: {scraper.config.headless}")
    print(f"  Timeout: {scraper.config.timeout}ms")
    print(f"  Browser manager: {scraper.browser_manager}")
    
    assert scraper.name == "dynamic_scraper", "Wrong scraper name"
    assert scraper.config is not None, "Config not initialized"
    assert scraper.browser_manager is None, "Browser manager should be None before initialize()"
    
    print("\n✅ Scraper initialized successfully")


async def test_browser_startup():
    """Test browser manager initialization"""
    print("\n" + "=" * 60)
    print("Test 2: Browser Startup")
    print("=" * 60)
    
    scraper = DynamicScraper(use_pool=False)
    
    print("  Initializing browser...")
    await scraper.initialize()
    
    print(f"  Browser manager: {scraper.browser_manager}")
    print(f"  Is initialized: {scraper.browser_manager.is_initialized()}")
    print(f"  Browser type: {scraper.config.browser_type.value}")
    
    assert scraper.browser_manager is not None, "Browser manager not created"
    assert scraper.browser_manager.is_initialized(), "Browser not initialized"
    
    print("\n✅ Browser started successfully")
    
    # Cleanup
    await scraper.cleanup()
    print("  Browser closed")


async def test_scrape_example_site():
    """Test scraping example.com with browser"""
    print("\n" + "=" * 60)
    print("Test 3: Scrape Example.com")
    print("=" * 60)
    
    scraper = DynamicScraper(use_pool=False)
    
    url = "https://example.com"
    print(f"  Scraping: {url}")
    
    result = await scraper.scrape_url(url)
    
    print(f"\n  Result:")
    print(f"    Success: {result.success}")
    print(f"    Status code: {result.status_code}")
    print(f"    Rows extracted: {result.rows_extracted}")
    print(f"    Columns: {result.columns_extracted}")
    print(f"    Response time: {result.response_time:.2f}s")
    
    if not result.success:
        print(f"\n  ❌ Error: {result.error}")
        print(f"  Warnings: {result.warnings}")
        raise AssertionError(f"Scraping failed: {result.error}")
    
    assert result.success, "Scraping should succeed"
    assert result.status_code == 200, f"Expected 200, got {result.status_code}"
    assert result.rows_extracted > 0, "Should extract at least one row"
    
    print(f"\n  Sample data (first 2 rows):")
    for i, row in enumerate(result.data[:2], 1):
        print(f"    {i}. {row}")
    
    print("\n✅ Scraping successful")
    
    await scraper.cleanup()


async def test_scrape_with_wait():
    """Test scraping with wait for selector"""
    print("\n" + "=" * 60)
    print("Test 4: Scrape with Wait Selector")
    print("=" * 60)
    
    scraper = DynamicScraper(use_pool=False)
    
    url = "https://example.com"
    wait_for = "h1"
    
    print(f"  Scraping: {url}")
    print(f"  Waiting for: {wait_for}")
    
    result = await scraper.scrape_url(
        url=url,
        wait_for=wait_for
    )
    
    print(f"\n  Result:")
    print(f"    Success: {result.success}")
    print(f"    Rows: {result.rows_extracted}")
    
    assert result.success, "Should succeed with wait_for"
    assert result.rows_extracted > 0, "Should extract data"
    
    print("\n✅ Wait selector working")
    
    await scraper.cleanup()


async def test_scrape_with_execute():
    """Test scraping via execute method"""
    print("\n" + "=" * 60)
    print("Test 5: Execute Method (Module Interface)")
    print("=" * 60)
    
    scraper = DynamicScraper(use_pool=False)
    
    parameters = {
        'url': 'https://example.com',
        'screenshot': False,
        'scroll': False
    }
    
    print(f"  Parameters: {parameters}")
    
    result = await scraper.execute(parameters)
    
    print(f"\n  Result:")
    print(f"    Success: {result.success}")
    print(f"    Execution time: {result.execution_time:.2f}s")
    print(f"    Data rows: {len(result.data) if result.data else 0}")
    print(f"    Metadata: {result.metadata}")
    
    assert result.success, "Execute should succeed"
    assert result.data is not None, "Should return data"
    assert 'browser' in result.metadata, "Should include browser metadata"
    assert result.metadata['javascript'] == True, "Should indicate JavaScript"
    
    if result.data:
        print(f"\n  Sample data:")
        for row in result.data[:2]:
            print(f"    {row}")
    
    print("\n✅ Execute method working")
    
    await scraper.cleanup()


async def test_browser_configs():
    """Test different browser configurations"""
    print("\n" + "=" * 60)
    print("Test 6: Browser Configurations")
    print("=" * 60)
    
    configs = {
        'optimized': get_browser_config('optimized'),
        'fast': get_browser_config('fast'),
        'mobile': get_browser_config('mobile'),
        'desktop': get_browser_config('desktop')
    }
    
    for name, config in configs.items():
        print(f"\n  Config: {name}")
        print(f"    Headless: {config.headless}")
        print(f"    Viewport: {config.viewport_width}x{config.viewport_height}")
        print(f"    Timeout: {config.timeout}ms")
        print(f"    Is mobile: {config.is_mobile}")
        
        scraper = DynamicScraper(config=config, use_pool=False)
        assert scraper.config.headless == config.headless
        assert scraper.config.viewport_width == config.viewport_width
    
    print("\n✅ All configs loaded correctly")


async def test_mobile_emulation():
    """Test mobile device emulation"""
    print("\n" + "=" * 60)
    print("Test 7: Mobile Emulation")
    print("=" * 60)
    
    config = get_browser_config('mobile')
    scraper = DynamicScraper(config=config, use_pool=False)
    
    print(f"  Viewport: {config.viewport_width}x{config.viewport_height}")
    print(f"  Is mobile: {config.is_mobile}")
    print(f"  Has touch: {config.has_touch}")
    
    result = await scraper.scrape_url("https://example.com")
    
    print(f"\n  Result:")
    print(f"    Success: {result.success}")
    print(f"    Rows: {result.rows_extracted}")
    
    assert result.success, "Mobile scraping should succeed"
    
    print("\n✅ Mobile emulation working")
    
    await scraper.cleanup()


async def test_multiple_urls():
    """Test scraping multiple URLs"""
    print("\n" + "=" * 60)
    print("Test 8: Multiple URLs (Batch Scraping)")
    print("=" * 60)
    
    scraper = DynamicScraper(use_pool=False)
    
    urls = [
        "https://example.com",
        "https://example.org"
    ]
    
    print(f"  Scraping {len(urls)} URLs...")
    
    results = await scraper.scrape_multiple(urls)
    
    print(f"\n  Results:")
    for i, result in enumerate(results, 1):
        print(f"    {i}. {urls[i-1]}")
        print(f"       Success: {result.success}")
        print(f"       Rows: {result.rows_extracted}")
        print(f"       Status: {result.status_code}")
    
    assert len(results) == len(urls), "Should return result for each URL"
    assert all(r.success for r in results), "All scrapes should succeed"
    
    print("\n✅ Multiple URLs working")
    
    await scraper.cleanup()


async def test_error_handling():
    """Test error handling with invalid URL"""
    print("\n" + "=" * 60)
    print("Test 9: Error Handling")
    print("=" * 60)
    
    scraper = DynamicScraper(use_pool=False)
    
    # Test invalid URL
    invalid_url = "https://this-domain-definitely-does-not-exist-12345.com"
    print(f"  Testing with invalid URL: {invalid_url}")
    
    result = await scraper.scrape_url(invalid_url)
    
    print(f"\n  Result:")
    print(f"    Success: {result.success}")
    print(f"    Error: {result.error}")
    
    assert not result.success, "Should fail for invalid URL"
    assert result.error is not None, "Should have error message"
    
    print("\n✅ Error handling working")
    
    await scraper.cleanup()


async def test_capabilities():
    """Test module capabilities"""
    print("\n" + "=" * 60)
    print("Test 10: Module Capabilities")
    print("=" * 60)
    
    scraper = DynamicScraper(use_pool=False)
    
    capabilities = scraper.get_capabilities()
    
    print(f"  Capabilities: {capabilities}")
    
    assert capabilities is not None, "Should return capabilities"
    
    print("\n✅ Capabilities working")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print(" " * 15 + "DYNAMIC SCRAPER TEST SUITE (PRODUCTION)")
    print("=" * 80)
    
    tests = [
        ("Playwright Installation", test_playwright_installation),
        ("Scraper Initialization", test_scraper_initialization),
        ("Browser Startup", test_browser_startup),
        ("Scrape Example Site", test_scrape_example_site),
        ("Wait for Selector", test_scrape_with_wait),
        ("Execute Method", test_scrape_with_execute),
        ("Browser Configs", test_browser_configs),
        ("Mobile Emulation", test_mobile_emulation),
        ("Multiple URLs", test_multiple_urls),
        ("Error Handling", test_error_handling),
        ("Module Capabilities", test_capabilities),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            error_msg = f"{name}: {str(e)}"
            errors.append(error_msg)
            print(f"\n❌ TEST FAILED: {name}")
            print(f"   Error: {e}")
        except Exception as e:
            failed += 1
            error_msg = f"{name}: {str(e)}"
            errors.append(error_msg)
            print(f"\n❌ TEST ERROR: {name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print(" " * 30 + "TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n  Total Tests: {len(tests)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    
    if errors:
        print(f"\n  Failed Tests:")
        for error in errors:
            print(f"    - {error}")
    
    if failed == 0:
        print("\n" + "=" * 80)
        print(" " * 25 + "🎉 ALL TESTS PASSED 🎉")
        print("=" * 80)
        print("\n✅ Dynamic scraper is production ready!")
        print("\n📊 Verified:")
        print("  ✓ Playwright installation")
        print("  ✓ Browser startup and shutdown")
        print("  ✓ Page navigation")
        print("  ✓ JavaScript execution")
        print("  ✓ Data extraction")
        print("  ✓ Mobile emulation")
        print("  ✓ Batch scraping")
        print("  ✓ Error handling")
        print("  ✓ Module interface")
    else:
        print("\n" + "=" * 80)
        print(" " * 25 + "❌ SOME TESTS FAILED ❌")
        print("=" * 80)
        raise AssertionError(f"{failed} test(s) failed")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
