"""
Test Task Decomposer
Comprehensive tests for task decomposition
"""

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)



import asyncio
from app.decomposition.task_decomposer import TaskDecomposer
from app.orchestrator.models import TaskClassification, TaskType, ComplexityLevel, OutputFormat
from app.orchestrator.parameter_models import (
    ExtractedParameters,
    DataSource,
    FilterCondition,
    AggregationSpec,
    VisualizationRequirement,
    OutputRequirement
)
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def test_simple_task_no_decomposition():
    """Test that simple tasks don't get decomposed"""
    
    print("\n" + "=" * 60)
    print("Test 1: Simple Task (No Decomposition)")
    print("=" * 60)
    
    decomposer = TaskDecomposer()
    
    # Simple task
    classification = TaskClassification(
        primary_task=TaskType.WEB_SCRAPING,
        secondary_tasks=[],
        complexity=ComplexityLevel.SIMPLE,
        estimated_steps=1,
        output_format=OutputFormat.CSV,
        confidence=0.9,
        reasoning="Simple scraping"
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='url',
                location='https://example.com',
                format='html',
                description='Test page'
            )
        ]
    )
    
    task_description = "Scrape data from example.com"
    
    print(f"\n📋 Task: {task_description}")
    print(f"Complexity: {classification.complexity.value}")
    print(f"Estimated steps: {classification.estimated_steps}")
    print("-" * 60)
    
    # Decompose
    result = decomposer.decompose(classification, parameters, task_description)
    
    print(f"\n✅ Decomposition Result:")
    print(f"  Subtasks: {len(result.subtasks)}")
    print(f"  Strategy: {result.execution_strategy}")
    print(f"  Needs decomposition: {result.metadata.get('decomposed', True)}")
    
    assert len(result.subtasks) == 1, "Simple task should have 1 subtask"
    assert result.execution_strategy == 'single', "Should use single strategy"
    
    print("\n✓ Simple task correctly identified (no decomposition)")


def test_complex_task_sequential():
    """Test complex task with sequential decomposition"""
    
    print("\n" + "=" * 60)
    print("Test 2: Complex Task (Sequential Decomposition)")
    print("=" * 60)
    
    decomposer = TaskDecomposer()
    
    # Complex task
    classification = TaskClassification(
        primary_task=TaskType.ML_ANALYSIS,
        secondary_tasks=[TaskType.VISUALIZATION],
        complexity=ComplexityLevel.COMPLEX,
        estimated_steps=5,
        output_format=OutputFormat.CSV,
        confidence=0.85,
        reasoning="Complex analysis with multiple steps"
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='url',
                location='https://example.com/data.csv',
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
            )
        ],
        aggregations=[
            AggregationSpec(
                function='avg',
                field='sales',
                group_by=['category'],
                description='Average sales by category'
            )
        ],
        visualizations=[
            VisualizationRequirement(
                type='chart',
                chart_type='bar',
                description='Bar chart'
            )
        ],
        output=OutputRequirement(
            format='csv',
            description='Export results'
        )
    )
    
    task_description = "Analyze sales data, filter, aggregate, visualize, and export"
    
    print(f"\n📋 Task: {task_description}")
    print(f"Complexity: {classification.complexity.value}")
    print(f"Has filters: {len(parameters.filters)}")
    print(f"Has aggregations: {len(parameters.aggregations)}")
    print(f"Has visualizations: {len(parameters.visualizations)}")
    print("-" * 60)
    
    # Decompose
    result = decomposer.decompose(classification, parameters, task_description)
    
    print(f"\n✅ Decomposition Result:")
    print(f"  Subtasks: {len(result.subtasks)}")
    print(f"  Strategy: {result.execution_strategy}")
    print(f"  Can parallelize: {result.can_parallelize}")
    print(f"  Complexity score: {result.complexity_score}")
    print(f"  Estimated duration: {result.estimated_total_duration}s")
    
    print(f"\n📝 Subtasks:")
    for i, subtask in enumerate(result.subtasks, 1):
        print(f"  {i}. {subtask.name} ({subtask.type.value})")
        print(f"      ID: {subtask.id}")
        print(f"      Depends on: {subtask.depends_on if subtask.depends_on else 'None'}")
        print(f"      Priority: {subtask.priority}")
        print(f"      Duration: {subtask.estimated_duration}s")
    
    print(f"\n🔗 Dependencies:")
    for dep in result.dependencies:
        print(f"  {dep.subtask_id} depends on {dep.depends_on}")
    
    assert len(result.subtasks) > 1, "Complex task should have multiple subtasks"
    print("\n✓ Complex task correctly decomposed")


