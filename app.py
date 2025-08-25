from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import requests
from openpyxl import Workbook
import io
import re

app = Flask(__name__)
CORS(app)

def parse_postnumre(postnumre_string):
    """Parser postnumre fra string til liste med individuelle postnumre"""
    if not postnumre_string or postnumre_string.strip() == '':
        return []
    
    postnumre = []
    # Del opp på komma
    for part in postnumre_string.split(','):
        part = part.strip()
        if '-' in part:
            # Håndter serier som "0001-0010"
            try:
                start, end = part.split('-')
                start_num = int(start.strip())
                end_num = int(end.strip())
                if start_num <= end_num:
                    for num in range(start_num, end_num + 1):
                        postnumre.append(f"{num:04d}")
            except ValueError:
                # Hvis parsing feiler, legg til som vanlig
                postnumre.append(part)
        else:
            # Enkelt postnummer
            postnumre.append(part)
    
    return postnumre

def hente_selskaper_med_kriterier(bransjekode, min_ansatte, max_ansatte, bedriftsnavn=None, poststed=None, organisasjonsform=None, registreringsdato=None, etablert_etter=None, momsregistrert=None, postnumre=None):
    """Henter selskaper basert på søkekriterier"""
    url = "https://data.brreg.no/enhetsregisteret/api/enheter"
    selskaper = []
    
    # Bygg API-parametere
    params = {
        'size': 1000
    }
    
    # Hvis vi har postnumre men ingen NACE-kode, bruk en generell søk for alle bransjer
    # Brønnøysundregisteret API krever minst én parameter, så vi bruker en som ikke begrenser bransjen
    if postnumre and (not bransjekode or not bransjekode.strip()):
        print("🔍 Ingen NACE-kode spesifisert, men postnumre gitt. Henter data fra alle bransjer.")
        
        # Bruk en generell parameter som ikke begrenser bransjen
        # Vi kan bruke 'size' for å få maksimalt antall resultater per side
        # Dette gir oss alle tilgjengelige selskaper uten å begrense på bransje
        # Merk: Brønnøysundregisteret API krever minst én parameter, så vi bruker size=1000
        params['size'] = 1000
        
        # Prøv å hente data uten begrensninger på bransje
        # Hvis dette ikke fungerer, bruk fallback med vanlige NACE-koder
        try:
            # Hent data uten begrensninger på bransje
            # Vi prøver først uten ekstra parametere, bare med size
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if '_embedded' in data and 'enheter' in data['_embedded']:
                    selskaper.extend(data['_embedded']['enheter'])
                    print(f"✅ Fant {len(data['_embedded']['enheter'])} bedrifter i første batch")
                    
                    # Håndter paginering for å få alle resultater
                    page = 0
                    while 'next' in data.get('_links', {}):
                        page += 1
                        params['page'] = page
                        
                        print(f"📄 Henter side {page + 1}...")
                        response = requests.get(url, params=params, timeout=30)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if '_embedded' in data and 'enheter' in data['_embedded']:
                                selskaper.extend(data['_embedded']['enheter'])
                                print(f"✅ Fant {len(data['_embedded']['enheter'])} bedrifter på side {page + 1}")
                            else:
                                break
                        else:
                            print(f"❌ Feil på side {page + 1}: {response.status_code}")
                            break
                else:
                    print(f"⚠️ Ingen '_embedded' eller 'enheter' i API response")
            else:
                print(f'❌ API feil: {response.status_code}')
                
        except Exception as e:
            print(f'💥 Feil under henting av data: {str(e)}')
            
                    # Hvis den generelle søket feiler, prøv med en bredere tilnærming
        print("🔄 Prøver bredere tilnærming for å få alle bedrifter...")
        
        # Bruk en parameter som gir oss alle selskaper
        # Prøv med 'registrertIMvaregisteret' som kan gi oss alle MVA-registrerte selskaper
        try:
            temp_params = {'registrertIMvaregisteret': 'true', 'size': 1000}
            response = requests.get(url, params=temp_params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if '_embedded' in data and 'enheter' in data['_embedded']:
                    selskaper.extend(data['_embedded']['enheter'])
                    print(f"✅ Fant {len(data['_embedded']['enheter'])} bedrifter med MVA-registrering")
                    
                    # Håndter paginering for å få alle resultater
                    page = 0
                    while 'next' in data.get('_links', {}):
                        page += 1
                        temp_params['page'] = page
                        
                        print(f"📄 Henter side {page + 1}...")
                        response = requests.get(url, params=temp_params, timeout=30)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if '_embedded' in data and 'enheter' in data['_embedded']:
                                selskaper.extend(data['_embedded']['enheter'])
                                print(f"✅ Fant {len(data['_embedded']['enheter'])} bedrifter på side {page + 1}")
                            else:
                                break
                        else:
                            print(f"❌ Feil på side {page + 1}: {response.status_code}")
                            break
        except Exception as e2:
            print(f"❌ Feil med MVA-parameter: {str(e2)}")
            
            # Hvis det også feiler, prøv med en annen generell tilnærming
            print("🔄 Prøver siste fallback - hent data fra alle bransjer...")
            
            # Bruk en liste med mange vanlige bransjer for å få bred dekning
            # Dette er ikke ideelt, men gir bedre dekning enn kun 9 bransjer
            bred_bransje_liste = [
                '70.220', '69.201', '62.010', '47.110', '56.100', '85.200', '86.100', '87.100', '88.100',
                '41.100', '42.100', '43.100', '45.100', '46.100', '47.100', '49.100', '50.100', '51.100',
                '52.100', '53.100', '55.100', '58.100', '59.100', '60.100', '61.100', '63.100', '64.100',
                '65.100', '66.100', '68.100', '69.100', '70.100', '71.100', '72.100', '73.100', '74.100',
                '75.100', '77.100', '78.100', '79.100', '80.100', '81.100', '82.100', '84.100', '85.100',
                '86.100', '87.100', '88.100', '90.100', '91.100', '92.100', '93.100', '94.100', '95.100',
                '96.100', '97.100', '98.100', '99.100'
            ]
            
            for bransje in bred_bransje_liste:
                try:
                    temp_params = {'naeringskode': bransje, 'size': 1000}
                    response = requests.get(url, params=temp_params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if '_embedded' in data and 'enheter' in data['_embedded']:
                            selskaper.extend(data['_embedded']['enheter'])
                            print(f"✅ Fant {len(data['_embedded']['enheter'])} bedrifter for bransje {bransje}")
                except Exception as e3:
                    print(f"❌ Feil for bransje {bransje}: {str(e3)}")
                    continue
        
        print(f"🎯 Totalt antall bedrifter funnet fra alle bransjer: {len(selskaper)}")
        
        # Filtrer resultater basert på søkekriterier
        if bedriftsnavn or poststed or postnumre or etablert_etter or momsregistrert is not None:
            selskaper = filtrer_selskaper(selskaper, bedriftsnavn, poststed, postnumre, etablert_etter, momsregistrert)
        
        print(f"🎯 Totalt antall bedrifter funnet etter filtrering: {len(selskaper)}")
        return selskaper
    
    # Legg til NACE-kode hvis spesifisert
    elif bransjekode and bransjekode.strip():
        params['naeringskode'] = bransjekode
    
    # Legg til antall ansatte hvis spesifisert
    if min_ansatte and min_ansatte > 0:
        params['fraAntallAnsatte'] = min_ansatte
    
    if max_ansatte and max_ansatte > 0:
        params['tilAntallAnsatte'] = max_ansatte
    
    # Legg til organisasjonsform hvis spesifisert
    if organisasjonsform:
        params['organisasjonsform'] = organisasjonsform
    
    # Legg til registreringsdato hvis spesifisert
    if registreringsdato:
        params['fraRegistreringsdatoEnhetsregisteret'] = registreringsdato
    
    print(f"🔍 Søker med parametere: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if '_embedded' in data and 'enheter' in data['_embedded']:
                selskaper.extend(data['_embedded']['enheter'])
                print(f"✅ Fant {len(data['_embedded']['enheter'])} bedrifter i første batch")
                
                # Håndter paginering
                page = 0
                while 'next' in data.get('_links', {}):
                    page += 1
                    params['page'] = page
                    
                    print(f"📄 Henter side {page + 1}...")
                    response = requests.get(url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if '_embedded' in data and 'enheter' in data['_embedded']:
                            selskaper.extend(data['_embedded']['enheter'])
                            print(f"✅ Fant {len(data['_embedded']['enheter'])} bedrifter på side {page + 1}")
                        else:
                            break
                    else:
                        print(f"❌ Feil på side {page + 1}: {response.status_code}")
                        break
            else:
                print(f"⚠️ Ingen '_embedded' eller 'enheter' i API response")
        else:
            print(f'❌ API feil: {response.status_code}')
            
    except Exception as e:
        print(f'💥 Feil under henting av data: {str(e)}')
    
    # Filtrer resultater basert på søkekriterier
    if bedriftsnavn or poststed or postnumre or etablert_etter or momsregistrert is not None:
        selskaper = filtrer_selskaper(selskaper, bedriftsnavn, poststed, postnumre, etablert_etter, momsregistrert)
    
    print(f"🎯 Totalt antall bedrifter funnet etter filtrering: {len(selskaper)}")
    return selskaper

def filtrer_selskaper(selskaper, bedriftsnavn=None, poststed=None, postnumre=None, etablert_etter=None, momsregistrert=None):
    """Filtrerer selskaper basert på søkekriterier"""
    filtrerte = selskaper
    
    if bedriftsnavn:
        bedriftsnavn_lower = bedriftsnavn.lower()
        filtrerte = [s for s in filtrerte if s.get('navn', '').lower().find(bedriftsnavn_lower) != -1]
        print(f"🔍 Filtrert på bedriftsnavn '{bedriftsnavn}': {len(filtrerte)} bedrifter igjen")
    
    if poststed:
        poststed_lower = poststed.lower()
        filtrerte = [s for s in filtrerte if s.get('forretningsadresse', {}).get('poststed', '').lower().find(poststed_lower) != -1]
        print(f"🔍 Filtrert på poststed '{poststed}': {len(filtrerte)} bedrifter igjen")
    
    if postnumre:
        print(f"🔍 Filtrerer på postnumre: {postnumre}")
        
        # Filtrer på postnumre
        postnummer_filtrerte = []
        for s in filtrerte:
            adresse = s.get('forretningsadresse', {})
            adresse_tekst = str(adresse.get('adresse', ''))
            postnummer_felt = str(adresse.get('postnummer', ''))
            
            # Sjekk om noen av postnumrene matcher
            matcher = False
            for postnummer in postnumre:
                if postnummer in adresse_tekst or postnummer in postnummer_felt:
                    matcher = True
                    break
            
            if matcher:
                postnummer_filtrerte.append(s)
        
        filtrerte = postnummer_filtrerte
        print(f"🔍 Filtrert på postnumre {postnumre}: {len(filtrerte)} bedrifter igjen")
    
    if etablert_etter:
        # Filtrer på etableringsår
        filtrerte = [s for s in filtrerte if s.get('etableringsdatoEnhetsregisteret', '')[:4] >= str(etablert_etter)]
        print(f"🔍 Filtrert på etablert etter {etablert_etter}: {len(filtrerte)} bedrifter igjen")
    
    if momsregistrert is not None:
        # Filtrer på momsregistrering
        filtrerte = [s for s in filtrerte if s.get('registrertIMvaregisteret') == momsregistrert]
        print(f"🔍 Filtrert på momsregistrert {momsregistrert}: {len(filtrerte)} bedrifter igjen")
    
    return filtrerte

@app.route('/')
def index():
    """Hovedside"""
    return render_template('index.html')

@app.route('/api/sok', methods=['POST'])
def sok_selskaper():
    """API-endepunkt for å søke etter selskaper"""
    try:
        data = request.get_json()
        bransjekode = data.get('bransjekode', '')
        min_ansatte = int(data.get('min_ansatte', 0)) if data.get('min_ansatte') else None
        max_ansatte = int(data.get('max_ansatte', 0)) if data.get('max_ansatte') else None
        bedriftsnavn = data.get('bedriftsnavn', '')
        poststed = data.get('poststed', '')
        postnumre_string = data.get('postnumre', '')
        organisasjonsform = data.get('organisasjonsform', '')
        registreringsdato = data.get('registreringsdato', '')
        etablert_etter = int(data.get('etablert_etter', 0)) if data.get('etablert_etter') else None
        momsregistrert = data.get('momsregistrert', '')
        export_all = data.get('export_all', False)
        
        # Parse postnumre
        postnumre = parse_postnumre(postnumre_string) if postnumre_string else None
        
        # Konverter momsregistrert til boolean hvis spesifisert
        if momsregistrert == 'true':
            momsregistrert = True
        elif momsregistrert == 'false':
            momsregistrert = False
        else:
            momsregistrert = None
        
        print(f"🚀 API søk mottatt:")
        print(f"   - Bransjekode: '{bransjekode}'")
        print(f"   - Min ansatte: {min_ansatte}")
        print(f"   - Max ansatte: {max_ansatte}")
        print(f"   - Bedriftsnavn: '{bedriftsnavn}'")
        print(f"   - Poststed: '{poststed}'")
        print(f"   - Postnumre: {postnumre}")
        print(f"   - Organisasjonsform: '{organisasjonsform}'")
        print(f"   - Registreringsdato: '{registreringsdato}'")
        print(f"   - Etablert etter: {etablert_etter}")
        print(f"   - Momsregistrert: {momsregistrert}")
        
        selskaper = hente_selskaper_med_kriterier(
            bransjekode, 
            min_ansatte, 
            max_ansatte,
            bedriftsnavn if bedriftsnavn else None,
            poststed if poststed else None,
            organisasjonsform if organisasjonsform else None,
            registreringsdato if registreringsdato else None,
            etablert_etter,
            momsregistrert,
            postnumre
        )
        
        # Formater data for frontend
        formaterte_selskaper = []
        for selskap in selskaper:
            # Håndter tomme verdier for antall ansatte
            antall_ansatte = selskap.get('antallAnsatte', '')
            if antall_ansatte == '' or antall_ansatte is None:
                antall_ansatte = 'Ukjent'
            
            # Hent telefonnummer fra kontaktinformasjon
            telefon = ''
            if 'kontaktinformasjon' in selskap:
                kontakt = selskap['kontaktinformasjon']
                if 'telefonnummer' in kontakt:
                    telefon = kontakt['telefonnummer']
                elif 'mobiltelefonnummer' in kontakt:
                    telefon = kontakt['mobiltelefonnummer']
            
            formaterte_selskaper.append({
                'organisasjonsnummer': selskap.get('organisasjonsnummer', ''),
                'navn': selskap.get('navn', ''),
                'poststed': selskap.get('forretningsadresse', {}).get('poststed', ''),
                'antall_ansatte': antall_ansatte,
                'nace_kode': selskap.get('naeringskode1', {}).get('kode', ''),
                'adresse': selskap.get('forretningsadresse', {}).get('adresse', ''),
                'telefon': telefon,
                'organisasjonsform': selskap.get('organisasjonsform', {}).get('kode', '')
            })
        
        # Returner alle resultater for statistikk og eksport
        return jsonify({
            'success': True,
            'selskaper': formaterte_selskaper,
            'antall': len(formaterte_selskaper)
        })
    
    except Exception as e:
        print(f"💥 Feil i API endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/eksporter', methods=['POST'])
def eksporter_excel():
    """API-endepunkt for å eksportere data til Excel"""
    try:
        data = request.get_json()
        selskaper = data.get('selskaper', [])
        
        if not selskaper:
            return jsonify({
                'success': False,
                'error': 'Ingen bedrifter å eksportere'
            }), 400
        
        # Opprett Excel-arbeidsbok
        wb = Workbook()
        sheet = wb.active
        sheet.title = "Selskaper"
        
        # Legg til overskrifter
        headers = ['Organisasjonsnummer', 'Navn', 'Poststed', 'Antall Ansatte', 'NACE-kode', 'Adresse', 'Telefon', 'Organisasjonsform']
        sheet.append(headers)
        
        # Legg til data
        for selskap in selskaper:
            sheet.append([
                str(selskap.get('organisasjonsnummer', '')),
                str(selskap.get('navn', '')),
                str(selskap.get('poststed', '')),
                str(selskap.get('antall_ansatte', '')),
                str(selskap.get('nace_kode', '')),
                str(selskap.get('adresse', '')),
                str(selskap.get('telefon', '')),
                str(selskap.get('organisasjonsform', ''))
            ])
        
        # Auto-juster kolonner
        for column in sheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            sheet.column_dimensions[column_letter].width = adjusted_width
        
        # Lagre til buffer
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='selskaper_export.xlsx'
        )
    
    except Exception as e:
        print(f"💥 Feil i eksport: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
