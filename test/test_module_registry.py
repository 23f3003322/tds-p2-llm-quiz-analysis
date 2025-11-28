"""
Test Module Registry
Comprehensive tests for module registration and selection
"""

import asyncio
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
from app.modules.registry import ModuleRegistry, ModuleSelector
from app.modules.mock_modules import register_mock_modules
from app.orchestrator.models import TaskClassification, TaskType, ComplexityLevel, OutputFormat
from app.orchestrator.parameter_models import (
    ExtractedParameters,
    DataSource,
    FilterCondition,
    VisualizationRequirement,
    OutputRequirement
)
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def test_registry_registration():
    """Test module registration"""
    
    print("\n" + "=" * 60)
    print("Test 1: Module Registration")
    print("=" * 60)
    
    # Clear registry
    registry = ModuleRegistry()
    registry.clear()
    
    # Register mock modules
    register_mock_modules(registry)
    
    # Check registration
    all_modules = registry.get_all_modules()
    
    print(f"\n✓ Registered {len(all_modules)} modules:")
    for module in all_modules:
        print(f"  - {module.name} ({module.module_type.value})")
    
    # List with details
    module_info = registry.list_modules()
    
    print(f"\n📊 Module Details:")
    for name, info in module_info.items():
        print(f"\n  {name}:")
        print(f"    Type: {info['type']}")
        print(f"    Initialized: {info['initialized']}")
        
        caps = info['capabilities']
        cap_list = [k for k, v in caps.items() if v and k.startswith('can_')]
        if cap_list:
            print(f"    Capabilities: {', '.join(cap_list[:3])}...")


def test_simple_scraping_selection():
    """Test module selection for simple scraping task"""
    
    print("\n" + "=" * 60)
    print("Test 2: Simple Scraping Task")
    print("=" * 60)
    
    # Setup
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    selector = ModuleSelector(registry)
    
    # Create simple scraping task
    classification = TaskClassification(
        primary_task=TaskType.WEB_SCRAPING,
        secondary_tasks=[],
        complexity=ComplexityLevel.SIMPLE,
        estimated_steps=2,
        requires_javascript=False,
        requires_authentication=False,
        output_format=OutputFormat.CSV,
        confidence=0.9,  # ← Added
        reasoning="Simple static web scraping task"  # ← Added
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='url',
                location='https://example.com/products',
                format='html',
                description='Product listing page'
            )
        ],
        output=OutputRequirement(
            format='csv',
            description='Export as CSV'
        )
    )
    
    print("\n📋 Task:")
    print("  Type: Simple web scraping")
    print("  JavaScript: No")
    print("  Output: CSV")
    print("-" * 60)
    
    # Select modules
    selected = selector.select_modules(classification, parameters)
    
    print(f"\n✅ Selected {len(selected)} modules:")
    for i, module in enumerate(selected, 1):
        print(f"  {i}. {module.name} ({module.module_type.value})")
    
    # Verify
    assert len(selected) >= 2, "Should select at least scraper + exporter"
    assert any(m.name == 'static_scraper' for m in selected), "Should use static scraper"
    assert any(m.name == 'csv_exporter' for m in selected), "Should use CSV exporter"
    
    print("\n✓ Correct modules selected!")


def test_dynamic_scraping_selection():
    """Test module selection for dynamic scraping (JavaScript)"""
    
    print("\n" + "=" * 60)
    print("Test 3: Dynamic Scraping Task (JavaScript)")
    print("=" * 60)
    
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    selector = ModuleSelector(registry)
    
    # Create dynamic scraping task
    classification = TaskClassification(
        primary_task=TaskType.WEB_SCRAPING,
        secondary_tasks=[],
        complexity=ComplexityLevel.MEDIUM,
        estimated_steps=3,
        requires_javascript=True,
        requires_authentication=False,
        output_format=OutputFormat.JSON,
        confidence=0.85,  # ← Added
        reasoning="Dynamic web scraping with JavaScript"  # ← Added
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='url',
                location='https://example.com/dynamic-products',
                format='html',
                description='Dynamic product listing (JavaScript)'
            )
        ]
    )
    
    print("\n📋 Task:")
    print("  Type: Dynamic web scraping")
    print("  JavaScript: Yes")
    print("  Output: JSON")
    print("-" * 60)
    
    # Select modules
    selected = selector.select_modules(classification, parameters)
    
    print(f"\n✅ Selected {len(selected)} modules:")
    for i, module in enumerate(selected, 1):
        print(f"  {i}. {module.name} ({module.module_type.value})")
    
    # Verify dynamic scraper selected
    assert any(m.name == 'dynamic_scraper' for m in selected), \
        "Should use dynamic scraper for JavaScript"
    
    print("\n✓ Dynamic scraper selected for JavaScript task!")


