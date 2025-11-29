"""
Web Scraping Modules
Static and dynamic web scraping implementations
"""

from app.modules.scrapers.base_scraper import BaseScraper, ScraperResult
from app.modules.scrapers.static_scraper import StaticScraper
from app.modules.scrapers.scraper_config import ScraperConfig
from app.modules.scrapers.dynamic_scraper import DynamicScraper  
from app.modules.scrapers.browser_manager import BrowserManager  
from app.modules.scrapers.browser_config import (
    BrowserConfig,
    BrowserPresets,
    get_browser_config 
)

__all__ = [
    "BaseScraper",
    "ScraperResult",
    "StaticScraper",
    "DynamicScraper",  
    "BrowserManager",  
    "BrowserConfig",  
    "BrowserPresets", 
    "get_browser_config", 
    "ScraperConfig"
]
