#!/bin/bash
#
# Spesen-App Test Script
# Testet die Installation und simuliert eine Kostenerstattung
#

set -e

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Arbeitsverzeichnis
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Test-Ergebnisse
TESTS_PASSED=0
TESTS_FAILED=0

# Test-Funktion
run_test() {
    local name="$1"
    local command="$2"

    echo -n "  Testing: $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    Spesen-App Tests                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# 1. Umgebungs-Tests
# ============================================================================
echo -e "${YELLOW}[1/5] Umgebungs-Tests${NC}"

run_test "Docker verfügbar" "command -v docker"
run_test "Docker Compose verfügbar" "docker compose version"
run_test ".env Datei existiert" "[ -f .env ]"
run_test "ANTHROPIC_API_KEY gesetzt" "grep -q '^ANTHROPIC_API_KEY=sk-ant' .env"
run_test "ENCRYPTION_KEY gesetzt" "grep -q '^ENCRYPTION_KEY=' .env && ! grep -q '^ENCRYPTION_KEY=$' .env"

# ============================================================================
# 2. Ordnerstruktur-Tests
# ============================================================================
echo -e "\n${YELLOW}[2/5] Ordnerstruktur-Tests${NC}"

run_test "data/ existiert" "[ -d data ]"
run_test "exports/ existiert" "[ -d exports ]"
run_test "belege/inbox/ existiert" "[ -d belege/inbox ]"
run_test "belege/archiv/ existiert" "[ -d belege/archiv ]"

# ============================================================================
# 3. Container-Tests
# ============================================================================
echo -e "\n${YELLOW}[3/5] Container-Tests${NC}"

# Prüfen ob Container läuft
if docker compose ps --format json 2>/dev/null | grep -q "spesen-app"; then
    CONTAINER_RUNNING=true
    run_test "Container läuft" "true"
else
    CONTAINER_RUNNING=false
    echo -e "  ${YELLOW}○${NC} Container nicht gestartet - starte für Tests..."
    docker compose up -d --quiet-pull 2>/dev/null || true
    sleep 5

    if docker compose ps --format json 2>/dev/null | grep -q "spesen-app"; then
        CONTAINER_RUNNING=true
        run_test "Container gestartet" "true"
    else
        run_test "Container starten" "false"
    fi
fi

if [ "$CONTAINER_RUNNING" = true ]; then
    run_test "Health-Check" "curl -sf http://localhost/health"
    run_test "Web-UI erreichbar" "curl -sf http://localhost/ | grep -q 'Spesenabrechnung'"
fi

# ============================================================================
# 4. API-Tests
# ============================================================================
echo -e "\n${YELLOW}[4/5] API-Tests${NC}"

if [ "$CONTAINER_RUNNING" = true ]; then
    run_test "GET /api/abrechnungen" "curl -sf http://localhost/api/abrechnungen"
    run_test "GET /api/personen" "curl -sf http://localhost/api/personen"

    # Test: Person hinzufügen und löschen
    echo -n "  Testing: POST /api/personen... "
    PERSON_RESPONSE=$(curl -sf -X POST http://localhost/api/personen \
        -H "Content-Type: application/json" \
        -d '{"name": "Test Person", "firma": "Test GmbH"}' 2>/dev/null)
    if echo "$PERSON_RESPONSE" | grep -q '"success"'; then
        PERSON_ID=$(echo "$PERSON_RESPONSE" | grep -o '"id":[0-9]*' | cut -d: -f2)
        echo -e "${GREEN}OK${NC} (ID: $PERSON_ID)"
        ((TESTS_PASSED++))

        # Aufräumen
        curl -sf -X DELETE "http://localhost/api/personen/$PERSON_ID" > /dev/null 2>&1
    else
        echo -e "${RED}FAILED${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "  ${YELLOW}○${NC} API-Tests übersprungen (Container nicht verfügbar)"
fi

# ============================================================================
# 5. Simulations-Test (Dry-Run)
# ============================================================================
echo -e "\n${YELLOW}[5/5] Simulations-Test${NC}"

# Test-Beleg erstellen (simuliert)
TEST_BELEG_DIR="$SCRIPT_DIR/belege/inbox"
TEST_BELEG="$TEST_BELEG_DIR/test_beleg_$(date +%s).txt"

if [ "$CONTAINER_RUNNING" = true ]; then
    echo -e "  ${BLUE}Erstelle Test-Beleg...${NC}"

    # Einfachen Text-Beleg erstellen (wird nicht von KI verarbeitet, nur für Struktur-Test)
    cat > "$TEST_BELEG" << 'EOF'
TESTBELEG - NICHT FÜR PRODUKTION

Tankstelle Mustermann
Musterstraße 123
12345 Musterstadt

Datum: 01.12.2025
Uhrzeit: 14:30

Super E10    45,00 L
Preis/L:      1,789 EUR
─────────────────────────
SUMME:       80,51 EUR

Bezahlt: EC-Karte

Vielen Dank für Ihren Einkauf!

[TEST-DATEI - WIRD AUTOMATISCH GELÖSCHT]
EOF

    echo -e "  ${GREEN}✓${NC} Test-Beleg erstellt: $(basename "$TEST_BELEG")"

    # CLI Dry-Run Test (ohne API-Aufruf, nur Struktur)
    echo -e "  ${BLUE}Teste CLI-Struktur (ohne KI-Verarbeitung)...${NC}"

    if docker compose exec -T app python -c "
import sys
sys.path.insert(0, '/app')
from cli import *

# Test: Kann Module importiert werden?
print('  ✓ CLI-Module geladen')

# Test: Kategorien definiert?
assert len(CATEGORIES) > 0, 'Keine Kategorien definiert'
print(f'  ✓ {len(CATEGORIES)} Kategorien definiert')

# Test: Währungen definiert?
assert len(FALLBACK_EXCHANGE_RATES) > 0, 'Keine Fallback-Kurse definiert'
print(f'  ✓ {len(FALLBACK_EXCHANGE_RATES)} Währungs-Fallback-Kurse')

print('  ✓ CLI-Struktur OK')
" 2>/dev/null; then
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗${NC} CLI-Struktur fehlerhaft"
        ((TESTS_FAILED++))
    fi

    # Test-Beleg aufräumen
    rm -f "$TEST_BELEG"
    echo -e "  ${GREEN}✓${NC} Test-Beleg aufgeräumt"
else
    echo -e "  ${YELLOW}○${NC} Simulations-Test übersprungen (Container nicht verfügbar)"
fi

# ============================================================================
# Zusammenfassung
# ============================================================================
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                      Testergebnisse                          ${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Bestanden:${NC} $TESTS_PASSED"
echo -e "  ${RED}Fehlgeschlagen:${NC} $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Alle Tests erfolgreich bestanden!               ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              Einige Tests sind fehlgeschlagen!               ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Tipps zur Fehlerbehebung:"
    echo -e "  - Führen Sie ${YELLOW}./setup.sh${NC} aus"
    echo -e "  - Prüfen Sie die .env Datei"
    echo -e "  - Starten Sie mit ${YELLOW}docker compose up -d${NC}"
    exit 1
fi
