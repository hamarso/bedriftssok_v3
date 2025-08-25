from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import requests
from openpyxl import Workbook
import io
import os
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

def hente_selskaper_med_kriterier(bransjekode, min_ansatte, bedriftsnavn=None, poststed=None, organisasjonsform=None, registreringsdato=None, postnumre=None):
    """Henter selskaper basert på søkekriterier"""
    url = "https://data.brreg.no/enhetsregisteret/api/enheter"
    selskaper = []
    
    # Oppdaterte parametere for Brønnøysundregisteret API
    params = {
        'naeringskode': bransjekode,
        'size': 1000
    }
    
    # Legg til antall ansatte parameter kun hvis det er større enn 0
    if min_ansatte > 0:
        params['fraAntallAnsatte'] = min_ansatte
    
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
            print(f"📊 API Response keys: {list(data.keys())}")
            
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
                print(f"📋 Response struktur: {data}")
        else:
            print(f'❌ API feil: {response.status_code}')
            print(f'📋 Response tekst: {response.text[:500]}')
            
    except Exception as e:
        print(f'💥 Feil under henting av data: {str(e)}')
    
    # Filtrer resultater basert på bedriftsnavn, poststed og postnumre
    if bedriftsnavn or poststed or postnumre:
        selskaper = filtrer_selskaper(selskaper, bedriftsnavn, poststed, postnumre)
    
    print(f"🎯 Totalt antall bedrifter funnet etter filtrering: {len(selskaper)}")
    return selskaper

