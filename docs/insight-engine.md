# Insight-Engine — Architektur

Stand: 2026-06 · Status: Konzept + erster Baustein (CoC / Break-even) live in v0.9.26

## Zweck

Nicht „noch ein Score". Das Ziel ist, die **Denk-Trajektorie eines Investors** nachzubauen:
vom Anwender der Standard-Methoden → über Mustererkennung → zur Anomalie → zur Hypothese →
zur adversarial gehärteten Einsicht → zum gelernten Edge. Über 197 Märkte gleichzeitig,
mit der Disziplin, die ein Mensch unter emotionalem Einsatz verliert.

**Oberster Leitsatz (aus CLAUDE.md):** Berechnung erwünscht, Halluzination verboten.
Die Engine findet nur, was **latent in den Daten** steckt. Bei dünner/MOCK-Datenlage produziert
sie keine Genialität, sondern selbstsicheren Unsinn — die Tier-/Konfidenz-/Adversarial-Regeln
sind kein Beiwerk, sie sind der einzige Schutz davor.

## Die ehrliche Grenze (warum „Samurai" ein System ist, kein Modell)

Das Modell (Claude) lernt **nicht über Sessions hinweg**. Es startet jede Session gleich gut.
Das „smarter und smarter" passiert nicht im Modell, sondern im **Tool als externem Gedächtnis**:
verifizierte Befunde, Anomalie-Register und Kalibrierungs-Log akkumulieren. Das Modell liest
diesen Stand zu Beginn und operiert darauf. Über Monate wird die *Kombination* zum Meister:

- **Adrian** → Richtung, Einsatz, Geschmack (welche Frage zählt)
- **Modell** → Breite, Tempo, gnadenloses Selbst-Angreifen (jede Verknüpfung prüfen)
- **Tool** → das Gedächtnis, das kompoundiert (wo Meisterschaft sich ablagert)

## Diagnostisch vs. Kalibrierung vs. Prognose — sauber getrennt

| Art | Zeitrichtung | Predictive? | Datenfest heute? |
|---|---|---|---|
| **Diagnostisch** (Anomalie: Modell ≠ Realität *jetzt*) | Gegenwart | nein | ja |
| **Kalibrierung** (waren *vergangene* Urteile richtig → Gewichte justieren) | Rückblick | nein | ja (Backtest auf HESTA-Historie) |
| **Prognose** (Markt entwickelt sich künftig so) | Zukunft | ja | nein → nur 🔴/🟡 Szenario mit Band |

„Smarter werden" = **Kalibrierung**, nicht Prognose. Heute misst das Tool seine eigene
Trefferquote mit 0 % — der erste echte Gewinn der Engine ist, diese Zahl überhaupt **messbar**
zu machen. Verbessern kann man nur, was man misst.

## Die 5 Phasen

| Phase | Mensch | Im Tool | Datenbedarf |
|---|---|---|---|
| **0 — Anwender** | kann die Formeln | CoC, Break-even, DCF, RevPAR, hedonische Schätzung über alle Märkte | vorhanden |
| **1 — Mustererkennung** | baut Intuition | Korrelationen/Cluster über Märkte → explizite Muster-Bibliothek | vorhanden |
| **2 — Anomalie-Detektor** | „hier stimmt was nicht" | Märkte, wo Modell ≠ Realität (z.B. günstig + tote Nachfrage, aber HESTA ↑ + Arbeitgeber ↑) → Edge-Kandidaten | vorhanden |
| **3 — Hypothese/Kausalität** | versteht *warum* | mechanistische These je Anomalie, via H0–H4-Leiter + §9-Inferenz | vorhanden + Proxies |
| **4 — Experte/Härtung** | trennt Einsicht von Wunschdenken | jede These adversarial angreifen; nur überlebt + ≥2 unabh. Signale → Edge mit Konfidenz | vorhanden |
| **5 — Meister/Lernschleife** | wird *über Zeit* besser | Edges speichern, gegen eintreffende Realität prüfen, Signal-Gewichte nachziehen | Monate (Forward) / sofort (Backtest) |

## Daten-Reihenfolge (kein Monate-Warten als Blocker)

1. **Vorhandene Daten holen (Roadmap A/B, ~Wochen):** HESTA hat Jahre Monats-Historie;
   BFS-Mietpreisindex, ARE-Zweitwohnungen, FPRE/Wüest existieren publiziert — fetchen, nicht warten.
   Einzige echte Lücke: STR-spezifische Occ/ADR realer Inserate (proxen oder scrapen).
2. **Backtest auf HESTA-Historie (sofort):** „Hätte das Modell Markt X 2022 markiert — bestätigten
   2023/24 es?" Gibt ein Kalibrierungs-Signal aus der Vergangenheit *ohne* zu warten.
   Caveat: validiert nur die Proxy-Kette (Hotel-Logiernächte), nicht die 🔴 MOCK-STR-Werte.
