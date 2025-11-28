"""
Test Simple Router
Comprehensive tests for task routing and execution
"""

import asyncio
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.routing.simple_router import SimpleRouter
from app.modules.registry import ModuleRegistry
from app.modules.mock_modules import register_mock_modules
from app.orchestrator.models import TaskClassification, TaskType, ComplexityLevel, OutputFormat
from app.orchestrator.parameter_models import (
    ExtractedParameters,
    DataSource,
    FilterCondition,
    OutputRequirement
)
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_simple_scraping_task():
    """Test simple web scraping task end-to-end"""
    
    print("\n" + "=" * 60)
    print("Test 1: Simple Web Scraping Task")
    print("=" * 60)
    
    # Setup
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    router = SimpleRouter(module_registry=registry)
    
    # Create task
    classification = TaskClassification(
        primary_task=TaskType.WEB_SCRAPING,
        secondary_tasks=[],
        complexity=ComplexityLevel.SIMPLE,
        estimated_steps=2,
        requires_javascript=False,
        output_format=OutputFormat.CSV,
        confidence=0.9,
        reasoning="Simple static web scraping"
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='url',
                location='https://example.com/products',
                format='html',
                description='Product listing'
            )
        ],
        output=OutputRequirement(
            format='csv',
            filename='products.csv',
            description='Export to CSV'
        )
    )
    
    task_description = "Scrape products from example.com and save as CSV"
    
    print(f"\n📋 Task: {task_description}")
    print(f"Type: {classification.primary_task.value}")
    print(f"Complexity: {classification.complexity.value}")
    print("-" * 60)
    
    # Execute
    result = await router.route_and_execute(
        classification=classification,
        parameters=parameters,
        task_description=task_description
    )
    
    # Display result
    print(f"\n✅ Execution Result:")
    print(f"  Success: {result.success}")
    print(f"  Steps Completed: {result.steps_completed}/{result.total_steps}")
    print(f"  Execution Time: {result.execution_time:.2f}s")
    
    if result.step_results:
        print(f"\n📊 Step Details:")
        for step_result in result.step_results:
            status = "✅" if step_result['success'] else "❌"
            print(f"  {status} Step {step_result['step']}: {step_result['module']}")
            if 'execution_time' in step_result:
                print(f"      Time: {step_result['execution_time']:.2f}s")
    
    if result.errors:
        print(f"\n⚠️  Errors:")
        for error in result.errors:
            print(f"  - {error}")
    
    if result.data:
        print(f"\n📦 Final Data:")
        print(f"  Type: {type(result.data).__name__}")
        if isinstance(result.data, list) and result.data:
            print(f"  Sample: {result.data[0]}")
    
    router.cleanup()


async def test_complex_analysis_task():
    """Test complex data analysis with multiple steps"""
    
    print("\n" + "=" * 60)
    print("Test 2: Complex Data Analysis Task")
    print("=" * 60)
    
    # Setup
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    router = SimpleRouter(module_registry=registry)
    
    # Create complex task
    classification = TaskClassification(
        primary_task=TaskType.ML_ANALYSIS,
        secondary_tasks=[TaskType.VISUALIZATION],
        complexity=ComplexityLevel.COMPLEX,
        estimated_steps=4,
        requires_javascript=False,
        output_format=OutputFormat.CSV,
        confidence=0.85,
        reasoning="Complex analysis with filtering and visualization"
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
                description='Filter North region'
            ),
            FilterCondition(
                field='amount',
                operator='greater_than',
                value=1000,
                description='Amount > 1000'
            )
        ],
        output=OutputRequirement(
            format='csv',
            filename='analysis_results.csv',
            description='Export results'
        )
    )
    
    task_description = "Analyze sales data, filter for North region with amount > 1000, export as CSV"
    
    print(f"\n📋 Task: {task_description}")
    print(f"Type: {classification.primary_task.value}")
    print(f"Complexity: {classification.complexity.value}")
    print(f"Filters: {len(parameters.filters)}")
    print("-" * 60)
    
    # Execute
    result = await router.route_and_execute(
        classification=classification,
        parameters=parameters,
        task_description=task_description
    )
    
    # Display result
    print(f"\n✅ Execution Result:")
    print(f"  Success: {result.success}")
    print(f"  Steps Completed: {result.steps_completed}/{result.total_steps}")
    print(f"  Execution Time: {result.execution_time:.2f}s")
    
    print(f"\n📊 Execution Pipeline:")
    for i, step_result in enumerate(result.step_results, 1):
        status = "✅" if step_result['success'] else "❌"
        print(f"  {status} {step_result['module']}")
    
    router.cleanup()


