import requests
import json

# Test data
test_data = {
    "selskaper": [
        {
            "organisasjonsnummer": "123456789",
            "navn": "Test Bedrift AS",
            "poststed": "Oslo",
            "antall_ansatte": "10",
            "nace_kode": "70.220",
            "adresse": "Testveien 1"
        },
        {
            "organisasjonsnummer": "987654321",
            "navn": "Test Bedrift 2 AS",
            "poststed": "Bergen",
            "antall_ansatte": "25",
            "nace_kode": "70.220",
            "adresse": "Testveien 2"
        }
    ]
}

# Test eksport API
url = "http://localhost:5000/api/eksporter"
headers = {"Content-Type": "application/json"}

try:
    print("🔍 Tester eksport API...")
    print(f"📤 Sender data: {json.dumps(test_data, indent=2)}")
    
    response = requests.post(url, json=test_data, headers=headers)
    
    print(f"📡 Response status: {response.status_code}")
    print(f"📡 Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("✅ Eksport vellykket!")
        print(f"📄 Fil størrelse: {len(response.content)} bytes")
        
        # Lagre filen lokalt for testing
        with open("test_export.xlsx", "wb") as f:
            f.write(response.content)
        print("💾 Fil lagret som 'test_export.xlsx'")
        
    else:
        print(f"❌ Eksport feilet: {response.status_code}")
        print(f"📋 Response tekst: {response.text}")
        
except Exception as e:
    print(f"💥 Feil: {str(e)}")
