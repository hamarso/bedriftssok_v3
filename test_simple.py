import requests
import json

def test_search_api():
    """Test søke-API-et"""
    url = "http://localhost:5000/api/sok"
    
    data = {
        "bransjekode": "70.220",
        "min_ansatte": 0,
        "page": 0
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Antall bedrifter: {result.get('antall')}")
            if result.get('selskaper'):
                print(f"Første bedrift: {result['selskaper'][0]}")
        else:
            print(f"Feil: {response.text}")
            
    except Exception as e:
        print(f"Feil: {e}")

if __name__ == "__main__":
    test_search_api()
