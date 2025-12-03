# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spesen-App is a German expense tracking application with AI-powered receipt recognition using Claude Vision. It provides both a Flask web interface and a CLI tool for batch processing receipts.

## Common Commands

### Development

```bash
# Local development (requires Python 3.11+, tesseract, poppler)
python app.py                    # Start Flask dev server on port 5000
python cli.py /path/to/receipts --name "Name" --monat "Nov 2025"

# Using the CLI wrapper (auto-selects Docker or local)
./spesen scan /path/to/receipts --name "Name" --monat "Nov 2025"
./spesen sort /path/to/receipts --dry-run
```

### Docker

```bash
# Simple setup (no reverse proxy)
docker compose -f docker-compose.simple.yml up -d    # Port 5001

# Production setup (with Traefik)
docker compose up -d                                  # Port 80

# Run CLI in container
docker compose exec app python cli.py /data/belege --name "Name" --monat "Nov 2025"

# Rebuild after code changes
docker compose build && docker compose up -d
```

### Testing

```bash
uv run pytest           # With uv
python -m pytest        # Without uv
```

## Architecture

### Core Components

- **`app.py`** - Flask web application with REST API
  - Routes: `/`, `/health`, `/api/abrechnungen`, `/api/einstellungen`, `/api/parse-beleg`, `/export/*`
  - Uses Claude Vision API for receipt analysis
  - SQLite database (`data/spesen.db`) for persistence

- **`cli.py`** - Command-line tool for batch processing
  - Scans folders for receipts (PDF, JPG, PNG)
  - MD5-based caching to avoid re-processing
  - Automatic currency conversion (EZB rates)
  - Exports to Excel, PDF, JSON
  - Saves to same SQLite database as web app

- **`sort_belege.py`** - Receipt sorting utility
  - Extracts dates from filenames/metadata
  - Organizes receipts into monthly folders
  - MD5-based duplicate detection

- **`spesen`** - Shell wrapper script
  - Auto-detects Docker vs local environment
  - Converts host paths to container paths

### Data Flow

1. Receipt image/PDF → OCR (Tesseract) → Text extraction
2. Text + Image → Claude Vision API → Structured JSON
3. JSON → SQLite database (`abrechnungen` + `ausgaben` tables)
4. Database → Excel/PDF export

### Database Schema

```
abrechnungen (id, name, monat, datum, konto, blz, created_at, updated_at)
ausgaben (id, abrechnung_id, kategorie, daten[JSON])
einstellungen (id, name, iban_encrypted, bic_encrypted, bank, unterschrift_base64)
personen (id, name, firma)
```

### Docker Volumes

- `./data:/app/data` - SQLite database, cache
- `./exports:/app/exports` - Generated reports
- `./logs:/app/logs` - Gunicorn logs
- `~/Documents/Scans:/data/belege:ro` - Receipt source folder
- `~/Desktop/Belege:/data/uber:ro` - Additional receipt folder

## Key Patterns

### Receipt Categories

```python
CATEGORIES = {
    'fahrtkosten_kfz': 'Fuel receipts',
    'fahrtkosten_pauschale': 'Public transport tickets',
    'bewirtung': 'Restaurant/entertainment',
    'telefonkosten': 'Phone/prepaid',
    'sonstiges': 'Uber, Taxi, Parking, Hotel'
}
```

### Currency Conversion

CLI fetches live exchange rates from ECB (European Central Bank) API. Fallback rates are hardcoded for offline use. Foreign currency amounts are converted to EUR and original amount noted in description.

### Caching

Both web app and CLI share the same cache file (`data/.beleg_cache.json`). Cache key is MD5 hash of file content. Use `--no-cache` to force re-processing.

## Environment Variables

```
ANTHROPIC_API_KEY     # Required - Claude API key
DATA_DIR              # Optional - Default: ./data
GUNICORN_WORKERS      # Optional - Default: CPU*2+1
LOG_LEVEL             # Optional - Default: info
```

## Language

The application UI, CLI output, and database content are in German. Code comments and variable names are mixed German/English.
