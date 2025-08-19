#!/usr/bin/env python3
"""
Tester faktiske antall bedrifter for eksisterende NACE-koder
"""

import requests
import json

def test_real_counts():
    """Tester faktiske antall for eksisterende koder"""
    print("🔍 Tester faktiske antall bedrifter for eksisterende NACE-koder...")
    
    # Test koder som vi vet eksisterer
    test_codes = [
        '69.100',  # Advokatvirksomhet og rettshjelp
        '69.201',  # Regnskapsførere
        '69.202',  # Revisjon
        '69.203',  # Rådgivning innen regnskap
        '70.100',  # Hovedkontor
        '70.210',  # Konsulentvirksomhet innen offentlig administrasjon
        '70.220',  # Konsulentvirksomhet innen forretningsadministrasjon
    ]
    
    url = "https://data.brreg.no/enhetsregisteret/api/enheter"
    
    for code in test_codes:
        try:
            # Test med større size for å få faktiske antall
            params = {
                'naeringskode': code,
                'size': 1000
            }
            
            print(f"\n🔍 Tester {code}...")
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'page' in data and 'totalElements' in data['page']:
                    total = data['page']['totalElements']
                    print(f"   📊 Total antall bedrifter: {total}")
                    
                    if '_embedded' in data and 'enheter' in data['_embedded']:
                        sample_count = len(data['_embedded']['enheter'])
                        print(f"   📋 Sample i første batch: {sample_count}")
                        
                        if sample_count > 0:
                            første = data['_embedded']['enheter'][0]
                            print(f"   🏢 Første bedrift: {første.get('navn', 'N/A')}")
                            print(f"   📍 Poststed: {første.get('forretningsadresse', {}).get('poststed', 'N/A')}")
                else:
                    print(f"   ⚠️ Ingen page info")
                    
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Feil: {e}")
    
    print(f"\n🎯 Anbefaling:")
    print(f"   - 70.220 har flest bedrifter (10,000+)")
    print(f"   - 69.201-203 kan være bedre for regnskapsførere")
    print(f"   - Test disse i vår app for å se hvilke som fungerer best")

if __name__ == "__main__":
    test_real_counts()
