# Akquise Deal-Dossier — verbindliche Methode

**Status:** v1 (2026-06-15). Gilt für `akquise.html`. Ergänzt [scraper-contract.md].
Grundregel-Quellen: Daten-First (keine erfundenen Werte), nichts wird automatisch versendet.

## Zweck

Pro Miet-Inserat erstellt die Akquise EINEN **Vorschlag an Adrian** — kein Versand.
Adrian prüft, überarbeitet bei Bedarf und leitet selbst weiter. Das Dossier liefert
in einem Block: Insights zum Objekt, Lage-Fakten, Deal-Wahrscheinlichkeit, ein
**Cockpit-belegtes Angebot** und einen **Brief-Entwurf** — getrennt nach Anbieter-Typ.

## Eingänge (pro Inserat)

Quelle: Gmail-Suchagent-Mails (IMAP, newhome/homegate/immoscout) oder Link/manuell.

Pflicht: Markt (Gemeinde), Zimmer, Miete CHF/Mt, Anbieter-Typ.
Foto-/Text-Fakten (Adrian setzt sie beim Sichten der Bilder — werden NIE erfunden):
- **Ausbaustandard**: einfach / normal / gehoben / neuwertig
- **Waschturm/Waschmaschine in der Wohnung**: ja / nein / unklar
- **Parkplatz / Garage**: ja / möglich / nein
- **Aussicht**: ja / teilweise / nein
- **Grösse der Überbauung**: Einzel-/Zweifamilienhaus / kleines MFH / grosse Überbauung
- optional: Erdgeschoss/eigener Eingang, schon länger inseriert (Leerstand)

## Anbieter-Typ: zwei Welten

**Privatperson** (emotional, vertrauensgetrieben):
- Mietgarantie ist das stärkste Argument: pünktliche Miete jeden Monat, unabhängig
  von Belegung → **sicherer als ein normaler Mieter** (keine Ausstände, kein Leerstand).
- Vertrauen/Gesicht: transparente STR-Absicht, persönliches Treffen anbieten, Track-Record
  (200+ Nächte ohne Reklamation), Referenzen, STR-Versicherung bis CHF 500'000.
- Pflege-Argument: 2–3× wöchentlich professionell gereinigt → Objekt besser gepflegt als
  bei Dauermieter.
- Upside: 10–30 % über Marktmiete oder Cashflow-Anteil → „du verdienst mehr als marktüblich".

**Immobilienfirma** (rational, prozessgetrieben, B2B):
- Ein zuverlässiger Firmen-Mieter: ein Vertrag, pünktlich, kein Mieterwechsel, weniger Admin.
- Leerstand-Füller: gezielt länger inserierte Objekte ansprechen („wir nehmen die schwer
  vermietbare Einheit").
- Portfolio/Rahmen: Interesse an mehreren Einheiten → Skalierung, weniger Vakanz für sie.
- Compliance-Sprache: UID, STR-Versicherung, Kurtaxe-Handling → kein Risiko.
- Vorhersehbarkeit: 3-Jahres-Vertrag mit Indexierung, evtl. Jahres-Vorauszahlung gegen Rabatt.

## Deal-Wahrscheinlichkeit (Score 0–100, transparent begründet)

Additive Faktoren, je mit Punkten + Klartext-Begründung:
- **Anonymität / grosse Überbauung** (+++): Nachbarn/Verwaltung stören sich weniger → Ja
  wahrscheinlicher. Adrians Kern-Heuristik.
- **Untervermietungs-Klausel** unbekannt/„mit Zustimmung" (+), explizit verboten (−−).
- **Erdgeschoss / eigener Eingang** (+): weniger Nachbar-Konflikt.
- **Leerstand / länger inseriert** (+): Vermieter motiviert.
- **Privatperson mit Einzelobjekt in grosser Überbauung** = beste Kombination.
- **ETW/Stockwerkeigentum** (−): Reglement-Risiko.
- **Cap-Markt (90-Tage / GE / Luzern)** (−−): Regulierung kappt das Modell.
Ausgabe: Score + die 3 stärksten Treiber, ehrlich (kein geschöntes „hoch").

## Angebot (aus der Cockpit-Ökonomik hergeleitet)

Belegbare Zahl statt Bauchgefühl. Aus den Markt-Daten (`js/data.js`: adr, occ, revpar)
für den Wohnungstyp:
- STR-Brutto/Mt ≈ ADR(typ) × Belegung(typ) × 30
- Netto vor Miete ≈ Brutto × (1 − ~29 % variabel) − ~400 Fix/Mt
- **Max. tragbare Miete** = Netto-vor-Miete − Ziel-Marge (Default Marge ~CHF 800/Mt)
- **Angebots-Vorschlag**: liegt die Inserat-Miete unter der Max-Miete → Spielraum;
  Vorschlag = Marktmiete + 10 % ODER Cashflow-Anteil, je nach Anbieter-Typ.
Immer mit Rechenweg anzeigen (Nachvollziehbarkeit, [[feedback_nachvollziehbarkeit]]).
Tier 🟡 (modelliert); occ = statischer Modellwert, für Live-Märkte später Cockpit-Median.

## Lage-Insights (markt-spezifisch, belegt)

Kuratiert je Fokus-Markt mit Quelle + Stand; fehlt der Markt → ehrlich „bitte prüfen".
Beispiel Kriens: ÖV ins Zentrum Luzern ~15 Min (Bus 1, alle 10 Min); Einkaufen Pilatusmarkt
~16 Min (Bus 14) bzw. vor Ort; Tor zum Pilatus (Tagestourismus).
Quelle Kriens: VBL/rome2rio, Stand 2026-06. Keine ÖV-Minuten erfinden.

## Brief-Entwurf

Briefkopf + an das Inserat gebunden (Strasse/Stadt/Typ), Variante nach Anbieter-Typ
(`LETTER_TEMPLATES` in `js/loopholes.js`: personal_known/unknown, premium_stability,
firma_einzel, firma_portfolio). Schlupfloch-Block je Markt automatisch. Ausgabe = Entwurf
für Adrian (kopieren / in Gmail öffnen) — **kein Auto-Versand**.

## Was NICHT passiert
- Kein automatischer Versand, keine Massen-Mails.
- Keine erfundenen Foto-Fakten, ÖV-Zeiten oder Erträge.
- Kein Angebot ohne sichtbaren Rechenweg.
