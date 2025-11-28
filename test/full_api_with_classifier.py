"""
Test full API with task fetcher and classifier
"""

import requests
import json

print("=" * 60)
print("Testing Full API with Classifier")
print("=" * 60)

# Test with a task that needs classification
test_request = {
    "email": "test@example.com",
    "secret": "secret",  # Use your actual secret from .env
    "url": "https://jsonplaceholder.typicode.com/posts/1"
}

print("\nSending request...")
print(f"API URL: http://localhost:8000/api/")
print(f"Task URL: {test_request['url']}")

response = requests.post(
    "http://localhost:8000/api/",
    json=test_request,
    headers={"Content-Type": "application/json"}
)

print(f"\n✅ Response Status: {response.status_code}")
print("\nResponse Body:")
result = response.json()
print(json.dumps(result, indent=2))

if response.status_code == 200:
    print("\n" + "=" * 60)
    print("Classification Results:")
    print("=" * 60)
    
    classification = result.get('classification', {})
    print(f"Primary Task: {classification.get('primary_task')}")
    print(f"Complexity: {classification.get('complexity')}")
    print(f"Estimated Steps: {classification.get('estimated_steps')}")
    print(f"Output Format: {classification.get('output_format')}")
    print(f"Confidence: {classification.get('confidence')}")
    print(f"\nReasoning: {classification.get('reasoning')}")
    
    if classification.get('suggested_tools'):
        print(f"\nSuggested Tools: {', '.join(classification['suggested_tools'])}")
    
    print("\n🎉 Success! Task classifier is working!")
else:
    print("\n❌ Error occurred")
