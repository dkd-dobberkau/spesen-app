# Spesen-App

Automatische Spesenabrechnung mit KI-gestützter Belegerkennung.

## Features

- **Web-App**: Flask-basierte Oberfläche zur Verwaltung von Spesenabrechnungen
- **CLI-Tool**: Batch-Verarbeitung von Belegen aus einem Ordner
- **KI-Erkennung**: Claude AI analysiert Belege und extrahiert Daten automatisch
- **Kategorien**: Fahrtkosten, Bewirtung, Telefonkosten, Uber/Taxi, etc.
- **Export**: Excel und PDF
- **Caching**: Bereits verarbeitete Belege werden gecacht

## Schnellstart

### Mit uv (empfohlen)

```bash
# uv installieren (falls nicht vorhanden)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Projekt einrichten
uv sync

# .env erstellen
cp .env.example .env
# ANTHROPIC_API_KEY in .env eintragen

# Web-App starten
uv run python app.py

# CLI verwenden
uv run python cli.py /pfad/zu/belegen --name "Max Mustermann" --monat "Dez 2025" --save-db -v
```

### Mit pip

```bash
# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# System-Dependencies (für OCR)
# macOS:
brew install tesseract tesseract-lang poppler

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-deu poppler-utils

# .env erstellen
cp .env.example .env
# ANTHROPIC_API_KEY in .env eintragen

# Web-App starten
python app.py
```

### Mit Docker

```bash
# .env erstellen
cp .env.example .env
# ANTHROPIC_API_KEY in .env eintragen

# Container starten
docker compose up -d

# Web-App: http://localhost:5000

# CLI im Container ausführen
docker compose exec app python cli.py /data/belege --name "Name" --monat "Dez 2025" -v
```

## CLI-Verwendung

```bash
# Belege verarbeiten und Excel/PDF exportieren
python cli.py /pfad/zu/belegen --name "Max Mustermann" --monat "Dez 2025"

# Mit Datenbank-Speicherung (für Web-App sichtbar)
python cli.py /pfad/zu/belegen --name "Max Mustermann" --monat "Dez 2025" --save-db

# Ausführliche Ausgabe
python cli.py /pfad/zu/belegen -n "Max Mustermann" -m "Dez 2025" -s -v

# Cache ignorieren (alle Belege neu verarbeiten)
python cli.py /pfad/zu/belegen --no-cache

# Nur JSON-Export
python cli.py /pfad/zu/belegen --format json
```

### CLI-Optionen

| Option | Kurz | Beschreibung |
|--------|------|--------------|
| `--name` | `-n` | Name für die Abrechnung |
| `--monat` | `-m` | Monat/Zeitraum (z.B. "Dez 2025") |
| `--output` | `-o` | Ausgabedatei |
| `--format` | `-f` | Format: excel, pdf, both, json |
| `--save-db` | `-s` | In Datenbank speichern |
| `--no-cache` | | Cache ignorieren |
| `--verbose` | `-v` | Ausführliche Ausgabe |

## Unterstützte Belegtypen

- **Fahrtkosten KFZ**: Tankbelege (Benzin, Diesel)
- **Fahrtkostenpauschale**: ÖPNV-Tickets, Bahnfahrkarten
- **Bewirtung**: Restaurant, Bar, Café
- **Uber/Taxi**: Automatische Stadt- und km-Erkennung
- **Telefonkosten**: Prepaid-Aufladungen, Mobilfunk
- **Sonstiges**: Parken, Hotel, etc.

## Konfiguration

### Umgebungsvariablen (.env)

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Verpflegungspauschalen

Die App enthält die deutschen Verpflegungspauschalen 2025 für verschiedene Länder.

## Projektstruktur

```
spesen-app/
├── app.py              # Flask Web-App
├── cli.py              # CLI-Tool
├── templates/
│   └── index.html      # Web-UI
├── requirements.txt    # pip Dependencies
├── pyproject.toml      # uv/pip Projekt-Config
├── Dockerfile          # Docker Image
├── docker-compose.yml  # Docker Compose
├── .env.example        # Beispiel-Konfiguration
├── .gitignore
└── README.md
```

## Datenbank

SQLite-Datenbank (`spesen.db`) mit folgenden Tabellen:

- `abrechnungen`: Spesenabrechungen (Name, Monat, Datum)
- `ausgaben`: Einzelne Ausgaben pro Abrechnung
- `einstellungen`: Benutzereinstellungen (Name, IBAN verschlüsselt)

## Sicherheit

- IBAN/BIC werden mit Fernet (AES) verschlüsselt gespeichert
- `secret.key` wird automatisch generiert und sollte nicht committed werden
- `.env` enthält API-Keys und ist in `.gitignore`

## Entwicklung

```bash
# Mit uv
uv sync --dev
uv run pytest

# Ohne uv
pip install -r requirements.txt
python -m pytest
```

## Lizenz

MIT
