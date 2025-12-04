# Spesen-App

Automatische Spesenabrechnung mit KI-gestützter Belegerkennung.

## Features

- **Web-App**: Flask-basierte Oberfläche zur Verwaltung von Spesenabrechnungen
- **CLI-Tool**: Batch-Verarbeitung von Belegen aus einem Ordner
- **KI-Erkennung**: Claude AI analysiert Belege und extrahiert Daten automatisch
- **Währungsumrechnung**: Automatische Konvertierung von Fremdwährungen (EZB-Kurse)
- **Kategorien**: Fahrtkosten, Bewirtung, Telefonkosten, Uber/Taxi, etc.
- **Export**: Excel, PDF und ZIP-Bundle (organisiert nach Jahr/Monat)
- **Inbox/Archiv**: Automatische Archivierung verarbeiteter Belege
- **Personen-Verwaltung**: Kontakte mit VCF-Import für Bewirtungsbelege
- **Caching**: Bereits verarbeitete Belege werden gecacht (MD5-basiert)
- **Production-Ready**: Gunicorn WSGI-Server + Traefik Reverse Proxy

## Schnellstart

### Mit Docker (empfohlen)

```bash
# Setup-Script ausführen (erstellt Ordner, .env, Keys)
./setup.sh

# Container starten
docker compose up -d

# Tests ausführen
./test.sh

# Web-App: http://localhost (Port 80)

# Belege verarbeiten (mit Archivierung)
docker compose exec app python cli.py /app/belege/inbox \
    --name "Max Mustermann" --monat "Dez 2025" --archive
```

### Manuelle Installation

```bash
# .env erstellen
cp .env.example .env
# ANTHROPIC_API_KEY in .env eintragen

# Container starten
docker compose up -d
```

### Mit uv (lokal)

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
uv run python cli.py belege/inbox --name "Max Mustermann" --monat "Dez 2025" --archive
```

### Mit pip (lokal)

```bash
# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

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

## Ordnerstruktur

```
spesen-app/
├── belege/
│   ├── inbox/              # Neue Belege hierher legen
│   └── archiv/             # Automatisch nach Verarbeitung
│       └── 2025/
│           └── 12_Dezember/
├── exports/                # Generierte Abrechnungen
│   └── 2025/
│       └── 12_Dezember/
│           ├── Spesen_Dez_2025.xlsx
│           ├── Spesen_Dez_2025.pdf
│           └── bewirtungsbelege/
├── data/                   # SQLite DB, Cache
└── logs/                   # Gunicorn Logs
```

> **Hinweis für Docker:** Diese Ordner werden über Volume-Mounts auf den Host gemappt (siehe `docker-compose.yml`). Dadurch bleiben alle Daten auch nach einem Container-Neustart oder -Update erhalten. Alternativ können die Volumes auch in einem persistenten Daten-Container oder Docker-Volume gespeichert werden.

## CLI-Verwendung

### Inbox/Archiv Workflow (empfohlen)

```bash
# 1. Belege in inbox ablegen
cp *.pdf belege/inbox/

# 2. Verarbeiten und automatisch archivieren
docker compose exec app python cli.py /app/belege/inbox \
    --name "Max Mustermann" --monat "Dez 2025" --archive

# → Belege werden nach belege/archiv/2025/12_Dezember/ verschoben
# → Export in exports/2025/12_Dezember/
```

### Klassische Verwendung

