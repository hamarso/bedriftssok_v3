#!/usr/bin/env python3
"""
Finner faktiske NACE-koder som eksisterer i Brønnøysundregisteret
"""

import requests
import json

def find_existing_nace_codes():
    """Finner NACE-koder som faktisk eksisterer"""
    print("🔍 Finner faktiske NACE-koder i Brønnøysundregisteret...")
    
    # Test forskjellige NACE-koder som kan være relatert til regnskap
    test_codes = [
        '69.100',  # Advokatvirksomhet og rettshjelp
        '69.200',  # Regnskapsførere, revisjon og rådgivning (vi vet denne ikke fungerer)
        '69.201',  # Regnskapsførere
        '69.202',  # Revisjon
        '69.203',  # Rådgivning innen regnskap
        '70.100',  # Hovedkontor
        '70.200',  # Konsulentvirksomhet
        '70.210',  # Konsulentvirksomhet innen offentlig administrasjon
        '70.220',  # Konsulentvirksomhet innen forretningsadministrasjon
        '70.221',  # Konsulentvirksomhet innen ledelse
        '70.222',  # Konsulentvirksomhet innen økonomi
        '70.223',  # Konsulentvirksomhet innen markedsføring
        '70.224',  # Konsulentvirksomhet innen HR
        '70.225',  # Konsulentvirksomhet innen IT
        '70.226',  # Konsulentvirksomhet innen andre forretningsområder
        '70.300',  # Annet hovedkontor
        '70.400',  # Annet hovedkontor
        '70.500',  # Annet hovedkontor
        '70.600',  # Annet hovedkontor
        '70.700',  # Annet hovedkontor
        '70.800',  # Annet hovedkontor
        '70.900',  # Annet hovedkontor
    ]
    
    url = "https://data.brreg.no/enhetsregisteret/api/enheter"
    
    existing_codes = []
    
    for code in test_codes:
        try:
            params = {
                'naeringskode': code,
                'size': 1  # Bare sjekk om det finnes noen
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if '_embedded' in data and 'enheter' in data['_embedded']:
                    count = len(data['_embedded']['enheter'])
                    if count > 0:
                        existing_codes.append((code, count))
                        print(f"   ✅ {code}: {count} bedrifter")
                    else:
                        print(f"   ⚠️ {code}: 0 bedrifter")
                else:
                    # Sjekk totalElements hvis det finnes
                    if 'page' in data and 'totalElements' in data['page']:
                        total = data['page']['totalElements']
                        if total > 0:
                            existing_codes.append((code, total))
                            print(f"   ✅ {code}: {total} bedrifter (fra totalElements)")
                        else:
                            print(f"   ❌ {code}: 0 bedrifter (fra totalElements)")
                    else:
                        print(f"   ❌ {code}: Ingen data")
            else:
                print(f"   ❌ {code}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   💥 {code}: Feil {e}")
    
    print(f"\n📊 Sammendrag:")
    print(f"   Totalt testet: {len(test_codes)} koder")
    print(f"   Eksisterende: {len(existing_codes)} koder")
    
    if existing_codes:
        print(f"\n🎯 Anbefalte NACE-koder for regnskapsrelaterte tjenester:")
        for code, count in sorted(existing_codes, key=lambda x: x[1], reverse=True):
            print(f"   - {code}: {count} bedrifter")
    
    return existing_codes

if __name__ == "__main__":
    find_existing_nace_codes()