3. **Forward-Log mitlaufen lassen (Monate):** jede Edge-Hypothese bekommt eine prüfbare Vorhersage
   + Ablaufdatum; reift im Hintergrund, während das Tool schon benutzt wird.

## Standard-Methoden (Phase 0) — Quellen und Tier

Lehrbuch-Standard, hohe Konfidenz für die Formeln selbst (CH-Ausprägung ggf. zu verifizieren).
Siehe `docs/fachliteratur.md` für die verifizierte Quellenliste.

- **Cash-on-Cash** = Jahres-Cashflow ÷ eingesetztes Kapital. Bei R2R: Kapital = Mietkaution
  (3 Monatsmieten, Art. 257e OR) + Setup-Möblierung. → live in Earn-Card, 🟡 MOD.
- **Break-even-Auslastung** = (Fixkosten + Mietzins) ÷ (Deckungsbeitrag/Nacht × 365). → live, 🟡 MOD.
- **RevPAR** = ADR × Auslastung. Bereits faktisch im Modell (ADR×Occ×Nächte).
- **DCF/NPV** für den Vertragshorizont inkl. Anlaufphase + Setup-Amortisation. Diskontsatz =
  risikofrei + Immobilien-Prämie + R2R-Operations-/Vertragsrisiko. → Roadmap.
- **Hedonische Regression** zur Modellierung fehlender ADR/Miete aus Markt-Attributen
  (Wüest/FPRE-Methode). Datenhungrig → Roadmap-Stufe.

## Rechts-Befunde als Rechenregel (verifiziert, Deep-Research 2026-06)

Aus der adversarial geprüften Recherche (80 Claims bestätigt, 15 widerlegt):

1. **Untermiet-Reform 24.11.2024 GESCHEITERT** (51.6 % Nein) — es gilt weiter altes Art. 262 OR.
   (Viele Ratgeber behaupten fälschlich Annahme.)
2. **Kein genereller 30–40 % Gewinndeckel** bei Untermiete (BGE 119 II 353 wird überlesen):
   verglichen wird Untermiet-Zimmermiete gegen anteilige Hauptmiete/Zimmer, aufgewertet für
   Möblierung/Service; ~30 % Differenz galt *im Einzelfall* als missbräuchlich, Grundsatzfrage offen.
   → Aufschlag begrenzt, Möblierungs-/Service-Zuschlag aber legitim. Kein Fixdeckel ins Tool.
3. **Tessin „Lex Airbnb": gewerblich ab < 4 Betten** (nicht 6), Registrierungspflicht seit 1.2.2022,
   max. 90 Tage. → präzisiert `REGULATORY_STOPS`.
4. **FPRE-Metaanalyse erscheint monatlich** (nicht quartalsweise).

## Nächste Schritte

- [x] Phase 0: CoC + Break-even sichtbar (v0.9.26)
- [x] `docs/fachliteratur.md` ablegen (v0.9.26)
- [x] Rechts-Befunde 1–4 als Caveats in Earn-Card / REGULATORY_STOPS (v0.9.27)
- [x] ARE-Zweitwohnungen-Pipeline + ZWG-Cap-Signal (v0.9.28)
- [x] BFS-Mietpreis-Pipeline + Kaltmiete-Reality-Anchor (v0.9.29)
- [x] Phase 2: Anomalie-Detektor (Modell-Realität-Gap) MVP (v0.9.30)
- [x] BFS-Leerstand-Pipeline (v0.9.31) — via SDMX `disseminate.stats.swiss/rest` gelöst
      (CH1.LWZ:DF_LWZ_1, gefilterte Slice). Mietverhandlungs-Hebel-Proxy pro Markt.
- [x] Phase 2 Ausbau: Cross-Markt Edge-Ranking (v0.9.31, Scout-View)
- [x] Phase 5: Backtest / Signal-Kalibrierung (v0.9.31) — Momentum-Hit-Rate 51 % (n=140),
      ehrlich als schwaches Signal ausgewiesen. Macht Signal-Güte erstmals messbar.
- [ ] Phase 5 Ausbau: Forward-Log (Edge-Hypothesen mit Ablaufdatum gegen eintreffende Daten)
- [ ] Signal-Verbesserung: Momentum-Kalibrierung (51 %) ist schwach → bessere Prädiktoren
      suchen (mehrjähriger Trend, Saison-bereinigt, kombinierte Signale) statt YoY allein
- [ ] STR-Occ/ADR aus 🔴 MOCK lösen (Inferenz-Engine / echte Quelle) — Hauptlimit der Edge-Qualität
