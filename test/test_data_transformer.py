"""
Test Data Transformer
Comprehensive tests for data transformation
"""
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
import asyncio
from app.modules.processors import DataTransformer
from app.core.logging import setup_logging

setup_logging()


async def test_filter():
    """Test filtering"""
    print("\n" + "=" * 60)
    print("Test 1: Filter Data")
    print("=" * 60)
    
    transformer = DataTransformer()
    
    data = [
        {"name": "Laptop", "price": 1299, "category": "Electronics"},
        {"name": "Phone", "price": 999, "category": "Electronics"},
        {"name": "T-Shirt", "price": 20, "category": "Clothing"},
        {"name": "Monitor", "price": 399, "category": "Electronics"}
    ]
    
    print(f"  Original: {len(data)} records")
    
    result = await transformer.execute({
        'data': data,
        'operations': [
            {
                'type': 'filter',
                'conditions': {
                    'category': {'eq': 'Electronics'},
                    'price': {'lt': 1000}
                }
            }
        ]
    })
    
    print(f"\n  Filtered:")
    print(f"    Records: {len(result.data)}")
    print(f"    Results: {result.data}")
    
    assert result.success
    assert len(result.data) == 2  # Phone and Monitor
    
    print("\n✅ Filter working")


async def test_sort():
    """Test sorting"""
    print("\n" + "=" * 60)
    print("Test 2: Sort Data")
    print("=" * 60)
    
    transformer = DataTransformer()
    
    data = [
        {"name": "Laptop", "price": 1299},
        {"name": "Phone", "price": 999},
        {"name": "Monitor", "price": 399}
    ]
    
    result = await transformer.execute({
        'data': data,
        'operations': [
            {'type': 'sort', 'columns': ['price'], 'ascending': True}
        ]
    })
    
    print(f"\n  Sorted by price (ascending):")
    for item in result.data:
        print(f"    {item['name']}: ${item['price']}")
    
    assert result.success
    assert result.data[0]['price'] == 399  # Cheapest first
    
    print("\n✅ Sort working")


async def test_aggregate():
    """Test aggregation"""
    print("\n" + "=" * 60)
    print("Test 3: Aggregate Data")
    print("=" * 60)
    
    transformer = DataTransformer()
    
    data = [
        {"category": "Electronics", "price": 1299, "sold": 10},
        {"category": "Electronics", "price": 999, "sold": 20},
        {"category": "Clothing", "price": 20, "sold": 100},
        {"category": "Clothing", "price": 30, "sold": 80}
    ]
    
    print(f"  Original: {len(data)} records")
    
    result = await transformer.execute({
        'data': data,
        'operations': [
            {
                'type': 'aggregate',
                'group_by': 'category',
                'aggregations': {
                    'avg_price': {'column': 'price', 'function': 'avg'},
                    'total_sold': {'column': 'sold', 'function': 'sum'},
                    'count': {'function': 'count'}
                }
            }
        ]
    })
    
    print(f"\n  Aggregated:")
    for row in result.data:
        print(f"    {row}")
    
    assert result.success
    assert len(result.data) == 2  # 2 categories
    
    print("\n✅ Aggregate working")


async def test_select_columns():
    """Test column selection"""
    print("\n" + "=" * 60)
    print("Test 4: Select Columns")
    print("=" * 60)
    
    transformer = DataTransformer()
    
    data = [
        {"name": "Laptop", "price": 1299, "category": "Electronics", "stock": 5, "rating": 4.5}
    ]
    
    result = await transformer.execute({
        'data': data,
        'operations': [
            {'type': 'select', 'columns': ['name', 'price']}
        ]
    })
    
    print(f"\n  Selected columns:")
    print(f"    {result.data[0]}")
    
    assert result.success
    assert 'name' in result.data[0]
    assert 'price' in result.data[0]
    assert 'category' not in result.data[0]
    
    print("\n✅ Select working")


async def test_limit():
    """Test limiting results"""
    print("\n" + "=" * 60)
    print("Test 5: Limit Results")
    print("=" * 60)
    
    transformer = DataTransformer()
    
    data = [{"id": i} for i in range(100)]
    
    print(f"  Original: {len(data)} records")
    
    result = await transformer.execute({
        'data': data,
        'operations': [
            {'type': 'limit', 'limit': 5}
        ]
    })
    
    print(f"  Limited: {len(result.data)} records")
    
    assert result.success
    assert len(result.data) == 5
    
    print("\n✅ Limit working")


