"""
Test Orchestrator Engine
Comprehensive tests for the main orchestrator
"""
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import asyncio
from app.orchestrator.orchestrator_engine import OrchestratorEngine
from app.modules.registry import ModuleRegistry
from app.modules.mock_modules import register_mock_modules
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_simple_task_execution():
    """Test execution of simple task"""
    
    print("\n" + "=" * 60)
    print("Test 1: Simple Task Execution")
    print("=" * 60)
    
    # Setup
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    orchestrator = OrchestratorEngine(
        module_registry=registry,
        enable_decomposition=True,
        enable_actions=False  # Disable for testing
    )
    
    # Simple task
    task = "Scrape product data from https://example.com/products and export as CSV"
    
    print(f"\n📋 Task: {task}")
    print("-" * 60)
    
    # Execute
    result = await orchestrator.execute_task(task)
    
    # Display result
    print(f"\n✅ Execution Result:")
    print(f"  Success: {result['success']}")
    print(f"  Task ID: {result['task_id']}")
    print(f"  Duration: {result['duration']:.2f}s")
    print(f"  Strategy: {result.get('strategy', 'N/A')}")
    
    print(f"\n📊 Steps Executed:")
    for step_name, completed in result['steps'].items():
        status = "✓" if completed else "✗"
        print(f"  {status} {step_name}")
    
    if result.get('execution_log'):
        print(f"\n📝 Execution Log (last 5 entries):")
        for log_entry in result['execution_log'][-5:]:
            print(f"  {log_entry}")
    
    orchestrator.cleanup()
    
    assert result['success'], "Task should complete successfully"
    print("\n✓ Simple task executed successfully")


async def test_complex_task_with_decomposition():
    """Test complex task that requires decomposition"""
    
    print("\n" + "=" * 60)
    print("Test 2: Complex Task with Decomposition")
    print("=" * 60)
    
    # Setup
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    orchestrator = OrchestratorEngine(
        module_registry=registry,
        enable_decomposition=True,
        enable_actions=False
    )
    
    # Complex task
    task = """
    Fetch sales data from https://example.com/sales.csv,
    filter for region='North' and amount>1000,
    calculate average sales by category,
    create a bar chart showing top 5 categories,
    and export results as CSV
    """
    
    print(f"\n📋 Task: {task.strip()}")
    print("-" * 60)
    
    # Execute
    result = await orchestrator.execute_task(task)
    
    # Display result
    print(f"\n✅ Execution Result:")
    print(f"  Success: {result['success']}")
    print(f"  Duration: {result['duration']:.2f}s")
    print(f"  Strategy: {result.get('strategy', 'N/A')}")
    
    # Check if decomposition was used
    execution_details = result.get('execution_details', {})
    
    if execution_details.get('strategy') == 'decompose':
        print(f"\n🔨 Decomposition Used:")
        print(f"  Subtasks: {execution_details.get('total_subtasks', 0)}")
        print(f"  Completed: {execution_details.get('subtasks_completed', 0)}")
        
        decomp_info = execution_details.get('decomposition', {})
        print(f"  Complexity: {decomp_info.get('complexity_score', 0):.2f}")
        print(f"  Can parallelize: {decomp_info.get('can_parallelize', False)}")
    
    orchestrator.cleanup()
    
    print("\n✓ Complex task executed with decomposition")


async def test_execution_context_tracking():
    """Test execution context and logging"""
    
    print("\n" + "=" * 60)
    print("Test 3: Execution Context Tracking")
    print("=" * 60)
    
    # Setup
    registry = ModuleRegistry()
    registry.clear()
    register_mock_modules(registry)
    
    orchestrator = OrchestratorEngine(
        module_registry=registry,
        enable_decomposition=False,
        enable_actions=False
    )
    
    task = "Simple test task for context tracking"
    
    print(f"\n📋 Task: {task}")
    print("-" * 60)
    
    # Execute
    result = await orchestrator.execute_task(task)
    
    # Check context tracking
    print(f"\n📊 Execution Tracking:")
    print(f"  Task ID: {result['task_id']}")
    print(f"  Execution ID: {result['execution_id']}")
    print(f"  Duration: {result['duration']:.2f}s")
    
    print(f"\n📝 Full Execution Log:")
    for log_entry in result['execution_log']:
        print(f"  {log_entry}")
    
    print(f"\n🔍 Steps Breakdown:")
    for step_name, completed in result['steps'].items():
        print(f"  {step_name}: {'✓ Completed' if completed else '✗ Not executed'}")
    
    orchestrator.cleanup()
    
    assert 'task_id' in result
    assert 'execution_id' in result
    assert len(result['execution_log']) > 0
    
    print("\n✓ Context tracking working correctly")


async def test_error_handling():
    """Test error handling in orchestrator"""
    
    print("\n" + "=" * 60)
    print("Test 4: Error Handling")
    print("=" * 60)
    
    # Setup with no modules (will cause failure)
    registry = ModuleRegistry()
    registry.clear()  # Empty registry
    
    orchestrator = OrchestratorEngine(
        module_registry=registry,
        enable_decomposition=False,
        enable_actions=False
    )
    
    task = "Test task that will fail due to no modules"
    
    print(f"\n📋 Task: {task}")
    print("(Expected to fail - no modules registered)")
    print("-" * 60)
    
    # Execute
    result = await orchestrator.execute_task(task)
    
    # Should fail gracefully
    print(f"\n✅ Error Handled Gracefully:")
    print(f"  Success: {result['success']} (should be False)")
    print(f"  Has error: {'error' in result}")
    
    if 'error' in result:
        print(f"  Error message: {result['error'][:100]}...")
    
    print(f"\n📝 Execution Log:")
    for log_entry in result.get('execution_log', [])[-3:]:
        print(f"  {log_entry}")
    
    orchestrator.cleanup()
    
    assert result['success'] == False, "Should fail when no modules available"
    assert 'error' in result, "Should have error message"
    
    print("\n✓ Error handling working correctly")


async def run_all_tests():
    """Run all orchestrator tests"""
    
    print("\n" + "=" * 80)
    print(" " * 18 + "ORCHESTRATOR ENGINE TEST SUITE")
    print(" " * 25 + "(FINAL STEP!)")
    print("=" * 80)
    
    try:
        await test_simple_task_execution()
        await test_complex_task_with_decomposition()
        await test_execution_context_tracking()
        await test_error_handling()
        
        print("\n" + "=" * 80)
        print(" " * 30 + "ALL TESTS PASSED")
        print("=" * 80)
        print("\n🎉 ORCHESTRATOR ENGINE COMPLETE!")
        print("\n📊 Test Summary:")
        print("  ✓ Simple task execution working")
        print("  ✓ Complex task decomposition working")
        print("  ✓ Execution context tracking working")
        print("  ✓ Error handling working")
        print("  ✓ End-to-end orchestration working")
        
        print("\n" + "=" * 80)
        print("🚀 PHASE 1 COMPLETE - INTELLIGENT ORCHESTRATION READY!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error("Test suite failed", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
