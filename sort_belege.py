#!/usr/bin/env python3
"""
Beleg-Sortierer - Sortiert Belege nach Monaten in Ordner

Verwendung:
    python sort_belege.py /pfad/zu/belegen
    python sort_belege.py /pfad/zu/belegen --output /pfad/zu/sortiert
    python sort_belege.py /pfad/zu/belegen --dry-run
    python sort_belege.py /pfad/zu/belegen --move  # Verschieben statt Kopieren
    python sort_belege.py /pfad/zu/belegen --skip-duplicates  # Duplikate überspringen
"""

import argparse
import hashlib
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Optional: Versuche Datum aus PDF/Bild-Metadaten zu lesen
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from pdf2image import pdfinfo_from_path
    PDF_INFO_AVAILABLE = True
except ImportError:
    PDF_INFO_AVAILABLE = False


# Deutsche Monatsnamen für Ordner
MONAT_NAMEN = {
    1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
    5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
}

# Kurze Monatsnamen (für Dateinamen-Erkennung)
MONAT_KURZ = {
    'jan': 1, 'feb': 2, 'mär': 3, 'mar': 3, 'apr': 4,
    'mai': 5, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
    'sep': 9, 'okt': 10, 'oct': 10, 'nov': 11, 'dez': 12, 'dec': 12
}


