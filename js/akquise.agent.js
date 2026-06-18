/* ============================================================================
   SwissSTR — akquise.agent.js  ·  Agent-Loop + Arbeitsplatz-Orchestrierung
   ----------------------------------------------------------------------------
   1:1 aus akquise.html ausgelagert (STATUS §7, Schritt 6 — Split nach Concern).
   Diese Hälfte = der LOOP: lokaler Heimstatt-Agent (127.0.0.1:8782) — Quellen
   scannen, Gmail-Inbox, Entwürfe, Anbieter-Dedup — PLUS die Lead-Board-/Deal-
   Arbeitsplatz-Orchestrierung (AKQWORK, Lead-Urteil, Lead-Auswahl) und der
   Boot-Block am Ende, der alles verdrahtet.

   Klassisches Skript (kein ES-Modul, non-strict) → identischer globaler Scope.
   Lädt NACH js/akquise.deal.js und ruft dessen Engine (dossOffer/renderDossier/
   initDossier/…) auf. Der Boot am Ende läuft, wenn BEIDE Dateien geladen sind.
   Verbatim, KEIN Verhalten geändert.
   ========================================================================== */
  // ====================== HEIMSTATT-AGENT (lokal, 127.0.0.1:8782) ======================
  const AKQ_AGENT = 'http://127.0.0.1:8782';
  let _akqState = { source: '', listing: null, wired: false, draftMeta: {} };

  async function akqApi(path, body) {
    const opt = body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {};
    const r = await fetch(AKQ_AGENT + path, opt);
    return r.json();
  }

  async function initAkquise() {
    const bar = document.getElementById('akqAgentBar');
    bar.innerHTML = '<span class="text-[color:var(--muted)]">Verbinde mit lokalem Akquise-Agenten …</span>';
    let up = false;
    try { const p = await akqApi('/api/ping'); up = p && p.ok; } catch (e) { up = false; }
    if (!up) {
      document.getElementById('akqMain').style.display = 'none';
      bar.innerHTML = `<div class="flex items-start gap-3"><span class="text-xl">🔌</span><div>
        <strong>Akquise-Agent nicht erreichbar.</strong> Das Tool läuft lokal auf deinem Laptop — starte es einmalig:
        <div class="mt-1 font-mono text-xs bg-[#F0EEE5] rounded px-2 py-1 inline-block">C:\\Users\\adria\\Claude\\heimstatt\\agent\\cockpit.cmd</div>
        <div class="text-xs text-[color:var(--muted)] mt-1">Doppelklick genügt — danach hier „erneut verbinden". Such-Strategien, Schlupflöcher, Checkliste & Brief-Generator funktionieren auch ohne Agent.</div>
        <button onclick="initAkquise()" class="mt-2 px-3 py-1.5 rounded border border-[color:var(--line)] text-xs">erneut verbinden</button></div></div>`;
      return;
    }
    bar.innerHTML = '<span class="text-[color:var(--green)]">● Agent verbunden</span> <span class="text-xs text-[color:var(--muted)]">— lokal (127.0.0.1) · nichts verlässt deinen Laptop · kein Auto-Versand</span>';
    document.getElementById('akqMain').style.display = '';
    await akqLoadSources();
    akqRenderOverview();
    akqRenderOutbox();
    akqRenderLandlords();
    if (!_akqState.wired) {
      document.getElementById('akqScan').onclick = akqScan;
      document.getElementById('akqMails').onclick = akqFindMails;
      document.getElementById('akqInbox').onclick = akqPollInbox;
      document.getElementById('akqOutboxRefresh').onclick = akqRenderOutbox;
      document.getElementById('akqOvSave').onclick = akqSaveDraft;
      document.getElementById('akqUrlBtn').onclick = akqCheckUrl;
      document.getElementById('akqUrl').oninput = akqUrlAutofill;
      document.getElementById('akqLlRefresh').onclick = akqRenderLandlords;
      document.getElementById('akqVwBtn').onclick = akqSearchVerwaltungen;
      // Doppel-Anschreiben-Warnung: bei jeder Anbieter-Eingabe gegen CRM matchen (debounced).
      let _llTmr;
      const onLlInput = () => { clearTimeout(_llTmr); _llTmr = setTimeout(() => { akqRefreshLlMatch(false); try { renderDossier(); } catch (e) {} }, 220); };
      const cEl = document.getElementById('dossLlCompany'), kEl = document.getElementById('dossLlContact');
      if (cEl) cEl.oninput = onLlInput;
      if (kEl) kEl.oninput = onLlInput;
      akqLoadLandlordCache(true).then(() => akqRefreshLlMatch(false));
      _akqState.wired = true;
    }
  }

  async function akqLoadSources() {
    const sel = document.getElementById('akqSrc');
    const r = await akqApi('/api/sources');
    sel.innerHTML = (r.sources || []).map(s => `<option>${s}</option>`).join('') || '<option value="">(keine Quelle)</option>';
    if ((r.sources || []).includes('sample_listings.json')) sel.value = 'sample_listings.json';
  }

  const akqFmt = n => n == null ? '—' : 'CHF ' + SwissFmt.num(n);
  const akqScoreColor = s => s >= 85 ? 'var(--green)' : s >= 70 ? '#C9A24A' : 'var(--red)';

  function akqCard(l) {
    const spreadCol = (l.spread || 0) >= 0 ? 'var(--green)' : 'var(--red)';
    const spread = l.spread != null ? ((l.spread >= 0 ? '+' : '') + akqFmt(l.spread)) : '—';
    const reasons = (l.reasons || []).slice(0, 2).map(r => `<div class="text-[11px] text-[color:var(--muted)]">› ${r}</div>`).join('');
    const town = (l.city || '').replace(/'/g, '');
    return `<div class="card p-4"><div class="flex items-start gap-4">
      <div class="text-center shrink-0 w-12"><div class="font-display text-2xl" style="color:${akqScoreColor(l.score)}">${l.score}</div><div class="text-[9px] text-[color:var(--muted)] uppercase">Score</div></div>
      <div class="flex-1 min-w-0">
        <div class="font-semibold truncate">${l.title || 'Inserat'}</div>
        <div class="text-sm text-[color:var(--muted)]">${l.city || ''}${l.canton ? ' ' + l.canton : ''} · ${l.rooms || '?'} Zi · ${akqFmt(l.rent)}/Mt${l.landlord ? ' · ' + l.landlord : ''}</div>
        <div class="flex flex-wrap gap-x-5 gap-y-1 mt-2 text-sm"><span>STR-Brutto <b>${akqFmt(l.str_brutto)}</b></span><span>Payout <b>${akqFmt(l.payout)}</b></span><span>Spread <b style="color:${spreadCol}">${spread}</b></span></div>
        ${reasons}
        <div class="flex flex-wrap items-center gap-2 mt-3">
          <button onclick='akqCompose(${JSON.stringify(l.id)})' class="px-3 py-1.5 rounded bg-[color:var(--red)] text-white text-xs font-semibold">Anschreiben</button>
          <select id="akqvar-${l.id}" class="border border-[color:var(--line)] rounded px-2 py-1 text-xs"><option value="">Auto-Variante</option><option value="first_listing">Erst-Inserat</option><option value="reengagement_neues_objekt">Re-Engagement</option></select>
          <label class="text-xs text-[color:var(--muted)]"><input type="checkbox" id="akqreal-${l.id}"> echter Claude</label>
          <button onclick='openMarket(${JSON.stringify(town)})' class="text-xs underline text-[color:var(--ink)]">→ Marktanalyse ${town}</button>
          ${/mock/i.test(l.id || '') || /mock/i.test(l.url || '')
            ? '<span class="text-xs text-[color:var(--red)]" title="Beispiel-Datensatz — diese Wohnung existiert nicht">⚠ Beispiel (nicht echt)</span>'
            : (l.url ? `<a href="${l.url}" target="_blank" class="text-xs underline text-[color:var(--muted)]">Inserat ↗</a>` : '')}
        </div>
      </div></div></div>`;
  }

  async function akqScan() {
    _akqState.source = document.getElementById('akqSrc').value;
    const stat = document.getElementById('akqStat'); stat.textContent = 'scanne …';
    const r = await akqApi('/api/scan', { source: _akqState.source, threshold: +document.getElementById('akqThr').value });
    if (r.error) { stat.textContent = '⚠ ' + r.error; return; }
    stat.textContent = `${r.total_seen} gesehen · ${r.rejected} gefiltert · ${r.ready} passend`;
    const list = r.listings || [];
    const isSample = /sample|mock/i.test(_akqState.source) || list.some(l => /mock/i.test(l.id || '') || /mock/i.test(l.url || ''));
    const banner = isSample
      ? `<div class="card p-3 mb-3" style="border-color:var(--red);background:rgba(229,57,43,.1)">
           <strong class="text-[color:var(--red)]">⚠ Beispiel-Inserate (Test) — diese Wohnungen existieren nicht.</strong>
           <div class="text-xs text-[color:var(--muted)] mt-0.5">Die Links führen ins Leere (z.B. „MOCK-006"). Score, Spread & Anschreiben zeigen aber echt, wie es mit realen Inseraten aussieht. Für <strong>echte</strong> Inserate: oben „⟳ Inserate aus Mails" (braucht deinen IMAP-Zugang in der Heimstatt-<code>.env</code>).</div>
         </div>`
      : '';
    document.getElementById('akqList').innerHTML = banner + (list.map(akqCard).join('') || '<div class="text-[color:var(--muted)] text-sm">Keine passenden Inserate über der Schwelle.</div>');
  }

  async function akqFindMails() {
    const stat = document.getElementById('akqStat'); stat.textContent = 'hole Inserate aus Mails …';
    const r = await akqApi('/api/find-mails', { since_days: 7, max: 50 });
    if (r.error) { stat.textContent = '⚠ ' + r.error; return; }
    stat.textContent = `${r.count} Inserate aus Mails → Quelle „${r.source}"`;
    await akqLoadSources();
    const sel = document.getElementById('akqSrc');
    if ([...sel.options].some(o => o.value === r.source || o.text === r.source)) sel.value = r.source;
  }

  // Eingehende Vermieter-Antworten ziehen + einordnen → schliesst den Loop.
  async function akqPollInbox() {
    const stat = document.getElementById('akqStat'), res = document.getElementById('akqInboxResult');
    stat.textContent = 'prüfe Antworten …'; res.innerHTML = '';
    const r = await akqApi('/api/inbox/poll', { max: 20, dry_run: true });
    if (r.error) { stat.textContent = '⚠ ' + r.error; return; }
    stat.textContent = `${r.fetched} ungelesen · ${r.matched} zugeordnet · ${r.classified} eingeordnet`;
    const mode = r.dry_run
      ? `<span class="px-1.5 py-0.5 rounded bg-[#F6EFD9] text-[#9a7b1f] font-semibold">Probelauf</span> ${r.anthropic_ready ? 'Probelauf (nichts geschrieben). Für echtes Einordnen + Status-Update den echten Lauf nutzen.' : 'kein API-Key → Mock-Classifier, nichts in CRM geschrieben (0 Kosten).'}`
      : `<span class="px-1.5 py-0.5 rounded bg-[#E6F3EC] text-[color:var(--green)] font-semibold">Echt-Lauf</span> Antworten eingeordnet + Status aktualisiert.`;
    let html = `<div class="mb-1">${mode}</div>`;
    if ((r.unmatched || []).length) {
      html += `<div class="text-[color:var(--muted)]">${r.unmatched.length} Mail(s) ohne Anbieter-Treffer (Absender nicht im Verzeichnis):</div>`
        + r.unmatched.map(u => `<div class="text-[color:var(--muted)]">· ${u.sender_email || '?'} — ${(u.subject || '').slice(0, 50)}</div>`).join('');
    }
    if ((r.errors || []).length) html += r.errors.map(e => `<div class="text-[color:var(--red)]">⚠ ${e}</div>`).join('');
    res.innerHTML = html;
    if (!r.dry_run) { akqRenderLandlords(); akqRenderOverview(); }
  }

  async function akqCompose(id) {
    const variant = document.getElementById('akqvar-' + id).value;
    const real = document.getElementById('akqreal-' + id).checked;
    const ov = document.getElementById('akqOv'); ov.style.display = 'flex';
    document.getElementById('akqOvMeta').textContent = '… generiere' + (real ? ' (echter Claude)' : ' (Mock, 0 Kosten)') + ' …';
    document.getElementById('akqOvSubj').value = ''; document.getElementById('akqOvBody').value = ''; document.getElementById('akqOvHint').textContent = '';
    _akqState.lastDraft = null; const _ab = document.getElementById('akqOvApprove'); if (_ab) _ab.style.display = 'none';
    // Anbieter aus der OBJEKT-Zone in den Brief-Dialog übernehmen (gleiche Quelle → kein Doppel-Tippen, CRM-Dedup greift).
    try {
      const c = (document.getElementById('dossLlCompany') || {}).value || '', k = (document.getElementById('dossLlContact') || {}).value || '';
      const of = document.getElementById('akqOvFirma'), ok = document.getElementById('akqOvKontakt');
      if (of && c && !of.value.trim()) of.value = c;
      if (ok && k && !ok.value.trim()) ok.value = k;
    } catch (e) {}
    const r = await akqApi('/api/compose', { source: _akqState.source, listing_id: id, variant, real });
    if (r.error) { document.getElementById('akqOvMeta').textContent = '⚠ ' + r.error; return; }
    _akqState.draftMeta = { variant: r.variant, model: r.model, cost: r.cost, listing_id: id };
    document.getElementById('akqOvMeta').textContent = `Variante ${r.variant} · ${r.model} · ~CHF ${r.cost}` + (r.review_required ? ' · ⚠ Review' : '');
    document.getElementById('akqOvSubj').value = r.subject;
    document.getElementById('akqOvBody').value = r.body;
    document.getElementById('akqOvHint').textContent = r.real ? 'Echter Claude-Text.' : 'Mock-Text — für echten Brief „echter Claude" anhaken.';
  }

  async function akqSaveDraft() {
    const m = _akqState.draftMeta || {};
    const hint = document.getElementById('akqOvHint');
    let landlordId = null;
    const firma = document.getElementById('akqOvFirma').value.trim();
    const kontakt = document.getElementById('akqOvKontakt').value.trim();
    if (firma || kontakt) {
      const ll = await akqApi('/api/landlord/add', {
        company: firma, contact: kontakt,
        role: document.getElementById('akqOvRolle').value.trim(),
        email: document.getElementById('akqOvMail').value.trim(),
      });
      if (ll.landlord_id) { landlordId = ll.landlord_id; if (ll.matched) hint.textContent = '↳ bekannter Anbieter verknüpft. '; }
      else if (ll.error) { hint.textContent = '⚠ Anbieter: ' + ll.error; return; }
    }
    const r = await akqApi('/api/outbox/save', {
      listing_id: m.listing_id, variant: m.variant, model: m.model, cost: m.cost, landlord_id: landlordId,
      subject: document.getElementById('akqOvSubj').value, body: document.getElementById('akqOvBody').value,
    });
    if (r.error) { hint.textContent = '⚠ ' + r.error; return; }
    _akqState.lastDraft = { id: r.draft_id, landlord_id: landlordId };
    hint.textContent += '✓ Entwurf gespeichert (' + r.draft_id + ')' + (landlordId ? ' + Anbieter im Verzeichnis' : '') + ' — kein Versand';
    const ab = document.getElementById('akqOvApprove');
    if (ab) { ab.style.display = ''; ab.disabled = !landlordId; ab.title = landlordId ? 'Hält im CRM fest, dass dieser Pitch raus ist (du sendest selbst via Gmail).' : 'Erst Firma/Kontakt + Speichern → dann als gesendet festhalten.'; }
    akqRenderOutbox();
    akqRenderLandlords();
    try { await akqLoadLandlordCache(true); akqRefreshLlMatch(false); } catch (e) {}
  }

  // Approve aus dem Overlay (nach „In Gmail öffnen"): nutzt den zuletzt gespeicherten Entwurf.
  async function akqOvApprove() {
    const ld = _akqState.lastDraft;
    const hint = document.getElementById('akqOvHint');
    if (!ld || !ld.id) { hint.textContent = '⚠ Erst „In Outbox" speichern, dann als gesendet festhalten.'; return; }
    if (!ld.landlord_id) { hint.textContent = '⚠ Für den CRM-Eintrag braucht es Firma/Kontaktperson oben — dann erneut speichern.'; return; }
    await akqApprove(ld.id, hint);
  }

  // Gmail-Compose aus dem Agent-Overlay (nutzt eingeloggtes Google-Konto). Kein Auto-Versand.
  function akqGmail() {
    const subj = document.getElementById('akqOvSubj').value;
    const body = document.getElementById('akqOvBody').value;
    const to = document.getElementById('akqOvMail').value.trim();
    const url = `https://mail.google.com/mail/?view=cm&fs=1${to ? '&to=' + encodeURIComponent(to) : ''}&su=${encodeURIComponent(subj)}&body=${encodeURIComponent(body)}`;
    window.open(url, '_blank', 'noopener');
    document.getElementById('akqOvHint').textContent = 'Gmail-Fenster geöffnet — senden bestätigst du dort.';
  }

  // ===== ANBIETER-DEDUP — Adrians Kern: "zwei Mal die selbe Person anschreiben wäre peinlich". =====
  // newhome blockt Auto-Scraping → Adrian tippt Firma/Kontakt ab; wir matchen tolerant gegen das CRM.
  let _akqLandlordCache = null; // letzte /api/landlords-Antwort, für sofortiges Matchen beim Tippen

  // Normalisieren: lowercase, trim, Rechtsform-/Branchen-Suffixe weg, Mehrfach-Spaces zu einem.
  function akqNormLl(s) {
    if (!s) return '';
    let t = String(s).toLowerCase().trim();
    t = t.replace(/[.,&]/g, ' ');
    // Rechtsform- und Branchen-Floskeln entfernen (als ganze Wörter)
    t = t.replace(/\b(ag|gmbh|sa|sàrl|sarl|kg|llc|immobilien|immo|immobilier|verwaltung|verwaltungs|treuhand|bewirtschaftung|liegenschaften|partner|partners|co)\b/g, ' ');
    t = t.replace(/\s+/g, ' ').trim();
    return t;
  }

  // Abgeleiteter Anbieter-Typ: Firma gefüllt → Immobilienfirma, sonst Privatperson.
  function akqDeriveLlType() {
    const company = (document.getElementById('dossLlCompany') || {}).value || '';
    const isFirma = !!company.trim();
    const badge = document.getElementById('dossLlTypeBadge');
    if (badge) { badge.textContent = isFirma ? 'Immobilienfirma' : 'Privatperson'; badge.className = 'proof-badge ' + (isFirma ? 'proof-green' : 'proof-amber'); }
    // dossType (hidden) für bestehende Score-/Brief-Logik mitführen (privat | firma).
    const dt = document.getElementById('dossType'); if (dt) dt.value = isFirma ? 'firma' : 'privat';
    return isFirma ? 'firma' : 'privat';
  }

  // Tolerantes Matchen: company ODER contact, normalisiert, Token-Überschneidung.
  // Marbet ≠ Konkordia → kein Treffer; "Marbet Immobilien AG" = "marbet immobilien" → Treffer.
  function akqLlMatchScore(qNorm, candNorm) {
    if (!qNorm || !candNorm) return 0;
    if (qNorm === candNorm) return 1;
    const a = new Set(qNorm.split(' ').filter(w => w.length >= 3));
    const b = new Set(candNorm.split(' ').filter(w => w.length >= 3));
    if (!a.size || !b.size) return 0;
    let inter = 0; a.forEach(w => { if (b.has(w)) inter++; });
    if (!inter) return 0;
    // Anteil der kleineren Menge, die getroffen wird (z.B. "marbet" trifft 1/1 → 1.0).
    return inter / Math.min(a.size, b.size);
  }

  function akqFindLlMatch(company, contact, landlords) {
    const cN = akqNormLl(company), kN = akqNormLl(contact);
    if (!cN && !kN) return null;
    let best = null, bestScore = 0;
    for (const x of (landlords || [])) {
      const xc = akqNormLl(x.company), xk = akqNormLl(x.contact);
      let sc = 0;
      if (cN) sc = Math.max(sc, akqLlMatchScore(cN, xc), akqLlMatchScore(cN, xk));
      if (kN) sc = Math.max(sc, akqLlMatchScore(kN, xk), akqLlMatchScore(kN, xc));
      if (sc >= 0.6 && sc > bestScore) { bestScore = sc; best = x; }
    }
    return best;
  }

  // Landlords aus CRM holen (cachen) + Doppel-Warnung neu rendern.
  async function akqLoadLandlordCache(force) {
    try {
      if (force || !_akqLandlordCache) {
        const r = await akqApi('/api/landlords');
        _akqLandlordCache = r.landlords || [];
      }
    } catch (e) { _akqLandlordCache = _akqLandlordCache || []; }
    return _akqLandlordCache;
  }

  // Zentral: Firma/Kontakt → Typ ableiten + gegen CRM matchen → rote/grüne Box + Ablage-Status.
  async function akqRefreshLlMatch(force) {
    try {
      akqDeriveLlType();
      const company = (document.getElementById('dossLlCompany') || {}).value || '';
      const contact = (document.getElementById('dossLlContact') || {}).value || '';
      const box = document.getElementById('akqDupWarn');
      const ablage = document.getElementById('akqAblageLl');
      const empty = !company.trim() && !contact.trim();
      const landlords = await akqLoadLandlordCache(force);
      const hit = empty ? null : akqFindLlMatch(company, contact, landlords);
      // Doppel-Warn-Box (ganz oben)
      if (box) {
        if (empty) { box.style.display = 'none'; box.innerHTML = ''; }
        else if (hit) {
          const when = hit.last_draft_at ? String(hit.last_draft_at).slice(0, 10) : (hit.last_at ? String(hit.last_at).slice(0, 10) : '—');
          const subj = hit.last_subject ? `„${hit.last_subject}"` : 'noch kein Entwurf';
          const stat = AKQ_STATUS[hit.status] || hit.status || '—';
          box.style.display = '';
          box.innerHTML = `<div class="p-3.5 rounded-lg" style="background:rgba(229,57,43,.14);border:1.5px solid var(--red)">
            <div class="font-semibold text-[color:var(--red)] text-sm">⚠ Diesen Anbieter hast du schon kontaktiert — nicht doppelt anschreiben!</div>
            <div class="text-sm mt-1"><b>${(hit.company || hit.contact || '—')}</b>${hit.company && hit.contact ? ' (' + hit.contact + ')' : ''} · ${subj} am ${when} · Status <b>${stat}</b> · ${hit.drafts || 0} Entwurf/Entwürfe</div>
            <div class="text-[11px] text-[color:var(--muted)] mt-1">Treffer im Anbieter-Verzeichnis (normalisiert). Falsch erkannt? Tippe genauer.</div></div>`;
        } else {
          box.style.display = '';
          box.innerHTML = `<div class="p-2.5 rounded-lg" style="background:rgba(63,174,124,.10);border:1px solid rgba(63,174,124,.4)">
            <div class="text-sm text-[color:var(--green)] font-semibold">✓ Neuer Anbieter — noch nicht kontaktiert.</div>
            <div class="text-[11px] text-[color:var(--muted)] mt-0.5">Kein Treffer im Verzeichnis. Beim Speichern wird er erfasst, damit künftige Leads dagegen deduplizieren.</div></div>`;
        }
      }
      // Ablage-Karte: Status des AKTUELLEN Anbieters (nicht globale Kontaktliste).
      if (ablage) {
        if (empty) ablage.innerHTML = '<span class="text-[color:var(--muted)]">Kein Anbieter erfasst — tippe Firma/Kontaktperson oben.</span>';
        else if (hit) {
          const stat = AKQ_STATUS[hit.status] || hit.status || '—';
          ablage.innerHTML = `<span style="color:var(--red)">●</span> <b>${hit.company || hit.contact}</b> — bereits im CRM · Status <b>${stat}</b> · ${hit.drafts || 0} Entwurf/Entwürfe`;
        } else {
          ablage.innerHTML = `<span style="color:var(--green)">●</span> <b>${company || contact}</b> — neu, noch nicht im CRM`;
        }
      }
      return hit;
    } catch (e) { return null; }
  }

  // "Anbieter ins CRM" (auch ohne Anschreiben) — schreibt Firma+Kontakt, dedupliziert serverseitig.
  async function akqSaveLandlordOnly() {
    const hint = document.getElementById('dossLlSaveHint');
    const company = document.getElementById('dossLlCompany').value.trim();
    const contact = document.getElementById('dossLlContact').value.trim();
    if (!company && !contact) { if (hint) hint.textContent = '⚠ Erst Firma oder Kontaktperson eintippen.'; return; }
    if (hint) hint.textContent = 'speichere …';
    try {
      const ll = await akqApi('/api/landlord/add', { company, contact, type: akqDeriveLlType() === 'firma' ? 'klein_verwaltung' : 'privat', canton: (_akqState.lead || {}).canton || null });
      if (ll.error) { if (hint) hint.textContent = '⚠ ' + ll.error; return; }
      if (hint) hint.textContent = ll.matched ? '↳ war schon im Verzeichnis (verknüpft).' : '✓ Anbieter ins CRM aufgenommen.';
      await akqLoadLandlordCache(true);
      akqRefreshLlMatch(false);
      akqRenderLandlords();
    } catch (e) { if (hint) hint.textContent = '⚠ Agent nicht erreichbar.'; }
  }

  const AKQ_STATUS = { cold: 'neu', contacted: 'angeschrieben', warm: 'warm', negotiating: 'in Verhandlung', won: 'gewonnen', lost: 'verloren', blacklist: 'gesperrt' };
  async function akqRenderLandlords() {
    const el = document.getElementById('akqLandlords');
    try {
      const r = await akqApi('/api/landlords');
      const d = r.landlords || [];
      _akqLandlordCache = d; // Dedup-Cache aktuell halten
      try { akqRefreshLlMatch(false); } catch (e) {}
      if (!d.length) { el.innerHTML = '<div class="text-[color:var(--muted)] text-sm">Noch keine Anbieter erfasst. Sobald du einen Entwurf mit Anbieter-Angaben speicherst, erscheint er hier.</div>'; return; }
      el.innerHTML = `<table class="w-full text-sm"><thead><tr class="text-[10px] uppercase tracking-wider text-[color:var(--muted)] border-b border-[color:var(--line)]">
        <th class="text-left py-1 px-2">Firma</th><th class="text-left py-1 px-2">Kontaktperson</th><th class="text-left py-1 px-2">Status</th><th class="text-right py-1 px-2">Entwürfe</th><th class="text-left py-1 px-2">Zuletzt</th></tr></thead><tbody>${
        d.map(x => `<tr class="border-b border-[color:var(--line)]">
          <td class="py-1.5 px-2 font-medium">${x.company || '—'}</td>
          <td class="py-1.5 px-2">${x.contact || '—'}${x.notes ? ` <span class="text-[10px] text-[color:var(--muted)]">(${x.notes})</span>` : ''}</td>
          <td class="py-1.5 px-2">${akqStatusCell(x)}</td>
          <td class="py-1.5 px-2 text-right">${x.drafts || 0}</td>
          <td class="py-1.5 px-2 text-[11px] text-[color:var(--muted)]">${x.last_subject ? (x.last_subject + (x.last_draft_at ? ' · ' + String(x.last_draft_at).slice(0,10) : '')) : '—'}</td>
        </tr>`).join('')}</tbody></table>`;
    } catch (e) { el.innerHTML = '<div class="text-[color:var(--muted)]">Verzeichnis nicht ladbar.</div>'; }
  }

  // Status-Zelle: gesperrte/cold/contacted nur als Label, ab da manueller Stufen-Vorschub.
  function akqStatusCell(x) {
    const opts = ['warm', 'negotiating', 'won', 'lost'];
    if (x.status === 'blacklist') return '<span class="text-xs">gesperrt</span>';
    const cur = AKQ_STATUS[x.status] || x.status;
    const sel = opts.map(s => `<option value="${s}"${x.status === s ? ' selected' : ''}>${AKQ_STATUS[s]}</option>`).join('');
    return `<select onchange='akqSetStatus(${JSON.stringify(x.id)}, this.value, this)' class="border border-[color:var(--line)] rounded px-1.5 py-0.5 text-xs bg-white" title="Stufe manuell setzen — „gewonnen" bestätigst du hier selbst">
      <option value="" disabled${['cold','contacted'].includes(x.status) ? ' selected' : ''}>${cur} →</option>${sel}</select>`;
  }
  async function akqSetStatus(landlordId, status, el) {
    if (!status) return;
    const r = await akqApi('/api/landlord/status', { landlord_id: landlordId, status });
    if (r.error) { if (el) el.title = '⚠ ' + r.error; akqRenderLandlords(); return; }
    akqRenderLandlords(); akqRenderOverview();
  }

  async function akqRenderOutbox() {
    const el = document.getElementById('akqOutbox');
    try {
      const r = await akqApi('/api/outbox');
      const d = r.drafts || [];
      el.innerHTML = d.length ? d.map(x => `<div class="card p-3 flex items-center justify-between gap-3">
        <div class="min-w-0"><div class="font-medium truncate">${x.subject || '(ohne Betreff)'}</div><div class="text-xs text-[color:var(--muted)]">${x.variant || ''} · ${x.id} · ${x.created_at || ''}</div></div>
        <div class="flex items-center gap-2 shrink-0">
          <span class="text-xs px-2 py-0.5 rounded-full border border-[color:var(--line)]">Entwurf</span>
          <button onclick='akqApprove(${JSON.stringify(x.id)})' class="text-xs px-2.5 py-1 rounded bg-[color:var(--green)] text-white font-semibold whitespace-nowrap" title="Hältst du fest, dass dieser Pitch raus ist (du sendest selbst via Gmail). Schreibt einen Kontakt ins CRM und hebt den Anbieter auf „angeschrieben". Kein Versand.">✅ Als gesendet markieren</button>
        </div></div>`).join('') : '<div class="text-[color:var(--muted)]">Noch keine Entwürfe vorbereitet.</div>';
    } catch (e) { el.innerHTML = '<div class="text-[color:var(--muted)]">Outbox nicht ladbar.</div>'; }
  }

  // Entwurf als „gesendet festgehalten" markieren → outbound-interaction im CRM,
  // Anbieter cold→contacted. KEIN Versand (Adrian sendet selbst via Gmail).
  async function akqApprove(draftId, statusEl) {
    const note = statusEl || document.getElementById('akqOvHint');
    const r = await akqApi('/api/outbox/approve', { draft_id: draftId, lead_signal: _akqState.signal || null });
    if (r.error) { if (note) note.textContent = '⚠ ' + r.error; return false; }
    if (note) note.textContent = '✓ im CRM festgehalten (Anbieter „angeschrieben") — kein Versand';
    akqRenderOutbox(); akqRenderLandlords(); akqRenderOverview();
    return true;
  }

  function akqParseUrl(url) {
    const u = (url || '').toLowerCase(); const out = {};
    let m = u.match(/\/ort-([a-zäöü0-9\-]+?)\//); if (m) out.city = m[1].split('-')[0].replace(/^\w/, c => c.toUpperCase());
    m = u.match(/\/(\d+(?:[.\-]\d+)?)\s*-?zimmer/); if (m) out.rooms = m[1].replace('-', '.');
    return out;
  }
  function akqUrlAutofill() {
    const p = akqParseUrl(document.getElementById('akqUrl').value);
    const c = document.getElementById('akqUrlCity'), r = document.getElementById('akqUrlRooms');
    if (p.city && !c.value) c.value = p.city;
    if (p.rooms && !r.value) r.value = p.rooms;
  }
  async function akqCheckUrl() {
    const url = document.getElementById('akqUrl').value.trim();
    const rent = +document.getElementById('akqUrlRent').value;
    const city = document.getElementById('akqUrlCity').value.trim();
    const rooms = +document.getElementById('akqUrlRooms').value;
    const stat = document.getElementById('akqUrlStat'); const res = document.getElementById('akqUrlResult');
    if (!url) { stat.textContent = '⚠ Bitte einen Inserat-Link einfügen.'; return; }
    stat.textContent = 'bewerte …'; res.innerHTML = '';
    const r = await akqApi('/api/check-url', { url, rent, city, rooms });
    if (r.error && !r.listing) { stat.textContent = '⚠ ' + r.error; return; }
    if (r.rejected) { stat.textContent = `Würde rausfallen: ${r.reason}`; res.innerHTML = ''; return; }
    _akqState.source = r.source || '_manuell.json';
    stat.textContent = '✓ bewertet';
    res.innerHTML = akqCard(r.listing);
  }

  async function akqRenderOverview() {
    const el = document.getElementById('akqOverview'); if (!el) return;
    let s = {}, f = {};
    try { s = await akqApi('/api/status'); } catch (e) {}
    try { f = await akqApi('/api/funnel'); } catch (e) {}
    const ov = f.overall || {};
    const num = (n, l) => `<div><div class="font-display text-2xl">${n ?? 0}</div><div class="text-[10px] uppercase tracking-wider text-[color:var(--muted)]">${l}</div></div>`;
    const cap = (on, name, note) => `<div class="flex items-center gap-2 text-sm py-0.5"><span style="color:${on ? 'var(--green)' : 'var(--muted)'}">${on ? '●' : '○'}</span><span>${name}</span>${note ? `<span class="text-[11px] text-[color:var(--muted)]">${note}</span>` : ''}</div>`;
    const convLine = ov.outbound > 0
      ? `<div class="text-sm mt-1">Auswertung: <b>${ov.outbound}</b> Anschreiben · Antwortquote <b>${ov.reply_rate}%</b> · positiv <b>${ov.positive_rate}%</b> · gewonnen <b>${ov.won_rate}%</b></div>`
      : `<div class="text-xs text-[color:var(--muted)] mt-1">Conversion-Auswertung läuft an, sobald Anschreiben festgehalten sind (Antwortquote · positiv · gewonnen, pro Variante & Briefing-Signal).</div>`;
    // Lernschleife: welches Briefing-Signal konvertiert wirklich (by_lead_signal)?
    const sig = f.by_lead_signal || {};
    const sigKeys = Object.keys(sig).filter(k => k && (sig[k].outbound || 0) > 0);
    const sigLabels = { neustarter: 'Neustarter', stille_perle: 'Stille Perle', top_verdiener: 'Top-Verdiener' };
    const sigLine = sigKeys.length
      ? `<div class="text-xs mt-1">Nach Briefing-Signal: ${sigKeys.map(k => `<b>${sigLabels[k] || k}</b> ${sig[k].outbound}× · ${sig[k].positive_rate}% positiv`).join(' · ')}</div>`
      : '';
    el.innerHTML = `
      <div class="flex items-center justify-between flex-wrap gap-2">
        <div class="font-semibold">📊 Akquise-Übersicht</div>
        <button onclick="akqRenderOverview()" class="text-xs underline text-[color:var(--muted)]">aktualisieren</button>
      </div>
      <div class="grid grid-cols-4 gap-3 mt-3 max-w-md">
        ${num(s.landlords, 'Anbieter')}${num(s.drafts, 'Entwürfe')}${num(s.recent30, 'in 30 T')}${num(s.interactions, 'Kontakte')}
      </div>
      ${convLine}
      ${sigLine}
      <details class="mt-4 pt-3 border-t border-[color:var(--line)]">
        <summary class="text-xs font-semibold uppercase tracking-wider text-[color:var(--muted)] cursor-pointer select-none">ℹ Was kann dieses System?</summary>
        <div class="grid sm:grid-cols-2 gap-x-6 mt-2">
          ${cap(true, 'Inserate finden', 'Scan · Link-Check · Suchagent-Mails')}
          ${cap(true, 'Anbieter-CRM + Verzeichnis', 'wer · Kontakt · Historie')}
          ${cap(true, 'Anschreiben (5 Varianten + Decision-Tree)', s.anthropic_ready ? 'echter Claude bereit' : 'Mock gratis · echter Claude via Key')}
          ${cap(s.imap_ready, 'Antworten lesen + einordnen', s.imap_ready ? 'IMAP bereit' : 'braucht IMAP-Zugang')}
          ${cap(true, 'Conversion lernen (beste Variante)', 'Funnel je Variante/Kanton')}
          ${cap(true, 'Verwaltungen-Suche', 'Web-Suche · kein Login · Lead-Quelle B2B')}
          ${cap(true, 'Versand via Gmail', 'manuell · dein Google-Konto · kein Auto-Versand')}
        </div>
        <div class="text-[11px] text-[color:var(--muted)] mt-2">Alles lokal in Heimstatt gebaut (v1.x, 8 Phasen). Über den lokalen Agenten verbunden — kein Auto-Versand.</div>
      </details>`;
  }

  async function akqSearchVerwaltungen() {
    const ort = document.getElementById('akqVwOrt').value.trim();
    const stat = document.getElementById('akqVwStat'), res = document.getElementById('akqVwResult');
    if (!ort) { stat.textContent = '⚠ Bitte einen Ort eingeben.'; return; }
    stat.textContent = 'suche …'; res.innerHTML = '';
    const r = await akqApi('/api/verwaltungen', { ort });
    if (r.error) { stat.textContent = '⚠ ' + r.error; return; }
    const d = r.results || []; _akqState.vw = d;
    stat.textContent = `${d.length} gefunden`;
    res.innerHTML = d.map((x, i) => `<div class="flex items-center justify-between gap-2 border border-[color:var(--line)] rounded px-3 py-1.5">
      <div class="min-w-0"><div class="font-medium text-sm truncate">${x.name}</div>
      <div class="text-[11px] text-[color:var(--muted)] truncate">${[x.address, x.phone, x.website].filter(Boolean).join(' · ') || (x.desc || '')}</div></div>
      <button onclick='akqAddVerwaltung(${i})' class="text-xs px-2 py-1 rounded bg-[color:var(--ink)] text-white whitespace-nowrap">→ ins Verzeichnis</button>
    </div>`).join('') || '<div class="text-[color:var(--muted)] text-sm">Nichts gefunden.</div>';
  }
  async function akqAddVerwaltung(i) {
    const x = (_akqState.vw || [])[i]; if (!x) return;
    const notes = [x.website, x.address, x.phone].filter(Boolean).join(' · ');
    const r = await akqApi('/api/landlord/add', { company: x.name, type: 'klein_verwaltung', notes });
    document.getElementById('akqVwStat').textContent = r.landlord_id
      ? (r.matched ? `„${x.name}" war schon im Verzeichnis ✓` : `„${x.name}" ins Verzeichnis ✓`)
      : ('⚠ ' + (r.error || ''));
    akqRenderLandlords(); akqRenderOverview();
  }

  // ====================== DEAL-ARBEITSPLATZ (Layout-Orchestrierung) ======================
  // Rein additiv: reicht Leads in die VORHANDENE Dossier-/Agent-Logik. Bricht nichts,
  // alles in try/catch. Lead-Quelle = newhome-Mietinserate aus dem Gmail-Abo + manueller Link.
  const AKQWORK = { leads: [], selKey: null, mode: 'fokus' };

  // Markt-Name aus einem Lead auf einen Eintrag in markets[] mappen (für occ/adr/cockpit).
  function akqMarketFor(name) {
    if (!name || typeof markets === 'undefined') return null;
    const n = String(name).toLowerCase().trim();
    return markets.find(m => m.name.toLowerCase() === n)
        || markets.find(m => m.name.toLowerCase().startsWith(n) || n.startsWith(m.name.toLowerCase()))
        || null;
  }

  // Mini-Lukrativitäts-Urteil PRO LEAD aus Cockpit-Ökonomik (dossOffer/dossDealScore).
  // rent vorhanden → echtes Spielraum-CHF; rent offen → STR-Stärke + Heuristik, klar gelabelt.
  function akqLeadVerdict(lead) {
    try {
      const m = akqMarketFor(lead.market);
      if (!m) return { amp: '#9CA3AF', label: 'Markt unbekannt', sub: 'kein Marktprofil', tier: '🟡' };
      // Zimmer konsistent schätzen: Kapazität → Schlafzimmer (~2 Pers/Zi) → CH-Zimmer via STREcon (Schlafzi+1.5), statt capacity/2 (unterschätzt). M25
      const rooms = parseFloat(lead.rooms) || (lead.capacity ? (STREcon.roomsFromBedrooms(Math.max(1, Math.round(lead.capacity / 2))) || 2.5) : 2.5);
      const rent = parseFloat(lead.rent || lead.price) || 0;
      // STABILE per-Lead-Kohorte (4. Arg = stableRooms): unabhängig vom globalen AKQ_F-Filter,
      // damit das Board-Urteil NICHT springt, wenn man einen anderen Lead anklickt.
      const o = dossOffer(m, rooms, null, rooms);
      const f = { building: 'gross', sublet: 'unklar', ground: false, vacant: !!lead.vacant, etw: false, view: 'nein' };
      const ds = dossDealScore(m, f);
      const tier = o.occTier === 'live' ? '🟢' : '🟡';
      if (rent > 0) {
        const sp = Math.round(o.maxMiete - rent);
        const amp = sp >= 600 ? 'var(--green)' : sp >= 0 ? '#C9A24A' : 'var(--red)';
        const lab = SwissFmt.signedChf(sp);
        return { amp, label: 'Spielraum ' + lab + '/Mt', sub: 'Score ' + ds.score + ' · Obergr. ' + chf(o.maxMiete), tier, score: ds.score, spielraum: sp };
      }
      // Keine Miete erfasst (manueller Link ohne Miete): STR-Ertrag + Heuristik, klar gelabelt.
      const amp = (o.maxMiete >= 2000 && ds.score >= 60) ? 'var(--green)' : (o.maxMiete >= 1000 || ds.score >= 50) ? '#C9A24A' : 'var(--red)';
      return { amp, label: 'STR trägt bis ' + chf(o.maxMiete) + '/Mt', sub: 'Miete offen · Score ' + ds.score, tier, score: ds.score };
    } catch (e) { return { amp: '#9CA3AF', label: '—', sub: '', tier: '🟡' }; }
  }

  function akqLeadKey(l) { return (l.source || 'x') + ':' + (l.url || l.host || l.id || Math.random()); }

  function akqRenderLeadBoard() {
    const fokus = document.getElementById('akqLeadList');
    const liste = document.getElementById('akqLeadListListMode');
    const stat = document.getElementById('akqLeadStatLine');
    if (!fokus) return;
    const leads = AKQWORK.leads;
    // Ehrlicher Leerzustand: Agent-aus oder keine Mails → NIE auf Airbnb/Briefing zurückfallen.
    const emptyHtml = AKQWORK.agentDown
      ? `<div class="lead-empty">🔌 <b>Agent aus.</b> Starte <span class="font-mono" style="color:var(--gold)">heimstatt\\agent\\cockpit.cmd</span>, dann erscheinen deine <b>newhome-Inserate aus dem Gmail-Abo</b> hier. Bis dahin kannst du oben einen newhome-Link manuell einfügen.</div>`
      : (AKQWORK.mailError
        ? `<div class="lead-empty">⚠ ${AKQWORK.mailError}</div>`
        : `<div class="lead-empty">Noch keine newhome-Inserate im Gmail-Abo gefunden. Lege auf <b>newhome.ch</b> einen Suchagenten an oder füge oben einen Inserat-Link manuell ein, dann <b>„⟳ aus Gmail"</b> klicken.</div>`);
    if (stat) stat.textContent = leads.length ? `${leads.length} newhome-Inserate · sortiert nach Lukrativität` : '';
    // Sortieren: höchster Score/Spielraum zuerst.
    leads.forEach(l => { l._v = akqLeadVerdict(l); });
    leads.sort((a, b) => ((b._v.spielraum ?? b._v.score ?? 0) - (a._v.spielraum ?? a._v.score ?? 0)));
    const srcLabel = { mail: 'Gmail', manuell: 'manuell' };
    const chip = (l) => {
      const v = l._v, sel = AKQWORK.selKey === akqLeadKey(l) ? ' sel' : '';
      return `<div class="leadchip${sel}" onclick='akqSelectLead(${JSON.stringify(akqLeadKey(l))})'>
        <span class="lr-amp" style="background:${v.amp}"></span>
        <span class="text-xs"><b>${(l.market || '—')}</b> · ${l.host || (l.rooms ? l.rooms + ' Zi' : 'Lead')}<br><span class="text-[color:var(--muted)]">${v.label} ${v.tier}</span></span>
      </div>`;
    };
    const row = (l) => {
      const v = l._v, sel = AKQWORK.selKey === akqLeadKey(l) ? ' sel' : '';
      return `<div class="leadrow${sel}" onclick='akqSelectLead(${JSON.stringify(akqLeadKey(l))})'>
        <span class="lr-amp" style="background:${v.amp}"></span>
        <div class="min-w-0"><div class="text-sm font-semibold truncate">${l.market || '—'} <span class="text-[10px] text-[color:var(--muted)] font-normal">${srcLabel[l.source] || l.source || ''}</span></div>
          <div class="text-[11px] text-[color:var(--muted)] truncate">${l.host ? l.host + ' · ' : ''}${l.rooms ? l.rooms + ' Zi · ' : ''}${v.sub}</div></div>
        <div class="text-right text-[11px] font-semibold" style="color:${v.amp}">${v.label}<br><span class="text-[color:var(--muted)] font-normal">${v.tier}</span></div>
      </div>`;
    };
    fokus.innerHTML = leads.length ? leads.map(chip).join('') : emptyHtml;
    if (liste) liste.innerHTML = leads.length ? leads.map(row).join('') : emptyHtml;
  }

  function akqSelectLead(key) {
    const l = AKQWORK.leads.find(x => akqLeadKey(x) === key);
    if (!l) return;
    // Vor dem Wechsel: aktuelle Anbieter-Eingabe am bisherigen Lead festhalten (persistiert mit dem Lead).
    try {
      const prev = _akqState.lead;
      if (prev) { prev.llCompany = (document.getElementById('dossLlCompany') || {}).value || ''; prev.llContact = (document.getElementById('dossLlContact') || {}).value || ''; }
    } catch (e) {}
    AKQWORK.selKey = key;
    _akqState.signal = l.signal || null;
    _akqState.lead = l;
    // Anbieter-Felder am Lead wiederherstellen (host aus Mail als Vorbelegung der Firma, falls leer).
    try {
      const cEl = document.getElementById('dossLlCompany'), kEl = document.getElementById('dossLlContact');
      if (cEl) cEl.value = l.llCompany != null ? l.llCompany : (l.host || '');
      if (kEl) kEl.value = l.llContact || '';
    } catch (e) {}
    // In die vorhandenen Dossier-Felder schreiben (Objektfakten bleiben LEER — Adrian sichtet Fotos).
    const setVal = (id, v) => { const el = document.getElementById(id); if (el && v != null && v !== '') el.value = v; };
    const ms = document.getElementById('dossMarket');
    const mm = akqMarketFor(l.market);
    if (ms && mm && [...ms.options].some(o => o.value === mm.name)) ms.value = mm.name;
    const rooms = l.rooms || (l.capacity ? (STREcon.roomsFromBedrooms(Math.max(1, Math.round(l.capacity / 2))) || '') : '');
    setVal('dossRooms', rooms);
    setVal('dossRent', l.rent || l.price || '');
    setVal('dossUrl', l.url || '');
    // Anbieter-Typ wird abgeleitet (Firma → firma) + Doppel-Warnung gegen CRM matchen.
    try { akqRefreshLlMatch(false); } catch (e) {}
    try { renderDossier(); } catch (e) {}
    try { akqSyncLaw(); } catch (e) {}
    // Lead-Banner zeigen (Übernahme-Hinweis + Agent-Handoff)
    try { akqShowLeadBanner(l); } catch (e) {}
    akqRenderLeadBoard();
    try { document.getElementById('akqWorkspace').scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {}
  }

  function akqShowLeadBanner(l) {
    const banner = document.getElementById('akqLeadBanner');
    if (!banner) return;
    const srcLabel = l.source === 'mail' ? 'newhome aus Gmail-Abo' : l.source === 'manuell' ? 'manueller Link' : 'Inserat';
    const lno = l.listing_no ? ' · Nr. ' + l.listing_no : '';
    banner.style.display = '';
    banner.innerHTML = `<div class="flex items-center justify-between flex-wrap gap-2">
      <div class="text-sm">📥 Mietinserat übernommen: <b>${l.market || '—'}</b>${l.host ? ' · ' + l.host : ''} · <b>${srcLabel}</b>${lno}.
        <span style="color:var(--muted)">Objektfakten (Ausbau/Waschturm/Strasse) aus den Fotos ergänzen — wird nicht erfunden.</span></div>
      <button onclick="akqGiveLeadToAgent()" class="px-3 py-1.5 rounded bg-[color:var(--gold)] text-[color:var(--ink)] text-xs font-bold whitespace-nowrap" title="Bewertet das Inserat im lokalen Agenten → danach greifen Anschreiben/Outbox/Approve daran">An Agenten geben →</button>
    </div>`;
    ensureLeadStat(banner);
  }

  // Law-Strip + Such-Strategien an den aktuell gewählten Markt koppeln.
  function akqSyncLaw() {
    const ms = document.getElementById('dossMarket');
    const m = ms ? markets.find(x => x.name === ms.value) : null;
    if (!m) return;
    const lbl = document.getElementById('akqLawMarket'); if (lbl) lbl.textContent = m.name;
    try { renderLoopholes(m, 'akqLoopholeCard', 'akqLoopholeBody'); } catch (e) {}
    try { renderChecklist(m, 'akqChecklist', 'akqChecklistMarket'); } catch (e) {}
    const ss = document.getElementById('akqStratMarket');
    if (ss && ss.value !== m.name && [...ss.options].some(o => o.value === m.name)) {
      ss.value = m.name; try { renderSearchStrats(m, 'akqSearchStrats', 'akqStratMarketLabel'); } catch (e) {}
    }
    const lb = document.getElementById('akqLetterBtn'); if (lb) lb.onclick = () => openLetterGen(m);
  }

  // ---- Lead-Quelle = newhome-Mietinserate aus Adrians Gmail-Abo ----
  // KEINE Airbnb/Briefing-Leads (das wären STR-Betreiber/Konkurrenz, keine Akquise-Ziele).
  // Die Leads sind Wohnungen, die ZU VERMIETEN sind und die Adrian als R2R übernehmen kann.
  // Quelle: /api/find-mails (IMAP zieht newhome/homegate/immoscout-Suchagent-Mails) → /api/scan.
  let _akqLeadsLoading = false;
  async function akqLoadMailLeads(opts) {
    const stat = document.getElementById('akqLeadStatLine');
    const silent = opts && opts.silent;
    if (_akqLeadsLoading) return AKQWORK.leads.filter(l => l.source === 'mail');
    _akqLeadsLoading = true;
    if (stat && !silent) stat.textContent = 'hole newhome-Inserate aus dem Gmail-Abo …';
    try {
      // Agent erreichbar?
      let up = false;
      try { const p = await akqApi('/api/ping'); up = p && p.ok; } catch (e) { up = false; }
      if (!up) { AKQWORK.agentDown = true; return []; }
      AKQWORK.agentDown = false;
      const fm = await akqApi('/api/find-mails', { since_days: 14, max: 50 });
      if (fm.error) { AKQWORK.mailError = fm.error; return []; }
      AKQWORK.mailError = null;
      const sc = await akqApi('/api/scan', { source: fm.source, threshold: 0 });
      return (sc.listings || []).map(l => ({
        source: 'mail', market: l.city, canton: l.canton, host: l.landlord,
        rooms: l.rooms, rent: l.rent, url: l.url, id: l.id, score: l.score,
        title: l.title, street: l.street, listing_no: akqListingNo(l.url),
      }));
    } catch (e) { AKQWORK.agentDown = true; return []; }
    finally { _akqLeadsLoading = false; }
  }

  // newhome-Inserat-Nummer aus der URL ziehen (newhome.ch/.../id/<n>).
  function akqListingNo(url) {
    const m = (url || '').match(/(?:\/id\/|listingId=|\/(\d{6,}))/i);
    return m ? (m[1] || m[0].replace(/\D/g, '')) : null;
  }

  function akqMergeLeads(newLeads) {
    const seen = new Set(AKQWORK.leads.map(akqLeadKey));
    newLeads.forEach(l => { const k = akqLeadKey(l); if (!seen.has(k)) { seen.add(k); AKQWORK.leads.push(l); } });
    akqRenderLeadBoard();
  }

  async function akqLeadBoardInit() {
    // Erst gescrapte Nicht-BFS-Märkte ergänzen, damit Verdict/Markt der Mail-Leads auflöst.
    try { await akqAugmentMarkets(); akqRebuildMarketSelects(); } catch (e) {}
    // Start mit den newhome-Mail-Inseraten (kein Airbnb/Briefing).
    AKQWORK.leads = await akqLoadMailLeads({ silent: true });
    akqRenderLeadBoard();
    // Manueller newhome-Lead
    const addBtn = document.getElementById('akqLeadManualAdd');
    if (addBtn) addBtn.onclick = () => {
      const url = document.getElementById('akqLeadManualUrl').value.trim();
      const rent = document.getElementById('akqLeadManualRent').value.trim();
      if (!url && !rent) return;
      const p = (typeof akqParseUrl === 'function') ? akqParseUrl(url) : {};
      akqMergeLeads([{ source: 'manuell', market: p.city || (document.getElementById('dossMarket') || {}).value || '', rooms: p.rooms || '', rent: rent || '', url, listing_no: akqListingNo(url) }]);
      document.getElementById('akqLeadManualUrl').value = ''; document.getElementById('akqLeadManualRent').value = '';
    };
    const rl = document.getElementById('akqLeadReload'); if (rl) rl.onclick = akqLeadMails;
    const mb = document.getElementById('akqLeadMails'); if (mb) mb.onclick = akqLeadMails;
  }

  // newhome-Inserate frisch aus dem Gmail-Abo ziehen (Agent nötig).
  async function akqLeadMails() {
    const stat = document.getElementById('akqLeadStatLine');
    if (stat) stat.textContent = 'hole newhome-Inserate aus dem Gmail-Abo …';
    const fresh = await akqLoadMailLeads();
    // Nur Mail-Leads ersetzen, manuelle behalten.
    AKQWORK.leads = AKQWORK.leads.filter(l => l.source !== 'mail');
    akqMergeLeads(fresh);
    if (stat) {
      if (AKQWORK.agentDown) stat.textContent = '⚠ Agent aus — starte heimstatt\\agent\\cockpit.cmd, dann erscheinen deine newhome-Inserate.';
      else if (AKQWORK.mailError) stat.textContent = '⚠ ' + AKQWORK.mailError;
      else stat.textContent = `${fresh.length} newhome-Inserate aus dem Gmail-Abo · sortiert nach Lukrativität`;
    }
  }

  // ---- Ansichts-Umschalter Fokus ↔ Liste ----
  function akqSetMode(mode) {
    AKQWORK.mode = mode;
    try { localStorage.setItem('akq_view_mode', mode); } catch (e) {}
    const root = document.getElementById('akqWorkRoot');
    const board = document.getElementById('akqLeadBoard');
    const listPane = document.getElementById('akqListPane');
    const fokusList = document.getElementById('akqLeadList');
    if (mode === 'liste') {
      root && root.classList.add('list-mode');
      if (listPane) listPane.style.display = '';
      if (board) board.style.display = 'none';   // Lead-Liste übernimmt die Auswahl links
    } else {
      root && root.classList.remove('list-mode');
      if (listPane) listPane.style.display = 'none';
      if (board) board.style.display = '';
      if (fokusList) fokusList.className = 'lead-scroll-fokus';
    }
    document.querySelectorAll('#akqViewToggle button').forEach(b => b.classList.toggle('on', b.dataset.mode === mode));
    akqRenderLeadBoard();
  }
  function akqInitToggle() {
    let saved = 'fokus'; try { saved = localStorage.getItem('akq_view_mode') || 'fokus'; } catch (e) {}
    document.querySelectorAll('#akqViewToggle button').forEach(b => { b.onclick = () => akqSetMode(b.dataset.mode); });
    akqSetMode(saved);
  }

  // ====================== INIT ======================
  initDossier();
  initAkqStrats();
  // Dossier-Markt-Wechsel koppelt Law-Strip + Such-Strategien.
  try { ['dossMarket','dossType','dossRooms','dossRent'].forEach(id => { const el = document.getElementById(id); if (el) el.addEventListener('change', () => { try { akqSyncLaw(); } catch(e){} }); }); } catch (e) {}
  try { const dm = document.getElementById('dossMarket'); if (dm) dm.addEventListener('change', renderDossier); } catch (e) {}
  akqInitToggle();
  // Pitch-Zone (Zone 3) verdrahten: Variante-Toggle + Gmail/Gesendet.
  try {
    document.querySelectorAll('#dossPitchToggle button').forEach(b => {
      b.onclick = () => {
        _dossPitchVariant = parseInt(b.dataset.pitch, 10) || 1;
        document.querySelectorAll('#dossPitchToggle button').forEach(x => x.classList.toggle('on', x === b));
        try { renderDossier(); } catch (e) {}
      };
    });
    const pg = document.getElementById('dossPitchGmail');
    if (pg) pg.onclick = () => {
      const m = markets.find(x => x.name === (document.getElementById('dossMarket') || {}).value);
      const body = (document.getElementById('dossPitchBody') || {}).textContent || '';
      const subj = 'Anfrage zu Ihrem Inserat' + (m ? ' in ' + m.name : '');
      window.open('https://mail.google.com/mail/?view=cm&fs=1&su=' + encodeURIComponent(subj) + '&body=' + encodeURIComponent(body), '_blank');
    };
    const ps = document.getElementById('dossPitchSent');
    if (ps) ps.onclick = () => { const s = document.getElementById('dossPitchStat'); if (s) s.textContent = 'als gesendet vermerkt ✓ — im Verzeichnis Status setzen'; };
  } catch (e) {}
  akqLeadBoardInit();
  try { akqSyncLaw(); } catch (e) {}
  // Gescrapte Nicht-BFS-Märkte früh ergänzen + Dropdowns neu bauen, DANN Hash-Lead anwenden,
  // damit Arth/Spreitenbach/Dietikon/Ennetbürgen selektierbar sind (sonst „Markt unbekannt").
  (async () => {
    try { await akqAugmentMarkets(); akqRebuildMarketSelects(); } catch (e) {}
    try { akqApplyLeadFromHash(); } catch (e) {}
    try { if (AKQWORK.leads && AKQWORK.leads.length) akqRenderLeadBoard(); } catch (e) {}
  })();
  window.addEventListener('hashchange', () => { try { akqApplyLeadFromHash(); } catch (e) {} });
  initAkquise();
