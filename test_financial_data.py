import requests
import json

def test_financial_data():
    """Test å hente finansdata fra Brønnøysundregisteret"""
    
    # Test med en kjent bedrift (f.eks. Equinor)
    test_org_numbers = [
        "940451084",  # Equinor
        "995849364",  # :-) INVEST AS (fra tidligere test)
        "123456789"   # Test nummer
    ]
    
    for org_num in test_org_numbers:
        print(f"\n🔍 Tester organisasjonsnummer: {org_num}")
        
        try:
            # Hent detaljert bedriftsinformasjon
            url = f"https://data.brreg.no/enhetsregisteret/api/enheter/{org_num}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Bedrift funnet: {data.get('navn', 'Ukjent navn')}")
                
                # Sjekk hvilke finansfelter som finnes
                print("📊 Tilgjengelige felter:")
                
                # Grunnleggende info
                basic_fields = ['organisasjonsnummer', 'navn', 'organisasjonsform', 'registreringsdatoEnhetsregisteret']
                for field in basic_fields:
                    if field in data:
                        print(f"   - {field}: {data[field]}")
                
                # Finansdata
                financial_fields = [
                    'antallAnsatte', 'registreringsdatoEnhetsregisteret', 'konkurs', 'underAvvikling',
                    'underTvangsavviklingEllerTvangsopplosning', 'maaMeldasFraRegnskapsregisteret',
                    'maaMeldasFraEnhetsregisteret', 'maaMeldasFraAnsattregisteret'
                ]
                
                print("\n💰 Finansrelaterte felter:")
                for field in financial_fields:
                    if field in data:
                        print(f"   - {field}: {data[field]}")
                
                # Sjekk om det finnes regnskapsdata
                if 'regnskapsregisteret' in data:
                    print("\n📈 Regnskapsdata tilgjengelig!")
                    regnskap = data['regnskapsregisteret']
                    print(f"   - Regnskapsår: {regnskap.get('regnskapsaar', 'Ukjent')}")
                    print(f"   - Siste regnskap: {regnskap.get('sisteRegnskapsaar', 'Ukjent')}")
                
                # Sjekk ansattregisteret
                if 'ansattregisteret' in data:
                    print("\n👥 Ansattdata tilgjengelig!")
                    ansatte = data['ansattregisteret']
                    print(f"   - Antall ansatte: {ansatte.get('antallAnsatte', 'Ukjent')}")
                    print(f"   - Siste oppdatering: {ansatte.get('sisteAarsmodning', 'Ukjent')}")
                
            else:
                print(f"❌ Feil: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"💥 Feil: {e}")

if __name__ == "__main__":
    test_financial_data()