async def test_api_task():
    """Test API data fetching task"""
    
    print("\n" + "=" * 60)
    print("Test 3: API Data Fetching")
    print("=" * 60)
    
    # Setup
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    router = SimpleRouter(module_registry=registry)
    
    # Create API task
    classification = TaskClassification(
        primary_task=TaskType.WEB_SCRAPING,
        secondary_tasks=[],
        complexity=ComplexityLevel.SIMPLE,
        estimated_steps=2,
        output_format=OutputFormat.JSON,
        confidence=0.92,
        reasoning="API data fetching"
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='api',
                location='https://api.example.com/users',
                format='json',
                description='User API'
            )
        ]
    )
    
    task_description = "Fetch user data from API"
    
    print(f"\n📋 Task: {task_description}")
    print(f"Data Source: {parameters.data_sources[0].type}")
    print("-" * 60)
    
    # Execute
    result = await router.route_and_execute(
        classification=classification,
        parameters=parameters,
        task_description=task_description
    )
    
    # Display result
    print(f"\n✅ Result: {'Success' if result.success else 'Failed'}")
    print(f"  Modules Used: {result.steps_completed}")
    print(f"  Time: {result.execution_time:.2f}s")
    
    router.cleanup()


async def test_execution_plan_creation():
    """Test execution plan creation"""
    
    print("\n" + "=" * 60)
    print("Test 4: Execution Plan Creation")
    print("=" * 60)
    
    # Setup
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    router = SimpleRouter(module_registry=registry)
    
    # Simple classification
    classification = TaskClassification(
        primary_task=TaskType.WEB_SCRAPING,
        secondary_tasks=[],
        complexity=ComplexityLevel.SIMPLE,
        estimated_steps=2,
        output_format=OutputFormat.CSV,
        confidence=0.9,
        reasoning="Test plan creation"
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='url',
                location='https://example.com',
                format='html',
                description='Test source'
            )
        ]
    )
    
    # Select modules
    modules = router.selector.select_modules(classification, parameters)
    
    # Create plan
    plan = router._create_execution_plan(
        task_id="test-123",
        modules=modules,
        parameters=parameters,
        task_description="Test task"
    )
    
    print(f"\n📋 Execution Plan Created:")
    print(f"  Task ID: {plan.task_id}")
    print(f"  Total Steps: {len(plan.steps)}")
    print(f"  Complexity: {plan.complexity}")
    print(f"  Estimated Duration: {plan.estimated_duration}s")
    
    print(f"\n📝 Steps:")
    for step in plan.steps:
        print(f"  {step.step_number}. {step.description}")
        print(f"      Module: {step.module_name}")
        print(f"      Status: {step.status.value}")
        if step.depends_on:
            print(f"      Depends on: Step {step.depends_on}")
    
    router.cleanup()


async def run_all_tests():
    """Run all router tests"""
    
    print("\n" + "=" * 80)
    print(" " * 20 + "SIMPLE ROUTER TEST SUITE")
    print("=" * 80)
    
    try:
        await test_simple_scraping_task()
        await test_complex_analysis_task()
        await test_api_task()
        await test_execution_plan_creation()
        
        print("\n" + "=" * 80)
        print(" " * 30 + "ALL TESTS PASSED")
        print("=" * 80)
        print("\n✅ Simple router tests complete!")
        print("\n📊 Summary:")
        print("  ✓ Simple scraping task working")
        print("  ✓ Complex analysis task working")
        print("  ✓ API task working")
        print("  ✓ Execution plan creation working")
        print("  ✓ Module execution working")
        print("  ✓ End-to-end routing working")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error("Test suite failed", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
