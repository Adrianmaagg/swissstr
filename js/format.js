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

  // Frische-AMPEL aus einem fetched-Datum (YYYY-MM-DD…). EHRLICH statt rohem Datum:
  // ein 9-Tage-alter Scrape darf nicht aussehen wie heute (Daten-First/Glaubwürdigkeit).
  // Regel (Adrian: vor einem echten Deal frisch nachziehen): ≤1d 🟢 frisch · 2–3d 🟡 ·
  // ≥4d 🔴 veraltet. Liefert {days,tier,dot,ageTxt,label}. asOf optional (Default heute).
  function freshness(dateStr, asOf) {
    if (!dateStr) return { days: null, tier: 'unknown', dot: '⚪', ageTxt: 'kein Datum', label: '⚪ kein Datum' };
    var t = Date.parse(String(dateStr).slice(0, 10));
    if (isNaN(t)) return { days: null, tier: 'unknown', dot: '⚪', ageTxt: 'kein Datum', label: '⚪ kein Datum' };
    var now = asOf ? Date.parse(String(asOf).slice(0, 10)) : Date.now();
    var days = Math.max(0, Math.round((now - t) / 864e5));
    var tier = days <= 1 ? 'fresh' : days <= 3 ? 'aging' : 'stale';
    var dot = tier === 'fresh' ? '🟢' : tier === 'aging' ? '🟡' : '🔴';
    var ageTxt = days === 0 ? 'heute' : days === 1 ? 'gestern' : days + ' Tage alt';
    return { days: days, tier: tier, dot: dot, ageTxt: ageTxt, label: dot + ' ' + ageTxt };
  }

  root.SwissFmt = { num: num, int: int, chf: chf, signedChf: signedChf, escapeHtml: escapeHtml, freshness: freshness };
})(window);
