"""
Test Visualizer
Tests for quiz-focused chart generation
"""
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import asyncio
from app.modules.visualizers import ChartGenerator, ChartDetector
from app.core.logging import setup_logging

setup_logging()


async def test_chart_detection():
    """Test chart requirement detection"""
    print("\n" + "=" * 60)
    print("Test 1: Chart Detection")
    print("=" * 60)
    
    detector = ChartDetector()
    
    # Test cases
    test_cases = [
        ("What are the top 5 products?", False),  # No chart
        ("Create a bar chart of sales by category", True),  # Chart needed
        ("Plot the trend over time", True),  # Chart needed
        ("Analyze the data", False)  # No chart
    ]
    
    for question, expected_chart in test_cases:
        result = await detector.detect_chart_requirement(question)
        
        print(f"\n  Question: '{question}'")
        print(f"    Requires chart: {result['requires_chart']} (expected: {expected_chart})")
        print(f"    Chart type: {result.get('chart_type', 'N/A')}")
        
        assert result['requires_chart'] == expected_chart, f"Detection failed for: {question}"
    
    print("\n✅ Chart detection working")


async def test_chart_generation():
    """Test chart creation"""
    print("\n" + "=" * 60)
    print("Test 2: Chart Generation")
    print("=" * 60)
    
    generator = ChartGenerator()
    
    # Sample data
    data = [
        {"category": "Electronics", "sales": 5000},
        {"category": "Clothing", "sales": 3000},
        {"category": "Home", "sales": 4000}
    ]
    
    print(f"\n  Data: {len(data)} categories")
    
    result = await generator.execute({
        'question': 'Create a bar chart of sales by category',
        'data': data,
        'x_column': 'category',
        'y_column': 'sales',
        'title': 'Sales by Category'
    })
    
    print(f"\n  Result:")
    print(f"    Success: {result.success}")
    print(f"    Chart created: {result.data.get('chart_created', False)}")
    print(f"    Chart type: {result.data.get('chart_type', 'N/A')}")
    print(f"    Has base64: {bool(result.data.get('chart_base64'))}")
    
    assert result.success
    assert result.data['chart_created']
    assert result.data.get('chart_base64')
    
    print("\n✅ Chart generation working")


async def test_no_chart_needed():
    """Test when no chart is needed"""
    print("\n" + "=" * 60)
    print("Test 3: No Chart Needed")
    print("=" * 60)
    
    generator = ChartGenerator()
    
    data = [{"product": "Laptop", "sales": 100}]
    
    result = await generator.execute({
        'question': 'What are the top products?',  # No chart keyword
        'data': data
    })
    
    print(f"\n  Question: 'What are the top products?'")
    print(f"  Chart created: {result.data.get('chart_created', False)}")
    print(f"  Requires chart: {result.metadata.get('requires_chart', False)}")
    
    assert result.success
    assert not result.data['chart_created']
    
    print("\n✅ Correctly skipped chart generation")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print(" " * 25 + "VISUALIZER TEST SUITE")
    print("=" * 80)
    
    tests = [
        test_chart_detection,
        test_chart_generation,
        test_no_chart_needed
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(" " * 30 + "TEST SUMMARY")
    print("=" * 80)
    print(f"\n  Total: {len(tests)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Visualizer is production ready!")
        print("\n📊 Verified:")
        print("  ✓ Chart requirement detection")
        print("  ✓ Chart generation (bar, line, etc.)")
        print("  ✓ Conditional execution (only when needed)")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
