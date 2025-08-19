from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import requests
from openpyxl import Workbook
import io
import os

app = Flask(__name__)
CORS(app)

def hente_selskaper_med_kriterier(bransjekode, min_ansatte):
    """Henter selskaper basert på bransjekode og minimum antall ansatte"""
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
    
    print(f"🎯 Totalt antall bedrifter funnet: {len(selskaper)}")
    return selskaper

@app.route('/')
def index():
    """Hovedside"""
    return render_template('index.html')

@app.route('/api/sok', methods=['POST'])
def sok_selskaper():
    """API-endepunkt for å søke etter selskaper"""
    try:
        data = request.get_json()
        bransjekode = data.get('bransjekode', '70.220')
        min_ansatte = int(data.get('min_ansatte', 0))
        
        print(f"🚀 API søk mottatt:")
        print(f"   - Bransjekode: {bransjekode}")
        print(f"   - Min ansatte: {min_ansatte}")
        
        selskaper = hente_selskaper_med_kriterier(bransjekode, min_ansatte)
        
        print(f"📊 Rå data mottatt: {len(selskaper)} bedrifter")
        
        # Formater data for frontend
        formaterte_selskaper = []
        for selskap in selskaper:
            # Håndter tomme verdier for antall ansatte
            antall_ansatte = selskap.get('antallAnsatte', '')
            if antall_ansatte == '' or antall_ansatte is None:
                antall_ansatte = 'Ukjent'
            
            formaterte_selskaper.append({
                'organisasjonsnummer': selskap.get('organisasjonsnummer', ''),
                'navn': selskap.get('navn', ''),
                'poststed': selskap.get('forretningsadresse', {}).get('poststed', ''),
                'antall_ansatte': antall_ansatte,
                'nace_kode': selskap.get('naeringskode1', {}).get('kode', ''),
                'adresse': selskap.get('forretningsadresse', {}).get('adresse', '')
            })
        
        print(f"✅ Formaterte data: {len(formaterte_selskaper)} bedrifter")
        
        # Log første bedrift for debugging
        if formaterte_selskaper:
            første = formaterte_selskaper[0]
            print(f"📋 Eksempel på formatert bedrift:")
            print(f"   - Navn: {første.get('navn', 'N/A')}")
            print(f"   - NACE: {første.get('nace_kode', 'N/A')}")
            print(f"   - Ansatte: {første.get('antall_ansatte', 'N/A')}")
        
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
        
        # Opprett Excel-arbeidsbok
        wb = Workbook()
        sheet = wb.active
        sheet.title = "Selskaper"
        
        # Legg til overskrifter
        headers = ['Organisasjonsnummer', 'Navn', 'Poststed', 'Antall Ansatte', 'NACE-kode', 'Adresse']
        sheet.append(headers)
        
        # Legg til data
        for selskap in selskaper:
            sheet.append([
                selskap.get('organisasjonsnummer', ''),
                selskap.get('navn', ''),
                selskap.get('poststed', ''),
                selskap.get('antall_ansatte', ''),
                selskap.get('nace_kode', ''),
                selskap.get('adresse', '')
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
