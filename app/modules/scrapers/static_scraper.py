"""
Static Web Scraper
BeautifulSoup-based scraper for static HTML pages
"""

from typing import Dict, Any, List, Optional
import time
import asyncio

import requests
from bs4 import BeautifulSoup

from app.modules.scrapers.base_scraper import BaseScraper, ScraperResult
from app.modules.scrapers.scraper_config import ScraperConfig, DEFAULT_CONFIG
from app.modules.scrapers.scraper_utils import (
    extract_table_data,
    extract_list_data,
    extract_with_selectors,
    extract_text_clean,
    detect_encoding
)
from app.modules.base import ModuleCapability, ModuleResult
from app.modules.capabilities import ScrapingCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class StaticScraper(BaseScraper):
    """
    Static web scraper using BeautifulSoup
    For simple HTML pages without JavaScript
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        super().__init__(name="static_scraper")
        self.config = config or DEFAULT_CONFIG
        self.session = requests.Session()
        
        # Setup session
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            **self.config.custom_headers
        })
        
        if self.config.skip_ssl_verify:
            self.session.verify = False
        
        logger.debug("StaticScraper initialized")
    
    def get_capabilities(self) -> ModuleCapability:
        return ScrapingCapability.STATIC
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """
        Execute scraping
        
        Args:
            parameters: Scraping parameters
                - url: URL to scrape (required)
                - selectors: CSS selectors (optional)
                - columns: Column names to extract (optional)
                - max_results: Maximum results (optional)
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
        
        logger.info(f"[SCRAPER] Scraping URL: {url}")
        
        start_time = time.time()
        
        # Build selectors
        selectors = parameters.get('selectors', {})
        columns = parameters.get('columns', [])
        
        if columns and not selectors:
            # Auto-generate simple selectors
            selectors = {col: f'.{col}' for col in columns}
        
        # Scrape
        result = await self.scrape_url(
            url=url,
            selectors=selectors,
            max_results=parameters.get('max_results')
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
                    'content_type': result.content_type,
                    'status_code': result.status_code
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
        max_results: Optional[int] = None,
        **kwargs
    ) -> ScraperResult:
        """
        Scrape a single URL
        
        Args:
            url: URL to scrape
            selectors: CSS selectors for data extraction
            max_results: Maximum results to return
            **kwargs: Additional options
            
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
        
        logger.info(f"Scraping: {url}")
        
        try:
            # Fetch page
            response = await self._fetch_page(url)
            
            if not response:
                return ScraperResult(
                    success=False,
                    url=url,
                    error="Failed to fetch page"
                )
            
            # Parse HTML
            soup = self._parse_html(response.content, response.encoding)
            
            # Extract data
            if selectors:
                data = self._extract_with_selectors(soup, selectors)
            else:
                data = self._extract_auto(soup)
            
            # Limit results
            if max_results and len(data) > max_results:
                data = data[:max_results]
            
            # Build result
            columns = list(data[0].keys()) if data else []
            
            result = ScraperResult(
                success=True,
                url=url,
                data=data,
                rows_extracted=len(data),
                columns_extracted=columns,
                status_code=response.status_code,
                response_time=response.elapsed.total_seconds(),
                selectors_used=list(selectors.keys()) if selectors else []
            )
            
            logger.info(f"✓ Scraped {len(data)} rows from {url}")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Scraping failed for {url}: {e}", exc_info=True)
            
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
            urls: List of URLs to scrape
            selectors: CSS selectors for data extraction
            **kwargs: Additional options
            
        Returns:
            List[ScraperResult]: List of results
        """
        logger.info(f"Scraping {len(urls)} URLs")
        
        results = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Scraping {i}/{len(urls)}: {url}")
            
            result = await self.scrape_url(url, selectors, **kwargs)
            results.append(result)
            
            # Rate limiting
            if i < len(urls):
                await asyncio.sleep(self.config.rate_limit_delay)
        
        logger.info(f"✓ Scraped {len(urls)} URLs")
        
        return results
    
    async def _fetch_page(self, url: str) -> Optional[requests.Response]:
        """Fetch page with retries"""
        
        for attempt in range(self.config.max_retries):
            try:
                response = await asyncio.to_thread(
                    self.session.get,
                    url,
                    timeout=self.config.timeout
                )
                
                response.raise_for_status()
                
                return response
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    logger.error(f"All retries failed for {url}")
                    return None
    
    def _parse_html(self, content: bytes, encoding: Optional[str] = None) -> BeautifulSoup:
        """Parse HTML content"""
        
        # Detect encoding if not provided
        if not encoding:
            encoding = detect_encoding(content)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, self.config.parser)
        
        return soup
    
    def _extract_with_selectors(
        self,
        soup: BeautifulSoup,
        selectors: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Extract data using CSS selectors"""
        return extract_with_selectors(soup, selectors)
    
    def _extract_auto(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Auto-detect and extract data"""
        
        # Try tables first
        table_data = extract_table_data(soup)
        if table_data:
            logger.debug(f"Extracted {len(table_data)} rows from table")
            return table_data
        
        # Try lists
        list_data = extract_list_data(soup)
        if list_data:
            logger.debug(f"Extracted {len(list_data)} items from list")
            return [{'item': item} for item in list_data]
        
        # Extract all text paragraphs as fallback
        paragraphs = soup.find_all(['p', 'div', 'span'])
        
        data = []
        for i, p in enumerate(paragraphs[:50]):  # Limit to 50
            text = extract_text_clean(p)
            if text and len(text) > 10:  # Skip very short text
                data.append({
                    'index': i + 1,
                    'text': text
                })
        
        logger.debug(f"Extracted {len(data)} text blocks")
        
        return data
    
    def cleanup(self):
        """Clean up resources"""
        if self.session:
            self.session.close()
        logger.debug("StaticScraper cleanup complete")