```bash
# Belege verarbeiten (speichert automatisch in DB)
python cli.py /pfad/zu/belegen --name "Max Mustermann" --monat "Dez 2025"

# Ohne Datenbank-Speicherung
python cli.py /pfad/zu/belegen --monat "Dez 2025" --no-db

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
| `--output` | `-o` | Ausgabedatei (überschreibt auto-Pfad) |
| `--format` | `-f` | Format: excel, pdf, both, json |
| `--archive` | `-a` | Belege nach Verarbeitung archivieren |
| `--no-db` | | NICHT in Datenbank speichern |
| `--no-cache` | | Cache ignorieren |
| `--verbose` | `-v` | Ausführliche Ausgabe |

### Shell-Wrapper

```bash
# Automatische Docker/Local-Erkennung
./spesen scan belege/inbox --monat "Dez 2025" --archive
./spesen sort /pfad/zu/belegen --dry-run
```

## Docker-Konfigurationen

| Datei | Beschreibung |
|-------|--------------|
| `docker-compose.yml` | Production mit Traefik, HTTPS-ready |
| `docker-compose.simple.yml` | Einfaches Setup ohne Reverse Proxy (Port 5001) |

### Production-Features

- **Gunicorn** WSGI-Server (multi-worker)
- **Traefik** Reverse Proxy
- **Let's Encrypt** HTTPS (konfigurierbar)
- **Health Checks** für Container-Orchestrierung
- **Logging** in `/app/logs/`
- **Non-root User** im Container

## Unterstützte Belegtypen

- **Fahrtkosten KFZ**: Tankbelege (Benzin, Diesel)
- **Fahrtkosten ÖPNV**: ÖPNV-Tickets, Bahnfahrkarten
- **Bewirtung**: Restaurant, Bar, Café (+ Bewirtungsbeleg-PDF)
- **Uber/Taxi**: Automatische Stadt- und km-Erkennung
- **Telefonkosten**: Prepaid-Aufladungen, Mobilfunk
- **Sonstiges**: Parken, Hotel, etc.

## Währungsumrechnung

Fremdwährungen (CHF, DKK, USD, etc.) werden automatisch nach EUR konvertiert:
- Aktuelle Kurse von der EZB (European Central Bank)
- Fallback-Kurse wenn offline
- Original-Betrag wird in der Beschreibung vermerkt

## Konfiguration

### Umgebungsvariablen (.env)

```env
# Erforderlich
ANTHROPIC_API_KEY=sk-ant-api03-...

# Encryption Key für sensible Daten (IBAN, BIC)
# Generieren: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=

# Optional
GUNICORN_WORKERS=4
LOG_LEVEL=info
DATA_DIR=/app/data
EXPORTS_DIR=/app/exports
ARCHIV_DIR=/app/belege/archiv
```

### Verpflegungspauschalen

Die App enthält die deutschen Verpflegungspauschalen 2025 für verschiedene Länder.

## API-Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/` | GET | Web-UI |
| `/health` | GET | Health Check (für Container) |
| `/api/abrechnungen` | GET/POST | Abrechnungen verwalten |
| `/api/einstellungen` | GET/POST | Einstellungen |
| `/api/parse-beleg` | POST | Beleg mit KI analysieren |
| `/export/excel` | POST | Excel-Export |
| `/export/pdf` | POST | PDF-Export |
| `/export/zip` | POST | ZIP-Bundle (Excel + PDF + Belege) |
| `/export/bewirtungsbeleg` | POST | Bewirtungsbeleg nach §4 EStG |
| `/api/personen` | GET/POST | Personen verwalten |
| `/api/personen/import-vcf` | POST | VCF-Kontakte importieren |
| `/api/beleg/<hash>` | GET | Original-Beleg abrufen |

## Datenbank

SQLite-Datenbank (`data/spesen.db`) mit folgenden Tabellen:

- `abrechnungen`: Spesenabrechungen (Name, Monat, Datum)
- `ausgaben`: Einzelne Ausgaben pro Abrechnung (JSON-Daten)
- `einstellungen`: Benutzereinstellungen (Name, IBAN verschlüsselt)
- `personen`: Gespeicherte Personen für Bewirtungsbelege

## Sicherheit

- IBAN/BIC werden mit Fernet (AES) verschlüsselt gespeichert
- `ENCRYPTION_KEY` in `.env` speichern für Persistenz nach Redeployment
- Fallback auf `data/secret.key` für Abwärtskompatibilität
- `.env` enthält API-Keys und ist in `.gitignore`
- Non-root User im Docker-Container
- Gunicorn mit Request-Limits

## Lizenz

MIT