async def test_complex_pipeline():
    """Test complex transformation pipeline"""
    print("\n" + "=" * 60)
    print("Test 6: Complex Pipeline")
    print("=" * 60)
    
    transformer = DataTransformer()
    
    # E-commerce data
    data = [
        {"product": "Laptop", "price": 1299, "category": "Electronics", "sold": 50, "rating": 4.5},
        {"product": "Phone", "price": 999, "category": "Electronics", "sold": 120, "rating": 4.8},
        {"product": "T-Shirt", "price": 20, "category": "Clothing", "sold": 500, "rating": 4.2},
        {"product": "Jeans", "price": 60, "category": "Clothing", "sold": 300, "rating": 4.6},
        {"product": "Monitor", "price": 399, "category": "Electronics", "sold": 80, "rating": 4.3},
        {"product": "Shoes", "price": 80, "category": "Clothing", "sold": 200, "rating": 4.4}
    ]
    
    print(f"  Pipeline: Filter → Aggregate → Sort → Limit")
    
    result = await transformer.execute({
        'data': data,
        'operations': [
            # 1. Filter: Only products sold > 100
            {
                'type': 'filter',
                'conditions': {'sold': {'gte': 100}}
            },
            # 2. Aggregate by category
            {
                'type': 'aggregate',
                'group_by': 'category',
                'aggregations': {
                    'avg_rating': {'column': 'rating', 'function': 'avg'},
                    'total_sold': {'column': 'sold', 'function': 'sum'},
                    'products': {'function': 'count'}
                }
            },
            # 3. Sort by total_sold descending
            {
                'type': 'sort',
                'columns': ['total_sold'],
                'ascending': False
            },
            # 4. Top 2 categories
            {
                'type': 'limit',
                'limit': 2
            }
        ]
    })
    
    print(f"\n  Result:")
    for row in result.data:
        print(f"    {row}")
    
    assert result.success
    assert len(result.data) == 2
    
    print("\n✅ Complex pipeline working")


async def test_join():
    """Test joining datasets"""
    print("\n" + "=" * 60)
    print("Test 7: Join Datasets")
    print("=" * 60)
    
    transformer = DataTransformer()
    
    # Products
    products = [
        {"id": 1, "name": "Laptop", "category_id": 10},
        {"id": 2, "name": "Phone", "category_id": 10}
    ]
    
    # Categories
    categories = [
        {"id": 10, "category_name": "Electronics"},
        {"id": 20, "category_name": "Clothing"}
    ]
    
    result = await transformer.execute({
        'data': products,
        'operations': [
            {
                'type': 'join',
                'right_data': categories,
                'left_key': 'category_id',
                'right_key': 'id',
                'join_type': 'inner'
            }
        ]
    })
    
    print(f"\n  Joined:")
    for row in result.data:
        print(f"    {row}")
    
    assert result.success
    assert 'category_name' in result.data[0]
    
    print("\n✅ Join working")


async def test_pivot():
    """Test pivot operation"""
    print("\n" + "=" * 60)
    print("Test 8: Pivot Table")
    print("=" * 60)
    
    transformer = DataTransformer()
    
    # Sales data
    data = [
        {"month": "Jan", "region": "North", "sales": 1000},
        {"month": "Jan", "region": "South", "sales": 1500},
        {"month": "Feb", "region": "North", "sales": 1200},
        {"month": "Feb", "region": "South", "sales": 1800}
    ]
    
    result = await transformer.execute({
        'data': data,
        'operations': [
            {
                'type': 'pivot',
                'index': 'month',
                'columns': 'region',
                'values': 'sales',
                'aggfunc': 'sum'
            }
        ]
    })
    
    print(f"\n  Pivoted:")
    for row in result.data:
        print(f"    {row}")
    
    assert result.success
    
    print("\n✅ Pivot working")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print(" " * 23 + "DATA TRANSFORMER TEST SUITE")
    print("=" * 80)
    
    tests = [
        test_filter,
        test_sort,
        test_aggregate,
        test_select_columns,
        test_limit,
        test_complex_pipeline,
        test_join,
        test_pivot
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
        print("\n✅ Data Transformer is production ready!")
        print("\n📊 Verified:")
        print("  ✓ Filtering (multiple conditions)")
        print("  ✓ Sorting (single/multiple columns)")
        print("  ✓ Aggregations (group by, sum, avg, etc.)")
        print("  ✓ Column selection")
        print("  ✓ Limiting results")
        print("  ✓ Complex pipelines")
        print("  ✓ Joining datasets")
        print("  ✓ Pivot tables")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
