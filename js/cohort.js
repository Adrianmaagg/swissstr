/* ============================================================================
   SwissSTR — cohort.js  ·  SwissCohort = EINE WAHRHEIT für "Profi"-Kohorten
   ----------------------------------------------------------------------------
   Es gibt ZWEI verschiedene "Profi"-Fragen, die vorher über die Seiten gedriftet
   sind (STATUS §7 "Profi-/Operator-Definition 3× gedriftet"). Sie werden hier
   bewusst GETRENNT benannt, damit sie nie wieder verwechselt werden:

   (A) isProfi  — TRACK-RECORD: "Wird dieses Inserat von einem echten Betreiber
       geführt?" Gate des Cockpit-Profi-Filters und der Startseiten-Kohorte.
       cal_managed!==false · reviews>=10 · kein Monats-Block (>=45d) ·
       (Buchungs-Velocity >=2 Bew/Monat ODER Mehrfach-Betreiber).
       Multi-Unit zählt MIT, weil die Lebenszeit-vpm neue/skalierende Profis
       verwässert (years_hosting=0 → vpm 0 → fälschlich raus). >=10 Bew bleibt Pflicht.

   (B) isBusyForOccBenchmark — BELEGUNG: "Ist dieses Inserat NACHWEISLICH busy
       genug, um die realistische Belegungs-Untergrenze eines Marktes zu setzen?"
       Gate der akquise-"Profi-Belegung". ANDERE Frage als (A): occ@30>=40 &
       reviews>=30. (Bewusst occ-basiert — bewertet, was Ernsthafte rausholen.)

   ⚠ OFFEN für Adrian (Produktentscheid, hier NICHT verändert): ob (B) künftig auf
   (A) umstellen soll. Bisher divergent; akquise behauptete fälschlich Gleichheit.

   Reine Funktionen, kein DOM/State — wie js/economics.js. HOSTPF (host-portfolios)
   wird als Argument hereingereicht, nie als globale Abhängigkeit.
   ========================================================================== */
(function (root) {
  'use strict';

  /* ---------- (A) Track-Record-Profi ---------- */
  var PROFI_VPM = 2;      // Buchungs-Velocity: Bewertungen pro Monat (reviews / Monate-als-Gastgeber)
  var MIN_REV = 10;       // Mindest-Bewertungen = echter Track-Record (kein Geister-Inserat)
  var BLOCK_MAX_D = 45;   // >=45d am Stück = Host-Sperre statt gestreuter Buchungen → kein echter Gast

  function revPerMonth(l) { return (l.reviews && l.years_hosting) ? l.reviews / (l.years_hosting * 12) : 0; }
  function hostMulti(l, hostpf) { var p = (hostpf || {})[l.host_id]; return !!p && p.total >= 2; }
  function isProfi(l, hostpf) {
    return l.cal_managed !== false && (l.reviews || 0) >= MIN_REV && (l.cal_longest_block_days || 0) < BLOCK_MAX_D
      && (revPerMonth(l) >= PROFI_VPM || hostMulti(l, hostpf));
  }

  /* ---------- (B) Belegungs-Benchmark (andere Frage als A) ---------- */
  var OCC_MIN = 40;       // occ@30 >= 40% = nachweislich gut belegt
  var OCC_REV_MIN = 30;   // + genug Track-Record, dass die Belegung belastbar ist
  function isBusyForOccBenchmark(l) {
    try { return l.cal_managed !== false && (((l.occ && l.occ['30']) || 0) >= OCC_MIN) && ((l.reviews || 0) >= OCC_REV_MIN); }
    catch (e) { return false; }
  }

  /* ---------- (C) KANONISCHE Markt-Schlagzeile — EINE WAHRHEIT für start + cockpit-Default ----------
     Damit derselbe Markt nicht drei verschiedene Belegung/Preis zeigt (start=Median ALLER,
     cockpit=Mittelwert Profi, akquise=zimmer-gematcht). Festgelegt mit Adrian (2026-06-19):
     Median der Track-Record-Profi-Kohorte über das H-Tage-Fenster (Median statt Mittelwert →
     kein Luxus-Ausreisser zieht den Schnitt hoch). Objekt-spezifische Sichten (akquise, nach
     Zimmerzahl) bleiben bewusst anders, sind aber als solche beschriftet. */
  function _median(arr) {
    var v = (arr || []).filter(function (x) { return x != null; }).sort(function (a, b) { return a - b; });
    if (!v.length) return null;
    var n = v.length;
    return n % 2 ? v[(n - 1) / 2] : Math.round((v[n / 2 - 1] + v[n / 2]) / 2);
  }
  function marketHeadline(listings, hostpf, H) {
    H = H || '30';
    var pro = (listings || []).filter(function (l) { return l.entire && isProfi(l, hostpf); });  // R2R = nur ganze Wohnungen (B-Gate)
    return {
      occ: _median(pro.map(function (l) { return (l.occ && l.occ[H] != null) ? l.occ[H] : null; })),
      price: _median(pro.map(function (l) { return l.price_chf || null; })),
      n: pro.length
    };
  }

  root.SwissCohort = {
    PROFI_VPM: PROFI_VPM, MIN_REV: MIN_REV, BLOCK_MAX_D: BLOCK_MAX_D,
    revPerMonth: revPerMonth, hostMulti: hostMulti, isProfi: isProfi,
    OCC_MIN: OCC_MIN, OCC_REV_MIN: OCC_REV_MIN, isBusyForOccBenchmark: isBusyForOccBenchmark,
    marketHeadline: marketHeadline
  };
})(window);
