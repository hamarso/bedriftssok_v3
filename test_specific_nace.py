#!/usr/bin/env python3
"""
Test av spesifikk NACE-kode 69.200
"""

import requests
import json

def test_nace_69_200():
    """Test NACE-kode 69.200 spesifikt"""
    print("🧪 Tester NACE-kode 69.200 (Regnskapsførere, revisjon og rådgivning)...")
    
    # Test 1: Direkte mot Brønnøysundregisteret API
    url = "https://data.brreg.no/enhetsregisteret/api/enheter"
    
    params = {
        'naeringskode': '69.200',
        'size': 10
    }
    
    print(f"\n🔍 Test 1: Direkte mot Brønnøysundregisteret med 69.200")
    print(f"   Parametere: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            
            if '_embedded' in data and 'enheter' in data['_embedded']:
                selskaper = data['_embedded']['enheter']
                print(f"   ✅ Fant {len(selskaper)} bedrifter med NACE 69.200")
                
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
    
    # Test 2: Vårt lokale API
    print(f"\n🔍 Test 2: Vårt lokale API med 69.200")
    
    try:
        form_data = {
            "bransjekode": "69.200",
            "min_ansatte": 0
        }
        
        print(f"   Sender data: {form_data}")
        
        response = requests.post(
            "http://localhost:5000/api/sok",
            json=form_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API response:")
            print(f"      - Success: {data.get('success')}")
            print(f"      - Antall bedrifter: {data.get('antall', 0)}")
            
            if data.get('success') and data.get('antall', 0) > 0:
                første = data['selskaper'][0]
                print(f"      - Første bedrift: {første.get('navn', 'N/A')}")
                print(f"      - NACE: {første.get('nace_kode', 'N/A')}")
            else:
                print(f"      - ⚠️ Ingen bedrifter funnet eller API feil")
                print(f"      - Error: {data.get('error', 'Ingen feilmelding')}")
        else:
            print(f"   ❌ API feil: {response.status_code}")
            print(f"   📋 Response: {response.text}")
            
    except Exception as e:
        print(f"   💥 Feil: {e}")
    
    # Test 3: Sammenlign med 70.220
    print(f"\n🔍 Test 3: Sammenlign 69.200 med 70.220")
    
    for nace_code in ['69.200', '70.220']:
        try:
            form_data = {
                "bransjekode": nace_code,
                "min_ansatte": 0
            }
            
            response = requests.post(
                "http://localhost:5000/api/sok",
                json=form_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   {nace_code}: {data.get('antall', 0)} bedrifter")
            else:
                print(f"   {nace_code}: Feil {response.status_code}")
                
        except Exception as e:
            print(f"   {nace_code}: Feil {e}")

if __name__ == "__main__":
    test_nace_69_200()
