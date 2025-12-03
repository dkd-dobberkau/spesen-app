# Spesenabrechnung App

Eine interaktive Flask-App mit Material Design zur Verwaltung von Spesenabrechnungen.

## Features

- **9 Kategorien** wie in deiner Excel-Vorlage:
  1. Fahrtkosten mit priv. Kfz. (automatische Berechnung mit 0,30 €/km)
  2. Fahrtkostenpauschale (RMV Ticket etc.)
  3. Bewirtungskosten
  4. Fachliteratur
  5. Büromaterial
  6. Telefonkosten
  7. Software
  8. Getränke
  9. Sonstiges (Parken, Taxi, Verpflegungspauschale, Uber)

- **Automatische Summenberechnung** pro Kategorie und gesamt
- **Lokale Speicherung** im Browser (localStorage)
- **Export als Excel** (.xlsx) mit Formatierung wie deine Vorlage
- **Export als PDF** mit professionellem Layout
- **Responsive Material Design** für Desktop und Mobile

## Installation

```bash
# In das Projektverzeichnis wechseln
cd spesen-app

# Virtuelle Umgebung erstellen (empfohlen)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# App starten
python app.py
```

Die App ist dann unter http://localhost:5000 erreichbar.

## Nutzung

1. **Grunddaten ausfüllen**: Monat, Name, Datum, Kontonummer, BLZ
2. **Spesen hinzufügen**: Kategorie aufklappen, Felder ausfüllen, + Button klicken
3. **Einträge löschen**: Mülleimer-Icon neben dem Eintrag
4. **Export**: Unten rechts Excel- oder PDF-Button klicken

## Struktur

```
spesen-app/
├── app.py              # Flask Backend
├── requirements.txt    # Python Dependencies
├── README.md          # Diese Datei
└── templates/
    └── index.html     # Frontend mit Material Design
```

## Technologien

- **Backend**: Flask (Python)
- **Frontend**: Materialize CSS (Material Design)
- **Excel Export**: openpyxl
- **PDF Export**: reportlab
