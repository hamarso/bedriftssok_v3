#!/usr/bin/env python3
"""
Enkel test av app-funksjonaliteten
"""

import requests
import json

def test_api():
    """Test API-endepunktene"""
    base_url = "http://localhost:5000"
    
    print("🧪 Tester Bedriftssøk API...")
    
    # Test 1: Hovedside
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Hovedside fungerer")
        else:
            print(f"❌ Hovedside feilet: {response.status_code}")
    except Exception as e:
        print(f"❌ Kunne ikke nå hovedsiden: {e}")
        return
    
    # Test 2: Søk API med NACE-kode 70.220 og 0 ansatte
    try:
        test_data = {
            "bransjekode": "70.220",
            "min_ansatte": 0
        }
        
        print(f"\n🔍 Tester søk med: {test_data}")
        
        response = requests.post(
            f"{base_url}/api/sok",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("success"):
                print(f"✅ Søk API fungerer - Fant {data.get('antall', 0)} bedrifter")
                
                if data.get('antall', 0) > 0:
                    første = data['selskaper'][0]
                    print(f"📋 Første bedrift:")
                    print(f"   - Navn: {første.get('navn', 'N/A')}")
                    print(f"   - NACE: {første.get('nace_kode', 'N/A')}")
                    print(f"   - Ansatte: {første.get('antall_ansatte', 'N/A')}")
                else:
                    print("⚠️ Ingen bedrifter funnet - dette kan være problemet!")
            else:
                print(f"❌ Søk API returnerte feil: {data.get('error')}")
        else:
            print(f"❌ Søk API feilet: {response.status_code}")
            print(f"📋 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Kunne ikke teste søk API: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Test fullført!")
    print("📱 Åpne http://localhost:5000 i nettleseren for å bruke appen")

if __name__ == "__main__":
    test_api()
