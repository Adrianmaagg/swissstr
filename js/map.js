/* ============================================================================
   SwissSTR — map.js  ·  SwissMap = EINE WAHRHEIT für die Leaflet-Basiskarte
   ----------------------------------------------------------------------------
   Der CARTO-Dark-Basemap-Layer war 3× kopiert (start/cockpit/netzwerk). Hier
   zentralisiert (STATUS §7) — ein Basemap-Wechsel ist ab jetzt eine Stelle.

   Die Marker-/Popup-/Grenzen-Logik bleibt BEWUSST seiten-lokal (jede Karte zeigt
   anderes: Gemeinde-Zentrum, Operator-Punkte, Markt-Pins). Nur das Gerüst
   (L.map + Tile-Layer + scrollWheelZoom-Default) ist geteilt.

   tileOpts ist überschreibbar, weil die Seiten leicht gedriftet sind (start nutzt
   subdomains:'abcd' + eine eigene Attribution-Schreibweise) — output-neutral
   übernommen statt zwangsvereinheitlicht.

   Reine Factory, kein State. Setzt voraus, dass Leaflet (L) geladen ist, wenn
   create() AUFGERUFEN wird (nicht beim Laden des Moduls).
   ========================================================================== */
(function (root) {
  'use strict';

  var TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  var TILE_DEFAULTS = { attribution: '© OpenStreetMap, © CARTO', maxZoom: 19 };

  // create(elementId, { view:{center,zoom}, tileOpts }) → Leaflet-Map mit Dark-Basemap.
  function create(elementId, opts) {
    opts = opts || {};
    var m = L.map(elementId, { scrollWheelZoom: false });
    if (opts.view) m.setView(opts.view.center, opts.view.zoom);
    L.tileLayer(TILE_URL, Object.assign({}, TILE_DEFAULTS, opts.tileOpts)).addTo(m);
    return m;
  }

  root.SwissMap = { TILE_URL: TILE_URL, TILE_DEFAULTS: TILE_DEFAULTS, create: create };
})(window);
