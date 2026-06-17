// ============================================================================
// SwissSTR — Lauf-Ticker (News-Marquee unter dem Header)
// ----------------------------------------------------------------------------
// Wiederverwendbar, CSS selbst-injiziert. Jede Seite baut ihre EIGENEN Items
// aus echten Daten und ruft SwissTicker.mount(items).
//   items = Array von HTML-Strings (Seite ist fürs Escapen ihrer Daten zuständig).
// Optional: SwissTicker.mount(items, { label:'📰 …' }).
// Nahtlose Endlosschleife (Items doppelt), Pause bei Hover, Tempo ~ konstante px/s.
// ============================================================================
(function () {
  'use strict';
  let injected = false;
  function injectCSS() {
    if (injected) return; injected = true;
    const css = `
      .swt{overflow:hidden;border-bottom:1px solid var(--lineS,#161D2B);background:rgba(14,18,25,.6);
        position:relative;-webkit-mask-image:linear-gradient(90deg,transparent,#000 4%,#000 96%,transparent);
        mask-image:linear-gradient(90deg,transparent,#000 4%,#000 96%,transparent);}
      .swt-track{display:inline-flex;align-items:center;white-space:nowrap;padding:7px 0;
        animation:swt-scroll linear infinite;will-change:transform;}
      .swt:hover .swt-track{animation-play-state:paused;}
      .swt-i{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--muted,#8B93A3);
        font-family:'Inter',system-ui,sans-serif;padding:0 18px;border-right:1px solid var(--lineS,#161D2B);}
      .swt-i b{color:var(--text,#EDEAE2);font-weight:700;font-variant-numeric:tabular-nums;}
      .swt-i .hot{color:var(--gold,#D9B36A);font-weight:700;}
      .swt-i .up{color:var(--green,#3FAE7C);font-weight:700;}
      .swt-lab{display:inline-flex;align-items:center;gap:5px;font-size:10.5px;font-weight:700;
        text-transform:uppercase;letter-spacing:.06em;color:var(--gold,#D9B36A);padding:0 16px 0 2px;
        border-right:1px solid var(--lineS,#161D2B);white-space:nowrap;}
      @keyframes swt-scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
      @media(prefers-reduced-motion:reduce){.swt-track{animation:none;}}
    `;
    const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s);
  }

  function mount(items, opts) {
    if (!Array.isArray(items) || !items.length) return;
    injectCSS();
    opts = opts || {};
    const header = document.querySelector('header.top') || document.querySelector('header');
    if (!header) return;
    // bestehenden Ticker (z.B. bei Re-Mount) entfernen
    const old = document.getElementById('swTicker'); if (old) old.remove();

    const lab = opts.label ? `<span class="swt-lab">${opts.label}</span>` : '';
    const one = items.map(h => `<span class="swt-i">${h}</span>`).join('');
    const block = lab + one;
    const bar = document.createElement('div');
    bar.className = 'swt'; bar.id = 'swTicker';
    // Items DOPPELT → translateX(-50%) ergibt nahtlose Schleife
    bar.innerHTML = `<div class="swt-track">${block}${block}</div>`;
    // Tempo: ~ konstante Geschwindigkeit, proportional zur Anzahl Items
    const dur = Math.max(22, items.length * 4.2);
    bar.querySelector('.swt-track').style.animationDuration = dur + 's';
    header.insertAdjacentElement('afterend', bar);
  }

  window.SwissTicker = { mount };
})();
