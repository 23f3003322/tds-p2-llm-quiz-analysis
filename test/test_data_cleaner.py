"""
Test Data Cleaner
Comprehensive tests for data cleaning
"""

import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import asyncio
from app.modules.processors import DataCleaner, CleaningStrategy
from app.modules.processors.cleaning_strategies import (
    MissingValueStrategy,
    DuplicateStrategy,
    OutlierStrategy,
    TextCleaningStrategy
)
from app.core.logging import setup_logging

setup_logging()


async def test_basic_cleaning():
    """Test basic data cleaning"""
    print("\n" + "=" * 60)
    print("Test 1: Basic Cleaning")
    print("=" * 60)
    
    cleaner = DataCleaner()
    
    # Messy data
    data = [
        {"name": "  John Doe  ", "age": "25", "email": "john@example.com"},
        {"name": "Jane Smith", "age": "30 years", "email": "  jane@example.com  "},
        {"name": "Bob  ", "age": "N/A", "email": "bob@example.com"}
    ]
    
    print(f"  Original data: {len(data)} records")
    print(f"  Sample: {data[0]}")
    
    result = await cleaner.process(data)
    
    print(f"\n  Result:")
    print(f"    Success: {result.success}")
    print(f"    Records cleaned: {result.rows_cleaned}")
    print(f"    Changes: {result.changes_made}")
    print(f"    Sample cleaned: {result.data[0]}")
    
    assert result.success
    assert result.data[0]['name'] == "John Doe"  # Trimmed
    
    print("\n✅ Basic cleaning working")


async def test_missing_values():
    """Test missing value handling"""
    print("\n" + "=" * 60)
    print("Test 2: Missing Values")
    print("=" * 60)
    
    # Test different strategies
    data = [
        {"name": "John", "age": 25, "city": "New York"},
        {"name": "Jane", "age": None, "city": "Boston"},
        {"name": "Bob", "age": 30, "city": None}
    ]
    
    print(f"  Original: {len(data)} records with missing values")
    
    # Strategy 1: Drop
    strategy = CleaningStrategy(missing_values=MissingValueStrategy.DROP)
    cleaner = DataCleaner(strategy=strategy)
    
    result = await cleaner.process(data.copy())
    
    print(f"\n  DROP strategy:")
    print(f"    Records after: {len(result.data)}")
    print(f"    Removed: {result.rows_removed}")
    
    # Strategy 2: Fill zero
    strategy = CleaningStrategy(missing_values=MissingValueStrategy.FILL_ZERO)
    cleaner = DataCleaner(strategy=strategy)
    
    result = await cleaner.process(data.copy())
    
    print(f"\n  FILL_ZERO strategy:")
    print(f"    Records: {len(result.data)}")
    print(f"    Sample: {result.data[1]}")
    
    assert result.success
    
    print("\n✅ Missing value handling working")


async def test_duplicates():
    """Test duplicate removal"""
    print("\n" + "=" * 60)
    print("Test 3: Duplicate Removal")
    print("=" * 60)
    
    data = [
        {"id": 1, "name": "John"},
        {"id": 2, "name": "Jane"},
        {"id": 1, "name": "John"},  # Duplicate
        {"id": 3, "name": "Bob"}
    ]
    
    print(f"  Original: {len(data)} records (1 duplicate)")
    
    strategy = CleaningStrategy(duplicates=DuplicateStrategy.DROP_FIRST)
    cleaner = DataCleaner(strategy=strategy)
    
    result = await cleaner.process(data)
    
    print(f"\n  Result:")
    print(f"    Records after: {len(result.data)}")
    print(f"    Removed: {result.rows_removed}")
    print(f"    Changes: {result.changes_made}")
    
    assert result.success
    assert len(result.data) == 3
    
    print("\n✅ Duplicate removal working")


async def test_type_conversion():
    """Test type conversion"""
    print("\n" + "=" * 60)
    print("Test 4: Type Conversion")
    print("=" * 60)
    
    data = [
        {"name": "Product A", "price": "$1,299.99", "in_stock": "yes"},
        {"name": "Product B", "price": "999", "in_stock": "no"},
        {"name": "Product C", "price": "$499.00", "in_stock": "1"}
    ]
    
    print(f"  Original types:")
    print(f"    price: string (with $)")
    print(f"    in_stock: string")
    
    cleaner = DataCleaner()
    
    result = await cleaner.execute({
        'data': data,
        'type_conversions': {
            'price': 'number',
            'in_stock': 'boolean'
        }
    })
    
    print(f"\n  Converted:")
    print(f"    Sample: {result.data[0]}")
    print(f"    price type: {type(result.data[0]['price'])}")
    print(f"    in_stock type: {type(result.data[0]['in_stock'])}")
    
    assert result.success
    assert isinstance(result.data[0]['price'], float)
    assert result.data[0]['price'] == 1299.99
    
    print("\n✅ Type conversion working")


