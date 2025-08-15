"""
Vienkārša upload test
"""
import requests

def test_simple_upload():
    """Vienkārša upload test"""
    
    # API base URL
    API_BASE = "http://localhost:8000"
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"✅ Serveris darbojas: {response.json()}")
    except Exception as e:
        print(f"❌ Serveris nav pieejams: {e}")
        return
    
    # Test simple endpoint first
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✅ Health check: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test upload with minimal payload
    print("\n📤 Testējam upload...")
    
    # Create a minimal test file in memory
    test_content = b"Test content"
    files = {'file': ('test.pdf', test_content, 'application/pdf')}
    
    try:
        response = requests.post(f"{API_BASE}/api/v1/upload", files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_simple_upload()
