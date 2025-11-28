"""
Test Parameter Extractor
Comprehensive tests for parameter extraction
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

import asyncio
from app.orchestrator.parameter_extractor import ParameterExtractor
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_simple_scraping_task():
    """Test parameter extraction from simple web scraping task"""
    
    print("\n" + "=" * 60)
    print("Test 1: Simple Web Scraping Task")
    print("=" * 60)
    
    task = """
    Scrape the top 10 product names and prices from https://example.com/products
    and save the results as a CSV file.
    """
    
    print(f"\nTask: {task.strip()}")
    print("-" * 60)
    
    extractor = ParameterExtractor()
    
    try:
        result = await extractor.extract_parameters(task)
        
        print(f"\n✓ Extraction: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"✓ Method: {result.extraction_method}")
        print(f"✓ Confidence: {result.parameters.confidence:.2f}")
        
        params = result.parameters
        
        print(f"\n📊 Extracted Parameters:")
        print(f"  Data Sources: {len(params.data_sources)}")
        print(f"  URLs: {len(params.urls)}")
        print(f"  Filters: {len(params.filters)}")
        print(f"  Numerical Constraints: {len(params.numerical_constraints)}")
        print(f"  Columns: {len(params.columns)}")
        
        if params.data_sources:
            print(f"\n🌐 Data Sources:")
            for ds in params.data_sources:
                print(f"  - {ds.type}: {ds.location}")
                print(f"    Description: {ds.description}")
        
        if params.urls:
            print(f"\n🔗 URLs:")
            for url in params.urls:
                print(f"  - {url.url}")
                print(f"    Purpose: {url.purpose}")
        
        if params.numerical_constraints:
            print(f"\n🔢 Numerical Constraints:")
            for nc in params.numerical_constraints:
                print(f"  - {nc.type}: {nc.value}")
                print(f"    {nc.description}")
        
        if params.output:
            print(f"\n📄 Output:")
            print(f"  Format: {params.output.format}")
            print(f"  Description: {params.output.description}")
        
        print(f"\n⏱️  Estimated Time: {params.estimated_execution_time}s")
        print(f"🎯 Complexity: {params.complexity_score:.2f}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error("Test failed", exc_info=True)


async def test_complex_analysis_task():
    """Test parameter extraction from complex data analysis task"""
    
    print("\n" + "=" * 60)
    print("Test 2: Complex Data Analysis Task")
    print("=" * 60)
    
    task = """
    Download the sales data from https://example.com/data/sales.csv
    Filter for records where region is 'North' and sales_amount > 1000
    Group by product_category and calculate the average price
    Create a bar chart showing top 5 categories by average price
    Sort results in descending order
    Export as Excel file
    """
    
    print(f"\nTask: {task.strip()}")
    print("-" * 60)
    
    extractor = ParameterExtractor()
    
    try:
        result = await extractor.extract_parameters(task)
        
        print(f"\n✓ Success: {result.success}")
        print(f"✓ Confidence: {result.parameters.confidence:.2f}")
        
        params = result.parameters
        
        if params.filters:
            print(f"\n🔍 Filters ({len(params.filters)}):")
            for f in params.filters:
                print(f"  - {f.field} {f.operator} {f.value}")
                print(f"    {f.description}")
        
        if params.aggregations:
            print(f"\n📊 Aggregations ({len(params.aggregations)}):")
            for agg in params.aggregations:
                print(f"  - {agg.function}({agg.field})")
                if agg.group_by:
                    print(f"    Group by: {', '.join(agg.group_by)}")
                print(f"    {agg.description}")
        
        if params.sorting:
            print(f"\n↕️  Sorting ({len(params.sorting)}):")
            for sort in params.sorting:
                print(f"  - {sort.field} ({sort.order})")
        
        if params.visualizations:
            print(f"\n📈 Visualizations ({len(params.visualizations)}):")
            for viz in params.visualizations:
                print(f"  - {viz.type}")
                if viz.chart_type:
                    print(f"    Chart: {viz.chart_type}")
                print(f"    {viz.description}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error("Test failed", exc_info=True)


async def test_geographic_task():
    """Test parameter extraction with geographic filters"""
    
    print("\n" + "=" * 60)
    print("Test 3: Geographic Filtering Task")
    print("=" * 60)
    
    task = """
    Analyze weather data for cities in California from the last 7 days.
    Show average temperature by city on a map.
    """
    
    print(f"\nTask: {task.strip()}")
    print("-" * 60)
    
    extractor = ParameterExtractor()
    
    try:
        result = await extractor.extract_parameters(task)
        
        params = result.parameters
        
        if params.geographic_filters:
            print(f"\n🌍 Geographic Filters ({len(params.geographic_filters)}):")
            for gf in params.geographic_filters:
                print(f"  - {gf.type}: {gf.value}")
                print(f"    Field: {gf.field}")
                print(f"    {gf.description}")
        
        if params.time_ranges:
            print(f"\n📅 Time Ranges ({len(params.time_ranges)}):")
            for tr in params.time_ranges:
                print(f"  - Field: {tr.field}")
                if tr.relative:
                    print(f"    Relative: {tr.relative}")
                print(f"    {tr.description}")
        
        if params.visualizations:
            print(f"\n🗺️  Map Visualizations:")
            for viz in params.visualizations:
                if viz.type == 'map':
                    print(f"  - {viz.description}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def test_api_task():
    """Test parameter extraction with API requirements"""
    
    print("\n" + "=" * 60)
    print("Test 4: API Data Fetching Task")
    print("=" * 60)
    
    task = """
    Fetch user data from the API at https://api.example.com/users?page=1&limit=50
    Filter users where age > 25 and country = 'USA'
    Extract only the name, email, and join_date fields
    Save as JSON
    """
    
    print(f"\nTask: {task.strip()}")
    print("-" * 60)
    
    extractor = ParameterExtractor()
    
    try:
        result = await extractor.extract_parameters(task)
        
        params = result.parameters
        
        if params.data_sources:
            print(f"\n🔌 API Data Sources:")
            for ds in params.data_sources:
                if ds.type == 'api' or 'api' in ds.location.lower():
                    print(f"  - {ds.location}")
                    print(f"    Format: {ds.format}")
        
        if params.columns:
            print(f"\n📋 Column Selection ({len(params.columns)}):")
            for col in params.columns:
                print(f"  - {col.name}")
                print(f"    {col.description}")
        
        if params.requires_api_keys:
            print(f"\n🔑 Required API Keys:")
            for key in params.requires_api_keys:
                print(f"  - {key}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def test_time_series_task():
    """Test parameter extraction with time series"""
    
    print("\n" + "=" * 60)
    print("Test 5: Time Series Analysis Task")
    print("=" * 60)
    
    task = """
    Analyze stock prices for AAPL between 2023-01-01 and 2023-12-31
    Calculate daily returns and plot a line chart
    Show the top 10 days with highest returns
    """
    
    print(f"\nTask: {task.strip()}")
    print("-" * 60)
    
    extractor = ParameterExtractor()
    
    try:
        result = await extractor.extract_parameters(task)
        
        params = result.parameters
        
        if params.time_ranges:
            print(f"\n📅 Time Ranges:")
            for tr in params.time_ranges:
                if tr.start or tr.end:
                    print(f"  - Start: {tr.start or 'N/A'}")
                    print(f"    End: {tr.end or 'N/A'}")
                print(f"    {tr.description}")
        
        if params.aggregations:
            print(f"\n🧮 Calculations:")
            for agg in params.aggregations:
                print(f"  - {agg.description}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def run_all_tests():
    """Run all parameter extraction tests"""
    
    print("\n" + "=" * 80)
    print(" " * 20 + "PARAMETER EXTRACTOR TEST SUITE")
    print("=" * 80)
    
    try:
        await test_simple_scraping_task()
        await test_complex_analysis_task()
        await test_geographic_task()
        await test_api_task()
        await test_time_series_task()
        
        print("\n" + "=" * 80)
        print(" " * 30 + "ALL TESTS COMPLETE")
        print("=" * 80)
        print("\n✅ Parameter extraction tests finished!")
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        logger.error("Test suite failed", exc_info=True)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