def get_file_hash(filepath):
    """Berechnet MD5-Hash einer Datei"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(files):
    """Findet Duplikate anhand des MD5-Hashs"""
    hash_to_files = {}  # {hash: [filepath1, filepath2, ...]}

    for filepath in files:
        try:
            file_hash = get_file_hash(filepath)
            if file_hash not in hash_to_files:
                hash_to_files[file_hash] = []
            hash_to_files[file_hash].append(filepath)
        except Exception as e:
            print(f"  ⚠️  Hash-Fehler bei {filepath.name}: {e}")

    # Nur Gruppen mit mehr als einer Datei sind Duplikate
    duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}

    return hash_to_files, duplicates


def extract_date_from_filename(filename):
    """Versucht ein Datum aus dem Dateinamen zu extrahieren"""
    name = filename.lower()

    # Pattern 1: YYYY-MM-DD oder YYYY_MM_DD oder YYYYMMDD
    match = re.search(r'(20\d{2})[-_]?(0[1-9]|1[0-2])[-_]?(0[1-9]|[12]\d|3[01])', name)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    # Pattern 2: DD.MM.YYYY oder DD-MM-YYYY
    match = re.search(r'(0[1-9]|[12]\d|3[01])[.\-](0[1-9]|1[0-2])[.\-](20\d{2})', name)
    if match:
        return int(match.group(3)), int(match.group(2)), int(match.group(1))

    # Pattern 3: DD.MM.YY oder DD-MM-YY
    match = re.search(r'(0[1-9]|[12]\d|3[01])[.\-](0[1-9]|1[0-2])[.\-](\d{2})', name)
    if match:
        year = 2000 + int(match.group(3))
        return year, int(match.group(2)), int(match.group(1))

    # Pattern 4: Monat Jahr (z.B. "november_2025", "nov2025")
    for monat_kurz, monat_num in MONAT_KURZ.items():
        match = re.search(rf'{monat_kurz}\w*[_\-\s]*(20\d{{2}})', name)
        if match:
            return int(match.group(1)), monat_num, 1

    # Pattern 5: Jahr Monat (z.B. "2025_november", "2025-11")
    match = re.search(r'(20\d{2})[_\-\s]*(0[1-9]|1[0-2])', name)
    if match:
        return int(match.group(1)), int(match.group(2)), 1

    return None


def extract_date_from_file_metadata(filepath):
    """Versucht das Datum aus Datei-Metadaten zu lesen"""
    suffix = filepath.suffix.lower()

    # EXIF-Daten aus Bildern
    if PIL_AVAILABLE and suffix in ('.jpg', '.jpeg', '.tiff'):
        try:
            with Image.open(filepath) as img:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag in ('DateTime', 'DateTimeOriginal', 'DateTimeDigitized'):
                            # Format: "YYYY:MM:DD HH:MM:SS"
                            dt = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                            return dt.year, dt.month, dt.day
        except Exception:
            pass

    return None


def extract_date_from_modification_time(filepath):
    """Verwendet das Änderungsdatum der Datei als Fallback"""
    try:
        mtime = os.path.getmtime(filepath)
        dt = datetime.fromtimestamp(mtime)
        return dt.year, dt.month, dt.day
    except Exception:
        return None


def get_date_for_file(filepath, use_mtime=False):
    """Ermittelt das Datum für eine Datei (verschiedene Strategien)"""
    # 1. Aus Dateinamen
    date = extract_date_from_filename(filepath.name)
    if date:
        return date, 'filename'

    # 2. Aus Metadaten
    date = extract_date_from_file_metadata(filepath)
    if date:
        return date, 'metadata'

    # 3. Aus Änderungsdatum (optional)
    if use_mtime:
        date = extract_date_from_modification_time(filepath)
        if date:
            return date, 'mtime'

    return None, None


def get_month_folder_name(year, month, format_style='german'):
    """Erstellt den Ordnernamen für einen Monat"""
    if format_style == 'german':
        # Format: "2025-11 November" oder "November 2025"
        return f"{year}-{month:02d}_{MONAT_NAMEN[month]}"
    elif format_style == 'short':
        # Format: "2025-11"
        return f"{year}-{month:02d}"
    else:
        # Format: "Nov 2025"
        return f"{MONAT_NAMEN[month][:3]} {year}"


def scan_files(folder_path, recursive=False):
    """Scannt Ordner nach Belegen"""
    supported = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')
    folder = Path(folder_path)

    if recursive:
        files = [f for f in folder.rglob('*') if f.is_file() and f.suffix.lower() in supported]
    else:
        files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in supported]

    return sorted(files)


def main():
    parser = argparse.ArgumentParser(
        description='Sortiert Belege nach Monaten in Ordner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python sort_belege.py /Users/olivier/Documents/Scans
  python sort_belege.py /Users/olivier/Documents/Scans --output /Users/olivier/Documents/Belege
  python sort_belege.py /Users/olivier/Documents/Scans --dry-run
  python sort_belege.py /Users/olivier/Documents/Scans --move --use-mtime
  python sort_belege.py /Users/olivier/Documents/Scans --recursive
  python sort_belege.py /Users/olivier/Documents/Scans --skip-duplicates

Datum-Erkennung (Priorität):
  1. Aus Dateinamen (z.B. "2025-11-15_Beleg.pdf", "Rechnung_15.11.2025.jpg")
  2. Aus EXIF-Metadaten (bei Bildern)
  3. Aus Änderungsdatum (mit --use-mtime)

Duplikat-Erkennung:
  Dateien werden via MD5-Hash verglichen. Identische Dateien werden erkannt,
  auch wenn sie unterschiedliche Namen haben.
        """
    )

    parser.add_argument('folder', help='Ordner mit Belegen')
    parser.add_argument('--output', '-o', help='Zielordner (Standard: ./sortiert)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Nur anzeigen, was gemacht würde')
    parser.add_argument('--move', '-m', action='store_true',
                        help='Dateien verschieben statt kopieren')
    parser.add_argument('--use-mtime', action='store_true',
                        help='Änderungsdatum als Fallback verwenden')
    parser.add_argument('--recursive', '-r', action='store_true',
                        help='Unterordner rekursiv durchsuchen')
    parser.add_argument('--format', '-f', choices=['german', 'short', 'month'],
                        default='german', help='Ordner-Namensformat')
    parser.add_argument('--skip-duplicates', '-d', action='store_true',
                        help='Duplikate überspringen (nur erstes behalten)')
    parser.add_argument('--duplicates-folder', action='store_true',
                        help='Duplikate in separaten Ordner verschieben')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Ausführliche Ausgabe')

    args = parser.parse_args()

    # Ordner prüfen
    if not os.path.isdir(args.folder):
        print(f"❌ Ordner nicht gefunden: {args.folder}")
        sys.exit(1)

    # Zielordner
    output_dir = Path(args.output) if args.output else Path(args.folder) / 'sortiert'

    # Dateien scannen
    print(f"\n📁 Scanne: {args.folder}")
    files = scan_files(args.folder, recursive=args.recursive)

    if not files:
        print("❌ Keine Belege gefunden (PDF, JPG, PNG, TIFF)")
        sys.exit(1)

    print(f"📄 {len(files)} Dateien gefunden")

    # Duplikate erkennen
    print(f"\n🔍 Prüfe auf Duplikate (MD5-Hash)...")
    hash_to_files, duplicates = find_duplicates(files)

    # Duplikat-Statistik
    total_duplicates = sum(len(f) - 1 for f in duplicates.values())
    unique_files = len(hash_to_files)

    if duplicates:
        print(f"   {total_duplicates} Duplikate gefunden ({unique_files} einzigartige Dateien)")
        if args.verbose:
            print(f"\n📋 Duplikat-Gruppen:")
            for file_hash, dup_files in duplicates.items():
                print(f"   Hash {file_hash[:8]}...:")
                for f in dup_files:
                    print(f"      - {f.name}")
    else:
        print(f"   Keine Duplikate gefunden")

    # Dateien filtern (Duplikate entfernen wenn gewünscht)
    files_to_process = []
    skipped_duplicates = []
    seen_hashes = set()

    for filepath in files:
        try:
            file_hash = get_file_hash(filepath)
            if args.skip_duplicates or args.duplicates_folder:
                if file_hash in seen_hashes:
                    skipped_duplicates.append(filepath)
                    continue
                seen_hashes.add(file_hash)
            files_to_process.append((filepath, file_hash))
        except Exception:
            files_to_process.append((filepath, None))

    print(f"\n{'='*60}")

    # Dateien analysieren und gruppieren
    by_month = {}  # {(year, month): [(file, source, day, hash), ...]}
    unknown = []

    for filepath, file_hash in files_to_process:
        date, source = get_date_for_file(filepath, use_mtime=args.use_mtime)

        if date:
            year, month, day = date
            key = (year, month)
            if key not in by_month:
                by_month[key] = []
            by_month[key].append((filepath, source, day, file_hash))

            if args.verbose:
                hash_info = f" [{file_hash[:8]}]" if file_hash else ""
                print(f"  ✓ {filepath.name} → {MONAT_NAMEN[month]} {year} ({source}){hash_info}")
        else:
            unknown.append((filepath, file_hash))
            if args.verbose:
                print(f"  ? {filepath.name} → Datum unbekannt")

    # Zusammenfassung
    print(f"\n📊 Zusammenfassung:")
    print(f"   Erkannt: {sum(len(v) for v in by_month.values())} Dateien in {len(by_month)} Monaten")
    if unknown:
        print(f"   Unbekannt: {len(unknown)} Dateien")
    if skipped_duplicates:
        print(f"   Übersprungen (Duplikate): {len(skipped_duplicates)} Dateien")

    # Monate anzeigen
    print(f"\n📅 Monate:")
    for (year, month), files_list in sorted(by_month.items()):
        folder_name = get_month_folder_name(year, month, args.format)
        print(f"   {folder_name}: {len(files_list)} Dateien")

    if unknown:
        print(f"\n⚠️  Dateien ohne erkanntes Datum:")
        for f, h in unknown[:10]:
            print(f"   - {f.name}")
        if len(unknown) > 10:
            print(f"   ... und {len(unknown) - 10} weitere")

    if skipped_duplicates and args.verbose:
        print(f"\n🔄 Übersprungene Duplikate:")
        for f in skipped_duplicates[:10]:
            print(f"   - {f.name}")
        if len(skipped_duplicates) > 10:
            print(f"   ... und {len(skipped_duplicates) - 10} weitere")

    # Dry-run Ende
    if args.dry_run:
        print(f"\n🔍 Dry-run: Keine Dateien wurden kopiert/verschoben")
        print(f"   Zielordner wäre: {output_dir}")
        sys.exit(0)

    # Bestätigung
    action = 'verschoben' if args.move else 'kopiert'
    print(f"\n📦 Dateien werden nach {output_dir} {action}")

    # Dateien kopieren/verschieben
    copied = 0
    errors = 0

    for (year, month), files_list in sorted(by_month.items()):
        folder_name = get_month_folder_name(year, month, args.format)
        target_dir = output_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        for filepath, source, day, file_hash in files_list:
            target_path = target_dir / filepath.name

            # Bei Namenskonflikt: Nummer anhängen
            if target_path.exists():
                stem = filepath.stem
                suffix = filepath.suffix
                counter = 1
                while target_path.exists():
                    target_path = target_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

            try:
                if args.move:
                    shutil.move(str(filepath), str(target_path))
                else:
                    shutil.copy2(str(filepath), str(target_path))
                copied += 1

                if args.verbose:
                    print(f"  → {target_path.relative_to(output_dir)}")
            except Exception as e:
                errors += 1
                print(f"  ❌ Fehler bei {filepath.name}: {e}")

    # Unbekannte Dateien in "Unsortiert" Ordner
    if unknown:
        unsorted_dir = output_dir / '_Unsortiert'
        unsorted_dir.mkdir(parents=True, exist_ok=True)

        for filepath, file_hash in unknown:
            target_path = unsorted_dir / filepath.name

            if target_path.exists():
                stem = filepath.stem
                suffix = filepath.suffix
                counter = 1
                while target_path.exists():
                    target_path = unsorted_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

            try:
                if args.move:
                    shutil.move(str(filepath), str(target_path))
                else:
                    shutil.copy2(str(filepath), str(target_path))
                copied += 1
            except Exception as e:
                errors += 1

    # Duplikate in separaten Ordner (wenn gewünscht)
    if args.duplicates_folder and skipped_duplicates:
        dup_dir = output_dir / '_Duplikate'
        dup_dir.mkdir(parents=True, exist_ok=True)

        for filepath in skipped_duplicates:
            target_path = dup_dir / filepath.name

            if target_path.exists():
                stem = filepath.stem
                suffix = filepath.suffix
                counter = 1
                while target_path.exists():
                    target_path = dup_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

            try:
                if args.move:
                    shutil.move(str(filepath), str(target_path))
                else:
                    shutil.copy2(str(filepath), str(target_path))
            except Exception as e:
                print(f"  ❌ Fehler bei Duplikat {filepath.name}: {e}")

    print(f"\n{'='*60}")
    print(f"✅ {copied} Dateien {action}")
    if skipped_duplicates:
        if args.duplicates_folder:
            print(f"🔄 {len(skipped_duplicates)} Duplikate in _Duplikate/ Ordner")
        else:
            print(f"🔄 {len(skipped_duplicates)} Duplikate übersprungen")
    if errors:
        print(f"❌ {errors} Fehler")
    print(f"📁 Zielordner: {output_dir}")
    print(f"\n✨ Fertig!")


if __name__ == '__main__':
    main()
