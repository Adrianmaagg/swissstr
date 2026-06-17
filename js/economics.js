// js/economics.js — SwissSTR ZENTRALE RECHEN-ENGINE (Geld-Mathe).
// ============================================================================
// EINZIGE Quelle für: Belegungs-Fenster, Brutto-Run-Rate, Gast-/Host-pro-Nacht,
// Netto/Monat, Saison-Index und die Monat-für-Monat-Jahresprognose.
//
// WARUM: start.html, cockpit.html und index.html rechneten dieselben Grössen je
// mit eigener lokaler Formel → dieselbe Wohnung ergab je nach Seite andere Zahlen
// ("dauernd Unterschiede"). Ab jetzt gilt die Projekt-Regel hart:
//   *** Neue Markt-/Geld-Mathe IMMER über dieses Modul, nie eine zweite Formel. ***
// Spec + Abnahmekriterien: docs/economics-engine.md
//
// Reine Funktionen, kein DOM, kein State. Browser-Global `STREcon` (wie MARKET_COORDS).
// Verhaltensgleich zu cockpit.html v0.9.148 — die Formeln wurden 1:1 hierher gezogen.
// ============================================================================
(function (global) {
  'use strict';
  var r = Math.round;

  // Kanonische Belegungs-Fenster (Tage). Die Daten tragen occ je Fenster.
  var WINDOWS = ['3', '7', '14', '30', '45', '60', '90', '120'];
  // Default-Fenster = 30 T: gesettelt-mittlerer Horizont, Vorlaufzeit-entzerrt,
  // methodik-konform (kurze Fenster überzeichnen, lange sind reiner Ausblick).
  var DEFAULT_WINDOW = '30';

  // Kanonische R2R-Deal-Annahmen (CHF). Identisch auf allen Seiten; im Cockpit
  // überschreibt der Nutzer einzelne Felder (localStorage), die Defaults bleiben hier.
  //   gastFee/hostFee = Airbnb-Service-Gebühr Gast/Host in %
  //   kurtaxe = CHF/Nacht · traeger = wer die Kurtaxe zahlt ('Gast'|'Host')
  //   miete/internettv/wasserstrom = Fixkosten/Monat · clean/verbrauch = variabel je Reinigung
  //   stayLen = Schlüssel: alle X belegten Nächte 1 Reinigung (= Ø Aufenthaltsdauer)
  var DEFAULT_COSTS = {
    gastFee: 15, hostFee: 3, kurtaxe: 4, traeger: 'Gast',
    miete: 1800, internettv: 70, wasserstrom: 120, clean: 90, verbrauch: 15, stayLen: 3
  };

  function _costs(c) {
    if (!c) return DEFAULT_COSTS;
    var o = {}; for (var k in DEFAULT_COSTS) o[k] = DEFAULT_COSTS[k];
    for (var j in c) if (c[j] != null && c[j] !== '') o[j] = c[j];
    return o;
  }

  // Belegung% eines Inserats am Fenster H (oder null).
  function occAt(listing, H) {
    return (listing && listing.occ && listing.occ[H] != null) ? listing.occ[H] : null;
  }

  // ── BRUTTO Run-Rate (🟡 Modell): Nachtpreis × Belegung% × Tage. Vor allen Kosten.
  function grossMonthly(price, occPct) {
    return (price != null && occPct != null) ? r(price * occPct / 100 * 30) : null;
  }
  function grossAnnual(price, occPct) {
    return (price != null && occPct != null) ? r(price * occPct / 100 * 365) : null;
  }

  // ── Pro Nacht
  // Was der Gast zahlt = Nachtpreis + Airbnb-Gebühr (Gast %) + Kurtaxe (wenn Gast trägt).
  function gastPerNight(price, costs) {
    if (price == null) return null;
    var c = _costs(costs);
    return r(price * (1 + c.gastFee / 100) + (c.traeger === 'Gast' ? c.kurtaxe : 0));
  }
  // Was beim Host ankommt = Nachtpreis − Airbnb-Host-Gebühr % − Kurtaxe (wenn Host trägt).
  // Noch VOR den eigenen Kosten (Miete/Reinigung).
  function hostPerNight(price, costs) {
    if (price == null) return null;
    var c = _costs(costs);
    return r(price * (1 - c.hostFee / 100) - (c.traeger === 'Host' ? c.kurtaxe : 0));
  }

  // Belegte Nächte und Reinigungen (zentral, damit überall identisch gerundet).
  function nightsFor(occPct, days) { return r((occPct || 0) / 100 * (days || 30)); }
  function staysFor(nights, stayLen) { return stayLen > 0 ? r(nights / stayLen) : 0; }

  // Monats-Auslastung aus Jahresschnitt-Anker × Saison-Index, physisch gedeckelt.
  function monthOcc(anchorOcc, seasonIdx, cap) {
    var c = (cap == null) ? 92 : cap;
    return Math.max(0, Math.min(c, r((anchorOcc || 0) * (seasonIdx == null ? 1 : seasonIdx))));
  }

  // ── NETTO / Monat (Standard 30-Tage-Basis). Belegung% steuert die Einnahmen;
  //    die Miete läuft für alle Tage → die Belegung entscheidet über Plus/Minus.
  // Gibt das volle Geld-Fluss-Objekt zurück (für Cockpit-Kästen UND start-Karte).
  function netMonthly(opts) {
    opts = opts || {};
    var price = opts.price, occPct = opts.occPct;
    if (price == null || occPct == null) return null;
    var c = _costs(opts.costs);
    var days = opts.days || 30;
    var revNight = hostPerNight(price, c);
    var nights = nightsFor(occPct, days);
    var stays = staysFor(nights, c.stayLen);
    var einnahmen = revNight * nights;
    var fix = c.miete + c.internettv + c.wasserstrom;
    var variabel = stays * (c.clean + c.verbrauch);
    var netto = r(einnahmen - fix - variabel);
    return {
      revNight: revNight, nights: nights, stays: stays,
      einnahmen: einnahmen, fix: fix, variabel: variabel,
      netto: netto, nettoNacht: nights > 0 ? r(netto / nights) : null
    };
  }

  // ── Saison-Index aus BFS-Monats-Logiernächten: pro Kalendermonat auf Jahresschnitt 1.0
  //    normiert (Juli ≈ 1.42 Hochsaison, Januar ≈ 0.58 Nebensaison). null wenn keine Daten.
  function seasonalIndex(bfs) {
    if (!bfs || !bfs.months || !bfs.months.length) return null;
    var sm = Number(String(bfs.start).split('-')[1]) || 1;
    var sums = new Array(12); var cnts = new Array(12);
    for (var i = 0; i < 12; i++) { sums[i] = 0; cnts[i] = 0; }
    bfs.months.forEach(function (v, i) {
      if (v == null) return; var mo = (sm - 1 + i) % 12; sums[mo] += v; cnts[mo]++;
    });
    var avg = sums.map(function (s, i) { return cnts[i] ? s / cnts[i] : null; });
    var valid = avg.filter(function (x) { return x != null; });
    if (!valid.length) return null;
    var mean = valid.reduce(function (a, b) { return a + b; }, 0) / valid.length;
    return avg.map(function (x) { return x == null ? 1 : +(x / mean).toFixed(3); });
  }

  // ── NETTO Jahres-Prognose Monat-für-Monat (🟡 Modell aus zwei echten Quellen):
  //    Niveau = anchorOcc (Jahresschnitt) · Form = seasonIndex (BFS). Exakt dasselbe
  //    Geld-Modell wie netMonthly, nur pro Kalendermonat mit echten Tagen (28–31) und part.
  //    `months` = [{y, m0, dim, part}]. Gibt rows + Summen zurück (DOM macht die Seite).
  function annualForecast(opts) {
    opts = opts || {};
    var price = opts.price, anchorOcc = opts.anchorOcc, index = opts.index, months = opts.months;
    if (price == null || anchorOcc == null || !index || !months) return null;
    var c = _costs(opts.costs);
    var cap = opts.occCap == null ? 92 : opts.occCap;
    var revNight = hostPerNight(price, c);
    var fixM = c.miete + c.internettv + c.wasserstrom;
    var tInc = 0, tFix = 0, tVar = 0, tN = 0, occW = 0, dW = 0;
    var rows = months.map(function (o) {
      var occM = monthOcc(anchorOcc, index[o.m0], cap);
      var nights = r(occM / 100 * o.dim * o.part);
      var stays = staysFor(nights, c.stayLen);
      var inc = revNight * nights;
      var varc = stays * (c.clean + c.verbrauch);
      var fix = r(fixM * o.part);
      var net = inc - fix - varc;
      tInc += inc; tFix += fix; tVar += varc; tN += nights;
      occW += occM * o.dim * o.part; dW += o.dim * o.part;
      return { y: o.y, m0: o.m0, part: o.part, occM: occM, nights: nights, inc: inc, net: net };
    });
    return {
      rows: rows, revNight: revNight,
      tInc: tInc, tFix: tFix, tVar: tVar, tNet: tInc - tFix - tVar,
      tNights: tN, avgOcc: dW ? r(occW / dW) : null
    };
  }
  // Schneller Netto-Gesamtwert für einen Anker (Konservativ-Floor) ohne rows.
  function annualNet(opts) { var f = annualForecast(opts); return f ? f.tNet : null; }

  // ── R2R-AKQUISE: Wohnungsgrösse → Marktmiete → wieviel Miete trägt das STR? ──────────
  // Schweizer Kanton: Name (de/fr/it) → 2-Buchstaben-Code (Join auf BFS data/mietpreise.json).
  var CANTON_CODE = {
    'Zürich': 'ZH', 'Bern': 'BE', 'Berne': 'BE', 'Luzern': 'LU', 'Uri': 'UR', 'Schwyz': 'SZ',
    'Obwalden': 'OW', 'Nidwalden': 'NW', 'Glarus': 'GL', 'Zug': 'ZG', 'Freiburg': 'FR', 'Fribourg': 'FR',
    'Solothurn': 'SO', 'Basel-Stadt': 'BS', 'Basel-Landschaft': 'BL', 'Schaffhausen': 'SH',
    'Appenzell A.Rh.': 'AR', 'Appenzell Ausserrhoden': 'AR', 'Appenzell I.Rh.': 'AI', 'Appenzell Innerrhoden': 'AI',
    'St. Gallen': 'SG', 'Sankt Gallen': 'SG', 'Graubünden': 'GR', 'Aargau': 'AG', 'Thurgau': 'TG',
    'Tessin': 'TI', 'Ticino': 'TI', 'Waadt': 'VD', 'Vaud': 'VD', 'Wallis': 'VS', 'Valais': 'VS',
    'Neuenburg': 'NE', 'Neuchâtel': 'NE', 'Genf': 'GE', 'Genève': 'GE', 'Jura': 'JU'
  };

  // BFS-Nettomiete (kalt) → Bruttomiete inkl. NK (Akonto Neben-/Heizkosten). Annahme 🟡:
  // CH-typisch ~13% Aufschlag (≈ CHF 2.5–3/m²/Mt). Macht BFS vergleichbar mit der Cockpit-„Miete inkl. NK".
  var BFS_NK_UPLIFT = 1.13;

  // Schlafzimmer → CH-Zimmerzahl (Heuristik 🟡): Schlafzi + Wohnraum (+ Halbzimmer-Tradition).
  // 3 Schlafzi ≈ 4.5-Zi-Wohnung (Adrians Beispiel). null wenn unbekannt.
  function roomsFromBedrooms(bedrooms) {
    return (bedrooms == null || bedrooms < 0) ? null : bedrooms + 1.5;
  }

  // BFS-Marktmiete (Nettomiete) für eine Zimmerzahl aus den Kantons-Buckets (1..5; 5 = 5+).
  // Lineare Interpolation zwischen ganzen Buckets; 4.5 Zi → Mittel aus 4 und 5. null wenn fehlt.
  function bfsRent(roomsTable, rooms) {
    if (!roomsTable || rooms == null) return null;
    var keys = Object.keys(roomsTable).map(Number).filter(function (n) { return !isNaN(n); }).sort(function (a, b) { return a - b; });
    if (!keys.length) return null;
    var lo = keys[0], hi = keys[keys.length - 1];
    var x = Math.max(lo, Math.min(hi, rooms));          // auf verfügbare Spanne klemmen
    var f = Math.floor(x), c = Math.ceil(x);
    var vf = roomsTable[f] != null ? roomsTable[f] : roomsTable[String(f)];
    var vc = roomsTable[c] != null ? roomsTable[c] : roomsTable[String(c)];
    if (vf == null) return vc != null ? vc : null;
    if (vc == null || f === c) return vf;
    return r(vf + (vc - vf) * (x - f));
  }
  // Bruttomiete (inkl. NK) aus BFS-Netto.
  function bfsRentGross(roomsTable, rooms) {
    var net = bfsRent(roomsTable, rooms);
    return net == null ? null : r(net * BFS_NK_UPLIFT);
  }

  // Breakeven-Miete (inkl. NK, wie das Cockpit-Feld 'miete'): höchste Miete, bei der Netto/Monat
  // = targetNet (Default 0). = Host-Einnahmen − variabel − Internet/TV − Wasser/Strom − targetNet.
  // → das ist „bis hierhin trägt das STR die Miete". Belegung% = ehrliche Basis wählen (Jahresschnitt!).
  function breakevenRent(opts) {
    opts = opts || {};
    var price = opts.price, occPct = opts.occPct;
    if (price == null || occPct == null) return null;
    var c = _costs(opts.costs), days = opts.days || 30, targetNet = opts.targetNet || 0;
    var revNight = hostPerNight(price, c);
    var nights = nightsFor(occPct, days);
    var variabel = staysFor(nights, c.stayLen) * (c.clean + c.verbrauch);
    return r(revNight * nights - variabel - c.internettv - c.wasserstrom - targetNet);
  }

  // R2R-Spielraum: wieviel % über der Marktmiete kann der Operator bieten und bleibt bei targetNet?
  // breakeven & marketRent MÜSSEN dieselbe Basis sein (beide inkl. NK). null wenn unbestimmt.
  function rentHeadroomPct(breakeven, marketRent) {
    return (marketRent > 0 && breakeven != null) ? r((breakeven / marketRent - 1) * 100) : null;
  }

  var API = {
    WINDOWS: WINDOWS, DEFAULT_WINDOW: DEFAULT_WINDOW, DEFAULT_COSTS: DEFAULT_COSTS,
    occAt: occAt, grossMonthly: grossMonthly, grossAnnual: grossAnnual,
    gastPerNight: gastPerNight, hostPerNight: hostPerNight,
    nightsFor: nightsFor, staysFor: staysFor, monthOcc: monthOcc,
    netMonthly: netMonthly, seasonalIndex: seasonalIndex,
    annualForecast: annualForecast, annualNet: annualNet,
    CANTON_CODE: CANTON_CODE, BFS_NK_UPLIFT: BFS_NK_UPLIFT,
    roomsFromBedrooms: roomsFromBedrooms, bfsRent: bfsRent, bfsRentGross: bfsRentGross,
    breakevenRent: breakevenRent, rentHeadroomPct: rentHeadroomPct
  };
  global.STREcon = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
