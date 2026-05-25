// Stadt-spezifische rechtliche Schlupflöcher und Brief-Templates
// Quelle: Adrian Maag's Recherche + öffentliche Stadt-/Kantonsverordnungen
// WICHTIG: Diese Templates sind Vorlagen. Jeder Fall muss vor Versand mit der zuständigen
// Behörde / dem Eigentümer einzeln verifiziert werden.

const LOOPHOLES = {
  // ====== STÄDTE MIT TAGES-CAP ======
  "Luzern": {
    cap_rule: "90 Tage / Jahr für Wohnraum (in Kraft seit 01.01.2025)",
    main_loophole: {
      title: "Gewerbeflächen sind ausgenommen",
      description: "Räume die seit 2011 als Gewerbe (Büro, Atelier, Praxisraum, Werkstatt) genutzt werden und keinen Wohnraum verdrängen, fallen NICHT unter die 90-Tage-Beschränkung.",
      evidence: "Stadt Luzern hat dies 2× schriftlich bestätigt (Adrian Maag, 2024).",
      what_to_look_for: "Inserate für Büros, Ateliers, Studios mit Dusche, Praxisräume. Nutzungsart im Mietvertrag = Gewerbe.",
      risk_level: "🟢 niedrig — Stadt hat Position klar.",
    },
    secondary_options: [
      { title: "Möbliertes Mid-Term", description: "Aufenthalte ≥ 30 Tage gelten als Wohnen, nicht STR — fallen nicht unter Cap.", risk: "🟡 mittel" },
    ],
  },
  "Genève": {
    cap_rule: "90 Tage / Jahr für Wohnraum",
    main_loophole: {
      title: "Möbliertes Mid-Term ≥ 1 Monat",
      description: "Aufenthalte länger als 30 Tage gelten als Mid-Term-Mietverhältnis und fallen nicht unter die STR-Regulierung.",
      evidence: "Article 30A LDTR — Cantonal Office du logement.",
      what_to_look_for: "Listings die explizit Mid-Term-Stays > 30 Tage anbieten — UN-Mitarbeiter, Expats, Studenten.",
      risk_level: "🟡 mittel — Kanton kann Vermietungszweck prüfen.",
    },
    secondary_options: [
      { title: "Gewerbliche Beherbergung mit Bewilligung", description: "Mit Hotelpatent/Beherbergungsbewilligung kein 90-Tage-Cap — aber Aufwand hoch.", risk: "🟡 mittel" },
    ],
  },

  // ====== KANTONE MIT ZWEITWOHNUNGS-CAP ======
  "_canton_VS": {
    cap_rule: "20% Zweitwohnungs-Cap (Bundesgesetz Zweitwohnungen 2012) — kein Neubau wenn Anteil überschritten",
    main_loophole: {
      title: "Bestandsobjekte uneingeschränkt vermietbar",
      description: "Objekte die VOR 11.03.2012 als Zweitwohnung bewilligt waren, sind komplett von der Beschränkung ausgenommen.",
      evidence: "Art. 11 Zweitwohnungsgesetz.",
      what_to_look_for: "Wohnungen mit Baujahr vor 2012 oder Bewilligungsdatum vor 11.03.2012. Im Grundbuch ablesbar.",
      risk_level: "🟢 niedrig — gesetzlich verbrieft.",
    },
    secondary_options: [
      { title: "Touristisch bewirtschaftete Wohnung", description: "Neubau möglich wenn permanent über strukturierte Plattform vermietet (z.B. Reka, hotelähnlich)", risk: "🟡 mittel" },
    ],
  },
  "_canton_GR": {
    cap_rule: "20% Zweitwohnungs-Cap (gleiches Bundesgesetz)",
    main_loophole: {
      title: "Bestandsobjekte vor 11.03.2012",
      description: "Identisch zum Wallis — Bestandsobjekte vor diesem Datum fallen nicht unter den Cap.",
      what_to_look_for: "Im Grundbuch / Bewilligungs-Status ablesbar.",
      risk_level: "🟢 niedrig",
    },
  },

  // ====== STÄDTE MIT VOLKSINITIATIVE / PENDENTEM VERFAHREN ======
  "Zürich": {
    cap_rule: "Aktuell keine — Volksinitiative pendent, Abstimmung erwartet H1 2026",
    main_loophole: {
      title: "Bestandsschutz wenn vor Inkrafttreten gestartet",
      description: "Wer VOR Inkrafttreten der allfälligen Regulierung bereits STR-Vermietung betreibt, geniesst voraussichtlich Bestandsschutz mit Übergangsfrist.",
      what_to_look_for: "Jetzt starten, Dokumentation lückenlos führen.",
      risk_level: "🟡 mittel — Initiative kann scheitern oder strenger werden.",
    },
  },
};

