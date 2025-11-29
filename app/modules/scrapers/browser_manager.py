"""
Browser Manager
Manages Playwright browser lifecycle
"""

from typing import Optional, Dict, Any
import asyncio
from contextlib import asynccontextmanager

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright
)

from app.modules.scrapers.browser_config import (
    BrowserConfig,
    get_browser_config  # ← Updated import
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class BrowserManager:
    """
    Manages browser instances with Playwright
    Handles browser lifecycle and resource management
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        """
        Initialize browser manager
        
        Args:
            config: Browser configuration
        """
        self.config = config or get_browser_config()  # ← Simplified!
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._is_initialized = False
        
        logger.debug("BrowserManager initialized")
    
    async def initialize(self):
        """Initialize Playwright and launch browser"""
        if self._is_initialized:
            logger.debug("Browser already initialized")
            return
        
        try:
            logger.info(f"🚀 Launching {self.config.browser_type.value} browser (headless={self.config.headless})")
            
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Get browser type
            browser_type = getattr(self.playwright, self.config.browser_type.value)
            
            # Build launch arguments
            launch_args = {
                'headless': self.config.headless,
                'slow_mo': self.config.slow_mo,
                'args': self.config.browser_args
            }
            
            # Add proxy if configured
            if self.config.proxy_server:
                launch_args['proxy'] = {
                    'server': self.config.proxy_server
                }
                if self.config.proxy_username:
                    launch_args['proxy']['username'] = self.config.proxy_username
                    launch_args['proxy']['password'] = self.config.proxy_password
            
            # Launch browser
            self.browser = await browser_type.launch(**launch_args)
            
            # Create context
            await self._create_context()
            
            self._is_initialized = True
            logger.info("✓ Browser launched successfully")
            
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}", exc_info=True)
            raise
    
    async def _create_context(self):
        """Create browser context with configuration"""
        if not self.browser:
            raise RuntimeError("Browser not launched")
        
        context_args = {
            'viewport': {
                'width': self.config.viewport_width,
                'height': self.config.viewport_height
            },
            'ignore_https_errors': self.config.ignore_https_errors,
            'java_script_enabled': self.config.javascript_enabled,
            'accept_downloads': self.config.accept_downloads,
            'has_touch': self.config.has_touch,
            'is_mobile': self.config.is_mobile
        }
        
        # Add user agent if specified
        if self.config.user_agent:
            context_args['user_agent'] = self.config.user_agent
        
        # Add geolocation if specified
        if self.config.geolocation:
            context_args['geolocation'] = self.config.geolocation
            if 'geolocation' not in self.config.permissions:
                self.config.permissions.append('geolocation')
        
        # Add permissions
        if self.config.permissions:
            context_args['permissions'] = self.config.permissions
        
        # Create context
        self.context = await self.browser.new_context(**context_args)
        
        # Set default timeout
        self.context.set_default_timeout(self.config.timeout)
        self.context.set_default_navigation_timeout(self.config.navigation_timeout)
        
        logger.debug("Browser context created")
    
    async def new_page(self) -> Page:
        """
        Create new page
        
        Returns:
            Page: New browser page
        """
        if not self._is_initialized:
            await self.initialize()
        
        if not self.context:
            raise RuntimeError("Browser context not created")
        
        page = await self.context.new_page()
        logger.debug("New page created")
        
        return page
    
    @asynccontextmanager
    async def page(self):
        """
        Context manager for page
        Automatically closes page after use
        
        Usage:
            async with browser_manager.page() as page:
                await page.goto(url)
        """
        page = await self.new_page()
        try:
            yield page
        finally:
            await page.close()
            logger.debug("Page closed")
    
    async def close(self):
        """Close browser and cleanup"""
        if self.context:
            await self.context.close()
            logger.debug("Browser context closed")
        
        if self.browser:
            await self.browser.close()
            logger.debug("Browser closed")
        
        if self.playwright:
            await self.playwright.stop()
            logger.debug("Playwright stopped")
        
        self._is_initialized = False
        logger.info("✓ Browser cleanup complete")
    
    async def screenshot(
        self,
        page: Page,
        filename: str,
        full_page: bool = False
    ) -> str:
        """
        Take screenshot
        
        Args:
            page: Browser page
            filename: Screenshot filename
            full_page: Capture full page
            
        Returns:
            str: Screenshot path
        """
        import os
        
        # Create screenshots directory
        os.makedirs(self.config.screenshots_path, exist_ok=True)
        
        # Build path
        path = os.path.join(self.config.screenshots_path, filename)
        
        # Take screenshot
        await page.screenshot(path=path, full_page=full_page)
        
        logger.info(f"📸 Screenshot saved: {path}")
        
        return path
    
    async def wait_for_network_idle(
        self,
        page: Page,
        timeout: Optional[int] = None
    ):
        """
        Wait for network to be idle
        
        Args:
            page: Browser page
            timeout: Timeout in milliseconds
        """
        timeout = timeout or self.config.timeout
        
        try:
            await page.wait_for_load_state('networkidle', timeout=timeout)
            logger.debug("Network idle")
        except Exception as e:
            logger.warning(f"Network idle timeout: {e}")
    
    def is_initialized(self) -> bool:
        """Check if browser is initialized"""
        return self._is_initialized
