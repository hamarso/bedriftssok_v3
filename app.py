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
    
    # Bygg API-parametere basert på brukerens søkekriterier
    # Brønnøysundregisteret API krever minst én parameter, så vi legger til en generell hvis nødvendig
    
    # Legg til NACE-kode hvis spesifisert
    if bransjekode and bransjekode.strip():
        params['naeringskode'] = bransjekode
    
    # Legg til antall ansatte hvis spesifisert
    if min_ansatte and min_ansatte > 0:
        params['fraAntallAnsatte'] = min_ansatte
    
    if max_ansatte and max_ansatte > 0:
        params['tilAntallAnsatte'] = max_ansatte
    
    # Legg til organisasjonsform hvis spesifisert
    if organisasjonsform and organisasjonsform.strip():
        params['organisasjonsform'] = organisasjonsform
    
    # Legg til registreringsdato hvis spesifisert
    if registreringsdato and registreringsdato.strip():
        params['fraRegistreringsdatoEnhetsregisteret'] = registreringsdato
    
    # Hvis ingen parametere er satt, legg til en generell parameter for å oppfylle API-kravet
    if len(params) == 1:  # Kun 'size' er satt
        print("🔍 Ingen søkeparametere spesifisert. Bruker generell parameter for å oppfylle API-krav.")
        params['registrertIMvaregisteret'] = 'true'  # Alle MVA-registrerte selskaper
    
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
        # Returner tom liste hvis API-kallet feiler
        return []
    
    # Filtrer resultater basert på søkekriterier
    if bedriftsnavn or poststed or postnumre or etablert_etter or momsregistrert is not None:
        selskaper = filtrer_selskaper(selskaper, bedriftsnavn, poststed, postnumre, etablert_etter, momsregistrert)
    
    print(f"🎯 Totalt antall bedrifter funnet: {len(selskaper)}")
    return selskaper
    


def filtrer_selskaper(selskaper, bedriftsnavn=None, poststed=None, postnumre=None, etablert_etter=None, momsregistrert=None):
    """Filtrerer selskaper basert på søkekriterier"""
    # Sjekk at selskaper ikke er None
    if selskaper is None:
        print("⚠️ Selskaper er None, returnerer tom liste")
        return []
    
    filtrerte = selskaper
    
    if bedriftsnavn and bedriftsnavn.strip():
        bedriftsnavn_lower = bedriftsnavn.lower()
        filtrerte = [s for s in filtrerte if s.get('navn', '').lower().find(bedriftsnavn_lower) != -1]
        print(f"🔍 Filtrert på bedriftsnavn '{bedriftsnavn}': {len(filtrerte)} bedrifter igjen")
    
    if poststed and poststed.strip():
        poststed_lower = poststed.lower()
        filtrerte = [s for s in filtrerte if s.get('forretningsadresse', {}).get('poststed', '').lower().find(poststed_lower) != -1]
        print(f"🔍 Filtrert på poststed '{poststed}': {len(filtrerte)} bedrifter igjen")
    
    if postnumre and len(postnumre) > 0:
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
    
    if etablert_etter and etablert_etter > 0:
        # Filtrer på etableringsår
        filtrerte = [s for s in filtrerte if s.get('etableringsdatoEnhetsregisteret', '') and s.get('etableringsdatoEnhetsregisteret', '')[:4] >= str(etablert_etter)]
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
