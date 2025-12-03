#!/usr/bin/env python3
"""
Migration Script: Verknüpft bestehende Ausgaben mit file_hash aus dem Cache.

Matching-Strategie:
1. Datum + Betrag müssen übereinstimmen
2. Bei mehreren Matches: Beschreibung/Anbieter vergleichen
"""

import json
import os
import sqlite3
from difflib import SequenceMatcher

DATA_DIR = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(__file__), 'data'))
DATABASE = os.path.join(DATA_DIR, 'spesen.db')
CACHE_FILE = os.path.join(DATA_DIR, '.beleg_cache.json')


def similarity(a, b):
    """Berechnet Ähnlichkeit zwischen zwei Strings (0-1)."""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def normalize_betrag(betrag):
    """Normalisiert Betrag zu float mit 2 Dezimalstellen."""
    if isinstance(betrag, str):
        betrag = betrag.replace(',', '.').replace('€', '').strip()
    try:
        return round(float(betrag), 2)
    except (ValueError, TypeError):
        return None


def normalize_datum(datum):
    """Normalisiert Datum zu TT.MM.JJJJ Format."""
    if not datum:
        return None
    datum = str(datum).strip()
    # Bereits im richtigen Format?
    if len(datum) == 10 and datum[2] == '.' and datum[5] == '.':
        return datum
    # Format TT.MM.JJ -> TT.MM.20JJ
    if len(datum) == 8 and datum[2] == '.' and datum[5] == '.':
        return datum[:6] + '20' + datum[6:]
    return datum


def main():
    # Cache laden
    if not os.path.exists(CACHE_FILE):
        print(f"❌ Cache-Datei nicht gefunden: {CACHE_FILE}")
        return

    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)

    print(f"📦 Cache geladen: {len(cache)} Einträge")

    # Cache-Index nach Datum+Betrag aufbauen
    cache_index = {}  # {(datum, betrag): [(file_hash, cache_entry), ...]}
    for file_hash, entry in cache.items():
        datum = normalize_datum(entry.get('datum'))
        betrag = normalize_betrag(entry.get('betrag'))
        if datum and betrag is not None:
            key = (datum, betrag)
            if key not in cache_index:
                cache_index[key] = []
            cache_index[key].append((file_hash, entry))

    print(f"🔍 Index erstellt: {len(cache_index)} Datum+Betrag Kombinationen")

    # Datenbank öffnen
    if not os.path.exists(DATABASE):
        print(f"❌ Datenbank nicht gefunden: {DATABASE}")
        return

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Alle Ausgaben laden
    cursor.execute('SELECT id, kategorie, daten FROM ausgaben')
    ausgaben = cursor.fetchall()
    print(f"📊 Ausgaben geladen: {len(ausgaben)} Einträge")

    updated = 0
    skipped = 0
    not_found = 0

    for row in ausgaben:
        ausgabe_id = row['id']
        kategorie = row['kategorie']
        daten = json.loads(row['daten'])

        # Bereits verknüpft?
        if daten.get('file_hash'):
            skipped += 1
            continue

        # Datum und Betrag extrahieren
        datum = normalize_datum(daten.get('datum') or daten.get('monat'))

        # Betrag je nach Kategorie
        if kategorie == 'fahrtkosten_kfz':
            km = float(daten.get('km', 0) or 0)
            betrag = round(km * 0.30, 2)
        else:
            betrag = normalize_betrag(daten.get('betrag'))

        if not datum or betrag is None:
            not_found += 1
            continue

        # Im Cache suchen
        key = (datum, betrag)
        matches = cache_index.get(key, [])

        if not matches:
            not_found += 1
            continue

        # Besten Match finden
        best_match = None
        best_score = 0

        # Text zum Vergleichen aus DB-Eintrag
        db_text = ' '.join(filter(None, [
            daten.get('beschreibung', ''),
            daten.get('personen', ''),
            daten.get('ort', ''),
            daten.get('fahrstrecke', ''),
            daten.get('anlass', '')
        ]))

        for file_hash, cache_entry in matches:
            # Text zum Vergleichen aus Cache
            cache_text = ' '.join(filter(None, [
                cache_entry.get('beschreibung', ''),
                cache_entry.get('anbieter', ''),
                cache_entry.get('stadt', '')
            ]))

            score = similarity(db_text, cache_text)

            # Kategorie-Match gibt Bonus
            if cache_entry.get('kategorie') == kategorie:
                score += 0.3

            if score > best_score:
                best_score = score
                best_match = file_hash

        if best_match:
            # Update durchführen
            daten['file_hash'] = best_match
            cursor.execute(
                'UPDATE ausgaben SET daten = ? WHERE id = ?',
                (json.dumps(daten), ausgabe_id)
            )
            updated += 1

            # Details ausgeben
            cache_entry = cache[best_match]
            print(f"  ✅ ID {ausgabe_id}: {datum} | {betrag}€ -> {cache_entry.get('datei', 'unbekannt')} (Score: {best_score:.2f})")
        else:
            not_found += 1

    conn.commit()
    conn.close()

    print(f"\n📈 Zusammenfassung:")
    print(f"   ✅ Verknüpft: {updated}")
    print(f"   ⏭️  Übersprungen (bereits verknüpft): {skipped}")
    print(f"   ❌ Nicht gefunden: {not_found}")


if __name__ == '__main__':
    main()
