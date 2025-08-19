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
    
    # Test 2: Søk API
    try:
        test_data = {
            "bransjekode": "70.220",
            "min_ansatte": 100
        }
        
        response = requests.post(
            f"{base_url}/api/sok",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Søk API fungerer - Fant {data.get('antall', 0)} bedrifter")
            else:
                print(f"❌ Søk API returnerte feil: {data.get('error')}")
        else:
            print(f"❌ Søk API feilet: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Kunne ikke teste søk API: {e}")
    
    print("\n🎉 Test fullført!")
    print("📱 Åpne http://localhost:5000 i nettleseren for å bruke appen")

if __name__ == "__main__":
    test_api()
