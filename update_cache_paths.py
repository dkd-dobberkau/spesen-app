#!/usr/bin/env python3
"""
Aktualisiert den Cache mit vollständigen Dateipfaden.
Sucht die Dateien in bekannten Ordnern und ergänzt datei_pfad.

Pfad-Mapping für Docker:
  ~/Documents/Scans -> /data/scans
  ~/Desktop/Belege  -> /data/belege
"""

import json
import os
from pathlib import Path

DATA_DIR = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(__file__), 'data'))
CACHE_FILE = os.path.join(DATA_DIR, '.beleg_cache.json')

# Bekannte Beleg-Ordner (Host-Pfade)
SEARCH_DIRS = [
    os.path.expanduser('~/Documents/Scans'),
    os.path.expanduser('~/Desktop/Belege'),
    os.path.join(os.path.dirname(__file__), 'belege', 'archiv'),
]

# Mapping: Host-Pfad -> Container-Pfad
PATH_MAPPING = {
    os.path.expanduser('~/Documents/Scans'): '/data/scans',
    os.path.expanduser('~/Desktop/Belege'): '/data/belege',
    os.path.join(os.path.dirname(__file__), 'belege', 'archiv'): '/app/belege/archiv',
    os.path.join(os.path.dirname(__file__), 'belege'): '/app/belege',
}


def find_file(filename, search_dirs):
    """Sucht eine Datei rekursiv in den angegebenen Ordnern."""
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            if filename in files:
                return os.path.join(root, filename)
    return None


def convert_to_container_path(host_path):
    """Konvertiert einen Host-Pfad zum Container-Pfad."""
    for host_prefix, container_prefix in PATH_MAPPING.items():
        if host_path.startswith(host_prefix):
            return host_path.replace(host_prefix, container_prefix, 1)
    return host_path


def main():
    if not os.path.exists(CACHE_FILE):
        print(f"❌ Cache nicht gefunden: {CACHE_FILE}")
        return

    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)

    print(f"📦 Cache geladen: {len(cache)} Einträge")

    # Verfügbare Ordner anzeigen
    print("\n📂 Durchsuche Ordner:")
    for d in SEARCH_DIRS:
        exists = "✅" if os.path.exists(d) else "❌"
        print(f"   {exists} {d}")

    updated = 0
    already_set = 0
    not_found = 0

    print("\n🔍 Suche Dateien...")

    for file_hash, entry in cache.items():
        # Prüfen ob Pfad bereits ein Container-Pfad ist
        existing_path = entry.get('datei_pfad', '')
        if existing_path.startswith('/data/') or existing_path.startswith('/app/'):
            already_set += 1
            continue

        datei = entry.get('datei')
        if not datei:
            not_found += 1
            continue

        # Datei suchen
        found_path = find_file(datei, SEARCH_DIRS)

        if found_path:
            # Pfad für Container konvertieren
            container_path = convert_to_container_path(found_path)
            entry['datei_pfad'] = container_path
            updated += 1
            print(f"   ✅ {datei} -> {container_path}")
        else:
            not_found += 1
            print(f"   ❌ {datei} nicht gefunden")

    # Cache speichern
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"\n📈 Zusammenfassung:")
    print(f"   ✅ Pfade ergänzt: {updated}")
    print(f"   ⏭️  Bereits vorhanden: {already_set}")
    print(f"   ❌ Nicht gefunden: {not_found}")


if __name__ == '__main__':
    main()
