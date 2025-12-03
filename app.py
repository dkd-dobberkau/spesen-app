from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from cryptography.fernet import Fernet
import base64
import io
import json
import os
import sqlite3

app = Flask(__name__)

# Encryption key - in production, store this securely (e.g., environment variable)
KEY_FILE = 'secret.key'

def get_or_create_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        return key

ENCRYPTION_KEY = get_or_create_key()
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_data(data):
    if not data:
        return None
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    if not encrypted_data:
        return None
    return cipher.decrypt(encrypted_data.encode()).decode()

DATABASE = 'spesen.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS abrechnungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                monat TEXT NOT NULL,
                datum TEXT,
                konto TEXT,
                blz TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, monat)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ausgaben (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                abrechnung_id INTEGER NOT NULL,
                kategorie TEXT NOT NULL,
                daten TEXT NOT NULL,
                FOREIGN KEY (abrechnung_id) REFERENCES abrechnungen(id) ON DELETE CASCADE
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS einstellungen (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT,
                iban_encrypted TEXT,
                bic_encrypted TEXT,
                bank TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

# Verpflegungspauschalen 2025
VERPFLEGUNGSPAUSCHALEN = {
    'Deutschland': {'halbtag': 14.00, 'ganztag': 28.00},
    'Belgien': {'halbtag': 40.00, 'ganztag': 59.00},
    'Bulgarien': {'halbtag': 15.00, 'ganztag': 22.00},
    'Dänemark': {'halbtag': 50.00, 'ganztag': 75.00},
    'Finnland': {'halbtag': 36.00, 'ganztag': 54.00},
    'Frankreich': {'halbtag': 39.00, 'ganztag': 58.00},
    'Griechenland': {'halbtag': 27.00, 'ganztag': 40.00},
    'Großbritannien': {'halbtag': 38.00, 'ganztag': 57.00},
    'Irland': {'halbtag': 39.00, 'ganztag': 58.00},
    'Italien': {'halbtag': 28.00, 'ganztag': 42.00},
    'Kroatien': {'halbtag': 31.00, 'ganztag': 46.00},
    'Niederlande': {'halbtag': 32.00, 'ganztag': 47.00},
    'Österreich': {'halbtag': 33.00, 'ganztag': 50.00},
    'Polen': {'halbtag': 27.00, 'ganztag': 40.00},
    'Portugal': {'halbtag': 24.00, 'ganztag': 36.00},
    'Schweden': {'halbtag': 44.00, 'ganztag': 66.00},
    'Schweiz': {'halbtag': 43.00, 'ganztag': 64.00},
    'Spanien': {'halbtag': 28.00, 'ganztag': 42.00},
    'Tschechien': {'halbtag': 24.00, 'ganztag': 35.00},
    'USA': {'halbtag': 40.00, 'ganztag': 59.00},
}

CATEGORIES = {
    'fahrtkosten_kfz': {'name': 'Fahrtkosten mit priv. Kfz.', 'fields': ['datum', 'fahrstrecke', 'anlass', 'km'], 'rate': 0.30},
    'fahrtkosten_pauschale': {'name': 'Fahrtkostenpauschale', 'fields': ['monat', 'beschreibung', 'betrag']},
    'bewirtung': {'name': 'Bewirtungskosten', 'fields': ['datum', 'personen', 'betrag']},
    'fachliteratur': {'name': 'Fachliteratur', 'fields': ['datum', 'beschreibung', 'betrag']},
    'bueromaterial': {'name': 'Büromaterial', 'fields': ['datum', 'beschreibung', 'betrag']},
    'telefonkosten': {'name': 'Telefonkosten', 'fields': ['datum', 'beschreibung', 'betrag']},
    'software': {'name': 'Software', 'fields': ['datum', 'beschreibung', 'betrag']},
    'getraenke': {'name': 'Getränke', 'fields': ['datum', 'beschreibung', 'betrag']},
    'sonstiges': {'name': 'Sonstiges', 'fields': ['datum', 'typ', 'ort', 'betrag'], 
                  'types': ['Parken', 'Taxi', 'Verpflegungspauschale', 'Uber', 'Sonstiges']}
}

@app.route('/')
def index():
    return render_template('index.html', categories=CATEGORIES, verpflegungspauschalen=VERPFLEGUNGSPAUSCHALEN)

@app.route('/api/verpflegungspauschalen')
def get_verpflegungspauschalen():
    return jsonify(VERPFLEGUNGSPAUSCHALEN)

# API: Einstellungen laden
@app.route('/api/einstellungen', methods=['GET'])
def get_einstellungen():
    with get_db() as conn:
        row = conn.execute('SELECT * FROM einstellungen WHERE id = 1').fetchone()
        if row:
            return jsonify({
                'name': row['name'],
                'iban': decrypt_data(row['iban_encrypted']),
                'bic': decrypt_data(row['bic_encrypted']),
                'bank': row['bank']
            })
        return jsonify({'name': '', 'iban': '', 'bic': '', 'bank': ''})

# API: Einstellungen speichern
@app.route('/api/einstellungen', methods=['POST'])
def save_einstellungen():
    data = request.json

    iban_encrypted = encrypt_data(data.get('iban', ''))
    bic_encrypted = encrypt_data(data.get('bic', ''))

    with get_db() as conn:
        conn.execute('''
            INSERT INTO einstellungen (id, name, iban_encrypted, bic_encrypted, bank)
            VALUES (1, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                iban_encrypted = excluded.iban_encrypted,
                bic_encrypted = excluded.bic_encrypted,
                bank = excluded.bank,
                updated_at = CURRENT_TIMESTAMP
        ''', (data.get('name', ''), iban_encrypted, bic_encrypted, data.get('bank', '')))
        conn.commit()

    return jsonify({'success': True})

# API: Liste aller Abrechnungen
@app.route('/api/abrechnungen', methods=['GET'])
def list_abrechnungen():
    with get_db() as conn:
        rows = conn.execute(
            'SELECT id, name, monat, datum, konto, blz, created_at FROM abrechnungen ORDER BY created_at DESC'
        ).fetchall()
        return jsonify([dict(row) for row in rows])

# API: Abrechnung laden
@app.route('/api/abrechnungen/<int:abrechnung_id>', methods=['GET'])
def get_abrechnung(abrechnung_id):
    with get_db() as conn:
        abr = conn.execute(
            'SELECT * FROM abrechnungen WHERE id = ?', (abrechnung_id,)
        ).fetchone()
        if not abr:
            return jsonify({'error': 'Nicht gefunden'}), 404

        ausgaben_rows = conn.execute(
            'SELECT kategorie, daten FROM ausgaben WHERE abrechnung_id = ?', (abrechnung_id,)
        ).fetchall()

        expenses = {cat: [] for cat in CATEGORIES.keys()}
        for row in ausgaben_rows:
            if row['kategorie'] in expenses:
                expenses[row['kategorie']].append(json.loads(row['daten']))

        return jsonify({
            'meta': {
                'id': abr['id'],
                'name': abr['name'],
                'monat': abr['monat'],
                'datum': abr['datum'],
                'konto': abr['konto'],
                'blz': abr['blz']
            },
            'expenses': expenses
        })

# API: Abrechnung speichern (neu oder update)
@app.route('/api/abrechnungen', methods=['POST'])
def save_abrechnung():
    data = request.json
    meta = data.get('meta', {})
    expenses = data.get('expenses', {})

    with get_db() as conn:
        # Prüfen ob Abrechnung existiert (per ID oder Name+Monat)
        abrechnung_id = meta.get('id')

        if abrechnung_id:
            # Update existierende
            conn.execute('''
                UPDATE abrechnungen SET name=?, monat=?, datum=?, konto=?, blz=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (meta.get('name'), meta.get('monat'), meta.get('datum'),
                  meta.get('konto'), meta.get('blz'), abrechnung_id))
        else:
            # Versuche existierende per Name+Monat zu finden
            existing = conn.execute(
                'SELECT id FROM abrechnungen WHERE name=? AND monat=?',
                (meta.get('name'), meta.get('monat'))
            ).fetchone()

            if existing:
                abrechnung_id = existing['id']
                conn.execute('''
                    UPDATE abrechnungen SET datum=?, konto=?, blz=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (meta.get('datum'), meta.get('konto'), meta.get('blz'), abrechnung_id))
            else:
                # Neue Abrechnung erstellen
                cursor = conn.execute('''
                    INSERT INTO abrechnungen (name, monat, datum, konto, blz)
                    VALUES (?, ?, ?, ?, ?)
                ''', (meta.get('name'), meta.get('monat'), meta.get('datum'),
                      meta.get('konto'), meta.get('blz')))
                abrechnung_id = cursor.lastrowid

        # Alte Ausgaben löschen und neue einfügen
        conn.execute('DELETE FROM ausgaben WHERE abrechnung_id = ?', (abrechnung_id,))

        for kategorie, items in expenses.items():
            for item in items:
                conn.execute('''
                    INSERT INTO ausgaben (abrechnung_id, kategorie, daten)
                    VALUES (?, ?, ?)
                ''', (abrechnung_id, kategorie, json.dumps(item)))

        conn.commit()
        return jsonify({'success': True, 'id': abrechnung_id})

# API: Abrechnung löschen
@app.route('/api/abrechnungen/<int:abrechnung_id>', methods=['DELETE'])
def delete_abrechnung(abrechnung_id):
    with get_db() as conn:
        conn.execute('DELETE FROM ausgaben WHERE abrechnung_id = ?', (abrechnung_id,))
        conn.execute('DELETE FROM abrechnungen WHERE id = ?', (abrechnung_id,))
        conn.commit()
        return jsonify({'success': True})

@app.route('/export/excel', methods=['POST'])
def export_excel():
    data = request.json
    meta = data.get('meta', {})
    expenses = data.get('expenses', {})
    
    wb = Workbook()
    ws = wb.active
    ws.title = meta.get('monat', 'Spesen')
    
    # Styles
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill('solid', fgColor='333333')
    title_font = Font(color='333333', size=14, bold=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Header
    ws['A1'] = meta.get('monat', '')
    ws['A1'].font = title_font
    ws['C1'] = meta.get('name', 'Olivier Dobberkau')
    ws['C1'].font = title_font
    ws['F1'] = f"Datum {meta.get('datum', datetime.now().strftime('%d.%m.%y'))}"
    ws['F1'].font = title_font
    ws['H1'] = 'Summen'
    ws['H1'].font = Font(size=14, bold=True)
    
    row = 3
    gesamt = 0
    
    for cat_key, cat_info in CATEGORIES.items():
        cat_expenses = expenses.get(cat_key, [])
        cat_sum = 0
        
        # Category header
        ws.cell(row=row, column=1, value=f"{list(CATEGORIES.keys()).index(cat_key) + 1}. {cat_info['name']}")
        ws.cell(row=row, column=1).fill = header_fill
        ws.cell(row=row, column=1).font = header_font
        
        if cat_key == 'fahrtkosten_kfz':
            headers = ['', 'Datum', 'Fahrstrecke', 'Anlaß', 'km', '0,3', 'Betrag €']
            for i, h in enumerate(headers, 2):
                ws.cell(row=row, column=i, value=h)
                ws.cell(row=row, column=i).fill = header_fill
                ws.cell(row=row, column=i).font = header_font
        
        row += 1
        start_row = row
        
        for exp in cat_expenses:
            if cat_key == 'fahrtkosten_kfz':
                ws.cell(row=row, column=2, value=exp.get('datum', ''))
                ws.cell(row=row, column=3, value=exp.get('fahrstrecke', ''))
                ws.cell(row=row, column=4, value=exp.get('anlass', ''))
                km = float(exp.get('km', 0) or 0)
                ws.cell(row=row, column=5, value=km)
                betrag = km * 0.30
                ws.cell(row=row, column=7, value=betrag)
                cat_sum += betrag
            elif cat_key == 'sonstiges':
                ws.cell(row=row, column=1, value=exp.get('typ', ''))
                ws.cell(row=row, column=2, value=exp.get('datum', ''))
                ws.cell(row=row, column=3, value=exp.get('ort', ''))
                betrag = float(exp.get('betrag', 0) or 0)
                ws.cell(row=row, column=7, value=betrag)
                cat_sum += betrag
            elif cat_key == 'bewirtung':
                ws.cell(row=row, column=2, value=exp.get('datum', ''))
                ws.cell(row=row, column=4, value=exp.get('personen', ''))
                betrag = float(exp.get('betrag', 0) or 0)
                ws.cell(row=row, column=7, value=betrag)
                cat_sum += betrag
            else:
                ws.cell(row=row, column=2, value=exp.get('datum', '') or exp.get('monat', ''))
                ws.cell(row=row, column=3, value=exp.get('beschreibung', ''))
                betrag = float(exp.get('betrag', 0) or 0)
                ws.cell(row=row, column=7, value=betrag)
                cat_sum += betrag
            row += 1
        
        if not cat_expenses:
            row += 1
        
        # Sum for category
        ws.cell(row=row-1 if cat_expenses else row, column=8, value=cat_sum)
        ws.cell(row=row-1 if cat_expenses else row, column=8).number_format = '#,##0.00 €'
        gesamt += cat_sum
        row += 1
    
    # Total
    row += 1
    ws.cell(row=row, column=7, value='GESAMT')
    ws.cell(row=row, column=7).font = Font(bold=True)
    ws.cell(row=row, column=8, value=gesamt)
    ws.cell(row=row, column=8).font = Font(bold=True)
    ws.cell(row=row, column=8).number_format = '#,##0.00 €'
    
    # Bank details
    row += 2
    ws.cell(row=row, column=2, value=f"IBAN: {meta.get('iban', '')}")
    ws.cell(row=row, column=2).font = Font(color='333333')
    if meta.get('bic'):
        ws.cell(row=row, column=5, value=f"BIC: {meta.get('bic', '')}")
        ws.cell(row=row, column=5).font = Font(color='333333')
    ws.cell(row=row, column=7, value=meta.get('name', ''))
    ws.cell(row=row, column=7).font = Font(color='333333')
    
    # Column widths
    widths = [25, 12, 20, 30, 8, 8, 12, 12]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"Spesen_{meta.get('monat', 'Export').replace(' ', '_')}.xlsx"
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)

@app.route('/export/pdf', methods=['POST'])
def export_pdf():
    data = request.json
    meta = data.get('meta', {})
    expenses = data.get('expenses', {})
    
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, 
                           topMargin=15*mm, bottomMargin=15*mm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16,
                                  textColor=colors.HexColor('#333333'), spaceAfter=20)
    
    elements = []
    
    # Title
    title = f"Spesenabrechnung {meta.get('monat', '')} - {meta.get('name', 'Olivier Dobberkau')}"
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f"Datum: {meta.get('datum', datetime.now().strftime('%d.%m.%Y'))}", styles['Normal']))
    elements.append(Spacer(1, 10*mm))
    
    gesamt = 0
    
    for cat_key, cat_info in CATEGORIES.items():
        cat_expenses = expenses.get(cat_key, [])
        if not cat_expenses:
            continue
        
        cat_sum = 0
        elements.append(Paragraph(cat_info['name'], styles['Heading2']))
        
        # Build table data
        if cat_key == 'fahrtkosten_kfz':
            table_data = [['Datum', 'Fahrstrecke', 'Anlaß', 'km', 'Betrag']]
            for exp in cat_expenses:
                km = float(exp.get('km', 0) or 0)
                betrag = km * 0.30
                cat_sum += betrag
                table_data.append([exp.get('datum', ''), exp.get('fahrstrecke', ''), 
                                  exp.get('anlass', ''), f"{km:.0f}", f"{betrag:.2f} €"])
        elif cat_key == 'sonstiges':
            table_data = [['Typ', 'Datum', 'Ort', 'Betrag']]
            for exp in cat_expenses:
                betrag = float(exp.get('betrag', 0) or 0)
                cat_sum += betrag
                # Abkürzungen für lange Begriffe
                typ = exp.get('typ', '')
                if typ == 'Verpflegungspauschale':
                    typ = 'VP'
                table_data.append([typ, exp.get('datum', ''),
                                  exp.get('ort', ''), f"{betrag:.2f} €"])
        elif cat_key == 'bewirtung':
            table_data = [['Datum', 'Bewirtete Personen', 'Betrag']]
            for exp in cat_expenses:
                betrag = float(exp.get('betrag', 0) or 0)
                cat_sum += betrag
                table_data.append([exp.get('datum', ''), exp.get('personen', ''), f"{betrag:.2f} €"])
        else:
            table_data = [['Datum', 'Beschreibung', 'Betrag']]
            for exp in cat_expenses:
                betrag = float(exp.get('betrag', 0) or 0)
                cat_sum += betrag
                table_data.append([exp.get('datum', '') or exp.get('monat', ''), 
                                  exp.get('beschreibung', ''), f"{betrag:.2f} €"])
        
        table_data.append(['', '', 'Summe:', f"{cat_sum:.2f} €"] if len(table_data[0]) == 4
                         else ['', 'Summe:', f"{cat_sum:.2f} €"] if len(table_data[0]) == 3
                         else ['', '', '', 'Summe:', f"{cat_sum:.2f} €"])

        # Volle Seitenbreite: A4 = 210mm, minus 30mm Ränder = 180mm
        page_width = 180*mm
        num_cols = len(table_data[0])
        if cat_key == 'fahrtkosten_kfz':
            # Datum, Fahrstrecke, Anlaß, km, Betrag
            col_widths = [25*mm, 50*mm, 70*mm, 15*mm, 20*mm]
        elif cat_key == 'sonstiges':
            # Typ, Datum, Ort, Betrag
            col_widths = [30*mm, 25*mm, 100*mm, 25*mm]
        elif cat_key == 'bewirtung':
            # Datum, Personen, Betrag
            col_widths = [25*mm, 130*mm, 25*mm]
        else:
            # Datum, Beschreibung, Betrag
            col_widths = [25*mm, 130*mm, 25*mm]
        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 5*mm))
        gesamt += cat_sum
    
    # Total
    elements.append(Spacer(1, 10*mm))
    total_data = [['Gesamtsumme', f"{gesamt:.2f} €"]]
    total_table = Table(total_data, colWidths=[155*mm, 25*mm])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
    ]))
    elements.append(total_table)
    
    # Bank details
    if meta.get('iban'):
        elements.append(Spacer(1, 15*mm))
        bank_parts = [f"IBAN: {meta.get('iban', '')}"]
        if meta.get('bic'):
            bank_parts.append(f"BIC: {meta.get('bic', '')}")
        bank_parts.append(meta.get('name', ''))
        bank_info = " | ".join(bank_parts)
        elements.append(Paragraph(bank_info, styles['Normal']))

    # Abkürzungsverzeichnis
    elements.append(Spacer(1, 10*mm))
    abbr_style = ParagraphStyle('Abbr', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    elements.append(Paragraph("<b>Abkürzungen:</b> VP = Verpflegungspauschale", abbr_style))

    doc.build(elements)
    output.seek(0)
    
    filename = f"Spesen_{meta.get('monat', 'Export').replace(' ', '_')}.pdf"
    return send_file(output, mimetype='application/pdf', as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
