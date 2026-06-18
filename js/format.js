/* ============================================================================
   SwissSTR — format.js  ·  SwissFmt = EINE WAHRHEIT für CH-Zahlen + HTML-Escape
   ----------------------------------------------------------------------------
   Vorher dupliziert: der CHF-Kern (Math.round(n).toLocaleString('de-CH')) lag
   8× verstreut (cockpit/hotel/start/netzwerk/briefing/akquise), die HTML-Escape-
   Funktion 5-6× (teils als esc, teils als E). Hier zentralisiert (STATUS §7).

   HERLEITUNG Tausendertrenner (empirisch geprüft, nicht geraten):
   In modernem V8 (Chrome/Edge/Electron) liefert (1234567).toLocaleString('de-CH')
   bereits "1'234'567" mit GERADEM Apostroph (U+0027, charCode 39). Das ältere
   Idiom .replace(/,/g,"'") ist dort ein No-op — bleibt aber bewusst drin als
   Robustheit gegen Umgebungen (alte Engines / Node-ICU-Builds), die ',' emittieren.
   Folge: Seiten MIT und OHNE das replace erzeugen im Browser identische Ausgabe —
   genau das macht die Zentralisierung output-neutral.

   BEWUSST seiten-lokal (legitime Präsentations-Drift, NICHT hier vereinheitlicht):
   Null-Token ('–' en-dash vs '—' em-dash vs n||0 vs pass-through) und ob gerundet
   wird — das entscheidet die aufrufende Seite und bleibt am Call-Site stehen.

   Reine Funktionen, kein DOM/State — wie js/economics.js. Neue Zahl-Formatierung
   IMMER hier, nie eine zweite lokale Formel.
   ========================================================================== */
(function (root) {
  'use strict';

  // Roh-Zahl mit CH-Tausendertrenner, Dezimalen bleiben erhalten.
  function num(n) { return Number(n).toLocaleString('de-CH').replace(/,/g, "'"); }

  // Auf ganze Franken gerundet, mit Tausendertrenner.
  function int(n) { return num(Math.round(Number(n))); }

  // 'CHF ' + gerundeter Betrag. (Häufigster Fall: start/cockpit/netzwerk/briefing/akquise.)
  function chf(n) { return 'CHF ' + int(n); }

  // Vorzeichen-Variante für Differenzen (Spread/Cashflow): U+2212 MINUS,
  // Betrag NICHT zusätzlich gerundet (entspricht akquise fmtN/lab exakt).
  function signedChf(n) { return (n >= 0 ? '+' : '−') + 'CHF ' + num(Math.abs(Number(n))); }

  // HTML-Escape (4 Zeichen inkl. "), null/undefined → ''. Dominante Live-Variante.
  var ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' };
  function escapeHtml(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return ESC[c]; }); }

  root.SwissFmt = { num: num, int: int, chf: chf, signedChf: signedChf, escapeHtml: escapeHtml };
})(window);
