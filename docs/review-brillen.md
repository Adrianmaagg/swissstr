# Review-Brillen — durch wessen Augen wir die Seite prüfen

> **Warum dieses Dokument:** Eine Brille (der Anwender) übersieht die Hälfte. Bei einem Tool,
> das Deal-Entscheide trifft UND Dossiers an echte Eigentümer schickt, prüfen wir **durch mehrere
> Personas**. Jede entspricht einer realen Versagensart. Beim Dogfood/Review IMMER alle relevanten
> Brillen aufsetzen — nicht nur „funktioniert es?". (Adrian, 2026-06-19: „brauchen wir noch weitere
> Brillen?" — ja, diese.)

## Die Brillen

| # | Brille | Die Frage | Fängt typisch | Prio für SwissSTR |
|---|---|---|---|---|
| 1 | **Anwender** (Adrian, Betreiber) | Funktioniert der Flow, ist er klar, führt er zum Deal? | tote Links, leere Zustände, Verwirrung | Default |
| 2 | **Skeptiker** | „Woher wissen Sie das? Belegen Sie es." | erfundene Präzision, unbelegte Signale, widersprüchliche Zahlen | **hoch** |
| 3 | **Eigentümer / Gegenpartei** | Landet das Dossier oder blamiert es mich? Ist es fair + glaubwürdig für jemanden, dem die Wohnung gehört? | peinliche/falsche Zahlen im Pitch, Ton, Doppel-Anschreiben | **höchste** (Output geht an sie) |
| 4 | **Jurist / Regulator** | Untervermietung erlaubt? STR-Cap / Zweckentfremdung / Zweitwohnung / Kurtaxe? | Empfehlung für einen rechtlich toten Markt; der eigentliche Deal-Killer | **hoch** (heute ungated) |
| 5 | **Zahlen-Prüfer** (Due Diligence) | Stimmt das Modell? Konservativ oder optimistisch? Wo ist der Downside-Case? | systematisch zu optimistische Zahlen, fehlende Bandbreite, Modell ≠ Ist | **hoch** |
| 6 | **Laie** | Versteht das jemand ohne Vorwissen + Jargon? | ADR/RevPAR/NOI-Kauderwelsch, unerklärte Tier-Badges | mittel (= Klartext-Ziel) |

## Regeln

- **Jede Zahl muss sich selbst rechtfertigen können** (Brille 2). Wo sie das nicht kann → „woher?"-Beleg
  nachrüsten oder die Zahl raus. Die 3-Kohorten-Divergenz (start 63 % / cockpit 71 % / akquise 60 % für
  Vitznau) ist ein Brille-2-Versagen — sie wurde nur durch die Skeptiker-Frage sichtbar.
- **Was an Eigentümer geht (akquise-Dossier, Pitch, Brief), zuerst durch Brille 3.** Eine falsche Zahl
  dort ist teurer als zehn im internen Cockpit.
- **Vor „Markt X lohnt sich" immer Brille 4.** Eine Marktempfehlung ohne Rechts-Gate (Untervermietung/Cap)
  ist optimiert auf die falsche Grösse.
- **Bei jeder Geld-/Belegungszahl Brille 5:** ist das die Decke des Besten oder mein erreichbarer Boden?
  Conservative-Case mitliefern, nicht nur den Spitzenwert.
- **Nicht nur „es funktioniert" (Brille 1) reicht NIE als Review-Abschluss.**

## Befund-Beispiele (was die neuen Brillen aufgedeckt haben)

- Brille 2 → 3-Kohorten-Divergenz (eine Markt-Belegung, drei Zahlen) · STATUS §7-Queue #1.
- Brille 5 → Free-Scrape sieht keine Host-Daten → Profi-Konkurrenz 0 % vs real 61 % (InsideAirbnb) ·
  jetzt als Untergrenze auf netzwerk sichtbar.
- Brille 3 → die „Spitzenverdiener"-Schlagzeile (Vitznau 26'900/Mt aus 1 Luxus-Chalet) ist nicht der
  Boden, den ein Einsteiger erreicht — als Eigentümer-Versprechen riskant.
- Brille 4 → offen: regulierung.html existiert, gated aber die Empfehlung nicht.