def filtrer_selskaper(selskaper, bedriftsnavn=None, poststed=None, postnumre=None):
    """Filtrerer selskaper basert på navn, poststed og postnumre"""
    print(f"🔍 Starter filtrering av {len(selskaper)} bedrifter")
    print(f"🔍 Filtreringskriterier:")
    print(f"   - Bedriftsnavn: {bedriftsnavn if bedriftsnavn else 'Ikke spesifisert'}")
    print(f"   - Poststed: {poststed if poststed else 'Ikke spesifisert'}")
    print(f"   - Postnumre: {postnumre if postnumre else 'Ikke spesifisert'}")
    
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
        print(f"🔍 Antall bedrifter før postnummer-filtrering: {len(filtrerte)}")
        
        # Log første noen bedrifter for å se adressestrukturen
        for i, selskap in enumerate(filtrerte[:3]):
            adresse = selskap.get('forretningsadresse', {})
            print(f"   Bedrift {i+1}: {selskap.get('navn', 'N/A')}")
            print(f"     Adresse: {adresse.get('adresse', 'N/A')}")
            print(f"     Postnummer: {adresse.get('postnummer', 'N/A')}")
            print(f"     Poststed: {adresse.get('poststed', 'N/A')}")
        
        # Filtrer på postnumre - sjekk både adresse og postnummer-felt
        postnummer_filtrerte = []
        for s in filtrerte:
            adresse = s.get('forretningsadresse', {})
            adresse_tekst = str(adresse.get('adresse', ''))
            postnummer_felt = str(adresse.get('postnummer', ''))
            
            # Sjekk om noen av postnumrene matcher
            matcher = False
            for postnummer in postnumre:
                # Sjekk i adresse-tekst (mer fleksibel matching)
                if postnummer in adresse_tekst:
                    matcher = True
                    break
                # Sjekk i postnummer-felt (mer nøyaktig matching)
                if postnummer in postnummer_felt:
                    matcher = True
                    break
            
            if matcher:
                postnummer_filtrerte.append(s)
        
        filtrerte = postnummer_filtrerte
        print(f"🔍 Filtrert på postnumre {postnumre}: {len(filtrerte)} bedrifter igjen")
        
        # Log noen matchende bedrifter for debugging
        if filtrerte:
            print(f"🔍 Eksempler på matchende bedrifter:")
            for i, selskap in enumerate(filtrerte[:2]):
                adresse = selskap.get('forretningsadresse', {})
                print(f"   {i+1}. {selskap.get('navn', 'N/A')}")
                print(f"      Adresse: {adresse.get('adresse', 'N/A')}")
                print(f"      Postnummer: {adresse.get('postnummer', 'N/A')}")
    
    print(f"🔍 Filtrering ferdig: {len(filtrerte)} bedrifter igjen")
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
        min_ansatte = int(data.get('min_ansatte', 0)) if data.get('min_ansatte') else 0
        max_ansatte = int(data.get('max_ansatte', 0)) if data.get('max_ansatte') else 0
        bedriftsnavn = data.get('bedriftsnavn', '')
        poststed = data.get('poststed', '')
        postnumre_string = data.get('postnumre', '')
        organisasjonsform = data.get('organisasjonsform', '')
        registreringsdato = data.get('registreringsdato', '')
        etablert_etter = data.get('etablert_etter')
        momsregistrert = data.get('momsregistrert')
        page = int(data.get('page', 0))
        page_size = 100
        export_all = data.get('export_all', False)
        
        # Parse postnumre
        postnumre = parse_postnumre(postnumre_string) if postnumre_string else None
        
        print(f"🚀 API søk mottatt:")
        print(f"   - Bransjekode: '{bransjekode}' (tom hvis ikke spesifisert)")
        print(f"   - Min ansatte: {min_ansatte}")
        print(f"   - Max ansatte: {max_ansatte}")
        print(f"   - Bedriftsnavn: '{bedriftsnavn}'")
        print(f"   - Poststed: '{poststed}'")
        print(f"   - Postnumre: {postnumre}")
        print(f"   - Organisasjonsform: '{organisasjonsform}'")
        print(f"   - Registreringsdato: '{registreringsdato}'")
        print(f"   - Etablert etter: {etablert_etter}")
        print(f"   - Momsregistrert: {momsregistrert}")
        print(f"   - Side: {page}")
        print(f"   - Export all: {export_all}")
        
        # Sjekk om bransjekode er påkrevd
        if not bransjekode or bransjekode.strip() == '':
            return jsonify({
                'success': False,
                'error': 'NACE-kode (bransje) er påkrevd for søk'
            }), 400
        
        selskaper = hente_selskaper_med_kriterier(
            bransjekode, 
            min_ansatte, 
            bedriftsnavn if bedriftsnavn else None,
            poststed if poststed else None,
            organisasjonsform if organisasjonsform else None,
            registreringsdato if registreringsdato else None,
            postnumre
        )
        
        print(f"📊 Rå data mottatt: {len(selskaper)} bedrifter")
        
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
            
            # Hvis ingen telefonnummer funnet, prøv andre felter
            if not telefon:
                # Sjekk om det finnes telefonnummer i andre felter
                for key, value in selskap.items():
                    if 'telefon' in key.lower() and value:
                        telefon = value
                        break
            
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
        
        print(f"✅ Formaterte data: {len(formaterte_selskaper)} bedrifter")
        
        # Log første bedrift for debugging
        if formaterte_selskaper:
            første = formaterte_selskaper[0]
            print(f"📋 Eksempel på formatert bedrift:")
            print(f"   - Navn: {første.get('navn', 'N/A')}")
            print(f"   - NACE: {første.get('nace_kode', 'N/A')}")
            print(f"   - Ansatte: {første.get('antall_ansatte', 'N/A')}")
            print(f"   - Telefon: {første.get('telefon', 'N/A')}")
        
        # Hvis export_all er satt, returner alle resultater
        if export_all:
            print(f"📄 Eksport modus: Returnerer alle {len(formaterte_selskaper)} resultater")
            return jsonify({
                'success': True,
                'selskaper': formaterte_selskaper,
                'antall': len(formaterte_selskaper)
            })
        
        # Implementer paginering
        total_count = len(formaterte_selskaper)
        start_index = page * page_size
        end_index = start_index + page_size
        paginerte_selskaper = formaterte_selskaper[start_index:end_index]
        
        print(f"📄 Paginering: Side {page + 1}, viser {len(paginerte_selskaper)} av {total_count} totalt")
        
        return jsonify({
            'success': True,
            'selskaper': paginerte_selskaper,
            'antall': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'has_next': end_index < total_count,
            'has_previous': page > 0
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
        
        print(f"📊 Eksport startet med {len(selskaper)} bedrifter")
        
        if not selskaper:
            print("⚠️ Ingen bedrifter å eksportere")
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
        
        print(f"📊 Eksporterer {len(selskaper)} selskaper til Excel")
        print(f"📊 Første selskap data: {selskaper[0] if selskaper else 'Ingen data'}")
        
        # Legg til data
        for selskap in selskaper:
            # Sikre at alle verdier er strings og ikke None
            organisasjonsnummer = str(selskap.get('organisasjonsnummer', '')) if selskap.get('organisasjonsnummer') is not None else ''
            navn = str(selskap.get('navn', '')) if selskap.get('navn') is not None else ''
            poststed = str(selskap.get('poststed', '')) if selskap.get('poststed') is not None else ''
            antall_ansatte = str(selskap.get('antall_ansatte', '')) if selskap.get('antall_ansatte') is not None else ''
            nace_kode = str(selskap.get('nace_kode', '')) if selskap.get('nace_kode') is not None else ''
            adresse = str(selskap.get('adresse', '')) if selskap.get('adresse') is not None else ''
            telefon = str(selskap.get('telefon', '')) if selskap.get('telefon') is not None else ''
            organisasjonsform = str(selskap.get('organisasjonsform', '')) if selskap.get('organisasjonsform') is not None else ''
            
            sheet.append([
                organisasjonsnummer,
                navn,
                poststed,
                antall_ansatte,
                nace_kode,
                adresse,
                telefon,
                organisasjonsform
            ])
        
        print(f"✅ {len(selskaper)} bedrifter lagt til i Excel")
        
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
        try:
            wb.save(excel_file)
            excel_file.seek(0)
            print(f"📄 Excel-fil opprettet, størrelse: {len(excel_file.getvalue())} bytes")
            
            return send_file(
                excel_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='selskaper_export.xlsx'
            )
        except Exception as e:
            print(f"❌ Feil ved lagring av Excel-fil: {e}")
            print(f"❌ Feil type: {type(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Kunne ikke opprette Excel-fil: {str(e)}'
            }), 500
    
    except Exception as e:
        print(f"💥 Feil i eksport: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/nace-koder', methods=['GET'])
def hent_nace_koder():
    """API-endepunkt for å hente alle tilgjengelige NACE-koder"""
    try:
        print("🔍 Henter alle tilgjengelige NACE-koder...")
        
        # Hent alle NACE-koder fra Brønnøysundregisteret
        nace_koder = hent_alle_nace_koder()
        
        print(f"✅ Fant {len(nace_koder)} NACE-koder")
        
        return jsonify({
            'success': True,
            'nace_koder': nace_koder,
            'antall': len(nace_koder)
        })
    
    except Exception as e:
        print(f"💥 Feil ved henting av NACE-koder: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def hent_alle_nace_koder():
    """Henter alle tilgjengelige NACE-koder fra Brønnøysundregisteret"""
    url = "https://data.brreg.no/enhetsregisteret/api/enheter"
    nace_koder = set()
    
    # Test med forskjellige NACE-koder for å finne de som eksisterer
    # Vi kan ikke hente alle automatisk, så vi bruker en omfattende liste
    test_koder = [
        # 69 - Juridiske og regnskapsmessige tjenester
        '69.100', '69.101', '69.102', '69.103', '69.104', '69.105', '69.106', '69.107', '69.108', '69.109',
        '69.200', '69.201', '69.202', '69.203', '69.204', '69.205', '69.206', '69.207', '69.208', '69.209',
        
        # 70 - Hovedkontor og konsulentvirksomhet
        '70.100', '70.101', '70.102', '70.103', '70.104', '70.105', '70.106', '70.107', '70.108', '70.109',
        '70.200', '70.201', '70.202', '70.203', '70.204', '70.205', '70.206', '70.207', '70.208', '70.209',
        '70.210', '70.211', '70.212', '70.213', '70.214', '70.215', '70.216', '70.217', '70.218', '70.219',
        '70.220', '70.221', '70.222', '70.223', '70.224', '70.225', '70.226', '70.227', '70.228', '70.229',
        
        # 62 - IT-tjenester
        '62.010', '62.020', '62.030', '62.040', '62.050', '62.060', '62.070', '62.080', '62.090',
        
        # 43 - Bygge- og anleggsinstallasjon
        '43.100', '43.200', '43.210', '43.220', '43.290', '43.300', '43.400', '43.500', '43.600', '43.700', '43.800', '43.900',
        
        # 41 - Bygging av boliger
        '41.100', '41.200', '41.300', '41.400', '41.500', '41.600', '41.700', '41.800', '41.900',
        
        # 42 - Bygging av anlegg
        '42.100', '42.200', '42.210', '42.220', '42.300', '42.400', '42.500', '42.600', '42.700', '42.800', '42.900',
        
        # 47 - Varehandel
        '47.100', '47.200', '47.300', '47.400', '47.500', '47.600', '47.700', '47.800', '47.900',
        
        # 56 - Servering og drikkesteder
        '56.100', '56.200', '56.300', '56.400', '56.500', '56.600', '56.700', '56.800', '56.900',
        
        # 58 - Utgivelse av programvare
        '58.100', '58.200', '58.300', '58.400', '58.500', '58.600', '58.700', '58.800', '58.900',
        
        # 59 - Film, video og TV
        '59.100', '59.110', '59.120', '59.130', '59.140', '59.200', '59.300', '59.400', '59.500', '59.600', '59.700', '59.800', '59.900',
        
        # 60 - Radio og TV
        '60.100', '60.200', '60.300', '60.400', '60.500', '60.600', '60.700', '60.800', '60.900',
        
        # 61 - Telekommunikasjon
        '61.100', '61.200', '61.300', '61.400', '61.500', '61.600', '61.700', '61.800', '61.900',
        
        # 63 - IT-tjenesteyting
        '63.100', '63.110', '63.120', '63.200', '63.300', '63.400', '63.500', '63.600', '63.700', '63.800', '63.900',
        
        # 64 - Finansielle tjenester
        '64.100', '64.200', '64.300', '64.400', '64.500', '64.600', '64.700', '64.800', '64.900',
        
        # 65 - Forsikring og pensjon
        '65.100', '65.200', '65.300', '65.400', '65.500', '65.600', '65.700', '65.800', '65.900',
        
        # 66 - Finansielle tjenester
        '66.100', '66.200', '66.300', '66.400', '66.500', '66.600', '66.700', '66.800', '66.900',
        
        # 68 - Eiendomsvirksomhet
        '68.100', '68.200', '68.300', '68.400', '68.500', '68.600', '68.700', '68.800', '68.900',
        
        # 71 - Arkitektur og ingeniørvirksomhet
        '71.100', '71.200', '71.300', '71.400', '71.500', '71.600', '71.700', '71.800', '71.900',
        
        # 72 - Vitenskapelig forskning og utvikling
        '72.100', '72.200', '72.300', '72.400', '72.500', '72.600', '72.700', '72.800', '72.900',
        
        # 73 - Reklame og markedsundersøkelser
        '73.100', '73.200', '73.300', '73.400', '73.500', '73.600', '73.700', '73.800', '73.900',
        
        # 74 - Annen faglig, vitenskapelig og teknisk virksomhet
        '74.100', '74.200', '74.300', '74.400', '74.500', '74.600', '74.700', '74.800', '74.900',
        
        # 75 - Veterinærvirksomhet
        '75.100', '75.200', '75.300', '75.400', '75.500', '75.600', '75.700', '75.800', '75.900',
        
        # 77 - Utleie og leasing
        '77.100', '77.200', '77.300', '77.400', '77.500', '77.600', '77.700', '77.800', '77.900',
        
        # 78 - Arbeidskraft
        '78.100', '78.200', '78.300', '78.400', '78.500', '78.600', '78.700', '78.800', '78.900',
        
        # 79 - Reisearrangører, reisebyråer og reservasjonssystemer
        '79.100', '79.200', '79.300', '79.400', '79.500', '79.600', '79.700', '79.800', '79.900',
        
        # 80 - Sikkerhet og etterforskning
        '80.100', '80.200', '80.300', '80.400', '80.500', '80.600', '80.700', '80.800', '80.900',
        
        # 81 - Tjenester til bygninger og landskap
        '81.100', '81.200', '81.300', '81.400', '81.500', '81.600', '81.700', '81.800', '81.900',
        
        # 82 - Kontor- og andre forretningsstøttetjenester
        '82.100', '82.200', '82.300', '82.400', '82.500', '82.600', '82.700', '82.800', '82.900',
        
        # 85 - Utdanning
        '85.100', '85.200', '85.300', '85.400', '85.500', '85.600', '85.700', '85.800', '85.900',
        
        # 86 - Helse
        '86.100', '86.200', '86.300', '86.400', '86.500', '86.600', '86.700', '86.800', '86.900',
        
        # 87 - Omsorg
        '87.100', '87.200', '87.300', '87.400', '87.500', '87.600', '87.700', '87.800', '87.900',
        
        # 88 - Sosiale tjenester
        '88.100', '88.200', '88.300', '88.400', '88.500', '88.600', '88.700', '88.800', '88.900',
        
        # 90 - Kunst, underholdning og rekreasjon
        '90.100', '90.200', '90.300', '90.400', '90.500', '90.600', '90.700', '90.800', '90.900',
        
        # 91 - Biblioteker, arkiver, museer og andre kulturelle aktiviteter
        '91.100', '91.200', '91.300', '91.400', '91.500', '91.600', '91.700', '91.800', '91.900',
        
        # 92 - Spill og veddemål
        '92.100', '92.200', '92.300', '92.400', '92.500', '92.600', '92.700', '92.800', '92.900',
        
        # 93 - Sport, underholdning og rekreasjon
        '93.100', '93.200', '93.300', '93.400', '93.500', '93.600', '93.700', '93.800', '93.900',
        
        # 94 - Medlemsorganisasjoner
        '94.100', '94.200', '94.300', '94.400', '94.500', '94.600', '94.700', '94.800', '94.900',
        
        # 95 - Reparasjon av datamaskiner og personlige og husholdningsartikler
        '95.100', '95.200', '95.300', '95.400', '95.500', '95.600', '95.700', '95.800', '95.900',
        
        # 96 - Andre personlige tjenester
        '96.100', '96.200', '96.300', '96.400', '96.500', '96.600', '96.700', '96.800', '96.900',
        
        # 97 - Husholdninger som ansetter husholdningspersonale
        '97.000',
        
        # 98 - Husholdninger som produserer varer og tjenester for egen bruk
        '98.100', '98.200', '98.300', '98.400', '98.500', '98.600', '98.700', '98.800', '98.900',
        
        # 99 - Eksterritoriale organisasjoner og organer
        '99.000'
    ]
    
    print(f"🔍 Tester {len(test_koder)} NACE-koder...")
    
    for i, code in enumerate(test_koder):
        try:
            params = {
                'naeringskode': code,
                'size': 1  # Bare sjekk om det finnes noen
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Sjekk om det finnes bedrifter med denne koden
                if 'page' in data and 'totalElements' in data['page']:
                    total = data['page']['totalElements']
                    if total > 0:
                        nace_koder.add(code)
                        if len(nace_koder) % 10 == 0:  # Log hver 10. kode
                            print(f"   ✅ Funnet {len(nace_koder)} koder så langt...")
            
            # Legg til en liten pause for å ikke overbelaste API-et
            if i % 50 == 0:
                import time
                time.sleep(0.1)
                
        except Exception as e:
            # Ignorer feil for individuelle koder
            continue
    
    print(f"✅ Totalt funnet {len(nace_koder)} NACE-koder med bedrifter")
    return sorted(list(nace_koder))

if __name__ == '__main__':
    app.run(debug=True)
