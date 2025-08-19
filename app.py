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
    params = {
        'naeringskode': bransjekode,
        'fraAntallAnsatte': min_ansatte,
        'size': 1000
    }

    while True:
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if '_embedded' in data and 'enheter' in data['_embedded']:
                    selskaper.extend(data['_embedded']['enheter'])
                    if 'next' in data['_links']:
                        params['page'] = params.get('page', 0) + 1
                    else:
                        break
                else:
                    break
            else:
                print(f'Feil under henting av data: {response.status_code}')
                break
        except Exception as e:
            print(f'Feil under henting av data: {str(e)}')
            break

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
        min_ansatte = int(data.get('min_ansatte', 100))
        
        selskaper = hente_selskaper_med_kriterier(bransjekode, min_ansatte)
        
        # Formater data for frontend
        formaterte_selskaper = []
        for selskap in selskaper:
            formaterte_selskaper.append({
                'organisasjonsnummer': selskap.get('organisasjonsnummer', ''),
                'navn': selskap.get('navn', ''),
                'poststed': selskap.get('forretningsadresse', {}).get('poststed', ''),
                'antall_ansatte': selskap.get('antallAnsatte', ''),
                'nace_kode': selskap.get('naeringskode1', {}).get('kode', ''),
                'adresse': selskap.get('forretningsadresse', {}).get('adresse', '')
            })
        
        return jsonify({
            'success': True,
            'selskaper': formaterte_selskaper,
            'antall': len(formaterte_selskaper)
        })
    
    except Exception as e:
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
