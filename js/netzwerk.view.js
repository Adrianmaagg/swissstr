/* ============================================================================
   SwissSTR — netzwerk.view.js  ·  View-Logik der Netzwerk-Seite (erstes View-Modul)
   ----------------------------------------------------------------------------
   1:1 aus netzwerk.html ausgelagert (STATUS §7 — "klare Module, klare Schnittstellen").
   GEKAPSELT (Stufe 2): alles in EINER IIFE → kein interner Name leakt mehr in den
   globalen Scope. Die Seite referenziert von außen NICHTS (keine statischen oder
   generierten onclick-Handler — alle Events werden per .onclick= im Code verdrahtet),
   darum ist die öffentliche Oberfläche LEER: das Modul bootet sich selbst (boot() unten).
   Geladen NACH js/format.js (SwissFmt), js/ticker.js (SwissTicker), Leaflet (L), js/map.js.
   Verhalten unverändert — nur die Sichtbarkeit der internen Helfer ist jetzt dicht.
   ========================================================================== */
(function () {
'use strict';
const E=SwissFmt.escapeHtml;
const fmtCHF=n=>(n||n===0)?SwissFmt.chf(n):'–';
const mkey=m=>encodeURIComponent(String(m).trim().toLowerCase());
let NET=null, PROFILES=null, COMP=null, COMPROF=null, TAB='ops', SORT='', CROSS=false, Q='', TIER='';
const TIER_SHORT={extrem:'extrem big',big:'big big',mittel:'mittel big',small:'small big',unter:'unter 10'};

// "Wer steckt dahinter": recherchiertes Marken-Dossier per Namens-Match, sonst generisch nach Typ.
function operatorDossier(o){
  if(!PROFILES) return null;
  const nm=(o.name||'').toLowerCase();
  const hit=(PROFILES.profiles||[]).find(p=>(p.match||[]).some(mm=>nm.includes(mm)));
  if(hit) return {p:hit, researched:true};
  const g=(PROFILES.generic||{})[o.kind];
  return g?{p:g, researched:false}:null;
}
function kindBadge(o){
  const map={brand:['🏢 Marke','var(--gold)'],pro:['👤 Gross-Operator','var(--blue)'],person:['👤 Person','var(--faint)']};
  const x=map[o.kind]; if(!x) return '';
  return `<span class="pill" style="background:rgba(255,255,255,.04);color:${x[1]};border:1px solid ${x[1]}" title="${E(o.kind_label||'')}">${x[0]}</span>`;
}
function dossierHtml(o){
  const d=operatorDossier(o); if(!d) return '';
  const p=d.p;
  const tier=d.researched?`<span class="tier">🟢 recherchiert</span>`:`<span class="tier">🟡 Muster nach Typ</span>`;
  const src=(p.sources||[]).map(u=>`<a href="${E(u)}" target="_blank" rel="noopener" style="color:var(--blue)">Quelle↗</a>`).join(' · ');
  const rows=[
    ['Wer', p.what], ['Wie sie auftreten', p.appearance], ['Woher die Wohnungen', p.sourcing],
    ['Wie sie vorgehen', p.model], ['Verträge / Konditionen', p.contract], ['Lektion für dich', p.lesson]
  ].filter(r=>r[1]).map(r=>`<div class="dz-row"><span class="dz-k">${r[0]}</span><span class="dz-v">${E(r[1])}</span></div>`).join('');
  // Sichtbarer Auftritt: Website + Eigentuemer-Landingpage als Buttons
  const btn=[];
  if(p.website) btn.push(`<a class="dz-btn" href="${E(p.website)}" target="_blank" rel="noopener">🌐 Website ansehen ↗</a>`);
  if(p.owner_url && p.owner_url!==p.website) btn.push(`<a class="dz-btn gold" href="${E(p.owner_url)}" target="_blank" rel="noopener">📄 Eigentümer-/Landingpage ↗</a>`);
  const btns=btn.length?`<div class="dz-btns">${btn.join('')}</div>`:'';
  return `<div class="dz"><div class="dz-lab">Wer steckt dahinter — ${E(p.label||o.name||'')} ${tier}</div>${rows}${btns}<div class="dz-src">${src}</div></div>`;
}

const SORTS={
  nets:[['total_reviews','Operator-Bewertungen (Σ)'],['own_listings','Inserate (Σ)'],['est_month_chf','Ertrag/Mt (Σ, 🟡)'],['n_markets','Anzahl Märkte']],
  ops:[['total_listings','Gesamt-Portfolio (X-Ray) 🟢'],['host_total_reviews','Operator-Bewertungen'],['own_count','Erfasste Inserate'],['est_month_chf','Ertrag/Mt (🟡)']],
  mkts:[['n_chances','Positionierungs-Lücken'],['lead_share','Profi-Dominanz (Lead-Anteil)'],['total','Anzahl Inserate'],['n_operators','Anzahl Betreiber']]
};

function fillSort(){
  const s=document.getElementById('sort');
  const list=SORTS[TAB]||[];
  s.style.display=list.length?'':'none';
  if(!list.length){ SORT=''; return; }
  s.innerHTML=list.map(([v,l])=>`<option value="${v}">Sortieren: ${l}</option>`).join('');
  SORT=list[0][0]; s.value=SORT;
}

function memberRow(m){
  const op=(NET.operators||{})[m.uid]||{};
  const ls=(op.own||[]).map(o=>{
    const url=o.url||('https://www.airbnb.com/rooms/'+o.id);
    const pk=o.pickup, net=pk?pk.net:null;
    const pkTxt = (net!=null && net!==0)
      ? (net>0 ? ` · <b style="color:var(--green)" title="frei→belegt seit ${E(pk.date||'')}: ${pk.nb} gebucht, ${pk.fr} frei">▲ +${net} N gebucht</b>`
               : ` <span style="color:var(--faint)" title="seit ${E(pk.date||'')}: ${pk.nb} gebucht, ${pk.fr} frei">▼ ${net} N frei</span>`)
      : '';
    return `<a class="lk" href="${E(url)}" target="_blank" rel="noopener">↗ ${E(o.market)} · ${fmtCHF(o.price_chf)} · ${o.occ30!=null?o.occ30+'%':'–'} · ≈${fmtCHF(o.est_month)}/Mt${pkTxt}</a>`;
  }).join('');
  const tl=m.total_listings!=null?m.total_listings:op.total_listings;
  const bits=[];
  if(m.host_total_reviews!=null) bits.push(`<span style="color:var(--green)">${m.host_total_reviews} Bew. 🟢</span>`);
  if(m.host_rating) bits.push(`${m.host_rating}★`);
  if(m.host_title) bits.push(E(m.host_title));
  if(tl) bits.push(`<span style="color:var(--gold);font-weight:700">${tl} Inserate gesamt 🟢</span>`);
  else if(m.own_count) bits.push(`${m.own_count} eigene`);
  if(m.room_count>0) bits.push(`<span style="color:var(--amber)">🛏 ${m.room_count} Zi · ${m.entire_count||0} Whg</span>`);
  if(m.cohost_count) bits.push(`Co-Host bei ${m.cohost_count}`);
  const pb=m.playbook||op.playbook;
  const pbHtml=(pb&&pb.signals&&pb.signals.length)?`<div class="pb"><div class="pb-lab">▸ Wie ${E(m.name||'er/sie')} es umsetzt <span class="tier">🟡 aus den Inseraten abgeleitet</span></div><ul class="pb-sig">${pb.signals.map(s=>`<li>${E(s)}</li>`).join('')}</ul></div>`:'';
  const seen=(op.own||[]).length;
  const covNote=(tl&&tl>seen)?`<div class="cov" style="margin:5px 0 1px">Davon in unseren erfassten Märkten sichtbar: <b>${seen} von ${tl}</b> — der Rest liegt ausserhalb. Erfasste Inserate:</div>`:'';
  return `<div class="mem"><div class="mem-h"><span class="role ${m.role}">${m.role==='lead'?'Lead':m.role==='host'?'Eigenständig':'Assistent'}</span><b>${E(m.name||'?')}</b><span class="mem-meta">${bits.join(' · ')}</span></div>${pbHtml}${ls?`${covNote}<div class="mem-ls">${ls}</div>`:''}</div>`;
}

function netCard(n,rank){
  const cross=n.cross_market?`<span class="pill cross">⇄ ${n.n_markets} Märkte</span>`:'';
  const mkts=(n.markets||[]).map(m=>`<a class="mchip" href="cockpit.html?m=${mkey(m)}">${E(m)} →</a>`).join('');
  return `<div class="nrow"><div class="nhead" data-x>
      <span class="rank">${rank}</span>
      <span><span class="nlead">${E(n.lead_name||'?')}</span> <span class="amp">&amp; Netzwerk</span><br><span class="mem-meta">${n.n_members} Personen</span></span>
      <span class="nmeta">
        <span class="pill rev" title="Summe der Operator-Gesamt-Bewertungen = härtestes Profi-Signal">${n.total_reviews} Bew. 🟢</span>
        <span class="pill list">${n.own_listings} Inserate</span>
        ${objChip(n.entire_listings,n.room_listings)}
        ${earnPill(n.est_month_chf, n.own_listings, ((n.members||[]).reduce((s,mm)=>s+(mm.total_listings||0),0)) || null)}
        ${cross}<span class="arr">▾</span>
      </span></div>
    <div class="ndet" hidden>
      <div class="mkts">${mkts}</div>
      ${n.members.map(memberRow).join('')}
    </div></div>`;
}

function objChip(ent,room){
  ent=ent||0; room=room||0;
  if(room>0) return `<span class="pill obj" title="Objekt-Art aus erfassten Inseraten — Zimmer-Vermietung ist ein anderes Modell als ganze Wohnungen (R2R)">🛏 ${room} Zi · ${ent} Whg</span>`;
  if(ent>0) return `<span class="pill objpure" title="nur ganze Wohnungen (erfasst)">🏠 nur ganze Whg</span>`;
  return '';
}
function akqHref(market){
  let h=''; try{ h=btoa(unescape(encodeURIComponent(JSON.stringify({market:market||'',source:'netzwerk-strategie'})))); }catch(e){ h=''; }
  return 'akquise.html#lead='+h;
}
// Strategie-Kern: der Loop verdichtet je grossem Spieler Modell + stärksten Vorteil + „dein Zug" — verstehen → handeln.
function kernHtml(o){
  const d=operatorDossier(o); const p=d?d.p:null;
  const sigs=(o.playbook&&o.playbook.signals)||[];
  const edge=sigs.find(s=>/Belegung|Premium|Volumen|Superhost|Preis|Skalierung/.test(s))||sigs[0]||'';
  const model=p?p.model:''; const lesson=p?p.lesson:''; const mkt=(o.markets||[])[0]||'';
  if(!model && !edge && !lesson) return '';
  return `<div class="kern">
    <div class="kern-lab">🎯 Strategie-Kern${d&&d.researched?' · recherchiert':''}</div>
    ${model?`<div class="kern-line"><b>Modell:</b> ${E(model)}</div>`:''}
    ${edge?`<div class="kern-line"><b>Vorteil:</b> ${E(edge)}</div>`:''}
    ${lesson?`<div class="kern-line gold"><b>Dein Zug:</b> ${E(lesson)}</div>`:''}
    ${mkt?`<a class="akq-btn" href="${akqHref(mkt)}">→ In die Akquise (Markt „${E(mkt)}" übernehmen)</a>`:''}
  </div>`;
}
function compDossierHtml(uid){
  const p=(COMPROF&&COMPROF.by_uid&&COMPROF.by_uid[uid]);
  if(!p) return '<div class="cov" style="padding:8px 2px">Noch kein recherchiertes Dossier — nur Grösse + Host-Profil erfasst.</div>';
  const rows=[['Was',p.what],['Wie sie auftreten',p.appearance],['Woher die Wohnungen',p.sourcing],['Modell',p.model],['Verträge / Konditionen',p.contract],['Lektion für dich',p.lesson]]
    .filter(r=>r[1]).map(r=>`<div class="dz-row"><span class="dz-k">${r[0]}</span><span class="dz-v">${E(r[1])}</span></div>`).join('');
  const btn=[];
  if(p.website) btn.push(`<a class="dz-btn" href="${E(p.website)}" target="_blank" rel="noopener">🌐 Website ↗</a>`);
  if(p.owner_url && p.owner_url!==p.website) btn.push(`<a class="dz-btn gold" href="${E(p.owner_url)}" target="_blank" rel="noopener">📄 Eigentümer-/Landingpage ↗</a>`);
  const btns=btn.length?`<div class="dz-btns">${btn.join('')}</div>`:'';
  const src=(p.sources||[]).map(u=>`<a href="${E(u)}" target="_blank" rel="noopener" style="color:var(--blue)">Quelle↗</a>`).join(' · ');
  return `<div class="dz"><div class="dz-lab">Wer steckt dahinter — ${E(p.label||'')} <span class="tier">🟢 recherchiert</span></div>${rows}${btns}<div class="dz-src">${src}</div></div>`;
}
function compCard(c,rank){
  const prof='https://www.airbnb.com/users/show/'+c.uid;
  const has=!!(COMPROF&&COMPROF.by_uid&&COMPROF.by_uid[c.uid]);
  return `<div class="nrow"><div class="nhead"${has?' data-x':' style="cursor:default"'}>
      <span class="rank">${rank}</span>
      <span><span class="nlead">${E(c.name||c.dir_name||'?')}</span> <span class="pill" style="background:rgba(255,255,255,.04);color:var(--faint);border:1px solid var(--line)">🏢 CH-Verzeichnis</span>${has?' <span class="pill" style="background:rgba(63,174,124,.13);color:var(--green)">📖 Dossier</span>':''}</span>
      <span class="nmeta">
        ${c.tier?`<span class="pill tier-${c.tier}" title="${E(c.tier_label||'')}">${TIER_SHORT[c.tier]||c.tier}</span>`:''}
        <span class="pill list" style="background:rgba(217,179,106,.13);color:var(--gold)">${c.total_listings} Inserate gesamt 🟢</span>
        <a class="lk" href="${prof}" target="_blank" rel="noopener" style="margin:0">Host-Profil ↗</a>
        ${has?'<span class="arr">▾</span>':''}
      </span></div>
      ${has?`<div class="ndet" hidden>${compDossierHtml(c.uid)}</div>`:''}
    </div>`;
}
// Ertrags-Pille: Brutto/Mt NUR aus den ERFASSTEN Inseraten. Bei grossen Spielern, deren
// Gesamt-Portfolio (X-Ray) groesser ist als das hier Erfasste, wird der Umfang SICHTBAR gemacht —
// sonst liest sich die Zahl faelschlich als Gesamt-Ertrag des ganzen Portfolios (Secra: 1207 Inserate,
// aber CHF/Mt nur aus 1 erfassten). Eine Quelle fuer alle Ertrags-Pillen (Operator + Netzwerk).
function earnPill(est, ownCount, totalListings){
  if(est==null || Math.round(est)<=0) return '';   // rundet auf CHF 0 = keine belastbare Schaetzung (kein Preis/occ am erfassten Inserat) -> "CHF 0" waere irrefuehrend
  const partial = totalListings!=null && ownCount!=null && totalListings>ownCount;
  const scope = partial ? ` <span style="color:var(--faint);font-weight:400">· nur ${ownCount} von ${totalListings} erfasst</span>` : '';
  const tip = partial
    ? `Brutto/Mt nur aus den ${ownCount} hier erfassten Inseraten — NICHT das Gesamt-Portfolio (${totalListings}).`
    : 'Brutto-Schätzung der erfassten Inserate, Tier modelliert.';
  return `<span class="pill earn" title="${tip}">≈ ${fmtCHF(est)}/Mt${scope} 🟡</span>`;
}
// Aggregierter Pickup pro Betreiber: ECHTE gebuchte Naechte (frei->belegt) seit dem
// letzten Snapshot, summiert ueber die erfassten Inserate. Messung, kein Modell —
// beantwortet "wieviele Uebernachtungen kommen wirklich rein" (Adrians Proof-of-Work).
function opPickup(o){
  let nb=0, fr=0, n=0, date=null;
  (o.own||[]).forEach(l=>{
    const pk=l.pickup; if(!pk) return;
    nb+=pk.nb||0; fr+=pk.fr||0; n++;
    if(pk.date && (!date || pk.date>date)) date=pk.date;
  });
  return n ? {nb, fr, net:nb-fr, n, date} : null;
}
function pickupPill(p){
  if(!p || (!p.nb && !p.fr)) return '';
  const tip=`Seit ${E(p.date||'?')} über ${p.n} erfasste Inserate: ${p.nb} Nächte gebucht, ${p.fr} frei geworden (netto ${p.net>=0?'+':''}${p.net}). Echte Buchungen, gemessen — kein Modell.`;
  if(p.nb>0) return `<span class="pill" style="background:rgba(74,175,114,.13);color:var(--green)" title="${tip}">▲ ${p.nb} Nächte gebucht 🟢</span>`;
  return `<span class="pill" style="color:var(--faint)" title="${tip}">▼ ${p.fr} Nächte frei 🟢</span>`;
}
function opCard(o,rank){
  const m={uid:o.uid,name:o.name,role:o.role,host_total_reviews:o.host_total_reviews,host_rating:o.host_rating,host_title:o.host_title,own_count:o.own_count,cohost_count:o.cohost_count,total_listings:o.total_listings};
  const mkts=(o.markets||[]).map(x=>`<a class="mchip" href="cockpit.html?m=${mkey(x)}">${E(x)} →</a>`).join('');
  const netbadge=o.network_id?`<span class="pill cross" title="Teil eines Co-Host-Netzwerks">im Netzwerk</span>`:'';
  const tl=o.total_listings;
  const listPill=tl
    ? `<span class="pill list" style="background:rgba(217,179,106,.13);color:var(--gold)" title="Echtes Gesamt-Portfolio Airbnb-weit, vom Host-Profil durchleuchtet">${tl} Inserate gesamt 🟢${tl>o.own_count?` <span style="color:var(--faint);font-weight:400">(${o.own_count} hier)</span>`:''}</span>`
    : `<span class="pill list">${o.own_count} Inserate</span>`;
  const sector=o.sector?`<span class="sectorchip" title="Marktsektor (aus dem Portfolio abgeleitet)">${E(o.sector)}</span>`:'';
  return `<div class="nrow"><div class="nhead" data-x>
      <span class="rank">${rank}</span>
      <span><span class="nlead">${E(o.name||'?')}</span> ${kindBadge(o)}</span>
      <span class="nmeta">
        ${o.host_total_reviews!=null?`<span class="pill rev">${o.host_total_reviews} Bew. 🟢</span>`:''}
        ${o.tier?`<span class="pill tier-${o.tier}" title="${E(o.tier_label||'')} — nach echtem Gesamt-Portfolio">${TIER_SHORT[o.tier]||o.tier}</span>`:''}
        ${listPill}
        ${objChip(o.entire_count,o.room_count)}
        ${earnPill(o.est_month_chf, o.own_count, o.total_listings)}
        ${pickupPill(opPickup(o))}
        ${netbadge}<span class="arr">▾</span>
      </span></div>
    <div class="ndet" hidden>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:2px 0 6px">${sector}</div>
      ${kernHtml(o)}
      ${dossierHtml(o)}
      <div class="mkts">${mkts}</div>
      ${memberRow(m)}
    </div></div>`;
}

function statusTag(b){
  if(b.status==='chance')  return `<span class="seg-tag chance">↳ Lücke: Nachfrage da, Angebot dünn — hier positionieren</span>`;
  if(b.status==='besetzt'&&b.dominant) return `<span class="seg-tag besetzt">🔒 ${E(b.dominant.name)} besetzt (${b.dominant.share}%${b.dominant.reviews!=null?', '+b.dominant.reviews+' Bew.':''})</span>`;
  if(b.status==='leer')    return `<span class="seg-tag leer">kein Angebot</span>`;
  return '';
}
function mktCard(mc,rank){
  const tp=(mc.top_players||[]).map(p=>`<span class="mchip" title="${p.reviews!=null?p.reviews+' Operator-Bewertungen':''}">${E(p.name||'?')} <span style="color:var(--faint)">${p.role==='lead'?'Lead ':''}${p.n_in_market}× ${p.share}%</span></span>`).join('');
  const rows=(mc.bands||[]).map(b=>`<div class="seg ${b.status}">
     <span class="seg-b">${b.band}</span>
     <span class="num">${b.n} <span style="color:var(--faint)">(${b.share}%)</span></span>
     <span class="num">${b.occ!=null?b.occ+'%':'–'}</span>
     <span class="num">${b.price!=null?fmtCHF(b.price):'–'}</span>
     <span>${statusTag(b)}</span>
   </div>`).join('');
  const ch=mc.n_chances?`<span class="pill chance">${mc.n_chances} Lücke${mc.n_chances>1?'n':''}</span>`:'';
  return `<div class="nrow"><div class="nhead" data-x>
      <span class="rank">${rank}</span>
      <span><span class="nlead">${E(mc.market)}</span><br><span class="mem-meta">${mc.total} Inserate · ${mc.n_operators} Betreiber erfasst</span></span>
      <span class="nmeta">
        <span class="pill list">Belegung Median ${mc.occ_median!=null?mc.occ_median+'%':'–'}</span>
        <span class="pill earn" title="Anteil der Inserate, die Profi-Leads gehören">Profi-Dominanz ${mc.lead_share}%</span>
        ${ch}<span class="arr">▾</span>
      </span></div>
    <div class="ndet" hidden>
      <div class="pb-lab" style="color:var(--muted);margin:8px 0 5px">Wer deckt den Markt ab</div>
      <div class="mkts">${tp||'<span class="mem-meta">für diesen Markt noch keine Co-Host-Daten (täglicher Lauf erweitert)</span>'} <a class="mchip" href="cockpit.html?m=${mkey(mc.market)}" style="border-color:var(--gold);color:var(--gold)">Cockpit →</a></div>
      <div class="pb-lab" style="color:var(--muted);margin:13px 0 5px">Segmente — wo ist Platz <span class="tier">🟡 Belegung@30 vs. Markt, abgeleitet</span></div>
      <div class="seg-head"><span>Kapazität</span><span class="num">Angebote</span><span class="num">Belegung</span><span class="num">Median-Preis</span><span>Status</span></div>
      ${rows}
    </div></div>`;
}

let MAP=null;
function renderMap(){
  const ops=Object.values(NET.operators||{});
  // alle erfassten Inserate mit Koordinaten, optional auf Suche gefiltert
  const pts=[];
  ops.forEach(o=>{
    if(Q && !((o.name||'').toLowerCase().includes(Q) || (o.markets||[]).join(' ').toLowerCase().includes(Q))) return;
    (o.own||[]).forEach(l=>{ if(l.lat&&l.lon) pts.push({o,l}); });
  });
  if(MAP){ MAP.remove(); MAP=null; }
  MAP=SwissMap.create('opmap',{view:{center:[46.95,8.3],zoom:8}});
  const col={brand:'#D9B36A',pro:'#6FA8C9',person:'#8B93A3'};
  const bounds=[];
  pts.forEach(({o,l})=>{
    const c=col[o.kind]||'#8B93A3';
    const r=o.kind==='brand'?7:o.kind==='pro'?6:4;
    const mk=L.circleMarker([l.lat,l.lon],{radius:r,color:c,weight:1.5,fillColor:c,fillOpacity:.55});
    const tl=o.total_listings?`${o.total_listings} Inserate gesamt`:`${o.own_count} erfasst`;
    mk.bindPopup(`<b>${E(o.name||'?')}</b><br>${E(o.kind_label||'')} · ${tl}<br>${E(l.market)} · ${fmtCHF(l.price_chf)} · ${l.occ30!=null?l.occ30+'%':'–'}<br><a href="cockpit.html?m=${mkey(l.market)}" style="color:var(--gold)">Cockpit →</a> · <a href="${E(l.url||('https://www.airbnb.com/rooms/'+l.id))}" target="_blank" style="color:var(--blue)">Airbnb ↗</a>`);
    mk.addTo(MAP); bounds.push([l.lat,l.lon]);
  });
  if(bounds.length) MAP.fitBounds(bounds,{padding:[30,30],maxZoom:12});
  setTimeout(()=>MAP&&MAP.invalidateSize(),60);
}
// Top-Verdiener — das Playbook (zuoberst): die Operatoren mit dem hoechsten
// est_month_chf (gekappt, summiert ueber eigene Inserate). Repraesentatives
// Inserat = das mit dem hoechsten Einzel-est; Ausreisser-Preise NICHT anzeigen.
function tvLead(o){
  const own=(o.own||[]).filter(x=>x&&x.price_chf!=null);
  return own.length ? own.slice().sort((a,b)=>(b.est_month||0)-(a.est_month||0))[0] : null;
}
function renderTopVerdiener(){
  const box=document.getElementById('topverd'); if(!box) return;
  if(!NET){ box.innerHTML=''; return; }
  const top=Object.values(NET.operators||{})
    .filter(o=>o.own_count>=1 && Math.round(o.est_month_chf||0)>0)
    .sort((a,b)=>(b.est_month_chf||0)-(a.est_month_chf||0)).slice(0,10);
  if(!top.length){ box.innerHTML=''; return; }
  const rows=top.map((o,i)=>{
    const l=tvLead(o)||{};
    const meta=[(o.markets&&o.markets[0])?E(o.markets[0]):'?',
      l.capacity?l.capacity+' Pers':null,
      (l.occ30!=null)?l.occ30+'% belegt':null,
      (l.price_chf!=null&&!l.price_outlier)?fmtCHF(l.price_chf)+'/Nacht':null,
      o.own_count?(o.own_count+(o.own_count>1?' Inserate':' Inserat')):null
    ].filter(Boolean).join(' · ');
    const sh=o.superhost?`<span class="pill" style="background:rgba(217,179,106,.13);color:var(--gold)">Superhost</span>`:'';
    const rev=o.host_total_reviews!=null?`<span class="pill rev" title="Bewertungen über das ganze Operator-Portfolio (Lebenszeit) — das schärfste Profi-Signal. Neue Bewertungen/Monat (Velocity) reifen noch.">${o.host_total_reviews} Bew. 🟢</span>`:'';
    const pk=pickupPill(opPickup(o));
    return `<div class="nrow" style="display:flex;align-items:center;gap:12px;padding:10px 14px">
        <span class="rank">${i+1}</span>
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap"><span class="nlead">${E(o.name||'?')}</span> ${kindBadge(o)} ${sh} ${rev}</div>
          <div class="nmeta" style="color:var(--muted);font-size:13px;margin-top:3px">${meta} · <span class="tvdoss" data-q="${E((o.name||'').toLowerCase())}" data-nm="${E(o.name||'')}" style="color:var(--gold);cursor:pointer">→ Playbook</span></div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
          ${earnPill(o.est_month_chf,o.own_count,o.total_listings)}
          ${pk}
        </div>
      </div>`;
  }).join('');
  box.innerHTML=`
    <div style="display:flex;align-items:center;gap:10px;margin:6px 0 4px">
      <span class="pill" style="background:rgba(217,179,106,.13);color:var(--gold);letter-spacing:.04em">STRATEGIE</span>
      <h2 class="font-d" style="margin:0;font-size:1.3rem">Top-Verdiener — das Playbook</h2>
    </div>
    <div class="sub" style="margin:0 0 10px">Wer verdient am meisten, und was macht er anders? <b style="color:var(--gold)">→ Playbook</b> durchleuchtet, wie sie es umgesetzt haben. <span style="color:var(--faint)"><b style="color:var(--amber)">Ertrag 🟡 = modelliert</b> (Preis × Belegung × 30, erfasste Inserate, Ausreisser gekappt). <b style="color:var(--green)">▲ Nächte gebucht 🟢 = gemessen</b> (frei→belegt seit letztem Snapshot) — der echte Beweis, dass die Buchungen reinkommen. Bewertungen = Lebenszeit 🟢; neue Bew./Monat (Velocity) werden seit 16.06. geloggt und reifen.</span></div>
    <div style="display:flex;flex-direction:column;gap:7px">${rows}</div>`;
  box.querySelectorAll('.tvdoss').forEach(s=>s.onclick=()=>{
    const q=s.dataset.q, nm=s.dataset.nm;
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
    const ot=document.querySelector('.tab[data-tab="ops"]'); if(ot) ot.classList.add('on');
    TAB='ops'; Q=q; const sb=document.getElementById('search'); if(sb) sb.value=nm;
    const cl=document.getElementById('crossLbl'); if(cl) cl.textContent='nur Cross-Markt';
    fillSort(); render();
    const first=document.querySelector('#results .nhead[data-x]');
    if(first){ first.click(); first.scrollIntoView({behavior:'smooth',block:'center'}); }
  });
}

function render(){
  const box=document.getElementById('results');
  if(!NET){ box.innerHTML=''; return; }
  if(TAB==='karte'){
    MAP=null;
    box.innerHTML=`<div id="opmap"></div>
      <div class="maplg"><span><i style="background:#D9B36A"></i>Verwaltungs-Marke</span><span><i style="background:#6FA8C9"></i>Gross-Operator (Person)</span><span><i style="background:#8B93A3"></i>Person/klein</span></div>
      <div class="cov" style="margin-top:6px">Jeder Punkt = ein <b>von uns erfasstes</b> Inserat (mit Koordinate) in den gescrapten Märkten. Suche oben filtert auf einen Spieler. Das echte Gesamt-Portfolio (z.B. Stephanie 241) ist grösser — die volle Geo-Karte aller Inserate folgt mit Weg B (Profil-Pagination).</div>`;
    renderMap();
    return;
  }
  let items, html;
  if(TAB==='nets'){
    items=(NET.networks||[]).slice();
    if(CROSS) items=items.filter(n=>n.cross_market);
    if(Q) items=items.filter(n=>(n.lead_name||'').toLowerCase().includes(Q) || (n.markets||[]).join(' ').toLowerCase().includes(Q) || (n.members||[]).some(m=>(m.name||'').toLowerCase().includes(Q)));
    items.sort((a,b)=>(b[SORT]||0)-(a[SORT]||0));
    html=items.map((n,i)=>netCard(n,i+1)).join('');
  }else if(TAB==='ops'){
    items=Object.values(NET.operators||{}).filter(o=>o.own_count>=1);
    if(CROSS) items=items.filter(o=>o.n_markets>=2);
    if(TIER) items=items.filter(o=>o.tier===TIER);
    if(Q) items=items.filter(o=>(o.name||'').toLowerCase().includes(Q) || (o.markets||[]).join(' ').toLowerCase().includes(Q));
    items.sort((a,b)=>(b[SORT]||0)-(a[SORT]||0));
    html=items.slice(0,120).map((o,i)=>opCard(o,i+1)).join('');
  }else if(TAB==='ch'){ // CH-weite Konkurrenz aus Branchenverzeichnis (Discovery)
    if(!COMP||!COMP.competitors){ box.innerHTML=`<div class="empty">Noch keine CH-Konkurrenz-Daten — tools/discover_competitors.py laufen lassen.</div>`; return; }
    items=Object.values(COMP.competitors).filter(c=>c.total_listings);
    if(TIER) items=items.filter(c=>c.tier===TIER);
    if(Q) items=items.filter(c=>(c.name||'').toLowerCase().includes(Q)||(c.dir_name||'').toLowerCase().includes(Q));
    items.sort((a,b)=>(b.total_listings||0)-(a.total_listings||0));
    const tc=(COMP._meta||{}).tiers||{};
    box.innerHTML=`<div class="cov" style="margin:-6px 0 12px">CH-weite Verwalter aus Branchenverzeichnis (Airbtics) · echtes Portfolio per Host-Profil-X-Ray · <b>${items.length}</b> Firmen mit Grösse · extrem ${tc.extrem||0} · big ${tc.big||0} · mittel ${tc.mittel||0} · small ${tc.small||0}. Agieren CH-weit, auch ausserhalb unserer gescrapten Märkte.</div>`
      + items.slice(0,200).map((c,i)=>compCard(c,i+1)).join('');
    return;
  }else{ // mkts — Markt-Abdeckung & Lücken
    items=Object.values(NET.market_coverage||{});
    if(CROSS) items=items.filter(m=>m.n_chances>0);
    if(Q) items=items.filter(m=>(m.market||'').toLowerCase().includes(Q) || (m.top_players||[]).some(p=>(p.name||'').toLowerCase().includes(Q)));
    items.sort((a,b)=>(b[SORT]||0)-(a[SORT]||0));
    html=items.map((m,i)=>mktCard(m,i+1)).join('');
  }
  box.innerHTML=html || `<div class="empty">Keine Treffer für die aktuelle Auswahl.</div>`;
  box.querySelectorAll('.nhead[data-x]').forEach(h=>h.onclick=()=>{
    const d=h.parentElement.querySelector('.ndet'), a=h.querySelector('.arr');
    if(d){ d.hidden=!d.hidden; if(a) a.textContent=d.hidden?'▾':'▴'; }
  });
}

async function boot(){
  try{ PROFILES=await (await fetch('data/operator-profiles.json',{cache:'no-cache'})).json(); }catch(e){ PROFILES=null; }
  try{ COMP=await (await fetch('data/competitors-ch.json',{cache:'no-cache'})).json(); }catch(e){ COMP=null; }
  try{ COMPROF=await (await fetch('data/competitor-profiles.json',{cache:'no-cache'})).json(); }catch(e){ COMPROF=null; }
  try{ NET=await (await fetch('data/operator-network.json',{cache:'no-cache'})).json(); }
  catch(e){ document.getElementById('err').textContent='data/operator-network.json fehlt — zuerst tools/build_operator_network.py laufen lassen.'; return; }
  // Abdeckung: Märkte mit Co-Host-Daten
  const mset=new Set();
  Object.values(NET.operators||{}).forEach(o=>(o.markets||[]).forEach(m=>mset.add(m)));
  const nm=(NET._meta||{}).networks||0;
  document.getElementById('cov').innerHTML=`Datenbasis: <b>${mset.size} Gemeinden</b> mit Co-Host-Daten · <b>${nm} Netzwerke</b> · ${Object.values(NET.operators||{}).filter(o=>o.own_count>=1).length} Betreiber (mit eigenem Inserat) erfasst. Der tägliche Cloud-Lauf erweitert die Basis.<br><span style="color:var(--amber)">⚠ Profi-Dichte = Untergrenze:</span> der Free-Scrape sieht keine Host-Daten (InsideAirbnb-Quervergleich: wir 0% vs. real 61% Profi-Anteil) → die echte Konkurrenz ist <b>dichter</b> als hier erfasst. <a href="datenqualitaet.html?m=kriens" style="color:var(--gold)">Methoden-Vertrauen →</a>`;
  fillSort();
  document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on')); t.classList.add('on');
    TAB=t.dataset.tab; fillSort();
    document.getElementById('crossLbl').textContent = TAB==='mkts' ? 'nur mit Lücken' : 'nur Cross-Markt';
    render();
  });
  document.getElementById('sort').onchange=e=>{SORT=e.target.value;render();};
  document.getElementById('tierSel').onchange=e=>{TIER=e.target.value;render();};
  document.getElementById('crossOnly').onchange=e=>{CROSS=e.target.checked;render();};
  document.getElementById('search').oninput=e=>{Q=e.target.value.trim().toLowerCase();render();};
  render();
  renderTopVerdiener();
  mountNetTicker();
}
boot();

// Lauf-Ticker: die grossen Spieler dieser Seite (echte Operator-Daten)
function mountNetTicker(){
  if(!window.SwissTicker||!NET) return;
  const nm=(NET._meta||{}).networks||0, ops=Object.values(NET.operators||{}).filter(o=>o.own_count>=1).length;
  const nets=(NET.networks||[]).slice().sort((a,b)=>(b.total_reviews||0)-(a.total_reviews||0)).slice(0,12);
  const items=[
    `🕸️ <b>${nm}</b> Netzwerke · <b>${ops}</b> Betreiber erfasst (Co-Host-Graph)`,
    ...nets.map(n=>`👥 ${E(n.lead_name||'?')}-Netz · <b>${n.n_members||(n.members||[]).length}</b> Pers. · ${n.own_listings||0} Inserate · <b>${(n.total_reviews||0).toLocaleString('de-CH')}</b> Bew${n.cross_market?` · <span class="up">${n.n_markets} Märkte</span>`:''}`)
  ];
  SwissTicker.mount(items,{label:'🏆 Grosse Spieler'});
}
})();