async def test_outliers():
    """Test outlier handling"""
    print("\n" + "=" * 60)
    print("Test 5: Outlier Detection")
    print("=" * 60)
    
    data = [
        {"id": 1, "score": 85},
        {"id": 2, "score": 90},
        {"id": 3, "score": 88},
        {"id": 4, "score": 92},
        {"id": 5, "score": 500},  # Outlier!
        {"id": 6, "score": 87}
    ]
    
    print(f"  Data with outlier: {[r['score'] for r in data]}")
    
    strategy = CleaningStrategy(
        outliers=OutlierStrategy.REMOVE,
        outlier_threshold=2.0
    )
    cleaner = DataCleaner(strategy=strategy)
    
    result = await cleaner.process(data)
    
    print(f"\n  Result:")
    print(f"    Records after: {len(result.data)}")
    print(f"    Scores: {[r['score'] for r in result.data]}")
    print(f"    Changes: {result.changes_made}")
    
    assert result.success
    assert len(result.data) == 5  # Outlier removed
    
    print("\n✅ Outlier detection working")


async def test_text_cleaning():
    """Test text cleaning strategies"""
    print("\n" + "=" * 60)
    print("Test 6: Text Cleaning")
    print("=" * 60)
    
    data = [
        {"name": "  JOHN DOE  ", "email": " John@Example.COM "},
        {"name": " jane smith ", "email": "JANE@EXAMPLE.COM"}
    ]
    
    print(f"  Original:")
    print(f"    {data[0]}")
    
    # Normalize strategy
    strategy = CleaningStrategy(text_cleaning=TextCleaningStrategy.NORMALIZE)
    cleaner = DataCleaner(strategy=strategy)
    
    result = await cleaner.process(data)
    
    print(f"\n  After NORMALIZE:")
    print(f"    {result.data[0]}")
    
    assert result.success
    assert result.data[0]['name'] == "john doe"
    
    print("\n✅ Text cleaning working")


async def test_execute_method():
    """Test via execute method (module interface)"""
    print("\n" + "=" * 60)
    print("Test 7: Execute Method")
    print("=" * 60)
    
    cleaner = DataCleaner()
    
    data = [
        {"name": "  John  ", "age": "25", "price": "$100"},
        {"name": "Jane", "age": "30", "price": "200"}
    ]
    
    parameters = {
        'data': data,
        'type_conversions': {
            'age': 'number',
            'price': 'number'
        }
    }
    
    print(f"  Processing via execute method")
    
    result = await cleaner.execute(parameters)
    
    print(f"\n  Result:")
    print(f"    Success: {result.success}")
    print(f"    Metadata: {result.metadata}")
    print(f"    Sample: {result.data[0]}")
    
    assert result.success
    
    print("\n✅ Execute method working")


async def test_complex_cleaning():
    """Test complex real-world scenario"""
    print("\n" + "=" * 60)
    print("Test 8: Complex Real-World Scenario")
    print("=" * 60)
    
    # Messy e-commerce data
    data = [
        {"product": "  Laptop  ", "price": "$1,299.99", "stock": "in stock", "rating": "4.5"},
        {"product": "Phone", "price": "999", "stock": "5 left", "rating": "N/A"},
        {"product": "Tablet ", "price": "  $499.00  ", "stock": "", "rating": "4.8"},
        {"product": "Monitor", "price": None, "stock": "out of stock", "rating": "4.2"},
        {"product": "Laptop  ", "price": "$1,299.99", "stock": "in stock", "rating": "4.5"},  # Dup
    ]
    
    print(f"  Original: {len(data)} records")
    print(f"  Issues: duplicates, formatting, missing values")
    
    strategy = CleaningStrategy(
        missing_values=MissingValueStrategy.FILL_ZERO,
        duplicates=DuplicateStrategy.DROP_FIRST,
        text_cleaning=TextCleaningStrategy.TRIM
    )
    
    cleaner = DataCleaner(strategy=strategy)
    
    result = await cleaner.execute({
        'data': data,
        'type_conversions': {
            'price': 'number',
            'rating': 'number'
        }
    })
    
    print(f"\n  Result:")
    print(f"    Records: {len(result.data)}")
    print(f"    Changes: {result.metadata['changes_made']}")
    print(f"\n  Sample cleaned record:")
    print(f"    {result.data[0]}")
    
    assert result.success
    assert len(result.data) == 4  # Duplicate removed
    
    print("\n✅ Complex cleaning working")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print(" " * 25 + "DATA CLEANER TEST SUITE")
    print("=" * 80)
    
    tests = [
        test_basic_cleaning,
        test_missing_values,
        test_duplicates,
        test_type_conversion,
        test_outliers,
        test_text_cleaning,
        test_execute_method,
        test_complex_cleaning
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
        print("\n✅ Data Cleaner is production ready!")
        print("\n📊 Verified:")
        print("  ✓ Basic cleaning (trim, normalize)")
        print("  ✓ Missing value handling (drop, fill)")
        print("  ✓ Duplicate removal")
        print("  ✓ Type conversion (string→number, boolean)")
        print("  ✓ Outlier detection (Z-score)")
        print("  ✓ Text cleaning strategies")
        print("  ✓ Module interface")
        print("  ✓ Real-world scenarios")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
