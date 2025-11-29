"""
Data Extractor Module
Extracts specific values (secret codes, numbers, etc.) from scraped content
"""


from typing import Optional
from app.core.logging import get_logger
from app.modules.base import BaseModule, ModuleResult, ModuleType
from app.modules import ExtractionCapability
from app.modules.scrapers.scraper_utils import extract_text_clean
from bs4 import BeautifulSoup
import re
import json

logger = get_logger(__name__)


class DataExtractor(BaseModule):
    """Extracts secret codes, values, and data from scraped content"""
    
    def __init__(self):
        super().__init__(name="data_extractor", module_type=ModuleType.PROCESSOR)
        self.capabilities = ExtractionCapability.DATA_EXTRACTOR
    
    def get_capabilities(self) -> ExtractionCapability:
        return self.capabilities
    
    async def execute(
        self,
        parameters: dict,
        context: Optional[dict] = None
    ) -> ModuleResult:
        """Extract data from scraped content"""
        data = parameters.get('data', {})
        target = parameters.get('target', 'secret code').lower()
        
        logger.info(f"🔍 Extracting '{target}' from data")
        
        try:
            # Try common TDS secret code patterns
            if target in ['secret', 'secret code', 'code']:
                secret = self._extract_secret_code(data)
                if secret:
                    return ModuleResult(
                        success=True,
                        data={"secret_code": secret, "extracted": True}
                    )
            
            # JSON extraction
            json_data = self._extract_json(data)
            if json_data:
                return ModuleResult(
                    success=True,
                    data={"json": json_data}
                )
            
            # Text extraction
            text_data = self._extract_text(data)
            return ModuleResult(
                success=True,
                data={"text": text_data}
            )
            
        except Exception as e:
            return ModuleResult(
                success=False,
                error=f"Extraction failed: {str(e)}"
            )
    
    def _extract_secret_code(self, data: dict) -> str:
        """Extract secret code from TDS pages"""
        content = ""
        
        # Handle different data formats
        if isinstance(data, dict):
            for key, value in data.items():
                content += f"{str(value)} "
        elif isinstance(data, list):
            content = " ".join(str(item) for item in data)
        else:
            content = str(data)
        
        # Common TDS secret patterns
        patterns = [
            r'"secret"[:\s]*"([^"]+)"',
            r'secret[:\s]*"([^"]+)"',
            r'secret[:\s]*([a-zA-Z0-9]{8,})',
            r'code[:\s]*"([^"]+)"',
            r'([A-Z0-9]{16,})',  # Long uppercase codes
            r'([a-f0-9]{32})',    # Hex codes
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                secret = match.group(1).strip()
                logger.info(f"✓ Found secret code: {secret}")
                return secret
        
        logger.warning("No secret code found")
        return None
    
    def _extract_json(self, data: dict) -> dict:
        """Extract JSON from content"""
        content = ""
        if isinstance(data, dict):
            for key, value in data.items():
                content += str(value)
        
        # Find JSON blocks
        json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
        for json_str in json_matches:
            try:
                return json.loads(json_str)
            except:
                continue
        return {}
    
    def _extract_text(self, data: dict) -> str:
        """Extract clean text"""
        content = ""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    content += value + " "
        return extract_text_clean(content)
