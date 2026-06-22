// ============================================================================
// SwissSTR — Investor-ROI-Rechner (selbsttragendes Modul)
// ----------------------------------------------------------------------------
// Aus index.html herausgelöst (v0.9.153). Eigenständig, KEINE Abhängigkeit von
// der index.html-Engine (marketEconomics/AIRBNB_COMP) — damit der Investor-Teil
// NICHT an der täglichen Airbnb-Scrape-Kopplung hängt (Adrians Scrape-Sorge).
//
// Datenbasis: das geteilte `markets`-Array aus js/data.js (Markt-Baseline:
//   name/canton/adr/occ/revpar/grade — BFS/statisch, kein Tages-Scrape nötig).
// Ertragsmodell (bed/tier-Multiplikatoren) = dokumentierte Investor-Annahmen,
//   identisch zur ursprünglichen index.html-Logik. Keine geteilte Geld-Formel,
//   die anderswo dieselbe Zahl liefern müsste → kein stiller Fork-Drift.
//
// Einbinden:  <script src="js/data.js"></script>
//             <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
//             <script src="js/investor.js"></script>  → SwissInvestor.init()
// ============================================================================
(function () {
  'use strict';

  // ── Ertragsmodell-Konstanten (Investor-eigene Kopie, dokumentiert) ─────────
  const BED_CONFIGS = {
    '1':   { label: '1Z Studio', bedMult: 0.65, occMult: 1.10 },
    '2.5': { label: '2.5Z',      bedMult: 0.85, occMult: 1.05 },
    '3.5': { label: '3.5Z',      bedMult: 1.00, occMult: 1.00 },
    '4.5': { label: '4.5Z',      bedMult: 1.35, occMult: 0.92 },
    '5.5': { label: '5.5Z+',     bedMult: 1.85, occMult: 0.85 },
  };
  // Operator-Tiers: gleiche Wohnung, anderer Operator (Pricing-Power × Auslastung).
  const OPERATOR_TIERS = {
    bottom30: { adrMult: 0.92, occMult: 0.78 },
    median:   { adrMult: 1.00, occMult: 1.00 },
    top10:    { adrMult: 1.12, occMult: 1.15 },
  };
  // ── Deal-Kosten-Annahmen (EINE Quelle; Mathe UND Anzeige-Labels lesen von hier) ──
  // Investor-eigenes Modell (bewusst standalone, siehe Kopf-Kommentar). Daneben das
  // kanonische STREcon-Pendant der Live-Engine — eine Angleichung an akquise.html ist
  // ein PRODUKTENTSCHEID, kein Code-Fix (anderes Kostenmodell: Kauf-Investor vs R2R-Betreiber).
  const DEAL = {
    platformPct:    0.14,  // OTA-Gebühr auf Brutto       · STREcon: Host 3% + Gast 15% (split)
    kurtaxePct:     0.02,  // Kurtaxe-Proxy auf Brutto     · STREcon: CHF 4/Nacht, vom Gast getragen
    cleaningPctBuy: 0.08,  // Reinigung %-Brutto (Kauf)    · STREcon: CHF 90/Aufenthalt
    opexPctBuy:     0.012, // Unterhalt+Vers.+NK p.a. auf Kaufpreis
    stayNights:     4,     // Ø Aufenthalt → Putz-Frequenz · STREcon stayLen: 3
  };
  function bedKeyForCount(beds) { return beds <= 1 ? '1' : beds === 2 ? '2.5' : beds <= 3 ? '3.5' : beds === 4 ? '4.5' : '5.5'; }
  function tierMultsForPctile(p) {
    const B = OPERATOR_TIERS.bottom30, M = OPERATOR_TIERS.median, T = OPERATOR_TIERS.top10;
    const lerp = (a, b, f) => a + (b - a) * f;
    if (p <= 30) return { adrMult: B.adrMult, occMult: B.occMult };
    if (p <= 50) { const f = (p - 30) / 20; return { adrMult: lerp(B.adrMult, M.adrMult, f), occMult: lerp(B.occMult, M.occMult, f) }; }
    if (p <= 90) { const f = (p - 50) / 40; return { adrMult: lerp(M.adrMult, T.adrMult, f), occMult: lerp(M.occMult, T.occMult, f) }; }
    return { adrMult: T.adrMult, occMult: T.occMult };
  }
  // Markt-Baseline-Auslastung (statisch aus data.js; Fallback 60). Bewusst NICHT
  // die Live-Airbnb-occ — ein Kauf-Modell ist langfristig, kein Tages-Snapshot.
  const occBaseOf = m => (m && m.occ != null ? m.occ : 60);

  // ── Formatter ──────────────────────────────────────────────────────────────
  function fmt(n) { return 'CHF ' + Math.round(n).toLocaleString('de-CH').replace(/,/g, "'"); }
  function pct(n) { return (n * 100).toFixed(2) + '%'; }

  // Dezente dunkle Tints für Ampel-Hintergründe
  const TINT = { green: 'rgba(63,174,124,.16)', gold: 'rgba(217,179,106,.16)', grey: 'rgba(139,147,163,.14)', red: 'rgba(229,57,43,.16)' };

  // ── State ───────────────────────────────────────────────────────────────────
  let waterfallChart = null;
  let mgmtPct = 0.05;
  let invMode = 'buy';      // 'buy' | 'rent'
  let investorInited = false;
  let _r2rCtx = null;

  const $ = id => document.getElementById(id);
  const M = () => (typeof markets !== 'undefined' ? markets : []);

  // ── Init / Wiring ────────────────────────────────────────────────────────────
  function init() {
    if (!investorInited) {
      const sel = $('invMarket');
      if (sel) {
        sel.innerHTML = '';
        M().forEach(m => {
          const o = document.createElement('option');
          o.value = m.name; o.textContent = `${m.name} (${m.canton}) · RevPAR CHF ${m.revpar}`;
          sel.appendChild(o);
        });
        sel.value = M().some(m => m.name === 'Zermatt') ? 'Zermatt' : (M()[0] && M()[0].name);
        sel.addEventListener('change', updateInvestor);
      }
      ['invPrice', 'invEquity', 'invRate', 'invBeds', 'invPct', 'invRent', 'invSetup', 'invClean', 'invListingUrl', 'invPhotoUrl', 'invPk', 'invIncome'].forEach(id => {
        const el = $(id); if (el) el.addEventListener('input', updateInvestor);
      });
      document.querySelectorAll('[data-mgmt]').forEach(b => b.addEventListener('click', () => {
        document.querySelectorAll('[data-mgmt]').forEach(x => x.classList.remove('active'));
        b.classList.add('active');
        mgmtPct = b.dataset.mgmt === 'self' ? 0.05 : b.dataset.mgmt === 'hybrid' ? 0.15 : 0.25;
        updateInvestor();
      }));
      document.querySelectorAll('[data-invmode]').forEach(b => b.addEventListener('click', () => setInvMode(b.dataset.invmode)));
      const gen = $('invGenLetter'); if (gen) gen.addEventListener('click', genR2RLetter);
      const cpy = $('invCopyLetter'); if (cpy) cpy.addEventListener('click', copyR2RLetter);
      investorInited = true;
    }
    setInvMode(invMode);
  }

  function setInvMode(mode) {
    invMode = mode;
    document.querySelectorAll('[data-invmode]').forEach(b => b.classList.toggle('active', b.dataset.invmode === mode));
    document.querySelectorAll('[data-mode-group]').forEach(g => g.classList.toggle('hidden', g.dataset.modeGroup !== mode));
    const kpis = $('view-investor');
    if (kpis) {
      const capLabel = kpis.querySelector('[data-kpi-label="cap"]');
      const cocLabel = kpis.querySelector('[data-kpi-label="coc"]');
      if (capLabel) capLabel.textContent = mode === 'rent' ? 'Mietzins-Multiple' : 'Cap Rate';
      if (cocLabel) cocLabel.textContent = mode === 'rent' ? 'Annual / Setup' : 'Cash-on-Cash';
    }
    updateInvestor();
  }

  // ── Hauptberechnung ──────────────────────────────────────────────────────────
  function updateInvestor() {
    const sel = $('invMarket');
    const list = M();
    const m = list.find(x => x.name === (sel && sel.value)) || list[15] || list[0];
    if (!m) return;
    const beds = +$('invBeds').value;
    const pctile = +$('invPct').value;

    $('invBedsLabel').textContent = beds;
    $('invPctLabel').textContent = pctile <= 30 ? 'P25 (Bottom)' : pctile <= 55 ? 'P50 (Median)' : pctile <= 75 ? 'P75 (Top 25%)' : 'P90 (Top 10%)';

    const cfgEng = BED_CONFIGS[bedKeyForCount(beds)];
    const { adrMult: tAdr, occMult: tOcc } = tierMultsForPctile(pctile);
    const adrEng = Math.round((m.adr || 0) * cfgEng.bedMult * tAdr);
    const occEng = Math.min(95, Math.max(15, Math.round(occBaseOf(m) * cfgEng.occMult * tOcc)));
    const nightsEng = Math.round(365 * occEng / 100);
    const gross = adrEng * nightsEng;

    const platformFee = gross * DEAL.platformPct;
    const mgmtCost = gross * mgmtPct;
    const stayNights = DEAL.stayNights;
    const stays = nightsEng > 0 ? Math.max(1, Math.round(nightsEng / stayNights)) : 0;
    const kurtaxe = gross * DEAL.kurtaxePct;

    let cleaning, opex, interest, equity, cashflow, cap, coc, breakEvenMonths, badgeText;
    let amort = 0, cocBase = 0;

    if (invMode === 'rent') {
      const monthlyRent = +$('invRent').value;
      const setup = +$('invSetup').value;
      const cleanPer = +$('invClean').value;
      $('invRentLabel').textContent = fmt(monthlyRent);
      $('invSetupLabel').textContent = fmt(setup);
      $('invCleanLabel').textContent = 'CHF ' + cleanPer;

      const annualRent = monthlyRent * 12;
      cleaning = stays * cleanPer;
      const supplies = 12 * 150;
      const insurance = 720;
      const utilities = 12 * 180;
      opex = supplies + insurance + utilities;
      const noi = gross - platformFee - mgmtCost - cleaning - opex - kurtaxe;
      const annualCash = noi - annualRent;

      equity = setup; amort = 0; cocBase = setup;
      interest = annualRent;
      cashflow = annualCash;
      cap = monthlyRent > 0 ? (gross / 12) / monthlyRent : 0;
      coc = equity > 0 ? cashflow / equity : 0;
      breakEvenMonths = cashflow > 0 ? setup / (cashflow / 12) : Infinity;

      $('invGrossRev').textContent = fmt(gross);
      $('invNetRev').textContent = fmt(noi);
      $('invCap').textContent = cap.toFixed(2) + '×';
      $('invCoC').textContent = pct(coc);

      drawWaterfall({ gross, platformFee, mgmtCost, cleaning, opex, kurtaxe, noi, interest: annualRent, cashflow, mode: 'rent' });
      renderBreakdown({ mode: 'rent', setup, monthlyRent, supplies, insurance, utilities, gross, platformFee, mgmtCost, cleaning, kurtaxe, cleanPer, stays });
      renderListingPanel({ m, monthlyRent, beds, cap, cashflow, breakEvenMonths });
    } else {
      const price = +$('invPrice').value;
      const eqPct = +$('invEquity').value / 100;
      const rate = +$('invRate').value / 100;
      $('invPriceLabel').textContent = fmt(price);
      $('invEquityLabel').textContent = (eqPct * 100).toFixed(0) + '%';
      $('invRateLabel').textContent = (rate * 100).toFixed(2) + '%';

      cleaning = gross * DEAL.cleaningPctBuy;
      opex = price * DEAL.opexPctBuy;
      const noi = gross - platformFee - mgmtCost - cleaning - opex - kurtaxe;
      const loan = price * (1 - eqPct);
      interest = loan * rate;
      amort = Math.max(0, loan - price * 0.65) / 15;
      equity = price * eqPct;
      const closingCosts = price * 0.05;
      const furnishing = 12000;
      cocBase = equity + closingCosts + furnishing;
      cashflow = noi - interest - amort;
      cap = price > 0 ? noi / price : 0;
      coc = cocBase > 0 ? cashflow / cocBase : 0;

      $('invGrossRev').textContent = fmt(gross);
      $('invNetRev').textContent = fmt(noi);
      $('invCap').textContent = pct(cap);
      $('invCoC').textContent = pct(coc);

      drawWaterfall({ gross, platformFee, mgmtCost, cleaning, opex, kurtaxe, noi, interest, amort, cashflow, mode: 'buy' });
      renderBreakdown({ mode: 'buy', price, loan, rate, equity, gross, platformFee, mgmtCost, cleaning, opex, kurtaxe, interest, amort, closingCosts, furnishing });
      renderAffordability({ price, eqPct, loan });
    }

    // Sensitivität — modus-bewusst: die Mittelzelle (ADR 0% / Occ 0%) MUSS die Schlagzeilen-CoC
    // exakt reproduzieren. Im Rent-Modus skaliert die Reinigung mit der Belegung (mehr Aufenthalte),
    // NICHT mit dem Brutto (fixer CHF-Satz/Wechsel) — anders als der Buy-%-Satz vom Brutto.
    const occRange = [-10, -5, 0, 5, 10];
    const adrRange = [-15, -5, 0, 5, 15];
    const sensIsRent = invMode === 'rent';
    const sensCleanPer = sensIsRent ? (+$('invClean').value) : 0;
    let html = '<table class="w-full text-xs border-collapse"><thead><tr><th class="p-1"></th>';
    adrRange.forEach(a => html += `<th class="text-center p-1 text-[color:var(--muted)] font-medium">ADR ${a > 0 ? '+' : ''}${a}%</th>`);
    html += '</tr></thead><tbody>';
    occRange.forEach(o => {
      html += `<tr><td class="text-[color:var(--muted)] font-medium pr-2 p-1">Occ ${o > 0 ? '+' : ''}${o}%</td>`;
      adrRange.forEach(a => {
        const g2 = gross * (1 + a / 100) * (1 + o / 100);
        let noi2;
        if (sensIsRent) {
          // Aufenthalte skalieren mit Occ (nicht ADR); bei o=0 ⇒ stays2==stays ⇒ Reinigung==Schlagzeile.
          const stays2 = stays > 0 ? Math.max(1, Math.round(stays * (1 + o / 100))) : 0;
          const cleaning2 = stays2 * sensCleanPer;
          noi2 = g2 * (1 - DEAL.platformPct - mgmtPct - DEAL.kurtaxePct) - cleaning2 - opex;
        } else {
          noi2 = g2 * (1 - DEAL.platformPct - mgmtPct - DEAL.cleaningPctBuy - DEAL.kurtaxePct) - opex;
        }
        const cf = noi2 - interest - amort;
        const coc2 = cocBase > 0 ? cf / cocBase : 0;
        const color = coc2 >= 0.06 ? '#3FAE7C' : coc2 >= 0.02 ? '#D9B36A' : coc2 >= 0 ? '#8B93A3' : '#E5392B';
        const bg = coc2 >= 0.06 ? TINT.green : coc2 >= 0.02 ? TINT.gold : coc2 >= 0 ? TINT.grey : TINT.red;
        html += `<td class="text-center p-1 font-semibold" style="background:${bg};color:${color}">${pct(coc2)}</td>`;
      });
      html += '</tr>';
    });
    html += '</tbody></table>';
    $('invSensitivity').innerHTML = html;

    const swap = 0.0135;
    const spread = coc - swap;
    let verdict;
    if (invMode === 'rent') {
      if (cap >= 2.5 && breakEvenMonths < 12) verdict = `<span class="pill pill-green">Strong Deal</span>`;
      else if (cap >= 2.0 && breakEvenMonths < 18) verdict = `<span class="pill pill-gold">Solider Deal</span>`;
      else if (cap >= 1.5 && cashflow > 0) verdict = `<span class="pill pill-grey">Knapp profitabel</span>`;
      else verdict = `<span class="pill pill-red">Lass die Finger weg</span>`;
    } else {
      if (coc >= 0.07) verdict = `<span class="pill pill-green">Strong Buy</span>`;
      else if (coc >= 0.04) verdict = `<span class="pill pill-gold">Hold / Cautious Buy</span>`;
      else if (coc >= 0) verdict = `<span class="pill pill-grey">Marginal</span>`;
      else verdict = `<span class="pill pill-red">Avoid</span>`;
    }

    const beDenom = adrEng * 365 * (1 - DEAL.platformPct - mgmtPct - DEAL.cleaningPctBuy - DEAL.kurtaxePct);
    const beOcc = beDenom > 0 ? (interest + amort + opex) / beDenom : 0;

    const verdictBody = invMode === 'rent' ? `
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">Mietzins-Multiple</span><span class="font-semibold">${cap.toFixed(2)}× <span class="text-xs text-[color:var(--muted)]">(STR-Monat / Mietzins)</span></span></div>
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">Annual Cashflow</span><span class="font-semibold" style="color:${cashflow >= 0 ? 'var(--green)' : 'var(--red)'}">${fmt(cashflow)}</span></div>
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">Monatlich Netto</span><span class="font-semibold">${fmt(cashflow / 12)}</span></div>
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">Break-Even Setup</span><span class="font-semibold">${breakEvenMonths === Infinity ? 'nie' : breakEvenMonths.toFixed(1) + ' Monate'}</span></div>
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">Break-Even Occupancy</span><span class="font-semibold">${pct(beOcc)}</span></div>` : `
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">Cashflow / Jahr <span class="text-[10px]">nach Zins &amp; Amort.</span></span><span class="font-semibold" style="color:${cashflow >= 0 ? 'var(--green)' : 'var(--red)'}">${fmt(cashflow)}</span></div>
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">davon Amortisation <span class="text-[10px]">baut EK auf</span></span><span class="font-semibold">${fmt(amort)}</span></div>
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">Cash-on-Cash <span class="text-[10px]">auf eingesetztes Kapital</span></span><span class="font-semibold">${pct(coc)}</span></div>
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">10Y Swap (Risk-Free)</span><span class="font-semibold">${pct(swap)}</span></div>
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">Spread</span><span class="font-semibold" style="color:${spread >= 0.03 ? 'var(--green)' : 'var(--red)'}">${pct(spread)}</span></div>
        <div class="flex justify-between"><span class="text-[color:var(--muted)]">Break-Even Occupancy</span><span class="font-semibold">${pct(beOcc)}</span></div>`;
    $('invVerdict').innerHTML = `
      <div>${verdict}</div>
      <div class="text-sm space-y-2">
        ${verdictBody}
        <hr style="border-color:var(--line)"/>
        <div class="text-xs text-[color:var(--muted)]">
          ${m.grade === 'A' ? `Premium-Markt mit Supply-Lock. Erwartete Wertsteigerung +3–5% p.a. zusätzlich zum Cashflow.`
            : m.grade === 'B' ? `Solider Markt. Renditeschwankung von Saisonalität abhängig.`
            : `Schwächerer STR-Markt — primär für Eigennutzung oder Diversifikation geeignet.`}
        </div>
      </div>`;
  }

  // ── Tragbarkeit (Buy-Mode) ─────────────────────────────────────────────────
  function renderAffordability({ price, eqPct, loan }) {
    const pkEl = $('invPk'), incEl = $('invIncome');
    if (!pkEl || !incEl) return;
    const pkPct = (+pkEl.value || 0) / 100;
    const income = +incEl.value || 0;
    const pkLab = $('invPkLabel'); if (pkLab) pkLab.textContent = (pkPct * 100).toFixed(0) + '%';
    const incLab = $('invIncomeLabel'); if (incLab) incLab.textContent = fmt(income);
    const f = n => fmt(n);

    const calcInterest = loan * 0.05;
    const maintenance = price * 0.01;
    const amortBase = Math.max(0, loan - price * 0.65);
    const amortization = amortBase / 15;
    const calcCost = calcInterest + maintenance + amortization;
    const quote = income > 0 ? calcCost / income : Infinity;
    const tragOk = quote <= 1 / 3 + 1e-9;
    const tBadge = $('invTragBadge');
    if (tBadge) { tBadge.textContent = tragOk ? '✓ tragbar' : '✗ zu teuer'; tBadge.style.color = tragOk ? 'var(--green)' : 'var(--red)'; }
    const tBody = $('invTragBody');
    if (tBody) tBody.innerHTML = `
      <div class="flex justify-between"><span class="text-[color:var(--muted)]">Kalk. Kosten / Jahr</span><span class="font-semibold">${f(calcCost)}</span></div>
      <div class="flex justify-between"><span class="text-[color:var(--muted)]">Kalk-Zins 5%</span><span>${f(calcInterest)}</span></div>
      <div class="flex justify-between"><span class="text-[color:var(--muted)]">Unterhalt 1% + Amort.</span><span>${f(maintenance + amortization)}</span></div>
      <div class="flex justify-between" style="border-top:1px solid var(--line);padding-top:4px;margin-top:4px"><span class="text-[color:var(--muted)]">Quote vom Einkommen</span><span class="font-bold" style="color:${tragOk ? 'var(--green)' : 'var(--red)'}">${isFinite(quote) ? (quote * 100).toFixed(1) : '∞'}% <span class="text-[10px] font-normal text-[color:var(--muted)]">/ max 33%</span></span></div>`;

    const equityChf = price * eqPct;
    const pkChf = equityChf * pkPct;
    const hardChf = equityChf - pkChf;
    const hardNeeded = price * 0.10;
    const hardOk = hardChf >= hardNeeded - 1;
    const hBadge = $('invHardBadge');
    if (hBadge) { hBadge.textContent = hardOk ? '✓ erfüllt' : '✗ zu wenig'; hBadge.style.color = hardOk ? 'var(--green)' : 'var(--red)'; }
    const hBody = $('invHardBody');
    if (hBody) hBody.innerHTML = `
      <div class="flex justify-between"><span class="text-[color:var(--muted)]">Eigenkapital total</span><span class="font-semibold">${f(equityChf)} (${(eqPct * 100).toFixed(0)}%)</span></div>
      <div class="flex justify-between"><span class="text-[color:var(--muted)]">davon aus PK</span><span>${f(pkChf)}</span></div>
      <div class="flex justify-between"><span class="text-[color:var(--muted)]">hartes EK (Cash/3a)</span><span class="font-semibold" style="color:${hardOk ? 'var(--green)' : 'var(--red)'}">${f(hardChf)}</span></div>
      <div class="flex justify-between" style="border-top:1px solid var(--line);padding-top:4px;margin-top:4px"><span class="text-[color:var(--muted)]">nötig ≥10%</span><span>${f(hardNeeded)}</span></div>`;

    const v = $('invAffordVerdict');
    if (v) {
      if (tragOk && hardOk) { v.textContent = '🟢 Leistbar'; v.style.background = TINT.green; v.style.color = 'var(--green)'; }
      else if (tragOk || hardOk) { v.textContent = '🟡 Knapp — 1 Gate offen'; v.style.background = TINT.gold; v.style.color = 'var(--gold)'; }
      else { v.textContent = '🔴 Nicht leistbar'; v.style.background = TINT.red; v.style.color = 'var(--red)'; }
    }
  }

  // ── Cost-Breakdown (Mini-Businessplan) ─────────────────────────────────────
  function renderBreakdown(p) {
    const el = $('invBreakdown');
    if (!el) return;
    const row = (label, val, hint = '') => `
      <tr>
        <td style="padding:6px 12px 6px 0;color:var(--muted)">${label}${hint ? `<span style="display:block;font-size:10px;color:var(--faint)">${hint}</span>` : ''}</td>
        <td style="padding:6px 0;text-align:right;font-weight:600" class="num">${fmt(val)}</td>
      </tr>`;
    const sectionHead = (label) => `<tr><td colspan="2" style="padding:12px 0 4px;font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--gold);font-weight:700;border-bottom:1px solid var(--line)">${label}</td></tr>`;
    const total = (label, val, color = 'var(--text)') => `
      <tr style="border-top:1px solid var(--line)">
        <td style="padding:8px 0;font-weight:600">${label}</td>
        <td style="padding:8px 0;text-align:right;font-weight:700;font-size:15px;color:${color}" class="num">${fmt(val)}</td>
      </tr>`;

    if (p.mode === 'rent') {
      const annualRent = p.monthlyRent * 12;
      const monthlyFix = p.monthlyRent + (p.utilities / 12) + (p.insurance / 12) + (p.supplies / 12);
      const variablePerStay = p.cleanPer + (p.platformFee / p.stays);
      el.innerHTML = `
        <table style="width:100%;border-collapse:collapse"><tbody>
            ${sectionHead('💰 Einmalig (Setup)')}
            ${row('Möblierung &amp; Geschirr', p.setup * 0.62, 'Bett, Sofa, Küche, Esstisch, Lampen')}
            ${row('Bettwäsche, Handtücher, Deko', p.setup * 0.23, '~2 Sets, kleine Reserve')}
            ${row('Smart-Lock + Internet-Setup', p.setup * 0.08, 'Self-Check-In, Router/SIM')}
            ${row('Versicherung Jahresvorschuss', p.setup * 0.07, 'STR-spezifische Hausrat')}
            ${total('Setup gesamt', p.setup)}
            ${sectionHead('🏠 Monatlich fix')}
            ${row('Mietzins an Eigentümer', p.monthlyRent)}
            ${row('Strom / Wasser / Internet', p.utilities / 12, 'falls nicht im Mietzins')}
            ${row('STR-Versicherung (anteilig)', p.insurance / 12)}
            ${row('Verbrauchsmaterial', p.supplies / 12, 'Gewürze, Putzmittel, Wäsche-Refresh')}
            ${total('Fix-Kosten pro Monat', monthlyFix)}
            ${sectionHead(`🧹 Pro Aufenthalt (~${p.stays} Buchungen/Jahr)`)}
            ${row('Putzkosten', p.cleanPer, 'Putzfrau pro Wechsel')}
            ${row(`Plattform-Gebühr ${(DEAL.platformPct*100).toFixed(0)}%`, p.platformFee / p.stays, 'Airbnb / Booking durchschn.')}
            ${total('Variable pro Aufenthalt', variablePerStay)}
            ${sectionHead('📊 Jahres-Brutto vs. Kosten')}
            ${row('STR-Brutto-Ertrag', p.gross)}
            ${row('−Plattform-Gebühr', -p.platformFee)}
            ${row('−Management', -p.mgmtCost)}
            ${row('−Putzkosten gesamt', -p.cleaning)}
            ${row(`−Kurtaxe (${(DEAL.kurtaxePct*100).toFixed(0)}%)`, -p.kurtaxe)}
            ${row('−Mietzins Jahr', -annualRent)}
            ${row('−Verbrauch + Versicherung + NK', -(p.supplies + p.insurance + p.utilities))}
            ${total('Annual Cashflow', p.gross - p.platformFee - p.mgmtCost - p.cleaning - p.kurtaxe - annualRent - p.supplies - p.insurance - p.utilities, (p.gross - p.platformFee - p.mgmtCost - p.cleaning - p.kurtaxe - annualRent - p.supplies - p.insurance - p.utilities) >= 0 ? 'var(--green)' : 'var(--red)')}
        </tbody></table>`;
    } else {
      const closingCosts = p.closingCosts != null ? p.closingCosts : p.price * 0.05;
      const furnishing = p.furnishing != null ? p.furnishing : 12000;
      const amort = p.amort || 0;
      const hyp1 = Math.min(p.loan, p.price * 0.65);
      const hyp2 = Math.max(0, p.loan - p.price * 0.65);
      const annualFix = p.interest + amort + p.opex;
      const monthlyFix = annualFix / 12;
      const cf = p.gross - p.platformFee - p.mgmtCost - p.cleaning - p.opex - p.kurtaxe - p.interest - amort;
      el.innerHTML = `
        <table style="width:100%;border-collapse:collapse"><tbody>
            ${sectionHead('💰 Einmalig (Kauf + Setup)')}
            ${row('Eigenkapital', p.equity, `${((p.equity / p.price) * 100).toFixed(0)}% Anteil`)}
            ${row('Kaufnebenkosten ~5%', closingCosts, 'Notar, Grundbuch, Steuer, Bank-Setup (kantonsabhängig)')}
            ${row('Möblierung (geschätzt)', furnishing, 'STR-tauglich, mittlere Klasse')}
            ${total('Kapitaleinsatz gesamt', p.equity + closingCosts + furnishing)}
            ${sectionHead('🏦 Finanzierung')}
            ${row('1. Hypothek (≤65%)', hyp1, 'keine Amortisationspflicht')}
            ${row('2. Hypothek (65–80%)', hyp2, 'in 15 J. zu amortisieren')}
            ${row('Hypothekarzins p.a.', p.interest, `${(p.rate * 100).toFixed(2)}% auf CHF ${(p.loan / 1000).toFixed(0)}k`)}
            ${row('Pflicht-Amortisation p.a.', amort, '2. Hypothek ÷ 15 J. · baut EK auf')}
            ${sectionHead('🏠 Monatlich fix')}
            ${row('Zins + Amortisation', (p.interest + amort) / 12)}
            ${row('Unterhalt + Versicherung + NK', p.opex / 12, '1.2% des Kaufpreises p.a.')}
            ${total('Fix-Kosten pro Monat', monthlyFix)}
            ${sectionHead('📊 Jahres-Brutto vs. Kosten')}
            ${row('STR-Brutto-Ertrag', p.gross)}
            ${row(`−Plattform-Gebühr ${(DEAL.platformPct*100).toFixed(0)}%`, -p.platformFee)}
            ${row('−Management', -p.mgmtCost)}
            ${row(`−Cleaning (${(DEAL.cleaningPctBuy*100).toFixed(0)}%)`, -p.cleaning)}
            ${row('−Opex (Unterhalt + Vers.)', -p.opex)}
            ${row(`−Kurtaxe (${(DEAL.kurtaxePct*100).toFixed(0)}%)`, -p.kurtaxe)}
            ${row('−Hypothekarzins', -p.interest)}
            ${row('−Pflicht-Amortisation', -amort)}
            ${total('Freier Cashflow / Jahr', cf, cf >= 0 ? 'var(--green)' : 'var(--red)')}
        </tbody></table>`;
    }
  }

  // ── P&L-Wasserfall (Chart.js) ───────────────────────────────────────────────
  function drawWaterfall({ gross, platformFee, mgmtCost, cleaning, opex, kurtaxe, noi, interest, amort = 0, cashflow, mode }) {
    if (typeof Chart === 'undefined') return;
    const fixedLabel = mode === 'rent' ? '−Mietzins' : '−Zinsen';
    const steps = [
      { label: 'Brutto', v: gross, kind: 'pos' },
      { label: '−Plattform', v: -platformFee, kind: 'neg' },
      { label: '−Mgmt', v: -mgmtCost, kind: 'neg' },
      { label: '−Cleaning', v: -cleaning, kind: 'neg' },
      { label: '−Opex', v: -opex, kind: 'neg' },
      { label: '−Kurtaxe', v: -kurtaxe, kind: 'neg' },
      { label: 'NOI', v: noi, kind: 'noi' },
      { label: fixedLabel, v: -interest, kind: 'neg' },
      ...(amort > 0 ? [{ label: '−Amort.', v: -amort, kind: 'neg' }] : []),
      { label: 'Cashflow', v: cashflow, kind: cashflow >= 0 ? 'cf-pos' : 'cf-neg' },
    ];
    let running = 0;
    const bars = [];
    for (const s of steps) {
      if (s.kind === 'pos') { bars.push([0, s.v]); running = s.v; }
      else if (s.kind === 'neg') { const start = running; running += s.v; bars.push([running, start]); }
      else { bars.push([0, s.v]); running = s.v; }
    }
    const colors = steps.map(s => s.kind === 'pos' ? '#D9B36A' : s.kind === 'noi' ? '#6FA8C9' : s.kind === 'cf-pos' ? '#3FAE7C' : '#E5392B');

    if (waterfallChart) { waterfallChart.destroy(); waterfallChart = null; }
    const canvas = $('invWaterfall');
    if (!canvas) return;
    waterfallChart = new Chart(canvas, {
      type: 'bar',
      data: { labels: steps.map(s => s.label), datasets: [{ data: bars, backgroundColor: colors, borderColor: colors, borderWidth: 0, borderRadius: 3, borderSkipped: false, barPercentage: 0.82, categoryPercentage: 0.92 }] },
      options: {
        responsive: true, maintainAspectRatio: false, animation: { duration: 350 },
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => { const s = steps[c.dataIndex]; return s.label + ': ' + fmt(Math.abs(s.v)); } } } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#1F2839' }, ticks: { color: '#8B93A3', callback: v => 'CHF ' + (v / 1000).toFixed(0) + 'k', font: { size: 10 } } },
          x: { grid: { display: false }, ticks: { color: '#8B93A3', font: { size: 10 }, autoSkip: false, maxRotation: 0 } }
        }
      }
    });
  }

  // ── Inserat-Check + R2R-Anschreiben (Arbitrage-Modus) ───────────────────────
  function renderListingPanel({ m, monthlyRent, beds, cap, cashflow, breakEvenMonths }) {
    _r2rCtx = { m, monthlyRent, beds };
    const photoUrl = ($('invPhotoUrl').value || '').trim();
    const listingUrl = ($('invListingUrl').value || '').trim();
    const photoEl = $('invListingPhoto');
    if (photoEl) {
      if (/^https?:\/\//i.test(photoUrl)) {
        photoEl.innerHTML = `<img src="${photoUrl.replace(/"/g, '&quot;')}" alt="Inserat-Foto" style="width:100%;height:100%;object-fit:cover;max-height:180px" onerror="this.parentElement.textContent='⚠ Foto-URL lädt nicht'">`;
      } else { photoEl.innerHTML = 'Kein Foto<br>eingefügt'; }
    }
    let label, bg, col;
    if (cap >= 2.5 && breakEvenMonths < 12) { label = '🟢 Lohnt sich'; bg = TINT.green; col = 'var(--green)'; }
    else if (cap >= 2.0 && breakEvenMonths < 18) { label = '🟡 Solide'; bg = TINT.gold; col = 'var(--gold)'; }
    else if (cap >= 1.5 && cashflow > 0) { label = '⚪ Knapp'; bg = TINT.grey; col = 'var(--muted)'; }
    else { label = '🔴 Finger weg'; bg = TINT.red; col = 'var(--red)'; }
    const ampelEl = $('invListingAmpel');
    if (ampelEl) { ampelEl.textContent = label; ampelEl.style.background = bg; ampelEl.style.color = col; }
    const factsEl = $('invListingFacts');
    if (factsEl) factsEl.innerHTML = `
      <div class="flex justify-between"><span class="text-[color:var(--muted)]">Markt</span><span class="font-semibold">${m.name} (${m.canton})</span></div>
      <div class="flex justify-between"><span class="text-[color:var(--muted)]">Miete an Eigentümer</span><span class="font-semibold">${fmt(monthlyRent)}/Mt</span></div>
      <div class="flex justify-between"><span class="text-[color:var(--muted)]">STR-Multiple</span><span class="font-semibold">${cap.toFixed(2)}× <span class="text-[10px] text-[color:var(--muted)]">STR-Monat/Miete</span></span></div>
      <div class="flex justify-between"><span class="text-[color:var(--muted)]">Netto-Cashflow</span><span class="font-semibold" style="color:${cashflow >= 0 ? 'var(--green)' : 'var(--red)'}">${fmt(cashflow / 12)}/Mt</span></div>`;
    const openEl = $('invListingOpen');
    if (openEl) {
      if (/^https?:\/\//i.test(listingUrl)) { openEl.href = listingUrl; openEl.classList.remove('hidden'); }
      else { openEl.classList.add('hidden'); }
    }
  }

  function genR2RLetter() {
    if (!_r2rCtx) return;
    const { m, monthlyRent, beds } = _r2rCtx;
    const url = ($('invListingUrl').value || '').trim();
    const txt =
`Betreff: Mietinteresse — ${beds}-Zimmer-Wohnung in ${m.name}${url ? ' (' + url + ')' : ''}

Sehr geehrte Damen und Herren

Ihr Inserat für die ${beds}-Zimmer-Wohnung in ${m.name} spricht mich sehr an. Ich interessiere mich für eine langfristige Miete (mind. 2–3 Jahre) zu ${fmt(monthlyRent)}/Monat.

Kurz und transparent zu meinem Vorhaben: Ich vermiete die Wohnung möbliert und professionell als Zwischen-/Kurzzeit-Unterkunft für Geschäftsreisende und Feriengäste weiter. Das funktioniert ausschliesslich mit Ihrer ausdrücklichen, schriftlichen Zustimmung zur Untervermietung (Art. 262 OR) — die ich von Anfang an einhole.

Was Sie davon haben:
• Pünktliche, garantierte Mietzahlung jeden Monat — auch bei Leerstand auf meiner Seite.
• Ein einziger, fester Ansprechpartner statt wechselnder Mieter.
• Professioneller Unterhalt: regelmässige Reinigung, sofortige Behebung kleiner Schäden, eigene STR-Haftpflicht- und Inventarversicherung.
• Die Wohnung wird gepflegt wie ein Aushängeschild — kein "Abwohnen".

Ich bringe Erfahrung im Gastgeber-Betrieb mit und liefere gerne Referenzen, einen Identitätsnachweis und einen aktuellen Betreibungsregisterauszug.

Hätten Sie Zeit für ein kurzes Telefonat oder eine Besichtigung? Sie erreichen mich unter [Telefon] / [E-Mail].

Freundliche Grüsse
[Dein Name]`;
    const ta = $('invLetterText');
    if (ta) ta.value = txt;
    const wrap = $('invLetterWrap');
    if (wrap) wrap.classList.remove('hidden');
  }

  function copyR2RLetter() {
    const ta = $('invLetterText');
    if (!ta) return;
    const done = () => { const s = $('invLetterCopied'); if (s) { s.textContent = 'Kopiert ✓'; setTimeout(() => { s.textContent = ''; }, 2000); } };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(ta.value).then(done, () => { ta.select(); document.execCommand('copy'); done(); });
    else { ta.select(); document.execCommand('copy'); done(); }
  }

  window.SwissInvestor = { init };
})();
