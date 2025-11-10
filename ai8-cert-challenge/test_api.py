"""
Simple test script to verify the FastAPI backend is working
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_health():
    """Test basic health check"""
    print("Testing health endpoint...")
    response = requests.get(f"{API_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200

def test_api_health():
    """Test API health endpoint"""
    print("Testing API health endpoint...")
    try:
        response = requests.get(f"{API_URL}/api/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}\n")
        return False

def test_chat(openai_key: str):
    """Test chat endpoint"""
    print("Testing chat endpoint...")
    
    payload = {
        "message": "What events are happening this week?",
        "openai_api_key": openai_key,
        "cohere_api_key": "",
        "use_reranking": False
    }
    
    try:
        response = requests.post(f"{API_URL}/api/chat", json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if result.get("error"):
            print(f"Error: {result['error']}\n")
            return False
        else:
            print(f"Response: {result['response'][:200]}...\n")
            return True
    except Exception as e:
        print(f"Error: {e}\n")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Scout API Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Basic health
    if not test_health():
        print("❌ Basic health check failed. Is the server running?")
        exit(1)
    print("✅ Basic health check passed")
    
    # Test 2: API health
    test_api_health()
    print("ℹ️  API health check completed (may show errors if data not prepared)")
    
    # Test 3: Chat (requires API key)
    openai_key = input("\nEnter your OpenAI API key to test chat (or press Enter to skip): ").strip()
    
    if openai_key:
        if test_chat(openai_key):
            print("✅ Chat endpoint test passed")
        else:
            print("❌ Chat endpoint test failed")
    else:
        print("⏭️  Skipping chat test (no API key provided)")
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)

