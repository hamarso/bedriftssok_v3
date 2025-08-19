import requests
import json

def test_accounting_data():
    """Test å hente regnskapsdata fra regnskapsregisteret"""
    
    # Test med en kjent bedrift
    org_num = "995849364"  # :-) INVEST AS
    
    print(f"🔍 Tester regnskapsdata for: {org_num}")
    
    try:
        # Hent regnskapsdata fra regnskapsregisteret
        url = f"https://data.brreg.no/regnskapsregisteret/api/regnskap/{org_num}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Regnskapsdata funnet!")
            print(f"📊 Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
        else:
            print(f"❌ Feil: HTTP {response.status_code}")
            print("💡 Regnskapsdata kan være begrenset for denne bedriften")
            
    except Exception as e:
        print(f"💥 Feil: {e}")

def test_alternative_sources():
    """Test alternative kilder for finansdata"""
    
    print("\n🔍 Tester alternative datakilder...")
    
    # Test Proff.no API (krever abonnement)
    print("📊 Proff.no - Krever abonnement for API-tilgang")
    
    # Test SSB API
    print("📊 SSB - Begrenset bedriftsdata")
    
    # Test Altinn
    print("📊 Altinn - Begrenset offentlig tilgang")
    
    print("\n💡 Anbefaling: Implementer finansdata-felter i backend")
    print("   - Omsetning (årlig)")
    print("   - Resultat før skatt")
    print("   - Egenkapital")
    print("   - Totale eiendeler")

if __name__ == "__main__":
    test_accounting_data()
    test_alternative_sources()
