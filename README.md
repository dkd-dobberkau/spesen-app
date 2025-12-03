# Spesen-App

Automatische Spesenabrechnung mit KI-gestützter Belegerkennung.

## Features

- **Web-App**: Flask-basierte Oberfläche zur Verwaltung von Spesenabrechnungen
- **CLI-Tool**: Batch-Verarbeitung von Belegen aus einem Ordner
- **KI-Erkennung**: Claude AI analysiert Belege und extrahiert Daten automatisch
- **Kategorien**: Fahrtkosten, Bewirtung, Telefonkosten, Uber/Taxi, etc.
- **Export**: Excel und PDF
- **Caching**: Bereits verarbeitete Belege werden gecacht
- **Production-Ready**: Gunicorn WSGI-Server + Traefik Reverse Proxy

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

### Mit Docker (Entwicklung)

```bash
# .env erstellen
cp .env.example .env
# ANTHROPIC_API_KEY in .env eintragen

# Einfaches Setup ohne Reverse Proxy
docker compose -f docker-compose.simple.yml up -d

# Web-App: http://localhost:5001

# CLI im Container ausführen
docker compose exec app python cli.py /data/belege --name "Name" --monat "Dez 2025" -v
```

### Mit Docker (Production)

```bash
# .env erstellen mit Production-Einstellungen
cp .env.example .env

# Vollständiges Setup mit Traefik Reverse Proxy
docker compose up -d

# Web-App: http://localhost (Port 80)
# Traefik Dashboard: http://localhost:8080

# Für HTTPS: Zeilen in docker-compose.yml auskommentieren
# und Domain + E-Mail anpassen
```

## Docker-Konfigurationen

| Datei | Beschreibung |
|-------|--------------|
| `docker-compose.simple.yml` | Einfaches Setup ohne Reverse Proxy (Port 5001) |
| `docker-compose.yml` | Production mit Traefik, HTTPS-ready |

### Production-Features

- **Gunicorn** WSGI-Server (multi-worker)
- **Traefik** Reverse Proxy
- **Let's Encrypt** HTTPS (konfigurierbar)
- **Health Checks** für Container-Orchestrierung
- **Logging** in `/app/logs/`
- **Non-root User** im Container

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

# Optional für Production
GUNICORN_WORKERS=4
LOG_LEVEL=info
```

### Verpflegungspauschalen

Die App enthält die deutschen Verpflegungspauschalen 2025 für verschiedene Länder.

## Projektstruktur

```
spesen-app/
├── app.py                    # Flask Web-App
├── cli.py                    # CLI-Tool
├── gunicorn.conf.py          # Gunicorn WSGI-Config
├── templates/
│   └── index.html            # Web-UI
├── requirements.txt          # pip Dependencies
├── pyproject.toml            # uv/pip Projekt-Config
├── Dockerfile                # Multi-stage Docker Image
├── docker-compose.yml        # Production mit Traefik
├── docker-compose.simple.yml # Entwicklung ohne Proxy
├── .env.example              # Beispiel-Konfiguration
├── .gitignore
└── README.md
```

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

## Datenbank

SQLite-Datenbank (`spesen.db`) mit folgenden Tabellen:

- `abrechnungen`: Spesenabrechungen (Name, Monat, Datum)
- `ausgaben`: Einzelne Ausgaben pro Abrechnung
- `einstellungen`: Benutzereinstellungen (Name, IBAN verschlüsselt)

## Sicherheit

- IBAN/BIC werden mit Fernet (AES) verschlüsselt gespeichert
- `secret.key` wird automatisch generiert und sollte nicht committed werden
- `.env` enthält API-Keys und ist in `.gitignore`
- Non-root User im Docker-Container
- Gunicorn mit Request-Limits

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
