/* ============================================================================
   SwissSTR — akquise.deal.js  ·  Deal-Dossier-ENGINE der Akquise-Seite
   ----------------------------------------------------------------------------
   1:1 aus akquise.html ausgelagert (STATUS §7, Schritt 6 — Split nach Concern).
   Diese Hälfte = die ANALYSE: Markt-/Kohorte-/Saison-Daten, Cockpit-Cross-Filter,
   Such-Strategien, Schlupflöcher, Checkliste, Brief-Generator und das volle
   DEAL-DOSSIER (dossOffer/dossDealScore/dossMoney/dossForecast/renderDossier).
   Beantwortet „gegebener Markt/Objekt → Deal-Analyse".

   Klassisches Skript (kein ES-Modul, non-strict wie das Original) → identischer
   globaler Scope. Lädt VOR js/akquise.agent.js (die Agent-/Orchestrierungs-Hälfte
   ruft diese Engine auf, nicht umgekehrt). Setzt voraus: SwissFmt, SwissCohort,
   data.js (markets/coords), loopholes.js, STREcon. Verbatim, KEIN Verhalten geändert.
   ========================================================================== */
  // ====================== Akquise-Seite (eigenstaendig) ======================
  // Liest die statischen Markt-Daten (js/data.js) + Schlupfloecher (js/loopholes.js)
  // und spricht den lokalen Heimstatt-Agenten an (127.0.0.1:8782). Nichts verlaesst
  // den Laptop automatisch; Versand passiert nur manuell ueber Gmail/Mail-App.

  // occ kommt direkt aus der statischen Markt-Tabelle (modellierter Wert, 🟡).
  function occOf(m) { return m.occ; }
  function openMarket(name) { window.open('index.html', '_blank'); }

  // ---- Profi-Belegung: Belegungs-Benchmark aus nachweislich gut belegten Inseraten ----
  // Wenn fuer den Markt eine cockpit-<markt>.json vorliegt, kommt die STR-Belegung aus den
  // Inseraten, die NACHWEISLICH busy sind (occ@30>=40 & reviews>=30) — zentral in js/cohort.js
  // als SwissCohort.isBusyForOccBenchmark. WICHTIG: das ist eine ANDERE Frage als der Cockpit-
  // Track-Record-Filter (SwissCohort.isProfi, vpm/hostMulti-basiert) — bewusst getrennt, NICHT
  // identisch (frueherer Kommentar behauptete das faelschlich). Angleichen waere ein Produktentscheid.
  // angezeigte Belegung = Median occ@30 dieser Kohorte (robust gg. einzelne Ausreisser,
  // bewertet was Ernsthafte rausholen, NICHT den von Halbherzigen gedrueckten Median).
  // Kein Live-Cockpit → Fallback auf den Modellwert occOf (klar gekennzeichnet).
  const akqIsProfi = SwissCohort.isBusyForOccBenchmark;
  function akqMedian(arr) {
    const v = arr.filter(x => x != null).sort((a, b) => a - b);
    if (!v.length) return null;
    return v.length % 2 ? v[(v.length - 1) / 2] : (v[v.length / 2 - 1] + v[v.length / 2]) / 2;
  }
  // Cache: marktname -> { occ, nProfi, nAll, src } | { src:'none' } (kein File) | undefined (noch nicht geladen)
  const AKQ_COCKPIT_OCC = {};
  // BFS-Marktmiete (Nettomiete je Kanton×Zimmer, data/mietpreise.json) — Anker für den R2R-Spielraum.
  let AKQ_RENTS = null;   // { cantons:{CODE:{rooms:{...}}}, _meta:{year} } | null (nicht/noch nicht geladen)
  function akqCockpitFile(name) {
    // js/data.js-Marktname -> Dateiname (lowercase, Umlaute bleiben wie im data/-Ordner).
    return 'data/cockpit-' + String(name).toLowerCase().trim() + '.json';
  }
  async function loadCockpitOcc(name) {
    if (AKQ_COCKPIT_OCC[name] !== undefined) return AKQ_COCKPIT_OCC[name];
    try {
      const r = await fetch(akqCockpitFile(name), { cache: 'no-cache' });
      if (!r.ok) { AKQ_COCKPIT_OCC[name] = { src: 'none' }; return AKQ_COCKPIT_OCC[name]; }
      const d = await r.json();
      const ls = (d && d.listings) || [];
      const profis = ls.filter(akqIsProfi);
      const occ = akqMedian(profis.map(l => (l.occ && l.occ['30'])));
      // Median-STR-Nachtpreis der Profi-Kohorte (sonst aller Inserate) — Basis fuer den Geldrechner.
      const priceMed = akqMedian((profis.length ? profis : ls).map(l => l.price_chf).filter(x => x));
      if (occ == null) { AKQ_COCKPIT_OCC[name] = { src: 'none', price: priceMed != null ? Math.round(priceMed) : null, listings: ls }; return AKQ_COCKPIT_OCC[name]; }
      AKQ_COCKPIT_OCC[name] = { occ: Math.round(occ), price: priceMed != null ? Math.round(priceMed) : null, nProfi: profis.length, nAll: ls.length, listings: ls, src: 'live' };
    } catch (e) {
      AKQ_COCKPIT_OCC[name] = { src: 'none' };
    }
    return AKQ_COCKPIT_OCC[name];
  }

  // ---- Gescrapte Nicht-BFS-Märkte auflösbar machen (Arth/Spreitenbach/Dietikon/Ennetbürgen …) ----
  // Manifest data/cockpit-markets.json kennt ~29 gescrapte Märkte; nicht alle stehen in der
  // BFS-Liste markets[] (js/data.js). Fehlt ein Markt dort, gibt akqMarketFor(null) → „unbekannt"
  // und der Lead lädt kein Dashboard. Fix: einmalig die Manifest-Märkte als synthetische Einträge
  // ergänzen (gleiche Feld-Form wie js/data.js: name/canton(Code)/tags[]/occ:null), NUR was fehlt.
  // canton aus dem Manifest ist der volle Name ("Schwyz") → auf den 2-Buchstaben-Code mappen,
  // damit Such-Strategien (HOMEGATE_KANTON) und BFS-Marktmiete (AKQ_RENTS.cantons[code]) greifen.
  const AKQ_CANTON_CODE = {
    'zürich':'ZH','zuerich':'ZH','bern':'BE','luzern':'LU','uri':'UR','schwyz':'SZ',
    'obwalden':'OW','nidwalden':'NW','glarus':'GL','zug':'ZG','freiburg':'FR','fribourg':'FR',
    'solothurn':'SO','basel-stadt':'BS','basel-landschaft':'BL','schaffhausen':'SH',
    'appenzell ausserrhoden':'AR','appenzell innerrhoden':'AI','st. gallen':'SG','st.gallen':'SG',
    'sankt gallen':'SG','graubünden':'GR','graubuenden':'GR','aargau':'AG','thurgau':'TG',
    'tessin':'TI','ticino':'TI','waadt':'VD','vaud':'VD','wallis':'VS','valais':'VS',
    'neuenburg':'NE','neuchâtel':'NE','genf':'GE','genève':'GE','geneve':'GE','jura':'JU',
  };
  let AKQ_MARKETS_AUGMENTED = false;
  async function akqAugmentMarkets() {
    if (AKQ_MARKETS_AUGMENTED) return;
    try {
      await akqLoadFactBase();                                  // lädt AKQ_MARKETS_JSON (Manifest)
      if (typeof markets === 'undefined' || !Array.isArray(markets)) return;
      const mm = AKQ_MARKETS_JSON && Array.isArray(AKQ_MARKETS_JSON.markets) ? AKQ_MARKETS_JSON.markets : [];
      const have = new Set(markets.map(m => String(m.name || '').toLowerCase().trim()));
      let added = 0;
      for (const e of mm) {
        const nm = String(e.name || '').trim();
        if (!nm || have.has(nm.toLowerCase())) continue;        // BFS-Markt schon da → NICHT überschreiben
        const cc = e.canton ? (AKQ_CANTON_CODE[String(e.canton).toLowerCase().trim()] || null) : null;
        markets.push({ name: nm, canton: cc, tags: [], occ: null, _scraped: true });
        have.add(nm.toLowerCase());
        added++;
      }
      AKQ_MARKETS_AUGMENTED = true;
      return added;
    } catch (e) { AKQ_MARKETS_AUGMENTED = true; }
  }
  // Markt-Dropdowns (neu) befüllen — auch die ergänzten Märkte sollen selektierbar sein,
  // sonst greift [...ms.options].some(...) in akqSelectLead/akqApplyLeadFromHash nicht.
  function akqRebuildMarketSelects() {
    if (typeof markets === 'undefined' || !Array.isArray(markets) || !markets.length) return;
    const opts = markets.slice().sort((a, b) => a.name.localeCompare(b.name, 'de'))
      .map(m => `<option value="${m.name}">${m.name}${m._scraped ? ' ·🟡' : ''}</option>`).join('');
    for (const id of ['dossMarket', 'akqStratMarket']) {
      const sel = document.getElementById(id);
      if (!sel) continue;
      const keep = sel.value;
      sel.innerHTML = opts;
      if (keep && [...sel.options].some(o => o.value === keep)) sel.value = keep;
      else if (id === 'dossMarket') sel.value = 'Kriens';
    }
  }

  // ============================================================================
  // COCKPIT-CROSS-FILTER (portiert aus cockpit.html barChart/render). Der Kern:
  // die GEFILTERTE Kohorte (akqFiltered) treibt den Ertrag — dossMoney/dossOffer
  // nehmen Median occ@30 UND Median price aus genau diesen vergleichbaren Inseraten.
  // Eigener State (AKQ_F) + eigene Helfer, damit nichts mit dem Cockpit kollidiert.
  // ============================================================================
  const AKQ_F = { group: new Set(), rating: new Set(), vol: new Set(), type: new Set(), cap: new Set(), rooms: new Set() };
  let AKQ_METRIC = 'occ';   // 'occ' (Auslastung %) | 'umsatz' (CHF/Mt, Brutto-Modell)
  // Band-Helfer (1:1 cockpit.html-Logik)
  const akqOcc30 = l => (l && l.occ && l.occ['30'] != null) ? l.occ['30'] : null;
  const akqGroupOf = l => l.superhost ? 'Superhost' : 'Rest';
  const akqRatingBand = l => { const r = l.rating; if (r == null) return '?'; if (r >= 4.8) return '4.8–5.0'; if (r >= 4.65) return '4.65–4.79'; return 'unter 4.65'; };
  const akqVolBand = l => { const v = l.reviews || 0; if (v >= 100) return '100+ Bew.'; if (v >= 30) return '30–99'; return 'unter 30'; };
  const akqCapBucket = c => c == null ? '?' : c >= 5 ? '5+P' : c + 'P';
  const akqRoomBucket = b => b == null ? '?' : b >= 4 ? '4+ Zi' : b + ' Zi';
  // Objekt-Zimmer → Zimmer-Band (für die Default-Vorwahl; 4.5 Zi → "4+ Zi").
  function akqRoomBand(rooms) { const b = Math.floor((rooms || 0)); if (b >= 4) return '4+ Zi'; if (b >= 1) return b + ' Zi'; return null; }
  // 90-Tage-Cap (STR wirtschaftlich gekappt): aus data.js-Tag ODER Kanton GE / Stadt Luzern. EINE Quelle (C39).
  function akqHasCap90(m) { return (m.tags || []).some(t => t.includes('90-Tage-Cap')) || m.canton === 'GE' || m.name === 'Luzern'; }

  // Aktuelle Markt-Inserate (volles listings-Array aus dem Cockpit-Cache).
  function akqMarketListings(name) { const c = AKQ_COCKPIT_OCC[name]; return (c && Array.isArray(c.listings)) ? c.listings : []; }

  function akqMatchDim(l, dim) {
    const s = AKQ_F[dim]; if (!s || !s.size) return true;
    const v = dim === 'group' ? akqGroupOf(l) : dim === 'rating' ? akqRatingBand(l) : dim === 'vol' ? akqVolBand(l)
      : dim === 'type' ? (l.entire ? 'Wohnung' : 'Zimmer') : dim === 'cap' ? akqCapBucket(l.capacity) : akqRoomBucket(l.bedrooms);
    return s.has(v);
  }
  function akqPass(l, except) {
    for (const d of ['group', 'rating', 'vol', 'type', 'cap', 'rooms']) { if (except !== d && !akqMatchDim(l, d)) return false; }
    return true;
  }
  // except = eine Dimension, die beim Chart-Berechnen NICHT mitfiltert (sonst hätte ihr Balken immer n der Auswahl).
  function akqFiltered(name, except) { return akqMarketListings(name).filter(l => akqPass(l, except)); }
  function akqAvgOcc(list) { const v = list.map(akqOcc30).filter(x => x != null); return v.length ? Math.round(v.reduce((a, b) => a + b, 0) / v.length) : null; }
  function akqMedOcc(list) { return akqMedian(list.map(akqOcc30)); }
  const akqUmsatz = l => STREcon.grossMonthly(l.price_chf, akqOcc30(l));
  function akqMedUmsatz(list) { const v = akqMedian(list.map(akqUmsatz).filter(x => x != null)); return v == null ? null : Math.round(v); }
  function akqMedPrice(list) { const v = akqMedian(list.map(l => l.price_chf).filter(x => x)); return v == null ? null : Math.round(v); }

  // Ertrags-Kohorte: occ + price aus dem GEFILTERTEN Set (treibt dossMoney/dossOffer).
  // Nur wenn ein Filter aktiv ist UND das Set nicht leer — sonst Fallback auf die Profi-Kohorte.
  // roomsOverride (optional): STABILE per-Objekt-Kohorte, UNABHÄNGIG vom globalen AKQ_F.
  // Gefiltert nur nach dem Zimmer-Band DIESES Objekts + ganze Wohnung — feste Logik je Lead.
  // So springen die Board-Verdicts NICHT mehr, wenn man einen anderen Lead anklickt.
  function akqCohort(name, roomsOverride) {
    if (roomsOverride != null) {
      const rb = akqRoomBand(roomsOverride);
      let list = akqMarketListings(name).filter(l => l.entire);            // ganze Wohnung
      if (rb) { const byRoom = list.filter(l => akqRoomBucket(l.bedrooms) === rb); if (byRoom.length) list = byRoom; }
      if (!list.length) return null;
      const occ = akqMedOcc(list), price = akqMedPrice(list);
      if (occ == null) return null;
      return { occ: Math.round(occ), price: price, n: list.length, src: 'stable' };
    }
    const anyF = ['group', 'rating', 'vol', 'type', 'cap', 'rooms'].some(d => AKQ_F[d].size > 0);
    if (!anyF) return null;
    const list = akqFiltered(name, null);
    if (!list.length) return null;
    const occ = akqMedOcc(list), price = akqMedPrice(list);
    if (occ == null) return null;
    return { occ: Math.round(occ), price: price, n: list.length, src: 'cohort' };
  }

  // Ein Balken-Panel (Median occ ODER Umsatz je Kategorie unter den ANDEREN Filtern; leer = Marktlücke ⚑).
  function akqBarChart(elId, name, dim, cats) {
    const el = document.getElementById(elId); if (!el) return;
    const base = akqFiltered(name, dim);
    const rows = cats.map(c => { const list = base.filter(c.test); return { c, n: list.length, val: AKQ_METRIC === 'occ' ? akqMedOcc(list) : akqMedUmsatz(list) }; });
    const maxVal = AKQ_METRIC === 'occ' ? 100 : Math.max(1, ...rows.map(r => r.val || 0));
    const head = `<div class="bar-head"><span></span><span></span><span class="v">${AKQ_METRIC === 'occ' ? 'Ø Auslastung' : 'Umsatz/Mt'}</span><span class="v"><b>Inserate</b></span></div>`;
    el.innerHTML = head + rows.map(r => {
      const { c, n, val } = r;
      const sel = AKQ_F[dim].has(c.val);
      const empty = n === 0;
      const occv = AKQ_METRIC === 'occ' ? (val == null ? null : Math.round(val)) : val;
      const width = empty ? 100 : (occv == null ? 0 : (AKQ_METRIC === 'occ' ? occv : Math.round(occv / maxVal * 100)));
      const disp = empty ? '<span class="luecke" style="white-space:nowrap">⚑ Marktlücke</span>'
        : (occv == null ? '<span style="color:var(--faint)">–</span>' : (AKQ_METRIC === 'occ' ? occv + '%' : chf(occv)));
      return `<div class="bar-row${sel ? ' on' : ''}${empty ? ' empty' : ''}" data-d="${dim}" data-v="${akqEsc(c.val)}"${empty ? ' title="keine vergleichbaren Inserate in dieser Kategorie — mögliche Marktlücke"' : ''}>
        <span class="blab">${akqEsc(c.label)}</span>
        <div class="btrack">${empty ? '' : `<div class="bfill ${sel ? 'sel' : ''}" style="width:${width}%"></div>`}</div>
        <span class="bval">${disp}</span>
        <span class="bcnt" title="Anzahl vergleichbarer Inserate">${n}</span></div>`;
    }).join('');
    el.querySelectorAll('.bar-row:not(.empty)').forEach(r => r.onclick = () => akqToggleFilter(r.dataset.d, r.dataset.v));
  }
  function akqEsc(s) { return SwissFmt.escapeHtml(s); }

  // Toggle eines Filters → Panels + Ertrags-Kette SOFORT neu (der Kern des Wirings).
  function akqToggleFilter(dim, val) {
    const s = AKQ_F[dim]; s.has(val) ? s.delete(val) : s.add(val);
    try { renderDossier(); } catch (e) {}   // rechnet Ertrag/Netto/Spielraum/Prognose neu
    try { akqRenderFilters(); } catch (e) {}
  }

  // Das ganze Dashboard rendern (Panels + KPIs + Chips + Metrik-Schalter). Markt = aktuelles Dossier-Objekt.
  function akqRenderFilters() {
    const sel = document.getElementById('dossMarket'); if (!sel) return;
    const mName = sel.value;
    const tag = document.getElementById('akqXfMarketTag'); if (tag) tag.textContent = '· ' + mName;
    const list = akqMarketListings(mName);
    // Kein Live-Cockpit für den Markt → ehrlicher Hinweis, kein geratener Balken.
    if (!list.length) {
      document.querySelectorAll('#akqXfDetails .akqxf-card > div').forEach(d => d.innerHTML = '');
      const k = document.getElementById('akqXfKpis'); if (k) k.innerHTML = '';
      const a = document.getElementById('akqXfActive'); if (a) a.innerHTML = '<span class="text-[11px] text-[color:var(--faint)]">Für ' + akqEsc(mName) + ' liegt (noch) keine Cockpit-Inserateliste vor — die Filter erscheinen, sobald data/cockpit-' + akqEsc(mName.toLowerCase()) + '.json da ist. Ertrag rechnet solange aus dem Modell.</span>';
      const f = document.getElementById('akqXfFoot'); if (f) f.innerHTML = '';
      return;
    }
    // Metrik-Schalter
    document.querySelectorAll('#akqXfMetricTog button').forEach(b => b.classList.toggle('on', b.dataset.m === AKQ_METRIC));
    document.querySelectorAll('.akqxf-mword').forEach(e => e.textContent = AKQ_METRIC === 'occ' ? 'Auslastung' : 'Umsatz');
    const mn = document.getElementById('akqXfMetricNote'); if (mn) mn.innerHTML = AKQ_METRIC === 'occ' ? 'Median occ@30T je Kategorie' : '🟡 Median-Umsatz/Mt = Preis × Auslastung(30T) × 30 N · Brutto (Modell)';
    // KPIs der aktuellen Auswahl
    const cur = akqFiltered(mName, null);
    const occ = akqMedOcc(cur), price = akqMedPrice(cur), sh = cur.filter(l => l.superhost).length;
    const kp = document.getElementById('akqXfKpis');
    if (kp) kp.innerHTML = `
      <div class="akqxf-kpi"><div class="k">Auslastung 30T</div><div class="v num-tick" style="color:var(--gold)">${occ == null ? '–' : Math.round(occ) + '%'}</div></div>
      <div class="akqxf-kpi"><div class="k">vergleichbare Inserate</div><div class="v num-tick">${cur.length}</div></div>
      <div class="akqxf-kpi"><div class="k">Median Preis/N</div><div class="v num-tick">${price ? chf(price) : '–'}</div></div>
      <div class="akqxf-kpi"><div class="k">davon Superhost</div><div class="v num-tick" style="color:var(--green)">${sh}</div></div>`;
    // aktive Filter-Chips
    const chips = [];
    for (const d of ['group', 'rating', 'vol', 'type', 'cap', 'rooms']) for (const v of AKQ_F[d]) chips.push(`<button class="akqxf-fchip" data-d="${d}" data-v="${akqEsc(v)}">${akqEsc(v)}<span class="x">✕</span></button>`);
    const act = document.getElementById('akqXfActive');
    if (act) {
      act.innerHTML = chips.length ? chips.join('') : '<span class="text-[11px] text-[color:var(--faint)]">Kein Filter aktiv — klick einen oder mehrere Balken, um die Vergleichs-Kohorte zu schärfen. Der Ertrag rechnet sofort neu.</span>';
      act.querySelectorAll('.akqxf-fchip').forEach(b => b.onclick = () => akqToggleFilter(b.dataset.d, b.dataset.v));
    }
    // Panels
    akqBarChart('akqXfGroup', mName, 'group', [
      { label: 'Superhost', val: 'Superhost', test: l => l.superhost },
      { label: 'Rest', val: 'Rest', test: l => !l.superhost },
    ]);
    akqBarChart('akqXfRating', mName, 'rating', ['4.8–5.0', '4.65–4.79', 'unter 4.65'].map(v => ({ label: v, val: v, test: l => akqRatingBand(l) === v })));
    akqBarChart('akqXfVol', mName, 'vol', ['100+ Bew.', '30–99', 'unter 30'].map(v => ({ label: v, val: v, test: l => akqVolBand(l) === v })));
    akqBarChart('akqXfType', mName, 'type', [
      { label: 'Ganze Wohnung', val: 'Wohnung', test: l => l.entire },
      { label: 'Zimmer', val: 'Zimmer', test: l => !l.entire },
    ]);
    akqBarChart('akqXfCap', mName, 'cap', ['2P', '3P', '4P', '5+P'].map(v => ({ label: v, val: v, test: l => akqCapBucket(l.capacity) === v })));
    akqBarChart('akqXfRooms', mName, 'rooms', ['1 Zi', '2 Zi', '3 Zi', '4+ Zi'].map(v => ({ label: v, val: v, test: l => akqRoomBucket(l.bedrooms) === v })));
    const foot = document.getElementById('akqXfFoot');
    if (foot) { const ch = akqCohort(mName); foot.innerHTML = ch ? `Ertrag rechnet aus <b style="color:var(--gold)">${ch.n} vergleichbaren Inseraten</b> (Median occ@30 ${ch.occ}%${ch.price ? ' · Preis ' + chf(ch.price) : ''}) — 🟢 live aus dem Cockpit.` : 'Kein Filter aktiv — Ertrag aus der Profi-Kohorte des Markts (Default).'; }
  }

  // ---- Saison-Profil je Markt (market-facts.json → seasonalIndex/occ_band) für die Jahres-Prognose ----
  // Exakt wie cockpit.html load(): eigener BFS-Monatsdatensatz, sonst Regional-Proxy (cockpit-season-proxy.json).
  // Cache: markt -> { index:[12], occ_band, proxy, fetched } | { src:'none' } | undefined (noch nicht geladen).
  const AKQ_SEASON = {};
  let AKQ_FACTS = null, AKQ_PROXY = null, AKQ_MARKETS_JSON = null;   // einmalig geladene Quell-Files
  async function akqLoadFactBase() {
    if (AKQ_FACTS !== null) return;
    try { const [f, p, mm] = await Promise.all([
        fetch('data/market-facts.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : []),
        fetch('data/cockpit-season-proxy.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : {}),
        fetch('data/cockpit-markets.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : null),
      ]);
      AKQ_FACTS = f || []; AKQ_PROXY = p || {}; AKQ_MARKETS_JSON = mm;
    } catch (e) { AKQ_FACTS = AKQ_FACTS || []; AKQ_PROXY = AKQ_PROXY || {}; }
  }
  async function loadSeason(name) {
    if (AKQ_SEASON[name] !== undefined) return AKQ_SEASON[name];
    await akqLoadFactBase();
    try {
      const key = String(name || '').trim().toLowerCase();
      const facts = AKQ_FACTS || [];
      let mf = facts.find(x => String(x.name || '').trim().toLowerCase() === key), proxy = null;
      if (!mf) {                               // Regional-Proxy (Horw/Ebikon → Kriens etc.)
        const pn = (AKQ_PROXY || {})[key];
        if (pn) { mf = facts.find(x => String(x.name || '').trim().toLowerCase() === String(pn).trim().toLowerCase()); if (mf) proxy = pn; }
      }
      // Mess-Datum (Zeit-Anker für die Prognose) aus cockpit-markets.json, sonst heute.
      let fetched = null;
      try { const me = (AKQ_MARKETS_JSON && (AKQ_MARKETS_JSON.markets || [])).find(x => String(x.name || '').trim().toLowerCase() === key); fetched = me && me.fetched; } catch (e) {}
      const index = mf ? STREcon.seasonalIndex(mf.bfs_monthly) : null;
      AKQ_SEASON[name] = index ? { index, occ_band: mf.occ_band || null, proxy, fetched } : { src: 'none' };
    } catch (e) { AKQ_SEASON[name] = { src: 'none' }; }
    return AKQ_SEASON[name];
  }

  // ---- Editierbare Kosten-Defaults für den Geldrechner (wie cockpit PD, eigener localStorage-Key) ----
  // Start = STREcon.DEFAULT_COSTS; die Miete wird beim Render mit der geforderten Inserat-Miete vorbefüllt.
  const AKQ_PD = (function () {
    const base = {}; for (const k in STREcon.DEFAULT_COSTS) base[k] = STREcon.DEFAULT_COSTS[k];
    base.priceOv = ''; base.occOv = '';
    try { const s = JSON.parse(localStorage.getItem('akq_cockpit_price') || '{}'); for (const k in s) if (s[k] != null) base[k] = s[k]; } catch (e) {}
    return base;
  })();
  const AKQ_MONTHS = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
  let AKQ_FC = (function () { try { return localStorage.getItem('akq_fc') || 'rolling'; } catch (e) { return 'rolling'; } })();
  function akqDaysInMonth(y, m0) { return new Date(y, m0 + 1, 0).getDate(); }

  // ---- Such-Strategien (Homegate / ImmoScout24 Deep-Links) ----
  const HOMEGATE_KANTON = {
    ZH:'canton-zurich', BE:'canton-bern', LU:'canton-lucerne', UR:'canton-uri', SZ:'canton-schwyz',
    OW:'canton-obwalden', NW:'canton-nidwalden', GL:'canton-glarus', ZG:'canton-zug', FR:'canton-fribourg',
    SO:'canton-solothurn', BS:'canton-basel-stadt', BL:'canton-basel-landschaft', SH:'canton-schaffhausen',
    AR:'canton-appenzell-ausserrhoden', AI:'canton-appenzell-innerrhoden', SG:'canton-stgallen',
    GR:'canton-graubuenden', AG:'canton-aargau', TG:'canton-thurgau', TI:'canton-ticino', VD:'canton-vaud',
    VS:'canton-valais', NE:'canton-neuchatel', GE:'canton-geneva', JU:'canton-jura',
  };
  const ISC24_KANTON = {
    ZH:'zh', BE:'be', LU:'lu', UR:'ur', SZ:'sz', OW:'ow', NW:'nw', GL:'gl', ZG:'zg', FR:'fr',
    SO:'so', BS:'bs', BL:'bl', SH:'sh', AR:'ar', AI:'ai', SG:'sg', GR:'gr', AG:'ag', TG:'tg',
    TI:'ti', VD:'vd', VS:'vs', NE:'ne', GE:'ge', JU:'ju',
  };
  function homegateUrl(canton, rooms, maxPrice) {
    const slug = HOMEGATE_KANTON[canton] || 'country-switzerland';
    // Homegate-Zimmerfilter (verifiziert): ac=Zimmer von, ad=Zimmer bis. Band '25-35' = 2.5–3.5 Zi.
    // Max-Preis bewusst weggelassen — der Query-Param ist nicht stabil verifizierbar; Nutzer setzt ihn auf der Seite.
    let q = '';
    if (rooms && rooms.indexOf('-') > -1) { const p = rooms.split('-'); q = `?ac=${+p[0] / 10}&ad=${+p[1] / 10}`; }
    return `https://www.homegate.ch/rent/apartment/${slug}/matching-list${q}`;
  }
  function isc24Url(canton, rooms, maxPrice) {
    const code = ISC24_KANTON[canton] || '';
    return `https://www.immoscout24.ch/de/wohnung/mieten/kanton-${code}?pr=${maxPrice}&rfr=${rooms}`;
  }

  function renderSearchStrats(m, elId, labelId) {
    const el = document.getElementById(elId || 'akqSearchStrats');
    if (!el) return;
    const _lbl = document.getElementById(labelId || 'akqStratMarketLabel'); if (_lbl) _lbl.textContent = m.name;

    const cap90 = akqHasCap90(m);
    const adr = m.adr;
    // M24/W-C: Strategie-Budgets aus DERSELBEN Engine wie das Deal-Dossier (STREcon via dossOffer),
    // statt aus einer Magic-Zahlen-Kette -> eine Wahrheit Akquise <-> Dossier.
    const REP_ROOMS = { '15-25': 2, '25-35': 3, '35-45': 4 };
    const maxRentFor = (mkt, band) => { const off = dossOffer(mkt, REP_ROOMS[band]); return off && off.maxMiete != null ? Math.max(0, Math.round(off.maxMiete / 50) * 50) : 0; };
    const maxRentSmall  = maxRentFor(m, '15-25');
    const maxRentMedium = maxRentFor(m, '25-35');
    const strats = [];

    if (cap90) {
      const altMarkets = markets.filter(x => x.canton !== m.canton && !x.tags.some(t=>t.includes('90-Tage-Cap')) && x.cat === m.cat && x.grade <= 'B').sort((a,b)=>b.revpar-a.revpar).slice(0,2);
      strats.push({
        title: `⛔ ${m.name} mit 90-Tage-Cap — Suche stattdessen hier`,
        intro: `Reine STR-Arbitrage hier wirtschaftlich tot. Diese Alternativen haben ähnliches Profil ohne Cap:`,
        alternatives: altMarkets,
      });
      altMarkets.forEach(alt => {
        const altMax = maxRentFor(alt, '25-35');
        strats.push({
          title: `📍 Alternativ-Markt: ${alt.name} (${cantonNames[alt.canton]})`,
          rooms: '25-35', maxRent: altMax,
          reason: `Umsatz/verf. Nacht CHF ${alt.revpar}, Grade ${alt.grade}, ${alt.profile}. Kein Tages-Cap, deutlich entspannteres Vermieter-Klima.`,
          searchString: `2.5 - 3.5 Zimmer · ${cantonNames[alt.canton]} · max. CHF ${altMax}/Mt + NK · Klausel "Untervermietung nicht erlaubt" ausschließen`,
          homegate: homegateUrl(alt.canton, '25-35', altMax),
          isc24: isc24Url(alt.canton, '2.5', altMax),
        });
      });
    } else {
      // M24/W-C: Cashflow bei gebotener Miete aus DERSELBEN Engine wie das Dossier (STREcon via dossOffer),
      // statt einer zweiten Kostenformel (0.71/-400).
      const cfEst = (rent, band) => {
        const fl = dossOffer(m, REP_ROOMS[band], rent);
        const net = fl && fl.netto != null ? fl.netto : null;
        if (net == null) return '–';
        const low = Math.round(net * 0.85 / 50) * 50, high = Math.round(net * 1.15 / 50) * 50;
        const fmtN = SwissFmt.signedChf;
        return `${fmtN(low)} – ${fmtN(high)} / Mt`;
      };
      const compEst = (rooms) => {
        const baseListings = m.listings || 100;
        const typeShare = rooms === '15-25' ? 0.42 : rooms === '25-35' ? 0.31 : 0.13;
        const expectedSTRcount = Math.round(baseListings * typeShare);
        const onMarketCount = Math.max(3, Math.round(expectedSTRcount * 0.08));
        let level;
        if (onMarketCount <= 5) level = { label: 'tief', color: 'var(--green)', bg: 'rgba(63,174,124,.16)' };
        else if (onMarketCount <= 12) level = { label: 'mittel', color: 'var(--amber)', bg: 'rgba(224,162,62,.16)' };
        else level = { label: 'hoch — Vitamin B nötig', color: 'var(--red)', bg: 'rgba(229,57,43,.16)' };
        return { count: onMarketCount, level };
      };

      const cSmall = compEst('15-25');
      strats.push({
        title: `🎯 Studio / 1.5-Zimmer für Solo-/Couple-Gäste`,
        rooms: '15-25', maxRent: maxRentSmall,
        reason: `Niedrigste Setup-Kosten (~CHF 5'000) und schnellste Amortisation. Solo- und Pärchen-Reisen sind ~55% des STR-Bookings in ${m.name}.`,
        searchString: `1.5 - 2.5 Zimmer · ${m.name} und Umgebung · max. CHF ${maxRentSmall}/Mt + NK · keine "STR-Verbot"-Klausel`,
        cashflowEst: cfEst(maxRentSmall, '15-25'),
        competitorCount: cSmall.count, competitorLevel: cSmall.level,
        setupCost: '~CHF 4\'500–6\'000', breakEvenMonths: '6–10 Monate',
        hitRate: '~1 ernsthafte Rückantwort pro 8–12 Anfragen',
        inseratTipps: [
          'Auf "Untervermietung nur mit schriftlicher Zustimmung" achten — verhandelbar',
          'Wenn EG oder direkter Eingang: noch besser, weniger Konflikte mit Nachbarn',
          'Stockwerkeigentum bedeutet STWE-Reglement prüfen — kann STR verbieten',
        ],
        verhandlung: `Sage dem Eigentümer transparent dass du STR betreibst und biete <strong>20–30% Anteil am Cashflow</strong> über der Miete an. Viele Eigentümer nehmen das gerne als zusätzliche Einnahme.`,
        homegate: homegateUrl(m.canton, '15-25', maxRentSmall),
        isc24: isc24Url(m.canton, '1.5', maxRentSmall),
      });

      const cMed = compEst('25-35');
      strats.push({
        title: `👨‍👩‍👧 2.5–3.5-Zimmer für Familien (höherer Nachtpreis)`,
        rooms: '25-35', maxRent: maxRentMedium,
        reason: `Familien-Listings sind in ${m.cat}-Märkten chronisch knapp. Aufpreis CHF ${Math.round((adr*0.4))} pro Nacht möglich wenn Kinderbett + voll ausgestattete Küche + getrenntes Wohnzimmer.`,
        searchString: `2.5 - 3.5 Zimmer · ${m.name} · max. CHF ${maxRentMedium}/Mt + NK · Küche + Wohnzimmer · idealerweise EG (Kinder)`,
        cashflowEst: cfEst(maxRentMedium, '25-35'),
        competitorCount: cMed.count, competitorLevel: cMed.level,
        setupCost: '~CHF 7\'000–9\'500', breakEvenMonths: '8–14 Monate',
        hitRate: '~1 Rückantwort pro 6–10 Anfragen',
        inseratTipps: [
          'Familien-Setup heißt: Hochstuhl, Kinderbett, sichere Treppe, Spielsachen — Investiere in Erstausstattung',
          'Erdgeschoss oder 1. Stock mit Lift bevorzugt — Familien mit Kinderwagen meiden Treppen',
          'In der Nähe: Spielplatz, Coop/Migros zu Fuß, ÖV ≤ 5 Min',
        ],
        verhandlung: `Eigentümer mit eigenen Familien sind oft offener. Biete an, das Inserat <strong>vor dem ersten Gast persönlich vorzuführen</strong> — schafft Vertrauen.`,
        homegate: homegateUrl(m.canton, '25-35', maxRentMedium),
        isc24: isc24Url(m.canton, '2.5', maxRentMedium),
      });

      if (m.grade === 'A' || m.grade === 'B') {
        const luxMax = maxRentFor(m, '35-45');
        const cLux = compEst('35-45');
        strats.push({
          title: `🏔️ Premium 3.5+-Zimmer für höhere Margen`,
          rooms: '35-45', maxRent: luxMax,
          reason: `In Grade-${m.grade}-Märkten gibt's wenig hochwertige STR-Konkurrenz. Mit Designwohnung mit Balkon/Aussicht/Sauna Nachtpreis-Aufschlag <strong>+25–40%</strong>. Aber: hohes Risiko bei niedriger Auslastung.`,
          searchString: `3.5 - 4.5 Zimmer · ${m.name} · max. CHF ${luxMax}/Mt + NK · Aussicht / Balkon / Garage / Cheminée`,
          cashflowEst: cfEst(luxMax, '35-45'),
          competitorCount: cLux.count, competitorLevel: cLux.level,
          setupCost: '~CHF 12\'000–18\'000', breakEvenMonths: '12–24 Monate',
          hitRate: '~1 Rückantwort pro 4–7 Anfragen (Premium-Eigentümer sind selektiver)',
          inseratTipps: [
            'Aussicht, Balkon, Cheminée, Sauna sind die Killer-Features',
            'Auf Move-in-Condition achten — Premium-Möblierung lohnt nur bei Premium-Substanz',
            'Bei Eigentumswohnung: STWE-Reglement studieren',
          ],
          verhandlung: `Premium-Eigentümer wollen oft Stabilität statt Maximierung — biete <strong>3-Jahres-Vertrag mit kleiner Indexierung</strong> statt Cashflow-Anteil.`,
          homegate: homegateUrl(m.canton, '35-45', luxMax),
          isc24: isc24Url(m.canton, '3.5', luxMax),
        });
      }
    }

    el.innerHTML = strats.map(s => {
      if (s.alternatives) {
        return `<div class="p-3 bg-[#FCE7E4]/40 border border-[color:var(--red)]/30 rounded-lg">
          <div class="font-semibold text-sm">${s.title}</div>
          <div class="text-xs text-[color:var(--muted)] mt-1">${s.intro}</div>
        </div>`;
      }
      const tippsHtml = (s.inseratTipps || []).map(t => `<li>${t}</li>`).join('');
      const competitorBadge = s.competitorLevel ? `<span class="proof-badge" style="background:${s.competitorLevel.bg};color:${s.competitorLevel.color}" title="Grobe Heuristik aus Markt-Inseratzahl × Zimmer-Anteil — KEINE gemessene Miet-Konkurrenz">🔴 Konkurrenz-Schätzung: ${s.competitorLevel.label}</span>` : '';
      return `
        <div class="p-4 bg-white border border-[color:var(--line)] rounded-lg hover:border-[color:var(--ink)] transition">
          <div class="font-semibold text-base mb-1">${s.title}</div>
          <div class="text-xs text-[color:var(--muted)] mb-3 leading-relaxed">${s.reason}</div>
          ${competitorBadge ? `<div class="mb-3">${competitorBadge}</div>` : ''}
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3 p-3 bg-[#FAF8F1] rounded">
            <div><div class="text-[10px] uppercase tracking-wider text-[color:var(--muted)]">Cashflow netto/Mt</div><div class="font-semibold text-sm" style="color:${s.cashflowEst && s.cashflowEst.startsWith('+') ? 'var(--green)' : 'var(--ink)'}">${s.cashflowEst || '—'}</div></div>
            <div><div class="text-[10px] uppercase tracking-wider text-[color:var(--muted)]">Setup einmalig</div><div class="font-semibold text-sm">${s.setupCost || '—'}</div></div>
            <div><div class="text-[10px] uppercase tracking-wider text-[color:var(--muted)]">Break-Even</div><div class="font-semibold text-sm">${s.breakEvenMonths || '—'}</div></div>
            <div><div class="text-[10px] uppercase tracking-wider text-[color:var(--muted)]">Hit-Rate <span title="Heuristische Schätzung aus Erfahrungswerten — keine gemessene Quote. Der Funnel in der Akquise misst die echte Antwortquote, sobald Anschreiben festgehalten sind." style="color:#C9A24A">🟡</span></div><div class="font-semibold text-[11px] leading-tight">${s.hitRate || '—'}</div></div>
          </div>
          ${s.inseratTipps ? `<details class="mb-3"><summary class="text-xs font-semibold text-[color:var(--ink-2)] cursor-pointer hover:text-[color:var(--ink)]">📋 Worauf bei Inseraten achten</summary><ul class="text-xs text-[color:var(--ink-2)] mt-2 space-y-1 ml-4 list-disc">${tippsHtml}</ul></details>` : ''}
          ${s.verhandlung ? `<div class="mb-3 p-2 bg-[#E6F3EC]/40 border-l-2 border-[color:var(--green)] rounded text-xs"><strong class="text-[10px] uppercase tracking-wider text-[color:var(--green)]">💬 Verhandlungs-Tipp</strong><div class="mt-1">${s.verhandlung}</div></div>` : ''}
          <div class="text-xs bg-[#FAF8F1] p-2 rounded font-mono mb-2">${s.searchString}</div>
          <div class="flex gap-2 flex-wrap">
            <a href="${s.homegate}" target="_blank" rel="noopener" class="text-xs px-3 py-1.5 bg-[color:var(--ink)] text-white rounded hover:bg-black">Auf Homegate öffnen ↗</a>
            <a href="${s.isc24}" target="_blank" rel="noopener" class="text-xs px-3 py-1.5 border border-[color:var(--line)] rounded hover:border-[color:var(--ink)]">ImmoScout24 ↗</a>
            <button onclick="navigator.clipboard.writeText('${s.searchString.replace(/'/g,"\\'")}'); this.innerText='✓ Kopiert!'" class="text-xs px-3 py-1.5 border border-[color:var(--line)] rounded hover:border-[color:var(--ink)] text-[color:var(--muted)]">Such-String kopieren</button>
          </div>
        </div>`;
    }).join('');
  }

  // ---- Schlupfloecher ----
  function renderLoopholes(m, cardId, bodyId) {
    const card = document.getElementById(cardId || 'akqLoopholeCard');
    const body = document.getElementById(bodyId || 'akqLoopholeBody');
    if (!card || !body) return;
    const lh = (typeof LOOPHOLES !== 'undefined') ? (LOOPHOLES[m.name] || LOOPHOLES['_canton_' + m.canton]) : null;
    if (!lh) {
      body.innerHTML = `
        <div class="p-3 bg-white rounded border border-[color:var(--line)]">
          <div class="text-sm font-semibold mb-1">✓ Keine bekannten Cap-Regeln in ${m.name}</div>
          <div class="text-xs text-[color:var(--muted)]">365 Tage vermietbar nach aktuellem Stand. Empfehlung: Vor Abschluss noch die Hausordnung und Stockwerkeigentümer-Reglement prüfen falls ETW.</div>
        </div>`;
      return;
    }
    body.innerHTML = `
      <div class="p-3 bg-white rounded border border-[color:var(--line)] mb-2">
        <div class="flex items-center gap-2 mb-1"><span class="proof-badge proof-red">⚠ CAP</span><span class="text-sm font-semibold">${lh.cap_rule}</span></div>
      </div>
      <div class="p-3 bg-[#E6F3EC]/40 rounded border-l-4 border-[color:var(--green)]">
        <div class="text-xs font-bold uppercase tracking-wider text-[color:var(--green)] mb-1">💡 Schlupfloch</div>
        <div class="font-semibold text-sm">${lh.main_loophole.title}</div>
        <div class="text-xs text-[color:var(--ink-2)] mt-1">${lh.main_loophole.description}</div>
        ${lh.main_loophole.evidence ? `<div class="text-[11px] text-[color:var(--muted)] mt-2 italic">Belege: ${lh.main_loophole.evidence}</div>` : ''}
        ${lh.main_loophole.what_to_look_for ? `<div class="text-[11px] mt-2"><strong>Worauf achten:</strong> ${lh.main_loophole.what_to_look_for}</div>` : ''}
        ${lh.main_loophole.risk_level ? `<div class="text-[11px] mt-1">Risiko: ${lh.main_loophole.risk_level}</div>` : ''}
      </div>
      ${(lh.secondary_options || []).map(o => `
        <div class="mt-2 p-2 bg-[#F6EFD9]/40 rounded border-l-2 border-[#C9A24A] text-xs">
          <strong>${o.title}:</strong> ${o.description} ${o.risk ? `<span class="text-[color:var(--muted)]">· ${o.risk}</span>` : ''}
        </div>`).join('')}`;
  }

  // ---- Checkliste "Worauf achten" ----
  function renderChecklist(m, elId, labelId) {
    const target = document.getElementById(elId || 'akqChecklist');
    if (!target) return;
    const _cl = document.getElementById(labelId || 'akqChecklistMarket'); if (_cl) _cl.textContent = m.name;

    const cap90 = akqHasCap90(m);
    const isCapCanton = ['VS','GR'].includes(m.canton) || ['Gstaad','Lauterbrunnen','Grindelwald','Adelboden','Wengen','Mürren','Interlaken'].includes(m.name);
    const isPremium = m.grade === 'A';
    const isCity = m.profile === 'city';
    const isAlpine = m.cat === 'Alpen';

    const items = [
      { key:'subletting', title:'Untervermietungs-Klausel', status: isCity ? 'red' : (isCapCanton ? 'amber' : 'green'),
        note: isCity ? 'In Städten verbieten ~65% der Mietverträge Untervermietung explizit. Vor Vertragsunterzeichnung im Standardvertrag prüfen, ggf. schriftliche Erlaubnis einholen.'
          : isCapCanton ? 'In Cap-Kantonen sind 30–45% der Verträge restriktiv. Beim Eigentümer direkt nachfragen — viele erlauben STR gegen Anteil am Ertrag.'
          : 'Ländliche Gemeinden tolerieren Untervermietung meist. Trotzdem schriftliche Zustimmung einholen — schützt im Streitfall.' },
      { key:'tax_cap', title:'Kantonaler Tages-Cap', status: cap90 ? 'red' : 'green',
        note: cap90 ? '⚠️ Hier gilt 90-Tage-Cap pro Jahr. Macht reine STR-Vermietung wirtschaftlich tot. Entweder Hybrid (Mid-Term + Kurz) oder Markt wechseln.'
          : 'Keine kommunale Tages-Beschränkung aktuell. Risiko: Volksinitiative oder Stadt-Verordnung. Regulations-View checken.' },
      { key:'second_home', title:'Zweitwohnungs-Cap (Neubau)', status: isCapCanton ? 'amber' : 'green',
        note: isCapCanton ? 'Gemeinde hat >20% Zweitwohnungs-Anteil → Neubau seit 2012 verboten. Für dich: Wertanlage-Vorteil (Knappheit), aber kein eigener Neubau möglich.'
          : 'Keine Cap. Neubau möglich. Auch keine Knappheits-Prämie auf bestehende Objekte.' },
      { key:'stockwerk', title:'Stockwerkeigentum-Reglement', status:'amber',
        note:'Bei einer Eigentumswohnung (ETW): das STWE-Reglement kann Kurzaufenthalte verbieten. Vor Kauf einsehen — Mehrheitsbeschluss ist sonst der einzige Weg.' },
      { key:'kurtaxe', title:'Kurtaxe-Meldepflicht', status:'amber',
        note: isAlpine ? 'Alpenresorts haben oft Anmeldepflicht ab erster Buchung. Monatliche oder quartalsweise Abrechnung an Gemeinde. Aufwand: 1–2h/Monat.'
          : 'Auch in Städten muss Kurtaxe pro Gast/Nacht erhoben werden. Manche Gemeinden haben Online-Portal, andere noch Papier-Meldung.' },
      { key:'mwst', title:'MWSt ab CHF 100k Umsatz', status: isPremium ? 'red' : 'green',
        note: isPremium ? 'In A-Grade-Märkten knackst du die CHF 100k schnell. Dann MWSt-pflichtig (3.8% reduzierter Satz für Beherbergung). Plane Buchhalter ein.'
          : 'Bei mittlerem Markt liegt der Jahresumsatz meist unter CHF 100k → MWSt-befreit. Aber beobachten: bei Wachstum reaktiv anmelden.' },
      { key:'insurance', title:'STR-Versicherung', status:'amber',
        note:'Standard-Hausrat des Mieters deckt KEINE Gäste-Schäden. Du brauchst eine spezifische STR-Versicherung — Mobiliar/Helvetia bieten Tarife ab CHF 600/Jahr. Plattform-Versicherungen (Airbnb AirCover) sind nicht ausreichend.' },
      { key:'fire', title:'Brandschutz / Fluchtweg', status:'green',
        note:'Bei <5 Schlafzimmern in den meisten Kantonen keine Sonder-Auflagen. Rauchmelder pro Raum + Fluchtweg ohne Hindernis sind Pflicht. Feuerlöscher empfohlen.' },
      { key:'platform', title:'Plattform-Compliance', status:'amber',
        note:'Airbnb verlangt seit 2024 in CH die Steuer-Nr. (UID) im Listing. Booking.com seit 2025 ebenfalls. Ohne UID: Konto wird gesperrt. Beantragen kostenlos bei der ESTV.' },
      { key:'overall', title:'Gesamt-Risiko', status: cap90 ? 'red' : (isCity || isCapCanton ? 'amber' : 'green'),
        note: cap90 ? 'Sehr hoch — 90-Tage-Cap ist Deal-Killer. Nur als Eigennutzung + gelegentliche STR sinnvoll.'
          : (isCity ? 'Mittel — Untervermietungs-Klauseln sind das größte Risiko. Sorgfältige Vertragsprüfung notwendig.'
            : isCapCanton ? 'Mittel — Cap-Kanton bietet Knappheits-Schutz, aber Reglement und Vertrag sorgfältig prüfen.'
            : 'Tief — wenige strukturelle Hürden. Standard-Due-Diligence reicht.') },
    ];

    target.innerHTML = items.map(it => {
      const color = it.status === 'green' ? 'var(--green)' : it.status === 'red' ? 'var(--red)' : 'var(--amber)';
      const bg    = it.status === 'green' ? 'rgba(63,174,124,.16)' : it.status === 'red' ? 'rgba(229,57,43,.16)' : 'rgba(224,162,62,.16)';
      const icon  = it.status === 'green' ? '✓' : it.status === 'red' ? '✗' : '⚠';
      return `
        <details class="border border-[color:var(--line)] rounded-lg overflow-hidden">
          <summary class="p-3 flex items-start gap-3 cursor-pointer hover:bg-[#FAF8F1]">
            <div class="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold" style="background:${bg};color:${color}">${icon}</div>
            <div class="flex-1 min-w-0"><div class="font-semibold text-sm">${it.title}</div><div class="text-xs text-[color:var(--muted)]">Klicken für Details</div></div>
          </summary>
          <div class="px-3 pb-3 pt-1 text-xs text-[color:var(--ink-2)] border-t border-[color:var(--line)] bg-[#FAF8F1]">${it.note}</div>
        </details>`;
    }).join('');
  }

  // ---- Brief-Generator ----
  let currentLetterMarket = null;
  function openLetterGen(m) {
    currentLetterMarket = m;
    document.getElementById('letterCity').value = m?.name || '';
    document.getElementById('letterOverlay').classList.add('show');
    generateLetter();
  }
  function closeLetter() { document.getElementById('letterOverlay').classList.remove('show'); }
  function generateLetter() {
    const v = document.getElementById('letterVariant').value;
    const tpl = LETTER_TEMPLATES[v];
    if (!tpl) return;
    const city = document.getElementById('letterCity').value || '[Stadt]';
    const street = document.getElementById('letterStreet').value || '[Strasse + Nr.]';
    const propType = document.getElementById('letterPropType').value;
    const ownerFirst = document.getElementById('letterOwnerFirst').value;
    const formal = document.getElementById('letterFormalSalutation').value;
    const hook = document.getElementById('letterPersonalHook').value || '[Persönlicher Aufhänger — wo habt ihr euch kennengelernt, gemeinsame Bekannte, etc.]';
    const track = document.getElementById('letterTrackRecord').value || '200';
    const author = document.getElementById('letterAuthor').value || '[Dein Name]';

    const lh = LOOPHOLES[city] || LOOPHOLES['_canton_' + (currentLetterMarket?.canton || '')];
    let loopholeBlock = '';
    if (lh) {
      loopholeBlock = `Die von mir vorgesehene Nutzung als Kurzzeitvermietung ${lh.main_loophole.title.toLowerCase().includes('ausgenommen') ? 'fällt nicht unter' : 'umgeht'} die ${lh.cap_rule.toLowerCase()}. ${lh.main_loophole.description}${lh.main_loophole.evidence ? ' ' + lh.main_loophole.evidence : ''}`;
      document.getElementById('letterLoopholeHint').innerHTML = `<span class="proof-badge proof-green">● Schlupfloch erkannt</span> Für ${city}: ${lh.main_loophole.title}`;
    } else {
      loopholeBlock = `Da ${city} keine 90-Tage-Beschränkung kennt, ist eine ganzjährige Kurzzeitvermietung rechtlich möglich.`;
      document.getElementById('letterLoopholeHint').innerHTML = `<span class="proof-badge proof-amber">● Kein spezielles Schlupfloch</span> ${city} hat aktuell keine bekannten Cap-Regeln.`;
    }

    let out = tpl
      .replace(/\{\{vorname_eigentümer\}\}/g, ownerFirst || '[Vorname]')
      .replace(/\{\{anrede_eigentümer\}\}/g, formal)
      .replace(/\{\{persönlicher_aufhänger\}\}/g, hook)
      .replace(/\{\{wohnungs_typ\}\}/g, propType)
      .replace(/\{\{ausstattung\}\}/g, propType.includes('Gewerbe') ? 'Dusche und wenn möglich auch Küche' : 'voll ausgestatteter Küche')
      .replace(/\{\{strasse_inserat\}\}/g, street)
      .replace(/\{\{stadt\}\}/g, city)
      .replace(/\{\{schlupfloch_block\}\}/g, loopholeBlock)
      .replace(/\{\{zielgruppe\}\}/g, 'Paare oder Geschäftsreisende')
      .replace(/\{\{anzahl_übernachtungen\}\}/g, track)
      .replace(/\{\{tageszeit\}\}/g, new Date().getHours() < 17 ? 'Tag' : 'Feierabend')
      .replace(/\{\{absender_name\}\}/g, author)
      .replace(/\{\{absender_kontakt\}\}/g, '[Deine Email + Telefon]')
      .replace(/\{\{seit_jahr\}\}/g, '2018')
      .replace(/\{\{versicherungs_summe\}\}/g, '500\'000');
    document.getElementById('letterOutput').value = out;
  }
  function copyLetter() {
    const txt = document.getElementById('letterOutput').value;
    navigator.clipboard.writeText(txt).then(() => {
      document.querySelectorAll('#letterOverlay button').forEach(b => { if (b.innerText.includes('Kopieren') || b.innerText.includes('Kopiert')) b.innerText = '✓ Kopiert!'; });
      const sent = JSON.parse(localStorage.getItem('swissstr_outreach') || '[]');
      sent.push({ city: document.getElementById('letterCity').value, street: document.getElementById('letterStreet').value, date: new Date().toISOString(), status: 'copied' });
      localStorage.setItem('swissstr_outreach', JSON.stringify(sent));
    });
  }
  function letterSubject() {
    return `Anfrage zur ${document.getElementById('letterPropType').value} an ${document.getElementById('letterStreet').value}`;
  }
  function emailLetter() {
    const txt = document.getElementById('letterOutput').value;
    window.location.href = `mailto:?subject=${encodeURIComponent(letterSubject())}&body=${encodeURIComponent(txt)}`;
  }
  // Gmail-Compose im neuen Tab vorausfuellen (nutzt das eingeloggte Google-Konto). Kein Auto-Versand.
  function gmailLetter() {
    const txt = document.getElementById('letterOutput').value;
    const url = `https://mail.google.com/mail/?view=cm&fs=1&su=${encodeURIComponent(letterSubject())}&body=${encodeURIComponent(txt)}`;
    window.open(url, '_blank', 'noopener');
  }
  document.addEventListener('input', (e) => { if (e.target && e.target.id && e.target.id.startsWith('letter') && e.target.id !== 'letterOutput') generateLetter(); });
  document.addEventListener('change', (e) => { if (e.target && e.target.id && e.target.id.startsWith('letter') && e.target.id !== 'letterOutput') generateLetter(); });

  // ====================== DEAL-DOSSIER ======================
  // Kuratierte Lage-Fakten je Fokus-Markt (belegt, Stand 2026-06). Fehlt der Markt → ehrlich "prüfen".
  const AKQ_LOCATION = {
    "Kriens": { oev: "≈ 15 Min nach Luzern Bahnhof (Bus 1, alle 10 Min)", shop: "Pilatusmarkt (Coop u.a.) — ÖV ≈ 16 Min (Bus 14) oder vor Ort", extra: "Direkt an Luzern angrenzend · Tor zum Pilatus (Tagestourismus)", src: "VBL / rome2rio, Stand 2026-06" },
  };
  const chf = SwissFmt.chf;
  function dossRoomBucket(rooms) { return rooms <= 2 ? '15-25' : rooms <= 3.5 ? '25-35' : '35-45'; }
  function dossBucketLabel(b) { return b === '15-25' ? 'Studio/1.5–2 Zi' : b === '25-35' ? '2.5–3.5 Zi (Familie)' : '3.5+ Zi (Premium)'; }

  // Ziel-Marge/Mt: die Mindest-Marge, die Adrian behalten will, bevor er Miete bietet.
  const DOSS_MARGE = 800;
  // dossOffer — Markt×Grösse → ADR & Belegung modellieren (das ist Markt-Modell, keine Geld-Mathe),
  // ALLE CHF-Grössen dann über STREcon (zentrale Engine-Regel: keine zweite Geld-Formel).
  //   STR-Brutto/Mt   = STREcon.grossMonthly(ADR, occ)                  (price × occ% × 30)
  //   Betrieb/Mt      = STREcon-Fix (Internet/TV + Wasser/Strom) + variabel (Reinigung×Aufenthalte)
  //   Netto vor Miete = Brutto − Betrieb   (= netMonthly mit miete=0)
  //   max. tragbare Miete (Break-even Netto 0) = STREcon.breakevenRent(...)
  // bidRent = die aktuell gebotene Miete (Regler/Eingabe) → netMonthly mit miete=bidRent.
  // stableRooms (optional): zwingt eine STABILE, vom globalen AKQ_F unabhängige Kohorte nach
  // genau diesen Zimmern (für das Lead-Board, damit dessen Zahlen nicht beim Klick springen).
  function dossOffer(m, rooms, bidRent, stableRooms) {
    const b = dossRoomBucket(rooms);
    const adrMult = b === '15-25' ? 0.65 : b === '25-35' ? 0.85 : 1.35;
    const occMult = b === '15-25' ? 1.10 : b === '25-35' ? 1.00 : 0.92;
    let adrSize = Math.round(m.adr * adrMult);
    // Basis-Belegung + ADR: GEFILTERTE Vergleichs-Kohorte (🟢) wenn ein Filter aktiv, sonst Profi-Kohorte
    // (Live, 🟢), sonst Modell (🟡). occMult bleibt nur bei Modell/Profi (sonst doppelte Grössen-Korrektur,
    // die Kohorte ist ja schon nach Grösse gefiltert).
    const modelAdr = adrSize;   // Modell-ADR (m.adr × Grössen-Mult) als Plausibilitäts-Anker
    let occBase = occOf(m), occTier = 'mod', occMeta = null, cohortN = null, useMult = true;
    try {
      const ch = akqCohort(m.name, stableRooms);
      if (ch) {
        occBase = ch.occ; occTier = 'live'; occMeta = ch; cohortN = ch.n; useMult = false;
        // Kohorte-Preis NUR übernehmen, wenn die Stichprobe trägt (n≥4) UND kein Ausreisser
        // gegenüber dem Modell-ADR. Sonst bläht ein einzelnes Luxus-Inserat (z.B. CHF 876/N bei
        // n=2) die tragbare Miete unrealistisch auf (14k-Bug) → Modell-ADR behalten.
        if (ch.price != null && ch.n >= 4 && ch.price <= modelAdr * 2 && ch.price >= modelAdr * 0.45) {
          adrSize = ch.price;
        } else if (ch.price != null) {
          occMeta = Object.assign({}, ch, { priceCapped: true, rawPrice: ch.price });
        }
      }
      else { const c = AKQ_COCKPIT_OCC[m.name]; if (c && c.src === 'live' && c.occ != null) { occBase = c.occ; occTier = 'live'; occMeta = c; } }
    } catch (e) { /* Fallback bleibt Modell */ }
    const occSize = Math.min(95, Math.max(15, occBase * (useMult ? occMult : 1)));

    // ── Geld-Mathe ausschliesslich über STREcon ──────────────────────────────
    const grossM = STREcon.grossMonthly(adrSize, occSize);            // 🟡/🟢 Brutto/Mt
    // Betrieb/Mt = STREcon-Fix (Internet/TV + Wasser/Strom) + variabel (Reinigung×Aufenthalte),
    // OHNE Miete. netMonthly mit miete:0 liefert genau Brutto − Betrieb = Netto vor Miete.
    const flow0 = STREcon.netMonthly({ price: adrSize, occPct: occSize, costs: { miete: 0 } });
    const betrieb = flow0 ? (flow0.fix + flow0.variabel) : 0;         // = Internet/TV+Wasser+Reinigung
    const netVorMiete = flow0 ? flow0.netto : (grossM - betrieb);     // Brutto − Betrieb
    // max. tragbare Miete für Netto 0 = Break-even-Miete (STREcon).
    const breakeven = STREcon.breakevenRent({ price: adrSize, occPct: occSize }) || 0;
    const marge = DOSS_MARGE;
    const maxMiete = breakeven - marge;                              // mit Ziel-Marge
    // Netto/Mt bei gebotener Miete (Regler) — wieder über STREcon (miete = bidRent).
    let netto = null, bidFlow = null;
    if (bidRent != null) {
      bidFlow = STREcon.netMonthly({ price: adrSize, occPct: occSize, costs: { miete: bidRent } });
      netto = bidFlow ? bidFlow.netto : null;
    }
    return { b, adrSize, occSize, occBase, occTier, occMeta, occMult,
             grossM, betrieb, netVorMiete, breakeven, marge, maxMiete, netto, bidFlow };
  }

  function dossDealScore(m, f) {
    const cap90 = akqHasCap90(m);
    let score = 50; const drivers = [];
    const add = (pts, txt) => { score += pts; drivers.push({ pts, txt }); };
    if (f.building === 'gross') add(18, 'Grosse Überbauung → Anonymität, Vermieter/Nachbarn stören sich seltener');
    else if (f.building === 'mfh') add(5, 'Kleines Mehrfamilienhaus → mittlere Anonymität');
    else add(-8, 'Einzel-/Zweifamilienhaus → wenig Anonymität, Nachbarn nah');
    if (f.sublet === 'verboten') add(-25, 'Inserat schliesst Untervermietung aus → schwieriger Deal');
    else if (f.sublet === 'zustimmung') add(8, '„Nur mit Zustimmung" → verhandelbar, oft machbar');
    else add(5, 'Untervermietung nicht erwähnt → kein expliziter Stopper');
    if (f.ground) add(6, 'Erdgeschoss / eigener Eingang → weniger Nachbar-Konflikt');
    if (f.vacant) add(8, 'Länger inseriert → Vermieter motiviert (Leerstand kostet)');
    if (f.etw) add(-10, 'Eigentumswohnung → STWE-Reglement kann STR verbieten');
    if (f.view === 'ja') add(4, 'Aussicht → höherer Nachtpreis, leichter zu rechtfertigen');
    if (cap90) add(-20, `${m.name}: Tages-Cap (90 Tage) → Modell regulatorisch gekappt`);
    score = Math.max(5, Math.min(95, score));
    drivers.sort((a, b) => Math.abs(b.pts) - Math.abs(a.pts));
    return { score, drivers, cap90 };
  }

  const DOSS_STRAT = {
    privat: [
      '<b>Mietgarantie zuerst:</b> „Du bekommst die Miete jeden Monat — egal ob belegt. Das ist sicherer als ein normaler Mieter (keine Ausstände, kein Leerstand)." Das ist das stärkste Argument bei Privaten.',
      '<b>Vertrauen/Gesicht:</b> transparente STR-Absicht, persönliches Treffen anbieten, Track-Record (200+ Nächte ohne Reklamation), STR-Versicherung bis CHF 500\'000 nennen.',
      '<b>Pflege-Argument:</b> 2–3× wöchentlich professionell gereinigt → Wohnung besser gepflegt als bei einem Dauermieter.',
      '<b>Upside:</b> 10–30 % über Marktmiete oder Cashflow-Anteil anbieten → „du verdienst mehr als marktüblich".',
    ],
    firma: [
      '<b>Ein zuverlässiger Firmen-Mieter:</b> ein Vertrag, pünktlich, kein Mieterwechsel → weniger Admin und kein Ausfallrisiko für die Verwaltung.',
      '<b>Leerstand-Füller:</b> gezielt länger inserierte / schwer vermietbare Einheiten ansprechen — „wir nehmen sie euch ab".',
      '<b>Portfolio:</b> Interesse an mehreren Einheiten signalisieren → Skalierung, weniger Vakanz für die Firma.',
      '<b>Compliance-Sprache:</b> UID, STR-Haftpflicht, Kurtaxe-Handling übernehmen → ihr seid kein Risiko.',
      '<b>Vorhersehbarkeit:</b> 3-Jahres-Vertrag mit Indexierung, evtl. Jahres-Vorauszahlung gegen Rabatt.',
    ],
  };

  function dossInsightMeaning(f) {
    const out = [];
    out.push(f.finish === 'neuwertig' ? ['Ausbaustandard neuwertig/modern', 'trägt höheren Nachtpreis — als Premium-Foto-Set inszenieren']
      : f.finish === 'gehoben' ? ['Ausbaustandard gehoben', 'solide Nachtpreis-Basis']
      : f.finish === 'einfach' ? ['Ausbaustandard einfach/älter', 'Nachtpreis-Deckel — günstig einmieten, mit Möblierung/Deko aufwerten']
      : ['Ausbaustandard normal', 'Standard-Nachtpreis, Aufwertung über Einrichtung möglich']);
    if (f.laundry === 'ja') out.push(['Waschturm in der Wohnung', 'echter STR-Vorteil — kein Waschküchen-Konflikt, höhere Bewertung']);
    else if (f.laundry === 'nein') out.push(['Nur gemeinsame Waschküche', 'kleiner Minuspunkt für Gäste — eigene Waschmaschine nachrüsten erwägen']);
    if (f.park === 'ja') out.push(['Parkplatz/Garage vorhanden', 'Nachtpreis-Aufschlag + zieht Auto-Reisende/Familien']);
    else if (f.park === 'moeglich') out.push(['Parkplatz möglich', 'beim Vermieter mitverhandeln — als Zusatz buchbar']);
    if (f.view === 'ja') out.push(['Schöne Aussicht', 'Hero-Foto + Nachtpreis-Aufschlag +10–25 %']);
    if (f.building === 'gross') out.push(['Grosse Überbauung', 'Anonymität = höhere Ja-Wahrscheinlichkeit (Adrians Heuristik)']);
    return out;
  }

  // Gebotene Miete (Reglerwert) — pro Markt/Grösse gemerkt, Default = geforderte Miete.
  const DOSS_BID = { rent: null, market: null, rooms: null, ask: undefined };
  // Default-Vorwahl der Vergleichs-Filter (Zimmer-Band + ganze Wohnung) — pro Markt/Grösse einmal setzen.
  const DOSS_XF_PRESET = { market: null, rooms: null };

  // ============================================================================
  // VOLLER COCKPIT-GELDRECHNER (1:1 aus cockpit.html renderFlow/renderForecast portiert).
  // Vier editierbare Kästen + „Netto/Monat" + R2R-Spielraum + Jahres-Prognose — fürs
  // GEWÄHLTE Objekt. Antrieb: STR-Preis & Belegung aus dem MARKT (cockpit-<markt>.json,
  // Profi-Kohorte) bzw. Modell-ADR; die Miete vorbefüllt mit der geforderten Inserat-Miete.
  // GANZE Geld-Mathe nur über STREcon (eine Wahrheit Akquise ↔ Cockpit).
  // ============================================================================

  // Markt-Kontext fürs Objekt: Basis-Nachtpreis + Basis-Belegung + Tier. Override (AKQ_PD) sticht.
  function dossMoney(m, rooms) {
    // Basis-Belegung + Preis: GEFILTERTE Vergleichs-Kohorte (🟢) wenn Filter aktiv, sonst Live-Profi-Kohorte
    // (🟢), sonst Modellwert (🟡). So treiben die angewählten Filter Belegung UND Nachtpreis direkt.
    let occBase = occOf(m), occTier = 'mod', occMeta = null, cockpitPrice = null, cohortN = null, cohortSrc = null;
    try {
      const ch = akqCohort(m.name);
      if (ch) { occBase = ch.occ; occTier = 'live'; occMeta = ch; cockpitPrice = ch.price; cohortN = ch.n; cohortSrc = 'cohort'; }
      else { const c = AKQ_COCKPIT_OCC[m.name]; if (c && c.src === 'live' && c.occ != null) { occBase = c.occ; occTier = 'live'; occMeta = c; } if (c && c.price != null) cockpitPrice = c.price; }
    } catch (e) {}
    // Basis-Nachtpreis (ADR): Kohorten-/Cockpit-Median (Live) wenn vorhanden, sonst Modell-ADR × Grössen-Multiplikator.
    const b = dossRoomBucket(rooms);
    const adrMult = b === '15-25' ? 0.65 : b === '25-35' ? 0.85 : 1.35;
    const basePrice = cockpitPrice != null ? cockpitPrice : Math.round(m.adr * adrMult);
    const priceSrc = cohortSrc === 'cohort' ? ('Vergleichs-Kohorte · ' + cohortN + ' Inserate') : (cockpitPrice != null ? 'Cockpit-Median (Profi-Kohorte)' : 'Modell-Nachtpreis ' + chf(m.adr) + ' × ' + adrMult);
    // Aktive Werte: Override aus AKQ_PD, sonst Markt-Basis.
    const p = (AKQ_PD.priceOv !== '' && AKQ_PD.priceOv != null) ? +AKQ_PD.priceOv : basePrice;
    const occUsed = (AKQ_PD.occOv !== '' && AKQ_PD.occOv != null) ? +AKQ_PD.occOv : Math.round(occBase);
    return { basePrice, p, occBase, occUsed, occTier, occMeta, priceSrc, cohortN, cohortSrc };
  }

  // Die vier Kästen + Netto/Monat + R2R-Spielraum (rendert in #dossOut). Editierbar → live neu.
  function dossFlowHtml(m, rooms, askRent, ds, scoreCol) {
    const mc = dossMoney(m, rooms);
    const p = mc.p, occUsed = mc.occUsed;
    const PD = AKQ_PD;
    const occTierBadge = mc.occTier === 'live' ? '<span class="proof-badge proof-green">🟢 live</span>' : '<span class="proof-badge proof-amber">🟡 mod</span>';
    if (!p) return '<div class="fcmiss">Keine Preisbasis für ' + m.name + ' — Markt/Cockpit fehlt.</div>';
    const fee = Math.round(p * PD.gastFee / 100), hfee = Math.round(p * PD.hostFee / 100);
    const kurGuest = PD.traeger === 'Gast' ? PD.kurtaxe : 0, kurHost = PD.traeger === 'Host' ? PD.kurtaxe : 0;
    const gastTot = STREcon.gastPerNight(p, PD), revNight = STREcon.hostPerNight(p, PD);
    // Netto/Monat über STREcon — Miete = AKQ_PD.miete (mit der Inserat-Miete vorbefüllt).
    const nm = STREcon.netMonthly({ price: p, occPct: occUsed, costs: PD });
    const nights = nm.nights, stays = nm.stays, fix = nm.fix, variabel = nm.variabel, netto = nm.netto, einnahmen = nm.einnahmen, nettoNacht = nm.nettoNacht;
    const col = netto >= 0 ? 'var(--green)' : 'var(--red)';

    // R2R-Spielraum: Wohnungsgrösse → BFS-Marktmiete → Breakeven → wieviel % über Markt bietbar.
    let r2rHTML = '';
    try {
      const rt = (AKQ_RENTS && AKQ_RENTS.cantons && m.canton && AKQ_RENTS.cantons[m.canton]) ? AKQ_RENTS.cantons[m.canton].rooms : null;
      if (rt) {
        const netRent = STREcon.bfsRent(rt, rooms), grossRent = STREcon.bfsRentGross(rt, rooms);
        const be = STREcon.breakevenRent({ price: p, occPct: occUsed, costs: PD });
        const head = STREcon.rentHeadroomPct(be, grossRent);
        if (netRent != null && be != null && head != null) {
          const hc = head >= 20 ? 'var(--green)' : head >= 0 ? 'var(--gold)' : 'var(--red)';
          const yr = (AKQ_RENTS._meta && AKQ_RENTS._meta.year) ? ' (' + AKQ_RENTS._meta.year + ')' : '';
          const askLine = askRent != null && grossRent > 0
            ? `<div class="nrow"><span>geforderte Inserat-Miete</span><b>${chf(askRent)}/Mt <small style="color:var(--faint)">(${askRent > grossRent ? '+' : ''}${Math.round((askRent / grossRent - 1) * 100)} % vs Markt)</small></b></div>` : '';
          r2rHTML = `<div style="border-top:1px dashed var(--lineS);margin-top:12px;padding-top:10px">
            <div style="font-size:11px;color:var(--gold);font-weight:700;text-transform:uppercase;letter-spacing:.03em;margin-bottom:6px">🟡 R2R-Spielraum — was darfst du dem Eigentümer bieten? <span style="color:var(--faint);font-weight:500;text-transform:none">(Belegung ${occUsed} % Jahresschnitt)</span></div>
            <div class="nrow"><span>Wohnung ≈ <b>${rooms} Zi</b></span><b></b></div>
            <div class="nrow"><span>BFS-Marktmiete ${m.canton} · ${rooms} Zi${yr}</span><b>CHF ${chf(netRent).replace('CHF ', '')} netto <small style="color:var(--faint)">(+NK ≈ ${chf(grossRent).replace('CHF ', '')} brutto)</small></b></div>
            <div class="nrow"><span>STR trägt bis (Breakeven, inkl. NK)</span><b style="color:${be >= 0 ? 'var(--green)' : 'var(--red)'}">${chf(be)}/Mt</b></div>
            ${askLine}
            <div class="nbig"><span>Spielraum über Marktmiete</span><b style="color:${hc}">${head > 0 ? '+' : ''}${head} %</b></div>
            <div style="font-size:11px;color:var(--muted);line-height:1.55;margin-top:6px">Du könntest dem Eigentümer bis ${head > 0 ? '<b>+' + head + '% über der Marktmiete</b> (CHF ' + chf(STREcon.bfsRentGross(rt, rooms) * (1 + head / 100)).replace('CHF ', '') + '/Mt)' : 'maximal die Marktmiete'} bieten und bleibst bei dieser Belegung netto ±0 — so sticht dein R2R-Angebot den normalen Mieter. Quelle BFS-Kantonsschnitt (🟡), Mikrolage weicht ab.</div>
          </div>`;
        }
      }
    } catch (e) { r2rHTML = ''; }

    const flow = `
      <div class="text-[11px] text-[color:var(--muted)] mb-2">${rooms} Zi · ${m.name} · STR-Preis ${chf(p)} <span class="text-[color:var(--faint)]">(${mc.priceSrc})</span> · Belegung ${occUsed} % ${occTierBadge}${mc.cohortSrc === 'cohort' ? ' <span class="proof-badge proof-green" title="Ertrag aus den per Filter gewählten vergleichbaren Inseraten">aus ' + mc.cohortN + ' vergleichbaren</span>' : ''} · Deal-Score <b style="color:${scoreCol}">${ds.score}/100</b> <span style="color:#C9A24A">🟡 Heuristik</span></div>
      <div class="akqflow mb-1">
        <div class="flowbox guest"><div class="ft">Gast zahlt / Nacht</div>
          <div class="fr"><span>Nachtpreis <input class="akqPrice" type="number" placeholder="${mc.basePrice || ''}" value="${PD.priceOv}"></span><b>CHF ${p}</b></div>
          <div class="fr"><span>+ Airbnb <input id="akqGast" type="number" value="${PD.gastFee}"> %</span><b>${fee}</b></div>
          <div class="fr"><span>+ Kurtaxe <input id="akqKur" type="number" value="${PD.kurtaxe}"> ${PD.traeger === 'Gast' ? '' : '(Host)'}</span><b>${kurGuest || 0}</b></div>
          <div class="ftot"><span>Total Gast</span><b>CHF ${gastTot}</b></div></div>
        <div class="flowbox host"><div class="ft">Host nimmt ein / Nacht</div>
          <div class="fr"><span>Nachtpreis <input class="akqPrice" type="number" placeholder="${mc.basePrice || ''}" value="${PD.priceOv}"></span><b>CHF ${p}</b></div>
          <div class="fr"><span>− Airbnb-Host <input id="akqHost" type="number" value="${PD.hostFee}"> %</span><b>−${hfee}</b></div>
          <div class="fr"><span>Kurtaxe trägt <select id="akqTr"><option${PD.traeger === 'Gast' ? ' selected' : ''}>Gast</option><option${PD.traeger === 'Host' ? ' selected' : ''}>Host</option></select></span><b>−${kurHost || 0}</b></div>
          <div class="ftot"><span>kommt an / belegte N</span><b>CHF ${revNight}</b></div></div>
        <div class="flowbox fix"><div class="ft">Fixkosten / Monat (immer)</div>
          <div class="fr"><span>Miete inkl. NK <input id="akqMiete" type="number" value="${PD.miete}"></span><b></b></div>
          <div class="fr"><span>Internet + TV <input id="akqItv" type="number" value="${PD.internettv}"></span><b></b></div>
          <div class="fr"><span>Wasser + Strom <input id="akqWS" type="number" value="${PD.wasserstrom}"></span><b></b></div>
          <div class="ftot"><span>Fix total</span><b>CHF ${fix}</b></div></div>
        <div class="flowbox var"><div class="ft">Variable Kosten (je Reinigung)</div>
          <div class="fr"><span>Reinigung /Stk <input id="akqClean" type="number" value="${PD.clean}"></span><b></b></div>
          <div class="fr"><span>Verbrauch /Stk <input id="akqVer" type="number" value="${PD.verbrauch}"></span><b></b></div>
          <div class="fr"><span>Schlüssel: alle <input id="akqStayLen" type="number" step="0.5" value="${PD.stayLen}"> N 1×</span><b></b></div>
          <div class="ftot"><span>${stays} Reinigungen (${nights} N ÷ ${PD.stayLen})</span><b>CHF ${variabel}</b></div></div>
      </div>`;
    const net = `<div class="netresult">
      <div class="nt">Was bleibt — Netto / Monat · Belegung <input id="akqOcc" type="number" placeholder="${Math.round(mc.occBase) || ''}" value="${PD.occOv}"> %</div>
      <div class="nrow"><span>Einnahmen (${nights} belegte Nächte × CHF ${revNight})</span><b>+${einnahmen}</b></div>
      <div class="nrow"><span>− Fixkosten / Monat (Miete + Internet/TV + Wasser/Strom)</span><b>−${fix}</b></div>
      <div class="nrow"><span>− Variable (${stays} Reinigungen + Verbrauch)</span><b>−${variabel}</b></div>
      <div class="nbig"><span>Netto / Monat${nettoNacht != null ? ' (≈ CHF ' + nettoNacht + ' pro belegte Nacht)' : ''}</span><b style="color:${col}">CHF ${netto}</b></div>${r2rHTML}</div>`;
    return flow + net;
  }

  // Jahres-Prognose Monat-für-Monat (1:1 cockpit renderForecast). Rendert in #dossForecast.
  function dossForecast(m, rooms) {
    const body = document.getElementById('dossForecast');
    if (!body) return;
    try {
      document.querySelectorAll('#dossFcTog button').forEach(b => b.classList.toggle('on', b.dataset.fc === AKQ_FC));
      const seas = AKQ_SEASON[m.name];
      if (seas === undefined) {        // noch nicht geladen → lazy, dann erneut
        loadSeason(m.name).then(() => { if (document.getElementById('dossMarket').value === m.name) dossForecast(m, rooms); });
        body.innerHTML = '<div class="fcmiss">Saison-Profil wird geladen …</div>'; return;
      }
      if (!seas || !seas.index) {
        body.innerHTML = '<div class="fcmiss">Für ' + m.name + ' liegt noch kein Saison-Profil (BFS-Monatsdaten in market-facts.json) vor — ohne das wäre jede Monatszahl geraten. Netto/Monat oben gilt trotzdem.</div>'; return;
      }
      const mc = dossMoney(m, rooms);
      const p = mc.p;
      if (!p) { body.innerHTML = '<div class="fcmiss">Keine Preisbasis — Markt/Cockpit fehlt.</div>'; return; }
      const PD = AKQ_PD;
      // Zeit-Anker = Mess-Datum (cockpit-markets) sonst heute.
      const fp = String(seas.fetched || new Date().toISOString().slice(0, 10)).split('-').map(Number);
      const curY = fp[0] || new Date().getFullYear(), curM0 = (fp[1] || 1) - 1, today = fp[2] || 1;
      const idxNow = seas.index[curM0] || 1;
      const band = seas.occ_band || {};
      const bandMid = band.lower != null ? (band.upper != null ? (band.lower + band.upper) / 2 : band.lower) : null;
      // Anker (Jahresschnitt-Belegung): Eingabe > entsaisonalisierte Basis-Belegung > occ_band.
      let baseOcc, occSrc;
      if (PD.occOv !== '' && PD.occOv != null) { baseOcc = +PD.occOv; occSrc = 'deine Eingabe ' + baseOcc + '% Jahresschnitt'; }
      else if (mc.occBase != null && idxNow > 0) { baseOcc = Math.min(95, mc.occBase / idxNow); occSrc = (mc.occTier === 'live' ? 'Profi-Belegung ' : 'Modell ') + Math.round(mc.occBase) + '% ÷ Saison ' + idxNow.toFixed(2); }
      else if (bandMid != null) { baseOcc = bandMid; occSrc = 'occ_band ' + band.lower + '–' + band.upper + '%'; }
      else { body.innerHTML = '<div class="fcmiss">Keine Auslastungs-Basis — gib oben eine Belegung ein.</div>'; return; }
      const months = [];
      if (AKQ_FC === 'year') {
        for (let m0 = curM0; m0 < 12; m0++) { const dim = akqDaysInMonth(curY, m0); months.push({ y: curY, m0, dim, part: m0 === curM0 ? (dim - today + 1) / dim : 1 }); }
      } else {
        for (let i = 0; i < 12; i++) { const m0 = (curM0 + i) % 12, y = curY + Math.floor((curM0 + i) / 12); months.push({ y, m0, dim: akqDaysInMonth(y, m0), part: 1 }); }
      }
      const FY = STREcon.annualForecast({ price: p, anchorOcc: baseOcc, index: seas.index, months: months, costs: PD });
      const rows = FY.rows.map(o => `<div class="fcrow ${o.part < 1 ? 'part' : ''}">
        <div class="fcm">${AKQ_MONTHS[o.m0]}<small>${String(o.y).slice(2)}${o.part < 1 ? ' · Rest' : ''}</small></div>
        <div class="fcbar"><div class="l"><span>Auslastung</span><b>${o.occM}%</b></div><div class="fctrack"><div class="fcfill" style="width:${o.occM}%"></div></div></div>
        <div class="fcnet"><b style="color:${o.net >= 0 ? 'var(--green)' : 'var(--red)'}">${chf(o.net)}</b><small>${o.nights} N · ein. ${chf(o.inc).replace('CHF ', '')}</small></div></div>`).join('');
      const floorNet = (bandMid != null && Math.abs(bandMid - baseOcc) > 0.5 && (PD.occOv === '' || PD.occOv == null)) ? STREcon.annualNet({ price: p, anchorOcc: bandMid, index: seas.index, months: months, costs: PD }) : null;
      const modeLbl = AKQ_FC === 'year' ? ('Rest ' + curY + ' · ab ' + today + '. ' + AKQ_MONTHS[curM0]) : 'Nächste 12 Monate';
      const sum = `<div class="fcsum">
        <div class="st">${modeLbl}</div>
        <div class="sp">Geschätztes Gesamttotal · ${months.length} Monate · Ø Auslastung ${FY.avgOcc != null ? FY.avgOcc + '%' : '–'} · Preis CHF ${p}${seas.proxy ? ' · <span style="color:var(--amber)">⚠ Saison-Proxy ' + seas.proxy + '</span>' : ''}</div>
        <div class="srow"><span>Einnahmen (Host, ${FY.tNights} Nächte)</span><b>+${chf(FY.tInc).replace('CHF ', '')}</b></div>
        <div class="srow"><span>− Fixkosten (Miete + Internet/TV + Wasser/Strom)</span><b>−${chf(FY.tFix).replace('CHF ', '')}</b></div>
        <div class="srow"><span>− Variable (Reinigung + Verbrauch)</span><b>−${chf(FY.tVar).replace('CHF ', '')}</b></div>
        <div class="sbig"><span>Netto gesamt <small style="display:block;font-weight:500;color:var(--faint);font-size:10px">Kalender-Niveau (Obergrenze)</small></span><b style="color:${FY.tNet >= 0 ? 'var(--green)' : 'var(--red)'}">${chf(FY.tNet)}</b></div>
        ${floorNet != null ? `<div class="srow" style="border-top:1px dashed var(--lineS);margin-top:8px;padding-top:9px"><span>Konservativ — occ_band-Floor ${band.lower}–${band.upper}%</span><b style="color:${floorNet >= 0 ? 'var(--green)' : 'var(--red)'}">${chf(floorNet)}</b></div>` : ''}
        <div class="smeth">${seas.proxy ? '<b style="color:var(--amber)">⚠ Saison-Form via Proxy ' + seas.proxy + '</b> — BFS hat keine eigenen Hoteldaten für ' + m.name + ', die Saison-Wellen stammen vom Nachbarn. Niveau bleibt von ' + m.name + '. ' : ''}🟡 <b>Niveau</b> = ${occSrc} → Jahresschnitt ${Math.round(baseOcc)}%. <b>Form</b> = Hotel-Saisonkurve (BFS-Monatsdaten). Preis &amp; Kosten aus den Kästen oben. Gleiches Geld-Modell wie Netto/Monat, nur pro Kalendermonat.</div>
      </div>`;
      body.innerHTML = '<div class="fcgrid"><div class="fcmonths">' + rows + '</div>' + sum + '</div>';
    } catch (err) { body.innerHTML = '<div class="fcmiss">Prognose momentan nicht berechenbar (' + (err && err.message || err) + '). Netto/Monat oben ist unberührt.</div>'; }
  }

  // Kästen-/Belegungs-Eingaben verdrahten — schreiben AKQ_PD (localStorage) und rechnen Netto + R2R + Prognose live neu.
  function dossWireFlow(m, rooms, askRent) {
    const g = id => document.getElementById(id);
    const recalc = () => {
      try { localStorage.setItem('akq_cockpit_price', JSON.stringify(AKQ_PD)); } catch (e) {}
      const ds = dossDealScore(m, dossFacts());
      const scoreCol = ds.score >= 65 ? 'var(--green)' : ds.score >= 45 ? '#C9A24A' : 'var(--red)';
      const out = document.getElementById('dossOut');
      if (out) out.innerHTML = dossFlowHtml(m, rooms, askRent, ds, scoreCol);
      try { dossWireFlow(m, rooms, askRent); } catch (e) {}
      try { dossForecast(m, rooms); } catch (e) {}
    };
    const save = () => {
      AKQ_PD.gastFee = +g('akqGast').value || 0; AKQ_PD.hostFee = +g('akqHost').value || 0;
      AKQ_PD.kurtaxe = +g('akqKur').value || 0; AKQ_PD.traeger = g('akqTr').value;
      AKQ_PD.miete = +g('akqMiete').value || 0; AKQ_PD.internettv = +g('akqItv').value || 0;
      AKQ_PD.wasserstrom = +g('akqWS').value || 0; AKQ_PD.clean = +g('akqClean').value || 0;
      AKQ_PD.verbrauch = +g('akqVer').value || 0; AKQ_PD.stayLen = +g('akqStayLen').value || 0;
      AKQ_PD.occOv = g('akqOcc').value; recalc();
    };
    ['akqGast', 'akqHost', 'akqKur', 'akqMiete', 'akqItv', 'akqWS', 'akqClean', 'akqVer', 'akqStayLen', 'akqOcc'].forEach(id => { const e = g(id); if (e) e.onchange = save; });
    const tr = g('akqTr'); if (tr) tr.onchange = save;
    document.querySelectorAll('.akqPrice').forEach(e => e.onchange = () => { AKQ_PD.priceOv = e.value; recalc(); });
    // Prognose-Umschalter
    document.querySelectorAll('#dossFcTog button').forEach(b => b.onclick = () => { AKQ_FC = b.dataset.fc; try { localStorage.setItem('akq_fc', AKQ_FC); } catch (e) {} dossForecast(m, rooms); });
  }

  // Objektfakten aus dem Formular (für den Live-Regler, ohne renderDossier neu zu rufen).
  function dossFacts() {
    const g = id => document.getElementById(id);
    return {
      finish: g('dossFinish').value, laundry: g('dossLaundry').value, park: g('dossPark').value,
      view: g('dossView').value, building: g('dossBuilding').value, sublet: g('dossSublet').value,
      ground: g('dossGround').checked, vacant: g('dossVacant').checked, etw: g('dossEtw').checked,
    };
  }

  // Insights als kompakte Icon-Kacheln (Lage + Objekt). Deal-positive Kacheln grün umrandet.
  function dossInsightTilesHtml(f, loc, m, ds, o) {
    const tile = (icon, label, val, pos) => `
      <div class="rounded-lg p-2.5 border" style="border-color:${pos ? 'var(--green)' : 'var(--line)'};background:${pos ? 'rgba(63,174,124,.08)' : 'var(--panel)'}">
        <div class="text-lg leading-none">${icon}</div>
        <div class="text-[10px] uppercase tracking-wider text-[color:var(--muted)] mt-1">${label}</div>
        <div class="text-xs font-semibold mt-0.5" style="${pos ? 'color:var(--green)' : ''}">${val}</div>
      </div>`;
    // Lage-Kacheln (kuratiert + Quelle) oder ehrlicher Prüf-Hinweis.
    const lageTiles = loc
      ? tile('🚌', 'ÖV', loc.oev, false) + tile('🛒', 'Einkauf', loc.shop, false) + tile('📍', 'Lage', loc.extra, false)
      : tile('🚌', 'ÖV', 'auf sbb.ch prüfen', false) + tile('🛒', 'Einkauf', 'vor Ort prüfen', false) + tile('📍', 'Lage', `${m.name} — Mikrolage prüfen`, false);
    // Objekt-Kacheln (deal-positiv = grün).
    const fin = f.finish === 'neuwertig' ? ['✨', 'neuwertig/modern', true] : f.finish === 'gehoben' ? ['✨', 'gehoben', true]
      : f.finish === 'einfach' ? ['✨', 'einfach/älter', false] : ['✨', 'normal', false];
    const objTiles =
      tile(fin[0], 'Ausbau', fin[1], fin[2]) +
      tile('🌀', 'Waschturm', f.laundry === 'ja' ? 'in Wohnung' : f.laundry === 'nein' ? 'nur Waschküche' : 'unklar', f.laundry === 'ja') +
      tile('🅿️', 'Parkplatz', f.park === 'ja' ? 'vorhanden' : f.park === 'moeglich' ? 'möglich' : 'keiner', f.park === 'ja' || f.park === 'moeglich') +
      tile('🏔️', 'Aussicht', f.view === 'ja' ? 'schön' : f.view === 'teilweise' ? 'teilweise' : 'keine bes.', f.view === 'ja') +
      tile('🏢', 'Überbauung', f.building === 'gross' ? 'gross (anonym)' : f.building === 'mfh' ? 'kleines MFH' : 'Einzelhaus', f.building === 'gross') +
      tile('🔑', 'Untervermietung', f.sublet === 'verboten' ? 'ausgeschlossen' : f.sublet === 'zustimmung' ? 'mit Zustimmung' : 'nicht erwähnt', f.sublet !== 'verboten') +
      (f.ground ? tile('🚪', 'Eingang', 'EG/eigener Eingang', true) : '');
    return `
      <div class="mb-3">
        <div class="wp-h mb-1.5">Lage</div>
        <div class="grid grid-cols-3 gap-2">${lageTiles}</div>
        <div class="text-[10px] text-[color:var(--muted)] mt-1.5">Quelle: ${loc ? loc.src : 'noch nicht hinterlegt — ÖV-Zeit ab Adresse auf sbb.ch prüfen, nichts erfunden'}</div>
      </div>
      <div>
        <div class="wp-h mb-1.5">Objekt <span class="text-[color:var(--muted)] font-normal normal-case tracking-normal text-[10px]">(grün = deal-positiv · aus deinen Foto-Fakten)</span></div>
        <div class="grid grid-cols-3 gap-2">${objTiles}</div>
      </div>
      <div class="mt-3 p-3 rounded-lg" style="background:${ds.score >= 65 ? 'rgba(63,174,124,.12)' : ds.score >= 45 ? 'rgba(224,162,62,.12)' : 'rgba(229,57,43,.12)'}">
        <div class="wp-h mb-1">Deal-Treiber (Score ${ds.score}/100)</div>
        <ul class="text-xs space-y-0.5">${ds.drivers.slice(0, 4).map(d => `<li>${d.pts >= 0 ? '+' : '−'} ${d.txt}</li>`).join('')}</ul>
      </div>`;
  }

  function renderDossier() {
    const m = markets.find(x => x.name === document.getElementById('dossMarket').value);
    const out = document.getElementById('dossOut');
    if (!m) { out.innerHTML = '<div class="text-white/70 text-sm">Markt wählen.</div>'; return; }
    // Profi-Belegung (Live-Cockpit) lazy laden — bei Erstkontakt erneut rendern, sobald da.
    try {
      if (AKQ_COCKPIT_OCC[m.name] === undefined) {
        loadCockpitOcc(m.name).then(() => { if (document.getElementById('dossMarket').value === m.name) { DOSS_XF_PRESET.market = null; renderDossier(); } });
      }
    } catch (e) { /* Fallback bleibt Modell */ }
    const type = document.getElementById('dossType').value;
    const rooms = parseFloat(document.getElementById('dossRooms').value) || 2.5;
    const rent = parseFloat(document.getElementById('dossRent').value) || 0;
    const street = document.getElementById('dossStreet').value.trim();
    const url = document.getElementById('dossUrl').value.trim();
    const f = {
      finish: document.getElementById('dossFinish').value,
      laundry: document.getElementById('dossLaundry').value,
      park: document.getElementById('dossPark').value,
      view: document.getElementById('dossView').value,
      building: document.getElementById('dossBuilding').value,
      sublet: document.getElementById('dossSublet').value,
      ground: document.getElementById('dossGround').checked,
      vacant: document.getElementById('dossVacant').checked,
      etw: document.getElementById('dossEtw').checked,
    };
    const askRent = rent || null;
    // Die geforderte Inserat-Miete bevölkert das Miete-Feld des Geldrechners (der Akquise-Unterschied).
    // Nur beim Wechsel von Markt/Grösse/Ask setzen — manuelle Kästen-Edits bleiben sonst erhalten.
    const objChanged = DOSS_BID.market !== m.name || DOSS_BID.rooms !== rooms || DOSS_BID.ask !== askRent;
    if (objChanged) {
      if (askRent != null) AKQ_PD.miete = askRent;
      try { localStorage.setItem('akq_cockpit_price', JSON.stringify(AKQ_PD)); } catch (e) {}
      DOSS_BID.market = m.name; DOSS_BID.rooms = rooms; DOSS_BID.ask = askRent;
    }
    // DEFAULT-VORWAHL der Vergleichs-Filter beim Objekt-/Markt-Wechsel: Zimmer-Band des Objekts + ganze Wohnung.
    // Nur wenn Inserate da sind (sonst greifen die Filter erst beim Lazy-Load, siehe loadCockpitOcc-Callback unten).
    if (DOSS_XF_PRESET.market !== m.name || DOSS_XF_PRESET.rooms !== rooms) {
      if (akqMarketListings(m.name).length) {
        try {
          for (const d of ['group', 'rating', 'vol', 'type', 'cap', 'rooms']) AKQ_F[d].clear();
          const rb = akqRoomBand(rooms); if (rb) AKQ_F.rooms.add(rb);
          AKQ_F.type.add('Wohnung');
        } catch (e) {}
        DOSS_XF_PRESET.market = m.name; DOSS_XF_PRESET.rooms = rooms;
      }
    }
    const ds = dossDealScore(m, f);
    const loc = AKQ_LOCATION[m.name];
    const scoreCol = ds.score >= 65 ? 'var(--green)' : ds.score >= 45 ? '#C9A24A' : 'var(--red)';

    // --- ZONE 1: Objekt-Kopf = das newhome-Mietinserat sichtbar (Titel · Miete · Typ · Link · Foto) ---
    const objHead = document.getElementById('dossObjHead');
    if (objHead) {
      const lead = (_akqState.lead && _akqState.lead.url === url) ? _akqState.lead : null;
      const lno = lead ? lead.listing_no : (typeof akqListingNo === 'function' ? akqListingNo(url) : null);
      const portal = url ? (/newhome/i.test(url) ? 'newhome' : /homegate/i.test(url) ? 'Homegate' : /immoscout/i.test(url) ? 'ImmoScout24' : 'Inserat') : null;
      const photo = (lead && (lead.photo || lead.image || lead.img)) || null;
      objHead.innerHTML = `
        <div class="flex gap-3 items-start">
          <div class="flex-shrink-0 rounded-lg overflow-hidden border border-[color:var(--line)]" style="width:104px;height:78px;background:var(--panel)">
            ${photo
              ? `<img src="${photo}" alt="Inserat" style="width:100%;height:100%;object-fit:cover" onerror="this.parentNode.innerHTML='<div style=&quot;width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:var(--faint);font-size:26px&quot;>🏠</div>'">`
              : `<div style="width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--faint)"><div style="font-size:26px">🏠</div><div class="text-[9px] mt-0.5">Foto im Inserat</div></div>`}
          </div>
          <div class="min-w-0 flex-1">
            <div class="font-display text-lg leading-tight">${rooms} Zi · ${street || (lead && lead.street) || '(Strasse aus Inserat)'}, ${m.name}</div>
            <div class="text-xs mt-1 flex items-center gap-2 flex-wrap">
              <span class="proof-badge ${rent ? 'proof-green' : 'proof-amber'}">${rent ? chf(rent) + '/Mt' : 'Miete offen'}</span>
              <span class="proof-badge proof-amber">${type === 'privat' ? '👤 Privatperson' : '🏢 Immobilienfirma'}</span>
              ${portal ? `<span class="text-[10px] text-[color:var(--muted)]">${portal}${lno ? ' Nr. ' + lno : ''}</span>` : ''}
            </div>
            ${url ? `<div class="text-xs mt-1.5"><a href="${url}" target="_blank" rel="noopener" class="underline" style="color:var(--gold)">Inserat öffnen ↗</a></div>`
                  : `<div class="text-[11px] text-[color:var(--muted)] mt-1.5">Kein Link — Lead wählen oder Objektfakten erfassen.</div>`}
          </div>
        </div>`;
    }
    const mtag = document.getElementById('dossMarketTag'); if (mtag) mtag.textContent = '· aus Cockpit ' + m.name;

    // --- ZONE 2: Voller Cockpit-Geldrechner (4 Kästen + Netto/Monat + R2R-Spielraum) + Jahres-Prognose ---
    out.innerHTML = dossFlowHtml(m, rooms, askRent, ds, scoreCol);
    try { dossWireFlow(m, rooms, askRent); } catch (e) {}
    try { dossForecast(m, rooms); } catch (e) {}

    // --- hinter Aufklapper: Insights als kompakte Icon-Kacheln (Lage + Objekt) ---
    const ins = document.getElementById('dossInsightsOut');
    if (ins) ins.innerHTML = dossInsightTilesHtml(f, loc, m, ds);

    // --- hinter Aufklapper: Strategie + Verhandlung ---
    const stratOut = document.getElementById('dossStratOut');
    if (stratOut) stratOut.innerHTML = `
      <div class="wp-h mb-1">Strategie für ${type === 'privat' ? 'Privatperson' : 'Immobilienfirma'}</div>
      <ul class="text-sm space-y-1.5">${DOSS_STRAT[type].map(s => `<li>› ${s}</li>`).join('')}</ul>
      <button onclick="dossLetter()" class="mt-3 px-4 py-2 rounded bg-[color:var(--ink)] text-white text-sm font-semibold">Brief-Entwurf erstellen →</button>`;

    // --- Vergleichs-Markt-Filter-Dashboard rendern (steuert die Ertrags-Kohorte oben) ---
    try { akqRenderFilters(); } catch (e) {}

    // --- Pitch-Zone (rechts) mit dem Brieftext füllen ---
    try { dossFillPitch(m, type, f); } catch (e) {}
  }

  // Metrik-Umschalter (Auslastung % ↔ Umsatz CHF/Mt) für das Filter-Dashboard — einmal verdrahten.
  (function akqWireMetricTog() {
    function wire() {
      document.querySelectorAll('#akqXfMetricTog button').forEach(b => b.onclick = () => { AKQ_METRIC = b.dataset.m; try { akqRenderFilters(); } catch (e) {} });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire); else wire();
  })();

  // Pitch-Box (Zone 3) aus den Brief-Templates füllen — Variante folgt Anbieter-Typ.
  let _dossPitchVariant = 1;
  function dossFillPitch(m, type, f) {
    const body = document.getElementById('dossPitchBody');
    if (!body || typeof LETTER_TEMPLATES === 'undefined') return;
    const street = (document.getElementById('dossStreet') || {}).value || '[Strasse]';
    const rooms = (document.getElementById('dossRooms') || {}).value || '2.5';
    // Variante 1/2 je nach Anbieter-Typ.
    const keys = type === 'firma' ? ['firma_einzel', 'firma_portfolio'] : ['personal_unknown', 'premium_stability'];
    const key = keys[_dossPitchVariant - 1] || keys[0];
    let txt = LETTER_TEMPLATES[key] || '';
    txt = String(txt)
      .replace(/\{\{\s*schlupfloch_block\s*\}\}/gi, '')
      .replace(/\{\{\s*stadt\s*\}\}/gi, m.name)
      .replace(/\{\{\s*strasse_inserat\s*\}\}/gi, street)
      .replace(/\{\{\s*wohnungs_typ\s*\}\}/gi, rooms + '-Zimmer-Wohnung')
      .replace(/\{\{\s*absender_name\s*\}\}/gi, 'Adrian Maag')
      .replace(/\{\{\s*anzahl_übernachtungen\s*\}\}/gi, '200')
      .replace(/\{\{\s*anrede_eigentümer\s*\}\}/gi, 'Damen und Herren')
      .replace(/\{\{\s*zielgruppe\s*\}\}/gi, 'Geschäfts- und Wochenend-Gäste')
      .replace(/\{\{\s*versicherungs_summe\s*\}\}/gi, "500'000")
      .replace(/\n{3,}/g, '\n\n')
      .replace(/\{\{[^}]+\}\}/g, '[…]');
    body.textContent = txt || 'Kein Pitch-Template für diese Variante.';
    const hint = document.getElementById('dossPitchHint');
    if (hint) hint.textContent = (type === 'firma' ? 'Firma' : 'Privat') + ' · Variante ' + _dossPitchVariant + ' — kein Versand, du öffnest in Gmail und sendest selbst.';
  }

  // Brief-Generator aus dem Dossier öffnen — Variante + Strasse nach Anbieter-Typ vorbelegt.
  function dossLetter() {
    const m = markets.find(x => x.name === document.getElementById('dossMarket').value);
    if (!m) return;
    const type = document.getElementById('dossType').value;
    openLetterGen(m);
    const street = document.getElementById('dossStreet').value.trim();
    if (street) document.getElementById('letterStreet').value = street;
    document.getElementById('letterVariant').value = type === 'firma' ? 'firma_einzel' : 'personal_unknown';
    generateLetter();
  }

  function initDossier() {
    const sel = document.getElementById('dossMarket');
    if (!sel || typeof markets === 'undefined' || !markets.length) return;
    if (!sel.options.length) {
      sel.innerHTML = markets.slice().sort((a, b) => a.name.localeCompare(b.name, 'de')).map(m => `<option value="${m.name}">${m.name}</option>`).join('');
      sel.value = 'Kriens';
    }
    document.getElementById('dossBtn').onclick = renderDossier;
    // BFS-Marktmiete einmalig laden (Anker für den R2R-Spielraum), dann neu rendern.
    if (AKQ_RENTS === null) {
      fetch('data/mietpreise.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).then(j => {
        AKQ_RENTS = j || false;
        try { renderDossier(); } catch (e) {}
      }).catch(() => { AKQ_RENTS = false; });
    }
  }

  // ---- Mietinserat per Deep-Link übernehmen (akquise.html#lead=<base64>) ----
  // Befüllt Markt/Zimmer/Miete/URL vor + rendert das Dossier. Behandelt es als MANUELLEN
  // newhome-Lead (KEINE Airbnb-/Briefing-Quelle). Objektfakten bleiben LEER (nie erfinden —
  // Adrian sichtet die Fotos).
  function akqApplyLeadFromHash() {
    let payload = null;
    try {
      const m = (location.hash || '').match(/lead=([^&]+)/);
      if (!m) return;
      payload = JSON.parse(decodeURIComponent(escape(atob(m[1]))));
    } catch (e) { return; }
    if (!payload) return;
    _akqState.signal = null;
    const setVal = (id, v) => { const el = document.getElementById(id); if (el && v != null && v !== '') el.value = v; };
    // Markt nur setzen, wenn er in der Liste ist (sonst Default behalten).
    const ms = document.getElementById('dossMarket');
    if (ms && payload.market && [...ms.options].some(o => o.value === payload.market)) ms.value = payload.market;
    setVal('dossRooms', payload.rooms);
    setVal('dossRent', payload.price || payload.rent);
    setVal('dossUrl', payload.url);
    // Hash-Lead als manuellen newhome-Lead ins Board aufnehmen + selektieren.
    const hl = { source: 'manuell', market: payload.market, rooms: payload.rooms, rent: payload.price || payload.rent, url: payload.url, listing_no: (typeof akqListingNo === 'function' ? akqListingNo(payload.url) : null) };
    _akqState.lead = hl;
    try { renderDossier(); } catch (e) {}
    try { akqSyncLaw(); } catch (e) {}
    try {
      if (typeof akqMergeLeads === 'function') { akqMergeLeads([hl]); AKQWORK.selKey = akqLeadKey(hl); akqRenderLeadBoard(); }
    } catch (e) {}
    try { akqShowLeadBanner(hl); } catch (e) {}
    try { document.getElementById('dossOut').scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (e) {}
  }

  // Lead an den Agenten geben: /api/check-url (Inserat bewerten + in _manuell.json),
  // danach greifen Compose/Outbox/Approve daran. Signal bleibt für den Funnel gesetzt.
  async function akqGiveLeadToAgent() {
    const lead = _akqState.lead || {};
    const banner = document.getElementById('akqLeadBanner');
    const note = (t) => { const s = document.getElementById('akqLeadStat'); if (s) s.textContent = t; };
    if (!lead.url) { note('⚠ Dieser Lead hat keinen Inserat-Link — über „Inserat bewerten" unten manuell erfassen.'); ensureLeadStat(banner); return; }
    ensureLeadStat(banner); note('gebe Lead an den Agenten …');
    const rent = parseFloat(document.getElementById('dossRent').value) || 0;
    const rooms = parseFloat(document.getElementById('dossRooms').value) || 0;
    let r;
    try { r = await akqApi('/api/check-url', { url: lead.url, rent, rooms, city: lead.market }); }
    catch (e) { note('⚠ Agent nicht erreichbar — unten „Akquise-Agent" starten.'); return; }
    if (r.error && !r.listing) { note('⚠ ' + r.error); return; }
    if (r.rejected) { note('Würde rausfallen: ' + r.reason); return; }
    _akqState.source = r.source || '_manuell.json';
    note('✓ Lead bewertet — du kannst jetzt unten Anschreiben/Outbox/Approve nutzen (Signal „' + (_akqState.signal || '—') + '" wird beim Festhalten mitgeführt).');
    try {
      const res = document.getElementById('akqUrlResult');
      if (res && typeof akqCard === 'function') res.innerHTML = akqCard(r.listing);
      const su = document.getElementById('akqUrl'); if (su) su.value = lead.url;
      document.getElementById('akqMain') && (document.getElementById('akqMain').scrollIntoView({ behavior: 'smooth' }));
    } catch (e) {}
  }
  function ensureLeadStat(banner) {
    if (banner && !document.getElementById('akqLeadStat')) {
      const d = document.createElement('div'); d.id = 'akqLeadStat'; d.className = 'text-xs text-[color:var(--muted)] mt-1'; banner.appendChild(d);
    }
  }

  // ---- Akquise-Pack: eine Markt-Auswahl treibt alles ----
  function initAkqStrats() {
    const sel = document.getElementById('akqStratMarket');
    if (!sel || typeof markets === 'undefined' || !markets.length) return;
    const renderPack = (m) => {
      if (!m) return;
      renderSearchStrats(m, 'akqSearchStrats', 'akqStratMarketLabel');
      renderLoopholes(m, 'akqLoopholeCard', 'akqLoopholeBody');
      renderChecklist(m, 'akqChecklist', 'akqChecklistMarket');
      const lb = document.getElementById('akqLetterBtn'); if (lb) lb.onclick = () => openLetterGen(m);
    };
    if (!sel.options.length) {
      sel.innerHTML = markets.slice().sort((a, b) => a.name.localeCompare(b.name, 'de')).map(m => `<option value="${m.name}">${m.name}</option>`).join('');
      sel.onchange = () => renderPack(markets.find(x => x.name === sel.value));
    }
    renderPack(markets.find(x => x.name === sel.value) || markets[0]);
  }

