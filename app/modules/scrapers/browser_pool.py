"""
Browser Pool Manager
Reuses browser instances to avoid startup overhead
"""

import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from app.modules.scrapers.browser_manager import BrowserManager
from app.modules.scrapers.browser_config import (
    BrowserConfig,
    get_browser_config  # ← Updated import
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class BrowserPool:
    """
    Singleton browser pool
    Maintains a single browser instance for reuse
    """
    
    _instance: Optional['BrowserPool'] = None
    _browser_manager: Optional[BrowserManager] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_browser_manager(cls, config: Optional[BrowserConfig] = None) -> BrowserManager:
        """
        Get or create browser manager
        Reuses existing instance for performance
        """
        async with cls._lock:
            if cls._browser_manager is None or not cls._browser_manager.is_initialized():
                logger.info("🚀 Initializing browser pool")
                
                # Use optimized config if none provided
                browser_config = config or get_browser_config()  # ← Simplified!
                
                cls._browser_manager = BrowserManager(browser_config)
                await cls._browser_manager.initialize()
                logger.info("✓ Browser pool ready")
            
            return cls._browser_manager
    

    @classmethod
    async def cleanup(cls):
        """Cleanup browser pool"""
        async with cls._lock:
            if cls._browser_manager:
                await cls._browser_manager.close()
                cls._browser_manager = None
                logger.info("Browser pool cleaned up")


# Convenience function
async def get_pooled_browser(config: Optional[BrowserConfig] = None) -> 'BrowserManager':
    """Get browser from pool"""
    return await BrowserPool.get_browser_manager(config)
