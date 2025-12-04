#!/bin/bash
#
# Spesen-App Setup Script
# Erstellt alle notwendigen Ordner und konfiguriert die Umgebung
#

set -e

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    Spesen-App Setup                          ║"
echo "║     Automatische Spesenabrechnung mit KI-Belegerkennung      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Arbeitsverzeichnis
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Ordner erstellen
echo -e "${YELLOW}[1/4] Erstelle Ordnerstruktur...${NC}"

DIRS=(
    "data"
    "exports"
    "logs"
    "belege/inbox"
    "belege/archiv"
    "traefik/letsencrypt"
    "traefik/logs"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "  ${GREEN}✓${NC} $dir erstellt"
    else
        echo -e "  ${BLUE}○${NC} $dir existiert bereits"
    fi
done

# 2. .env Datei erstellen/aktualisieren
echo -e "\n${YELLOW}[2/4] Konfiguriere Umgebungsvariablen...${NC}"

if [ -f ".env" ]; then
    echo -e "  ${BLUE}○${NC} .env existiert bereits"

    # Prüfen ob ENCRYPTION_KEY fehlt
    if ! grep -q "^ENCRYPTION_KEY=" .env; then
        echo -e "  ${YELLOW}!${NC} ENCRYPTION_KEY fehlt - wird hinzugefügt"
        ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "")
        if [ -n "$ENCRYPTION_KEY" ]; then
            echo "" >> .env
            echo "# Encryption Key für sensible Daten (IBAN, BIC)" >> .env
            echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env
            echo -e "  ${GREEN}✓${NC} ENCRYPTION_KEY generiert und hinzugefügt"
        fi
    fi

    # Prüfen ob ANTHROPIC_API_KEY gesetzt ist
    if grep -q "^ANTHROPIC_API_KEY=$" .env || grep -q "^ANTHROPIC_API_KEY=sk-ant-api03-\.\.\.$" .env; then
        echo -e "  ${RED}!${NC} ANTHROPIC_API_KEY ist nicht konfiguriert"
        echo ""
        read -p "  Anthropic API Key eingeben (oder Enter zum Überspringen): " API_KEY
        if [ -n "$API_KEY" ]; then
            sed -i.bak "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$API_KEY|" .env && rm -f .env.bak
            echo -e "  ${GREEN}✓${NC} ANTHROPIC_API_KEY aktualisiert"
        fi
    else
        echo -e "  ${GREEN}✓${NC} ANTHROPIC_API_KEY ist konfiguriert"
    fi
else
    echo -e "  ${YELLOW}!${NC} Erstelle neue .env Datei"

    # API Key abfragen
    echo ""
    echo -e "  ${BLUE}Anthropic API Key benötigt für KI-Belegerkennung${NC}"
    echo -e "  Holen Sie sich einen Key unter: https://console.anthropic.com/settings/keys"
    echo ""
    read -p "  Anthropic API Key eingeben: " API_KEY

    # Encryption Key generieren
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "GENERATE_ME")

    cat > .env << EOF
# Anthropic API Key für Beleg-Erkennung
ANTHROPIC_API_KEY=${API_KEY:-sk-ant-api03-...}

# Encryption Key für sensible Daten (IBAN, BIC)
ENCRYPTION_KEY=$ENCRYPTION_KEY

# Optional: Weitere Einstellungen
# GUNICORN_WORKERS=4
# LOG_LEVEL=info
EOF

    echo -e "  ${GREEN}✓${NC} .env erstellt"

    if [ -z "$API_KEY" ]; then
        echo -e "  ${RED}!${NC} Bitte ANTHROPIC_API_KEY in .env nachtragen!"
    fi
fi

# 3. Dependencies prüfen
echo -e "\n${YELLOW}[3/4] Prüfe Abhängigkeiten...${NC}"

# Docker prüfen
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo -e "  ${GREEN}✓${NC} Docker $DOCKER_VERSION"
else
    echo -e "  ${RED}✗${NC} Docker nicht gefunden - bitte installieren: https://docs.docker.com/get-docker/"
fi

# Docker Compose prüfen
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short)
    echo -e "  ${GREEN}✓${NC} Docker Compose $COMPOSE_VERSION"
else
    echo -e "  ${RED}✗${NC} Docker Compose nicht gefunden"
fi

# Python prüfen (optional für lokale Entwicklung)
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "  ${GREEN}✓${NC} Python $PYTHON_VERSION (optional, für lokale Entwicklung)"
else
    echo -e "  ${BLUE}○${NC} Python nicht gefunden (nur für lokale Entwicklung benötigt)"
fi

# 4. Zusammenfassung
echo -e "\n${YELLOW}[4/4] Setup abgeschlossen!${NC}"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Nächste Schritte                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  1. ${BLUE}App starten:${NC}"
echo -e "     docker compose up -d"
echo ""
echo -e "  2. ${BLUE}Web-App öffnen:${NC}"
echo -e "     http://localhost"
echo ""
echo -e "  3. ${BLUE}Belege verarbeiten:${NC}"
echo -e "     - Belege in ${YELLOW}belege/inbox/${NC} ablegen"
echo -e "     - CLI ausführen:"
echo -e "       docker compose exec app python cli.py /app/belege/inbox \\"
echo -e "           --name \"Max Mustermann\" --monat \"Dez 2025\" --archive"
echo ""
echo -e "  4. ${BLUE}Tests ausführen:${NC}"
echo -e "     ./test.sh"
echo ""

# Prüfen ob API Key fehlt
if [ -f ".env" ] && (grep -q "^ANTHROPIC_API_KEY=$" .env || grep -q "^ANTHROPIC_API_KEY=sk-ant-api03-\.\.\.$" .env); then
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  WARNUNG: ANTHROPIC_API_KEY ist nicht konfiguriert!          ║${NC}"
    echo -e "${RED}║  Bitte in .env Datei eintragen.                              ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
fi