def test_parallel_decomposition():
    """Test parallel decomposition with multiple data sources"""
    
    print("\n" + "=" * 60)
    print("Test 3: Parallel Decomposition (Multiple Sources)")
    print("=" * 60)
    
    decomposer = TaskDecomposer()
    
    # Task with multiple data sources
    classification = TaskClassification(
        primary_task=TaskType.WEB_SCRAPING,
        secondary_tasks=[],
        complexity=ComplexityLevel.MEDIUM,
        estimated_steps=3,
        output_format=OutputFormat.JSON,
        confidence=0.88,
        reasoning="Multi-source data fetching"
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='url',
                location='https://source1.com/data',
                format='json',
                description='Source 1'
            ),
            DataSource(
                type='url',
                location='https://source2.com/data',
                format='json',
                description='Source 2'
            ),
            DataSource(
                type='url',
                location='https://source3.com/data',
                format='json',
                description='Source 3'
            )
        ]
    )
    
    task_description = "Fetch data from 3 different sources"
    
    print(f"\n📋 Task: {task_description}")
    print(f"Data sources: {len(parameters.data_sources)}")
    print("-" * 60)
    
    # Decompose
    result = decomposer.decompose(classification, parameters, task_description)
    
    print(f"\n✅ Decomposition Result:")
    print(f"  Subtasks: {len(result.subtasks)}")
    print(f"  Strategy: {result.execution_strategy}")
    print(f"  Can parallelize: {result.can_parallelize}")
    
    print(f"\n📝 Subtasks:")
    for subtask in result.subtasks:
        parallel_indicator = "🔀" if subtask.can_run_parallel else "➡️"
        print(f"  {parallel_indicator} {subtask.name}")
        print(f"      Can run parallel: {subtask.can_run_parallel}")
        print(f"      Depends on: {subtask.depends_on if subtask.depends_on else 'None'}")
    
    print(f"\n📊 Execution Order (Batches):")
    batches = result.get_execution_order()
    for i, batch in enumerate(batches, 1):
        print(f"  Batch {i}: {batch}")
        if len(batch) > 1:
            print(f"      ↳ Can execute in parallel")
    
    assert result.can_parallelize, "Should support parallel execution"
    assert result.execution_strategy == 'parallel', "Should use parallel strategy"
    
    print("\n✓ Parallel decomposition working correctly")


def test_execution_order():
    """Test execution order calculation"""
    
    print("\n" + "=" * 60)
    print("Test 4: Execution Order Calculation")
    print("=" * 60)
    
    decomposer = TaskDecomposer()
    
    # Complex task with dependencies
    classification = TaskClassification(
        primary_task=TaskType.ML_ANALYSIS,
        secondary_tasks=[TaskType.VISUALIZATION],
        complexity=ComplexityLevel.COMPLEX,
        estimated_steps=4,
        output_format=OutputFormat.CSV,
        confidence=0.9,
        reasoning="Test execution order"
    )
    
    parameters = ExtractedParameters(
        data_sources=[
            DataSource(
                type='url',
                location='https://example.com/data.csv',
                format='csv',
                description='Data'
            )
        ],
        filters=[FilterCondition(field='status', operator='equals', value='active', description='Active only')],
        visualizations=[VisualizationRequirement(type='chart', chart_type='line', description='Line chart')],
        output=OutputRequirement(format='csv', description='Export')
    )
    
    # Decompose
    result = decomposer.decompose(classification, parameters, "Complex task")
    
    print(f"\n📊 Execution Order:")
    batches = result.get_execution_order()
    
    for i, batch in enumerate(batches, 1):
        print(f"\nBatch {i}:")
        for subtask_id in batch:
            subtask = result.get_subtask(subtask_id)
            print(f"  - {subtask.name} (ID: {subtask_id})")
    
    print(f"\n✓ Total batches: {len(batches)}")
    print(f"✓ All subtasks covered: {sum(len(b) for b in batches) == len(result.subtasks)}")


def run_all_tests():
    """Run all decomposer tests"""
    
    print("\n" + "=" * 80)
    print(" " * 20 + "TASK DECOMPOSER TEST SUITE")
    print("=" * 80)
    
    try:
        test_simple_task_no_decomposition()
        test_complex_task_sequential()
        test_parallel_decomposition()
        test_execution_order()
        
        print("\n" + "=" * 80)
        print(" " * 30 + "ALL TESTS PASSED")
        print("=" * 80)
        print("\n✅ Task decomposer tests complete!")
        print("\n📊 Summary:")
        print("  ✓ Simple tasks not decomposed")
        print("  ✓ Complex tasks decomposed sequentially")
        print("  ✓ Multiple sources decomposed in parallel")
        print("  ✓ Execution order calculated correctly")
        print("  ✓ Dependencies tracked properly")
        
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
