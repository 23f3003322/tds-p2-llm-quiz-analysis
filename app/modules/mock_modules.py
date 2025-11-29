"""
Mock Modules for Testing
These simulate real modules until Phase 2 modules are built
"""

from typing import Dict, Any, Optional
import time

from app.modules.base import (
    BaseModule,
    ModuleType,
    ModuleCapability,
    ModuleResult
)
from app.modules.capabilities import (
    ScrapingCapability,
    ProcessingCapability,
    VisualizationCapability,
    OutputCapability
)

from app.core.logging import get_logger
from app.modules.registry import ModuleRegistry

logger = get_logger(__name__)


class MockStaticScraper(BaseModule):
    """Mock static web scraper"""
    
    def __init__(self):
        super().__init__(name="static_scraper", module_type=ModuleType.SCRAPER)
    
    def get_capabilities(self) -> ModuleCapability:
        return ScrapingCapability.STATIC
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """Mock scraping execution"""
        self.logger.info(f"[MOCK] Scraping static HTML from: {parameters.get('url')}")
        
        # Simulate work
        await self._simulate_work(1.0)
        
        # Mock data
        mock_data = [
            {'name': 'Product 1', 'price': '$10.99'},
            {'name': 'Product 2', 'price': '$24.99'},
            {'name': 'Product 3', 'price': '$15.49'}
        ]
        
        return ModuleResult(
            success=True,
            data=mock_data,
            metadata={'rows': len(mock_data), 'source': 'mock'},
            execution_time=1.0
        )
    
    async def _simulate_work(self, seconds: float):
        """Simulate async work"""
        import asyncio
        await asyncio.sleep(seconds)


class MockDynamicScraper(BaseModule):
    """Mock dynamic web scraper (Playwright)"""
    
    def __init__(self):
        super().__init__(name="dynamic_scraper", module_type=ModuleType.SCRAPER)
    
    def get_capabilities(self) -> ModuleCapability:
        return ScrapingCapability.DYNAMIC
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """Mock dynamic scraping"""
        self.logger.info(f"[MOCK] Scraping with JavaScript from: {parameters.get('url')}")
        
        await self._simulate_work(2.0)
        
        mock_data = [
            {'name': 'Dynamic Product 1', 'price': '$29.99'},
            {'name': 'Dynamic Product 2', 'price': '$49.99'}
        ]
        
        return ModuleResult(
            success=True,
            data=mock_data,
            metadata={'rows': len(mock_data), 'method': 'playwright'},
            execution_time=2.0
        )
    
    async def _simulate_work(self, seconds: float):
        import asyncio
        await asyncio.sleep(seconds)


class MockDataProcessor(BaseModule):
    """Mock data processor"""
    
    def __init__(self):
        super().__init__(name="data_processor", module_type=ModuleType.PROCESSOR)
    
    def get_capabilities(self) -> ModuleCapability:
        return ProcessingCapability.DATA_TRANSFORMER
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """Mock data processing"""
        self.logger.info("[MOCK] Processing data with filters and aggregations")
        
        # Get input data from context
        input_data = context.get('data', []) if context else []
        
        # Mock filtering
        if parameters.get('filters'):
            self.logger.info(f"[MOCK] Applying {len(parameters['filters'])} filters")
        
        # Mock aggregation
        if parameters.get('aggregations'):
            self.logger.info(f"[MOCK] Applying {len(parameters['aggregations'])} aggregations")
        
        mock_result = {
            'filtered_rows': len(input_data),
            'aggregated': True,
            'data': input_data
        }
        
        return ModuleResult(
            success=True,
            data=mock_result,
            metadata={'processed': True},
            execution_time=0.5
        )


class MockChartCreator(BaseModule):
    """Mock chart/visualization creator"""
    
    def __init__(self):
        super().__init__(name="chart_creator", module_type=ModuleType.VISUALIZER)
    
    def get_capabilities(self) -> ModuleCapability:
        return VisualizationCapability.CHART_CREATOR
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """Mock chart creation"""
        chart_type = parameters.get('chart_type', 'bar')
        self.logger.info(f"[MOCK] Creating {chart_type} chart")
        
        mock_chart = {
            'type': chart_type,
            'file': f'/tmp/chart_{chart_type}.png',
            'created': True
        }
        
        return ModuleResult(
            success=True,
            data=mock_chart,
            metadata={'chart_type': chart_type},
            execution_time=0.8
        )


class MockCSVExporter(BaseModule):
    """Mock CSV exporter"""
    
    def __init__(self):
        super().__init__(name="csv_exporter", module_type=ModuleType.EXPORTER)
    
    def get_capabilities(self) -> ModuleCapability:
        return OutputCapability.CSV_EXPORTER
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """Mock CSV export"""
        filename = parameters.get('filename', 'output.csv')
        self.logger.info(f"[MOCK] Exporting to CSV: {filename}")
        
        mock_export = {
            'filename': filename,
            'path': f'/tmp/{filename}',
            'rows': 10,
            'exported': True
        }
        
        return ModuleResult(
            success=True,
            data=mock_export,
            metadata={'format': 'csv'},
            execution_time=0.3
        )


class MockAPIClient(BaseModule):
    """Mock API client"""
    
    def __init__(self):
        super().__init__(name="api_client", module_type=ModuleType.API_CLIENT)
    
    def get_capabilities(self) -> ModuleCapability:
        return ScrapingCapability.API_CLIENT
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """Mock API call"""
        api_url = parameters.get('url', 'https://api.example.com')
        self.logger.info(f"[MOCK] Calling API: {api_url}")
        
        await self._simulate_work(0.5)
        
        mock_data = {
            'status': 'success',
            'data': [
                {'id': 1, 'name': 'Item 1'},
                {'id': 2, 'name': 'Item 2'}
            ]
        }
        
        return ModuleResult(
            success=True,
            data=mock_data,
            metadata={'api_url': api_url},
            execution_time=0.5
        )
    
    async def _simulate_work(self, seconds: float):
        import asyncio
        await asyncio.sleep(seconds)


def register_mock_modules(registry: Optional['ModuleRegistry'] = None):
    """
    Register all mock modules for testing
    
    Args:
        registry: Registry to register to (creates new if None)
    """
    from app.modules.registry import ModuleRegistry
    
    if registry is None:
        registry = ModuleRegistry()
    
    # Register all mock modules
    registry.register(MockStaticScraper())
    registry.register(MockDynamicScraper())
    registry.register(MockDataProcessor())
    registry.register(MockChartCreator())
    registry.register(MockCSVExporter())
    registry.register(MockAPIClient())
    
    logger.info("✅ Registered 6 mock modules for testing")
    
    return registry


def register_real_modules(registry: Optional['ModuleRegistry'] = None):
    """
    Register real (non-mock) modules
    
    Args:
        registry: Registry to register to (creates new if None)
    """
    from app.modules.registry import ModuleRegistry
    from app.modules.scrapers import StaticScraper
    
    if registry is None:
        registry = ModuleRegistry()
    
    # Register real modules
    registry.register(StaticScraper())
    
    logger.info("✅ Registered 1 real module (StaticScraper)")
    
    return registry