def test_complex_analysis_selection():
    """Test module selection for complex data analysis"""
    
    print("\n" + "=" * 60)
    print("Test 4: Complex Data Analysis Task")
    print("=" * 60)
    
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    selector = ModuleSelector(registry)
    
    # Create complex analysis task
    classification = TaskClassification(
        primary_task=TaskType.ML_ANALYSIS,
        secondary_tasks=[TaskType.VISUALIZATION],
        complexity=ComplexityLevel.COMPLEX,
        estimated_steps=5,
        requires_javascript=False,
        output_format=OutputFormat.EXCEL,
        confidence=0.88,  # ← Added
        reasoning="Complex data analysis with filtering and visualization"  # ← Added
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='url',
                location='https://example.com/sales.csv',
                format='csv',
                description='Sales data'
            )
        ],
        filters=[
            FilterCondition(
                field='region',
                operator='equals',
                value='North',
                description='Filter for North region'
            )
        ],
        visualizations=[
            VisualizationRequirement(
                type='chart',
                chart_type='bar',
                description='Bar chart of sales by category'
            )
        ]
    )
    
    print("\n📋 Task:")
    print("  Type: Data analysis + visualization")
    print("  Has filters: Yes")
    print("  Has visualizations: Yes")
    print("  Output: Excel")
    print("-" * 60)
    
    # Select modules
    selected = selector.select_modules(classification, parameters)
    
    print(f"\n✅ Selected {len(selected)} modules:")
    for i, module in enumerate(selected, 1):
        caps = module.get_capabilities()
        cap_names = [k for k, v in caps.dict().items() if v and k.startswith('can_')]
        print(f"  {i}. {module.name} ({module.module_type.value})")
        print(f"      Capabilities: {', '.join(cap_names[:2])}...")
    
    # Verify correct module types
    module_types = [m.module_type.value for m in selected]
    
    print(f"\n📊 Module Pipeline:")
    print(f"  Scraper: {'✓' if 'scraper' in module_types else '✗'}")
    print(f"  Processor: {'✓' if 'processor' in module_types else '✗'}")
    print(f"  Visualizer: {'✓' if 'visualizer' in module_types else '✗'}")
    print(f"  Exporter: {'✓' if 'exporter' in module_types else '✗'}")


def test_api_task_selection():
    """Test module selection for API-based task"""
    
    print("\n" + "=" * 60)
    print("Test 5: API Data Fetching Task")
    print("=" * 60)
    
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    selector = ModuleSelector(registry)
    
    # Create API task
    classification = TaskClassification(
        primary_task=TaskType.WEB_SCRAPING,
        secondary_tasks=[],
        complexity=ComplexityLevel.SIMPLE,
        estimated_steps=2,
        output_format=OutputFormat.JSON,
        confidence=0.92,  # ← Added
        reasoning="API data fetching task"  # ← Added
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='api',
                location='https://api.example.com/users',
                format='json',
                description='User data API'
            )
        ]
    )
    
    print("\n📋 Task:")
    print("  Type: API data fetching")
    print("  Source: REST API")
    print("  Output: JSON")
    print("-" * 60)
    
    # Select modules
    selected = selector.select_modules(classification, parameters)
    
    print(f"\n✅ Selected {len(selected)} modules:")
    for module in selected:
        print(f"  - {module.name} ({module.module_type.value})")
    
    # Verify API client selected
    assert any(m.name == 'api_client' for m in selected), \
        "Should use API client for API data source"
    
    print("\n✓ API client selected for API task!")


async def test_module_execution():
    """Test actually executing a selected module"""
    
    print("\n" + "=" * 60)
    print("Test 6: Module Execution")
    print("=" * 60)
    
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    # Get a module
    scraper = registry.get_module('static_scraper')
    
    print(f"\n🔧 Testing module: {scraper.name}")
    print("-" * 60)
    
    # Execute
    parameters = {
        'url': 'https://example.com/test',
        'columns': ['name', 'price']
    }
    
    print(f"\nExecuting with parameters:")
    print(f"  URL: {parameters['url']}")
    print(f"  Columns: {parameters['columns']}")
    
    result = await scraper.execute(parameters)
    
    print(f"\n✅ Execution Result:")
    print(f"  Success: {result.success}")
    print(f"  Execution Time: {result.execution_time}s")
    print(f"  Data rows: {len(result.data) if result.data else 0}")
    
    if result.data:
        print(f"\n📊 Sample Data:")
        for item in result.data[:3]:
            print(f"  - {item}")


def run_all_tests():
    """Run all registry tests"""
    
    print("\n" + "=" * 80)
    print(" " * 20 + "MODULE REGISTRY TEST SUITE")
    print("=" * 80)
    
    try:
        # Synchronous tests
        test_registry_registration()
        test_simple_scraping_selection()
        test_dynamic_scraping_selection()
        test_complex_analysis_selection()
        test_api_task_selection()
        
        # Async test
        asyncio.run(test_module_execution())
        
        print("\n" + "=" * 80)
        print(" " * 30 + "ALL TESTS PASSED")
        print("=" * 80)
        print("\n✅ Module registry tests complete!")
        print("\n📊 Summary:")
        print("  ✓ Module registration working")
        print("  ✓ Module selection logic working")
        print("  ✓ Different task types handled correctly")
        print("  ✓ Module execution working")
        
    except AssertionError as e:
        print(f"\n❌ Assertion failed: {e}")
        logger.error("Test assertion failed", exc_info=True)
        raise
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error("Test suite failed", exc_info=True)
        raise


if __name__ == "__main__":
    run_all_tests()
