"""
Test Static Web Scraper
Comprehensive tests for BeautifulSoup scraper
"""
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import asyncio
import pytest
pytest_plugins = ('pytest_asyncio',)
from app.modules.scrapers.static_scraper import StaticScraper
from app.modules.scrapers.scraper_config import ScraperConfig
from app.core.logging import setup_logging

setup_logging()


@pytest.mark.asyncio
async def test_scraper_initialization():
    """Test scraper initialization"""
    scraper = StaticScraper()
    
    assert scraper.name == "static_scraper"
    assert scraper.config is not None
    assert scraper.session is not None
    
    scraper.cleanup()


@pytest.mark.asyncio
async def test_scrape_example_site():
    """Test scraping example.com"""
    scraper = StaticScraper()
    
    result = await scraper.scrape_url("https://example.com")
    
    print(f"\n✓ Scraping result:")
    print(f"  Success: {result.success}")
    print(f"  Rows: {result.rows_extracted}")
    print(f"  Status: {result.status_code}")
    
    assert result.success
    assert result.status_code == 200
    assert result.rows_extracted > 0
    
    scraper.cleanup()


@pytest.mark.asyncio
async def test_scrape_with_execute():
    """Test scraping via execute method"""
    scraper = StaticScraper()
    
    parameters = {
        'url': 'https://example.com'
    }
    
    result = await scraper.execute(parameters)
    
    print(f"\n✓ Execute result:")
    print(f"  Success: {result.success}")
    print(f"  Data rows: {len(result.data) if result.data else 0}")
    
    assert result.success
    assert result.data is not None
    
    scraper.cleanup()


@pytest.mark.asyncio
async def test_url_validation():
    """Test URL validation"""
    scraper = StaticScraper()
    
    # Valid URLs
    assert scraper._validate_url("https://example.com")
    assert scraper._validate_url("http://example.com/page")
    
    # Invalid URLs
    assert not scraper._validate_url("not-a-url")
    assert not scraper._validate_url("ftp://example.com")
    
    scraper.cleanup()


@pytest.mark.asyncio
async def test_url_normalization():
    """Test URL normalization"""
    scraper = StaticScraper()
    
    assert scraper._normalize_url("example.com") == "https://example.com"
    assert scraper._normalize_url("http://example.com") == "http://example.com"
    
    scraper.cleanup()


@pytest.mark.asyncio
async def test_scraper_with_custom_config():
    """Test scraper with custom configuration"""
    config = ScraperConfig(
        timeout=10,
        max_retries=2,
        user_agent="Custom Agent"
    )
    
    scraper = StaticScraper(config=config)
    
    assert scraper.config.timeout == 10
    assert scraper.config.max_retries == 2
    
    scraper.cleanup()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
