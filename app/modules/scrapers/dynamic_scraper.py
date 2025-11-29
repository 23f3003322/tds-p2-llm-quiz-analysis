"""
Dynamic Web Scraper
Playwright-based scraper for JavaScript-heavy websites
"""

from typing import Dict, Any, List, Optional
import time
import asyncio

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from app.modules.scrapers.base_scraper import BaseScraper, ScraperResult
from app.modules.scrapers.browser_manager import BrowserManager
from app.modules.scrapers.browser_config import (
    BrowserConfig,
    get_browser_config  # ← Updated import
)
from app.modules.scrapers.scraper_utils import (
    extract_table_data,
    extract_list_data,
    extract_text_clean
)
from app.modules.base import ModuleCapability, ModuleResult
from app.modules.capabilities import ScrapingCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class DynamicScraper(BaseScraper):
    """
    Dynamic web scraper using Playwright
    For JavaScript-heavy websites and SPAs
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None, use_pool: bool = True):
        super().__init__(name="dynamic_scraper")
        
        # Use optimized config if none provided
        self.config = config or get_browser_config()  # ← Simplified!
        self.use_pool = use_pool
        self.browser_manager = None
        
        logger.debug(f"DynamicScraper initialized (headless={self.config.headless})")
    
    # Rest of the code stays exactly the same...
    def get_capabilities(self) -> ModuleCapability:
        """Get module capabilities"""
        return ScrapingCapability.DYNAMIC
    
    async def initialize(self) -> bool:
        """Initialize browser - use pool in production"""
        logger.debug(f"Initializing browser (use_pool={self.use_pool})...")
        
        try:
            if self.use_pool:
                from app.modules.scrapers.browser_pool import get_pooled_browser
                self.browser_manager = await get_pooled_browser(self.config)
            else:
                self.browser_manager = BrowserManager(self.config)
                await self.browser_manager.initialize()
            
            # Verify initialization
            if not self.browser_manager or not self.browser_manager.is_initialized():
                raise RuntimeError("Browser manager failed to initialize")
            
            logger.debug("✓ Browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}", exc_info=True)
            raise


    
    async def execute(
    self,
    parameters: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> ModuleResult:
        """
        Execute dynamic scraping
        
        Args:
            parameters: Scraping parameters
                - url: URL to scrape (required)
                - selectors: CSS selectors (optional)
                - wait_for: Selector to wait for (optional)
                - click_selectors: Selectors to click (optional)
                - scroll: Whether to scroll (optional)
                - screenshot: Take screenshot (optional)
            context: Execution context
            
        Returns:
            ModuleResult: Scraping result
        """
        url = parameters.get('url')
        
        if not url:
            return ModuleResult(
                success=False,
                error="URL parameter is required"
            )
        
        logger.info(f"[DYNAMIC SCRAPER] Scraping URL: {url}")
        
        start_time = time.time()
        
        # Initialize browser if needed
        if self.browser_manager is None:
            logger.debug("Initializing browser for execute...")
            await self.initialize()
        elif not self.browser_manager.is_initialized():
            logger.debug("Starting browser for execute...")
            await self.browser_manager.initialize()
        
        # Scrape
        result = await self.scrape_url(
            url=url,
            selectors=parameters.get('selectors'),
            wait_for=parameters.get('wait_for'),
            click_selectors=parameters.get('click_selectors', []),
            scroll=parameters.get('scroll', False),
            take_screenshot=parameters.get('screenshot', False)
        )
        
        execution_time = time.time() - start_time
        
        if result.success:
            return ModuleResult(
                success=True,
                data=result.data,
                metadata={
                    'url': url,
                    'rows_extracted': result.rows_extracted,
                    'columns': result.columns_extracted,
                    'browser': self.config.browser_type.value,
                    'javascript': True
                },
                execution_time=execution_time
            )
        else:
            return ModuleResult(
                success=False,
                error=result.error,
                execution_time=execution_time
            )


    async def scrape_url(
    self,
    url: str,
    selectors: Optional[Dict[str, str]] = None,
    wait_for: Optional[str] = None,
    click_selectors: List[str] = None,
    scroll: bool = False,
    take_screenshot: bool = False,
    **kwargs
) -> ScraperResult:
        """
        Scrape a URL with browser automation
        
        Args:
            url: URL to scrape
            selectors: CSS selectors for data extraction
            wait_for: Selector to wait for before scraping
            click_selectors: Selectors to click before scraping
            scroll: Scroll to bottom of page
            take_screenshot: Take screenshot
            
        Returns:
            ScraperResult: Scraping result
        """
        # Normalize URL
        url = self._normalize_url(url)
        
        # Validate URL
        if not self._validate_url(url):
            return ScraperResult(
                success=False,
                url=url,
                error=f"Invalid URL: {url}"
            )
        
        logger.info(f"🌐 Scraping with browser: {url}")
        
        try:
            # Initialize browser if needed - FIX HERE!
            if not self.browser_manager or not self.browser_manager.is_initialized():
                logger.debug("Initializing browser for scraping...")
                await self.initialize()  # ← This was missing/not working
            
            # Ensure browser_manager exists
            if not self.browser_manager:
                raise RuntimeError("Failed to initialize browser manager")
            
            # Create page
            async with self.browser_manager.page() as page:
                # Navigate to URL
                logger.info(f"Navigating to: {url}")
                response = await page.goto(
                    url,
                    wait_until=self.config.wait_until
                )
                
                if not response:
                    return ScraperResult(
                        success=False,
                        url=url,
                        error="Failed to load page"
                    )
                
                status_code = response.status
                logger.info(f"Page loaded | Status: {status_code}")
                
                # Wait for specific element
                if wait_for:
                    logger.info(f"Waiting for selector: {wait_for}")
                    try:
                        await page.wait_for_selector(
                            wait_for,
                            timeout=self.config.wait_for_selector_timeout
                        )
                    except PlaywrightTimeout:
                        logger.warning(f"Timeout waiting for: {wait_for}")
                
                # Click elements
                if click_selectors:
                    await self._click_elements(page, click_selectors)
                
                # Scroll page
                if scroll:
                    await self._scroll_page(page)
                
                # Wait for network idle
                await self.browser_manager.wait_for_network_idle(page)
                
                # Take screenshot
                if take_screenshot:
                    screenshot_name = f"scrape_{int(time.time())}.png"
                    await self.browser_manager.screenshot(page, screenshot_name)
                
                # Extract data
                if selectors:
                    data = await self._extract_with_selectors(page, selectors)
                else:
                    data = await self._extract_auto(page)
                
                # Build result
                columns = list(data[0].keys()) if data else []
                
                result = ScraperResult(
                    success=True,
                    url=url,
                    data=data,
                    rows_extracted=len(data),
                    columns_extracted=columns,
                    status_code=status_code,
                    selectors_used=list(selectors.keys()) if selectors else []
                )
                
                logger.info(f"✓ Scraped {len(data)} rows with browser")
                
                return result
                
        except Exception as e:
            logger.error(f"✗ Dynamic scraping failed for {url}: {e}", exc_info=True)
            
            return ScraperResult(
                success=False,
                url=url,
                error=str(e)
            )
    async def scrape_multiple(
    self,
    urls: List[str],
    selectors: Optional[Dict[str, str]] = None,
    **kwargs
) -> List[ScraperResult]:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of URLs
            selectors: CSS selectors
            
        Returns:
            List[ScraperResult]: Results
        """
        logger.info(f"Scraping {len(urls)} URLs with browser")
        
        # Initialize browser once for all URLs
        if self.browser_manager is None:
            logger.debug("Initializing browser for multiple URLs...")
            await self.initialize()
        elif not self.browser_manager.is_initialized():
            logger.debug("Starting browser for multiple URLs...")
            await self.browser_manager.initialize()
        
        results = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Scraping {i}/{len(urls)}: {url}")
            
            result = await self.scrape_url(url, selectors, **kwargs)
            results.append(result)
            
            # Small delay between requests
            if i < len(urls):
                await asyncio.sleep(1.0)
        
        logger.info(f"✓ Scraped {len(urls)} URLs with browser")
        
        return results

    async def _click_elements(self, page: Page, selectors: List[str]):
        """Click multiple elements"""
        for selector in selectors:
            try:
                logger.info(f"Clicking: {selector}")
                await page.click(selector)
                await asyncio.sleep(1.0)  # Wait after click
            except Exception as e:
                logger.warning(f"Failed to click {selector}: {e}")
    
    async def _scroll_page(self, page: Page):
        """Scroll to bottom of page"""
        logger.info("Scrolling page...")
        
        await page.evaluate("""
            async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 100;
                    const timer = setInterval(() => {
                        const scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        
                        if(totalHeight >= scrollHeight){
                            clearInterval(timer);
                            resolve();
                        }
                    }, 100);
                });
            }
        """)
        
        logger.debug("Scrolling complete")
    
    async def _extract_with_selectors(
        self,
        page: Page,
        selectors: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Extract data using selectors"""
        
        # Get page content
        content = await page.content()
        
        # Parse with BeautifulSoup (reuse existing utils)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        from app.modules.scrapers.scraper_utils import extract_with_selectors
        return extract_with_selectors(soup, selectors)
    
    async def _extract_auto(self, page: Page) -> List[Dict[str, Any]]:
        """Auto-detect and extract data"""
        
        # Get page content
        content = await page.content()
        
        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Try tables
        table_data = extract_table_data(soup)
        if table_data:
            return table_data
        
        # Try lists
        list_data = extract_list_data(soup)
        if list_data:
            return [{'item': item} for item in list_data]
        
        # Extract text blocks
        data = []
        paragraphs = soup.find_all(['p', 'div', 'span'])
        
        for i, p in enumerate(paragraphs[:50]):
            text = extract_text_clean(p)
            if text and len(text) > 10:
                data.append({
                    'index': i + 1,
                    'text': text
                })
        
        return data
    
    async def cleanup(self):
        """Clean up browser resources"""
        await self.browser_manager.close()
        logger.debug("DynamicScraper cleanup complete")
