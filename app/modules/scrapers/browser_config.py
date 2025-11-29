"""
Browser Configuration
Unified configuration for Playwright browser automation
Works for both development and production
"""

import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class BrowserType(str, Enum):
    """Browser types"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserConfig(BaseModel):
    """Configuration for browser automation"""
    
    # Browser settings
    browser_type: BrowserType = Field(
        default=BrowserType.CHROMIUM,
        description="Browser to use"
    )
    
    headless: bool = Field(
        default=True,
        description="Run browser in headless mode"
    )
    
    # Window settings
    viewport_width: int = Field(default=1280, description="Viewport width")
    viewport_height: int = Field(default=720, description="Viewport height")
    
    # Performance
    slow_mo: int = Field(
        default=0,
        description="Slow down operations by N milliseconds"
    )
    
    timeout: int = Field(
        default=15000,
        description="Default timeout in milliseconds"
    )
    
    navigation_timeout: int = Field(
        default=15000,
        description="Navigation timeout in milliseconds"
    )
    
    # JavaScript execution
    javascript_enabled: bool = Field(
        default=True,
        description="Enable JavaScript"
    )
    
    # Network
    ignore_https_errors: bool = Field(
        default=False,
        description="Ignore HTTPS errors"
    )
    
    user_agent: Optional[str] = Field(
        default="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        description="Custom user agent"
    )
    
    # Proxy
    proxy_server: Optional[str] = Field(
        None,
        description="Proxy server URL"
    )
    
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    
    # Downloads
    downloads_path: Optional[str] = Field(
        None,
        description="Path for file downloads"
    )
    
    # Screenshots
    screenshots_path: str = Field(
        default="./screenshots",
        description="Path for screenshots"
    )
    
    # Wait strategies
    wait_until: str = Field(
        default="domcontentloaded",
        description="Wait until condition (load, domcontentloaded, networkidle)"
    )
    
    wait_for_selector_timeout: int = Field(
        default=10000,
        description="Timeout for waiting for selectors"
    )
    
    # Cookies and storage
    accept_downloads: bool = Field(default=False, description="Accept downloads")
    has_touch: bool = Field(default=False, description="Emulate touch events")
    is_mobile: bool = Field(default=False, description="Emulate mobile device")
    
    # Geolocation
    geolocation: Optional[Dict[str, float]] = Field(
        None,
        description="Geolocation (latitude, longitude, accuracy)"
    )
    
    # Permissions
    permissions: List[str] = Field(
        default_factory=list,
        description="Browser permissions to grant"
    )
    
    # Extra args - optimized for production
    browser_args: List[str] = Field(
        default_factory=lambda: [
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-software-rasterizer",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--mute-audio",
        ],
        description="Browser launch arguments"
    )


# =============================================================================
# PRESET CONFIGURATIONS
# =============================================================================

class BrowserPresets:
    """Pre-configured browser settings for common use cases"""
    
    # Default optimized config - works everywhere
    OPTIMIZED = BrowserConfig(
        browser_type=BrowserType.CHROMIUM,
        headless=True,
        viewport_width=1280,
        viewport_height=720,
        timeout=15000,
        navigation_timeout=15000,
        wait_until="domcontentloaded",
        javascript_enabled=True,
        accept_downloads=False,
        has_touch=False,
        is_mobile=False
    )
    
    # Fast scraping - minimal wait times
    FAST = BrowserConfig(
        headless=True,
        timeout=10000,
        navigation_timeout=10000,
        wait_until="domcontentloaded",
        viewport_width=1280,
        viewport_height=720
    )
    
    # Desktop view
    DESKTOP = BrowserConfig(
        headless=True,
        viewport_width=1920,
        viewport_height=1080,
        is_mobile=False
    )
    
    # Mobile emulation
    MOBILE = BrowserConfig(
        headless=True,
        viewport_width=375,
        viewport_height=812,
        is_mobile=True,
        has_touch=True,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36"
    )
    
    # Debugging - visible browser, slow motion
    DEBUG = BrowserConfig(
        headless=False,
        slow_mo=500,
        timeout=60000,
        navigation_timeout=60000,
        viewport_width=1920,
        viewport_height=1080,
        browser_args=["--start-maximized"]
    )
    
    # Stealth mode - avoid detection
    STEALTH = BrowserConfig(
        headless=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        browser_args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox"
        ]
    )


# =============================================================================
# SMART CONFIG SELECTOR
# =============================================================================

def get_browser_config(preset: Optional[str] = None) -> BrowserConfig:
    """
    Get browser configuration
    Automatically selects optimal config based on environment
    
    Args:
        preset: Optional preset name (debug, fast, mobile, etc.)
        
    Returns:
        BrowserConfig: Browser configuration
        
    Examples:
        # Default optimized config
        config = get_browser_config()
        
        # Debug mode (visible browser)
        config = get_browser_config('debug')
        
        # Mobile emulation
        config = get_browser_config('mobile')
    """
    # Check for debug mode environment variable
    debug_mode = os.getenv('DEBUG_BROWSER', 'false').lower() == 'true'
    
    if debug_mode:
        return BrowserPresets.DEBUG
    
    # Use preset if specified
    if preset:
        preset_map = {
            'optimized': BrowserPresets.OPTIMIZED,
            'fast': BrowserPresets.FAST,
            'desktop': BrowserPresets.DESKTOP,
            'mobile': BrowserPresets.MOBILE,
            'debug': BrowserPresets.DEBUG,
            'stealth': BrowserPresets.STEALTH
        }
        return preset_map.get(preset.lower(), BrowserPresets.OPTIMIZED)
    
    # Default: optimized for both dev and production
    return BrowserPresets.OPTIMIZED


# Default configuration (for backward compatibility)
DEFAULT_BROWSER_CONFIG = BrowserPresets.OPTIMIZED
