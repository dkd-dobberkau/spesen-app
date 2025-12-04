# Spesen-App Backlog

## Priorisierung

- **P1** - Hohe Priorität (wichtig für Kernfunktionalität)
- **P2** - Mittlere Priorität (nützliche Erweiterung)
- **P3** - Niedrige Priorität (Nice-to-have)

---

## Funktionale Erweiterungen

### P1 - Hohe Priorität

- [ ] **Beleg-Suche**
  - Volltextsuche über OCR-Text, Beschreibungen und Kategorien
  - Filterung nach Datum, Betrag, Kategorie

- [ ] **Backup/Restore**
  - Export der kompletten Datenbank als ZIP (DB + Belege + Einstellungen)
  - Import/Restore-Funktion
  - Automatische Backups (täglich/wöchentlich)

- [ ] **Kilometergeld-Rechner**
  - Eingabe von Start/Ziel oder km-Anzahl
  - Automatische Berechnung mit aktueller Pauschale (0,30 €/km)
  - Integration in Kategorie "Fahrtkosten KFZ"

### P2 - Mittlere Priorität

- [ ] **Dashboard mit Statistiken**
  - Monatsübersicht mit Gesamtsummen
  - Kategorie-Verteilung als Tortendiagramm
  - Jahresvergleich als Balkendiagramm
  - Top-Ausgaben des Monats

- [ ] **Mehrere Benutzer/Profile**
  - Benutzer-Verwaltung mit Login
  - Jeder Benutzer hat eigene Abrechnungen und Einstellungen
  - Admin-Rolle für Benutzerverwaltung

- [ ] **Wiederkehrende Ausgaben**
  - Monatliche Pauschalen definieren (z.B. Handy 50€)
  - Automatisches Eintragen zum Monatsanfang
  - Übersicht und Verwaltung der Vorlagen

- [ ] **Beleg-Vorschau in Liste**
  - Thumbnail des Belegs in der Ausgaben-Liste
  - Hover für größere Vorschau
  - Schnellansicht ohne Modal

### P3 - Niedrige Priorität

- [ ] **Notizen zu Ausgaben**
  - Freitextfeld für zusätzliche Informationen
  - Interne Notizen (nicht im Export)

- [ ] **Tags/Labels**
  - Eigene Tags für Ausgaben definieren
  - Filterung nach Tags
  - Projekt-Zuordnung

- [ ] **Ausgaben-Vorlagen**
  - Häufige Ausgaben als Vorlage speichern
  - Schnelles Eintragen mit einem Klick

---

## Technische Verbesserungen

### P1 - Hohe Priorität

- [ ] **API-Authentifizierung**
  - JWT oder Session-basierte Authentifizierung
  - API-Keys für externe Zugriffe
  - Rate-Limiting

- [ ] **Logging & Monitoring**
  - Strukturiertes Logging (JSON)
  - Error-Tracking
  - Health-Metrics Endpoint

### P2 - Mittlere Priorität

- [ ] **Progressive Web App (PWA)**
  - Service Worker für Offline-Nutzung
  - App-Manifest für Installation
  - Push-Benachrichtigungen (optional)

- [ ] **Dark Mode**
  - Dunkles Theme für Web-App
  - System-Präferenz erkennen
  - Manueller Toggle

- [ ] **Performance-Optimierung**
  - Lazy Loading für Belege
  - Pagination für große Listen
  - Caching-Strategie verbessern

### P3 - Niedrige Priorität

- [ ] **Multi-Language (i18n)**
  - Englische Oberfläche
  - Sprachauswahl in Einstellungen
  - Übersetzbare Kategorien

- [ ] **Responsive Design verbessern**
  - Optimierung für Tablets
  - Touch-freundliche Bedienung
  - Swipe-Gesten

---

## Integrationen

### P2 - Mittlere Priorität

- [ ] **E-Mail-Import**
  - IMAP-Verbindung konfigurieren
  - Automatisches Scannen nach Beleg-Anhängen
  - Oder: Belege an spezielle E-Mail-Adresse senden

- [ ] **DATEV-Export**
  - Export im DATEV-kompatiblen Format
  - Konfigurierbare Kontenrahmen
  - Buchungssätze generieren

- [ ] **Cloud-Storage Integration**
  - Dropbox/Google Drive/OneDrive
  - Automatischer Upload von Exporten
  - Beleg-Sync

### P3 - Niedrige Priorität

- [ ] **Kalender-Integration**
  - Bewirtungen mit Kalender-Terminen verknüpfen
  - Teilnehmer aus Termin übernehmen
  - iCal-Export

- [ ] **Slack/Teams Benachrichtigungen**
  - Notification bei neuen Abrechnungen
  - Erinnerung an ausstehende Belege
  - Webhook-Integration

- [ ] **Buchhaltungs-Software Integration**
  - Lexware
  - WISO
  - sevDesk API

---

## UX-Verbesserungen

### P2 - Mittlere Priorität

- [ ] **Drag & Drop Upload**
  - Belege per Drag & Drop hochladen
  - Mehrere Dateien gleichzeitig
  - Upload-Fortschritt anzeigen

- [ ] **Keyboard Shortcuts**
  - Schnellzugriff für häufige Aktionen
  - Navigation mit Tastatur
  - Hilfe-Overlay (?)

- [ ] **Onboarding/Tutorial**
  - Erste-Schritte-Wizard
  - Feature-Tour für neue Benutzer
  - Kontextuelle Hilfe

### P3 - Niedrige Priorität

- [ ] **Undo/Redo**
  - Letzte Aktionen rückgängig machen
  - History der Änderungen

- [ ] **Bulk-Aktionen**
  - Mehrere Ausgaben auswählen
  - Massenbearbeitung (Kategorie ändern, löschen)

---

## Dokumentation

### P2 - Mittlere Priorität

- [ ] **API-Dokumentation**
  - OpenAPI/Swagger Spezifikation
  - Interaktive API-Docs
  - Beispiel-Requests

- [ ] **Benutzerhandbuch**
  - Schritt-für-Schritt Anleitungen
  - FAQ
  - Video-Tutorials (optional)

---

## Abgeschlossen

- [x] KI-gestützte Belegerkennung mit Claude
- [x] Web-App mit Flask
- [x] CLI-Tool für Batch-Verarbeitung
- [x] Excel- und PDF-Export
- [x] ZIP-Export (Bundle)
- [x] Bewirtungsbeleg nach §4 EStG
- [x] Währungsumrechnung (EZB-Kurse)
- [x] Inbox/Archiv Workflow
- [x] Personen-Verwaltung mit VCF-Import
- [x] Autocomplete für Bewirtete Personen
- [x] Docker-Setup mit Traefik
- [x] Setup- und Test-Scripts
- [x] Verschlüsselung sensibler Daten (IBAN/BIC)
- [x] Durchnummerierung der Belege (Export + Web-App)

---

## Ideen (ungefiltert)

_Hier können neue Ideen gesammelt werden, bevor sie priorisiert werden:_

- OCR-Verbesserung durch lokales Tesseract-Training
- Sprachsteuerung für Beleg-Erfassung
- QR-Code Scanner für digitale Belege
- Reisekosten-Modul mit Tagespauschalen
- Kreditkarten-Abgleich
- Foto-App für Smartphone (separate App)
- Automatische Kategorisierung ohne KI (regelbasiert)
- Währungs-Favoriten
- Beleg-Dublettenprüfung
- Archiv-Browser mit Kalenderansicht