// Brief-Template — basierend auf Adrian Maag's Markus-Beispiel (Luzern Gewerbe, 2024)
// Platzhalter: {{...}} werden vom Generator ersetzt.
const LETTER_TEMPLATES = {
  // Variante A: Persönlicher Kontakt (bekannte Person)
  "personal_known": `Hallo {{vorname_eigentümer}}

{{persönlicher_aufhänger}}

Ich hoffe, dir geht es gut 😊

Ich bin aktuell auf der Suche nach einer {{wohnungs_typ}} mit {{ausstattung}} und bin dabei auf die Fläche an {{strasse_inserat}} gestossen, die ihr ab sofort vermietet.

Darf ich dir kurz mein Vorhaben vorstellen?

{{schlupfloch_block}}

Vorgesehen ist eine ruhige Kurzzeitvermietung für ausgewählte {{zielgruppe}}. Der laufende Betrieb ist gering, da die Gäste in der Regel nur zwei- bis dreimal pro Tag ein- und ausgehen. Aus meinen bisherigen {{anzahl_übernachtungen}}+ Übernachtungen ergaben sich keinerlei Reklamationen.

Was ich bieten kann:

- Natürlich pünktliche Zahlungen
- Sorgfältige und professionelle Reinigung der Immobilie, zwei- bis dreimal pro Woche
- Klare Verantwortlichkeiten und geringe Umtriebe für die Eigentümerschaft
- Gut abgesichert (STR-spezifische Versicherung)
- Interesse an einer langfristigen Miete

Ich würde mich freuen, wenn sich die Möglichkeit für einen kurzen Austausch ergibt. Falls du Fragen oder Bedenken hast, lass es mich gerne wissen, vielleicht finden wir eine gute Lösung, die für beide Seiten passt.

Ich wünsche dir einen schönen {{tageszeit}}.

Freundliche Grüsse
{{absender_name}}`,

  // Variante B: Erstkontakt (unbekannte Person)
  "personal_unknown": `Sehr geehrte/r {{anrede_eigentümer}}

Ich bin auf das Inserat für die {{wohnungs_typ}} an {{strasse_inserat}} in {{stadt}} aufmerksam geworden, das aktuell zur Vermietung ausgeschrieben ist.

Darf ich Ihnen mein Vorhaben kurz vorstellen?

{{schlupfloch_block}}

Geplant ist eine ruhige Kurzzeitvermietung für ausgewählte {{zielgruppe}}. Der laufende Betrieb ist gering — Gäste gehen typischerweise nur zwei- bis dreimal pro Tag ein und aus. Aus meinen bisherigen {{anzahl_übernachtungen}}+ Übernachtungen sind keine Reklamationen entstanden.

Was ich Ihnen bieten kann:

- Pünktliche Mietzahlungen (idealerweise Vorauszahlung des Jahresmietzins gegen Rabatt)
- Sorgfältige und professionelle Reinigung der Immobilie, mehrmals wöchentlich
- Klare Verantwortlichkeiten — Sie haben keinen administrativen Aufwand
- STR-spezifische Haftpflichtversicherung
- Interesse an einer langfristigen Miete (3+ Jahre)

Ich würde mich freuen, wenn sich die Möglichkeit für einen unverbindlichen Austausch ergibt. Bei Fragen oder Bedenken finde ich gerne mit Ihnen eine Lösung, die für beide Seiten passt.

Mit freundlichen Grüssen
{{absender_name}}
{{absender_kontakt}}`,

  // Variante C: Premium-Eigentümer (Stabilität-Pitch)
  "premium_stability": `Sehr geehrte/r {{anrede_eigentümer}}

Das Inserat für die {{wohnungs_typ}} an {{strasse_inserat}} hat mein Interesse geweckt. Mir scheint, dass Sie für Ihre Liegenschaft jemanden suchen, der Stabilität und Sorgfalt bietet — beides kann ich nachweislich zusichern.

Mein Profil:
- Seit {{seit_jahr}} aktiver Vermieter im Kurz-Aufenthalts-Segment
- Track-Record von {{anzahl_übernachtungen}}+ Übernachtungen ohne Reklamationen
- Selektive Gäste-Auswahl: ausschliesslich {{zielgruppe}}
- Detaillierte Hausordnung + Rückerstattungs-Hinterlage
- STR-Versicherung gegen Schäden bis CHF {{versicherungs_summe}}

{{schlupfloch_block}}

Was ich anbiete:
- 3-Jahres-Mietvertrag mit Indexierung an Schweizer Mietzins-Index
- Möglichkeit auf Vorauszahlung der Jahresmiete gegen 3-5% Rabatt
- Quartalsweise Reporting (Auslastung, Reinigungs-Status, allfällige Wartungs-Punkte)
- Bei vorzeitigem Vertragsende: gepflegte Übergabe der Liegenschaft

Falls die Möglichkeit besteht, würde ich gerne einen persönlichen Besichtigungs-Termin vereinbaren.

Mit freundlichen Grüssen
{{absender_name}}`,
};
