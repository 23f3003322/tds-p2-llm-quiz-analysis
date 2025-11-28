"""
Test Task Classifier
"""

import asyncio
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.orchestrator.classifier import TaskClassifier, classify_task_quick
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_simple_classification():
    """Test simple task classification"""
    print("\n" + "=" * 60)
    print("Test 1: Simple Task Classification")
    print("=" * 60)
    
    task = "Scrape the top 10 headlines from HackerNews"
    
    classification = await classify_task_quick(task)
    
    print(f"\nTask: {task}")
    print(f"\nPrimary Task: {classification.primary_task.value}")
    print(f"Secondary Tasks: {[t.value for t in classification.secondary_tasks]}")
    print(f"Complexity: {classification.complexity.value}")
    print(f"Estimated Steps: {classification.estimated_steps}")
    print(f"Output Format: {classification.output_format.value}")
    print(f"Confidence: {classification.confidence:.2f}")
    print(f"\nReasoning: {classification.reasoning}")
    
    if classification.suggested_tools:
        print(f"Suggested Tools: {', '.join(classification.suggested_tools)}")


async def test_complex_classification():
    """Test complex multi-step task"""
    print("\n" + "=" * 60)
    print("Test 2: Complex Multi-Step Task")
    print("=" * 60)
    
    task = """Download the CSV from https://example.com/data.csv, 
    clean the data by removing duplicates and null values, 
    perform correlation analysis on numeric columns, 
    and create a heatmap visualization"""
    
    classification = await classify_task_quick(task)
    
    print(f"\nTask: {task}")
    print(f"\nPrimary Task: {classification.primary_task.value}")
    print(f"Secondary Tasks: {[t.value for t in classification.secondary_tasks]}")
    print(f"Complexity: {classification.complexity.value}")
    print(f"Estimated Steps: {classification.estimated_steps}")
    print(f"Key Entities: {classification.key_entities}")
    print(f"\nReasoning: {classification.reasoning}")


async def test_full_pipeline():
    """Test full pipeline with task fetcher"""
    print("\n" + "=" * 60)
    print("Test 3: Full Pipeline (Fetch + Classify)")
    print("=" * 60)
    
    from app.services.task_fetcher import TaskFetcher
    
    # Test with a JSON API
    url = "https://jsonplaceholder.typicode.com/posts/1"
    
    print(f"\nFetching from: {url}")
    
    async with TaskFetcher() as fetcher:
        task_info = await fetcher.fetch_task(url)
    
    print(f"Fetched content type: {task_info['content_type']}")
    print(f"Needs LLM analysis: {task_info.get('needs_llm_analysis', False)}")
    
    # Classify
    classifier = TaskClassifier()
    content_analysis, classification = await classifier.classify_with_content_check(task_info)
    
    if content_analysis:
        print(f"\nContent is direct task: {content_analysis.is_direct_task}")
    print(f"Primary Task: {classification.primary_task.value}")
    print(f"Complexity: {classification.complexity.value}")
    print(f"Confidence: {classification.confidence:.2f}")


async def main():
    """Run all tests"""
    try:
        await test_simple_classification()
        await test_complex_classification()
        await test_full_pipeline()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
    
    finally:
        # Close LLM client
        from app.utils.llm_client import close_llm_client
        await close_llm_client()


if __name__ == "__main__":
    asyncio.run(main())
