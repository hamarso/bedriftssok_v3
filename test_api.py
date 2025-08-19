#!/usr/bin/env python3
"""
Test av Brønnøysundregisteret API direkte
"""

import requests
import json

def test_brreg_api():
    """Test API-et direkte"""
    url = "https://data.brreg.no/enhetsregisteret/api/enheter"
    
    print("🧪 Tester Brønnøysundregisteret API direkte...")
    
    # Test 1: Søk med NACE-kode 70.220
    params1 = {
        'naeringskode': '70.220',
        'size': 10
    }
    
    print(f"\n🔍 Test 1: Søk med NACE-kode 70.220")
    print(f"   Parametere: {params1}")
    
    try:
        response = requests.get(url, params=params1, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            
            if '_embedded' in data and 'enheter' in data['_embedded']:
                selskaper = data['_embedded']['enheter']
                print(f"   ✅ Fant {len(selskaper)} bedrifter")
                
                if selskaper:
                    første = selskaper[0]
                    print(f"   📋 Første bedrift:")
                    print(f"      - Navn: {første.get('navn', 'N/A')}")
                    print(f"      - NACE: {første.get('naeringskode1', {}).get('kode', 'N/A')}")
                    print(f"      - Ansatte: {første.get('antallAnsatte', 'N/A')}")
            else:
                print(f"   ⚠️ Ingen '_embedded' eller 'enheter' i response")
                print(f"   📋 Response struktur: {data}")
        else:
            print(f"   ❌ Feil: {response.status_code}")
            print(f"   📋 Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   💥 Feil: {e}")
    
    # Test 2: Søk med antall ansatte
    params2 = {
        'naeringskode': '70.220',
        'fraAntallAnsatte': 100,
        'size': 10
    }
    
    print(f"\n🔍 Test 2: Søk med NACE-kode 70.220 og min 100 ansatte")
    print(f"   Parametere: {params2}")
    
    try:
        response = requests.get(url, params=params2, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if '_embedded' in data and 'enheter' in data['_embedded']:
                selskaper = data['_embedded']['enheter']
                print(f"   ✅ Fant {len(selskaper)} bedrifter med min 100 ansatte")
            else:
                print(f"   ⚠️ Ingen resultater med antall ansatte filter")
        else:
            print(f"   ❌ Feil: {response.status_code}")
            
    except Exception as e:
        print(f"   💥 Feil: {e}")
    
    # Test 3: Søk uten antall ansatte filter
    params3 = {
        'naeringskode': '70.220',
        'size': 10
    }
    
    print(f"\n🔍 Test 3: Søk med NACE-kode 70.220 uten antall ansatte filter")
    print(f"   Parametere: {params3}")
    
    try:
        response = requests.get(url, params=params3, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if '_embedded' in data and 'enheter' in data['_embedded']:
                selskaper = data['_embedded']['enheter']
                print(f"   ✅ Fant {len(selskaper)} bedrifter uten ansatte filter")
            else:
                print(f"   ⚠️ Ingen resultater")
        else:
            print(f"   ❌ Feil: {response.status_code}")
            
    except Exception as e:
        print(f"   💥 Feil: {e}")

if __name__ == "__main__":
    test_brreg_api()
