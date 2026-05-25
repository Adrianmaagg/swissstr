// SwissSTR static data — loaded as a regular <script> before the main inline script.
// Markets are the 81 Swiss towns the prototype covers. BFS HESTA data is layered on
// at runtime via fetch('data/hesta-snapshot.json') (see loadHesta in index.html).
//
// x/y are only set for markets shown on the main map; the rest appear in search
// and the detail view only.

const markets = [
  // ====== CITIES ======
  { name: "Zürich",         canton: "ZH", x: 470, y: 195, listings: 1720, adr: 215, occ: 72, revpar: 155, grade: "B", profile: "city",    peak: "Juli",    tags: ["Stadt","Business","Kunst"], cat: "Stadt" },
  { name: "Genève",         canton: "GE", x: 130, y: 330, listings: 1178, adr: 138, occ: 73, revpar: 100, grade: "C", profile: "city",    peak: "Juni",    tags: ["Stadt","UN","Events","90-Tage-Cap"], cat: "Stadt" },
  { name: "Basel",          canton: "BS", x: 320, y: 130, listings: 922,  adr: 144, occ: 60, revpar: 86,  grade: "C", profile: "events",  peak: "April",   tags: ["Stadt","Art Basel"], cat: "Stadt" },
  { name: "Bern",           canton: "BE", x: 330, y: 230, listings: 520,  adr: 165, occ: 62, revpar: 102, grade: "C", profile: "city",    peak: "Juli",    tags: ["Stadt","UNESCO","Bundesstadt"], cat: "Stadt" },
  { name: "Lausanne",       canton: "VD",                listings: 680,  adr: 162, occ: 68, revpar: 110, grade: "C", profile: "city",    peak: "Juni",    tags: ["Stadt","Lac Léman","IOC"], cat: "Stadt" },
  { name: "Luzern",         canton: "LU", x: 425, y: 235, listings: 700,  adr: 195, occ: 65, revpar: 127, grade: "C", profile: "summer",  peak: "Juli",    tags: ["Stadt","See","Asien-Tourismus","90-Tage-Cap"], cat: "Stadt" },
  { name: "Winterthur",     canton: "ZH",                listings: 215,  adr: 132, occ: 58, revpar: 77,  grade: "D", profile: "city",    peak: "Juni",    tags: ["Stadt"], cat: "Stadt" },
  { name: "St. Gallen",     canton: "SG",                listings: 245,  adr: 128, occ: 56, revpar: 72,  grade: "D", profile: "city",    peak: "Juli",    tags: ["Stadt","Stiftsbibliothek","UNESCO"], cat: "Stadt" },
  { name: "Neuchâtel",      canton: "NE",                listings: 165,  adr: 138, occ: 55, revpar: 76,  grade: "D", profile: "summer",  peak: "Juli",    tags: ["See","Universität"], cat: "Stadt" },
  { name: "Fribourg",       canton: "FR",                listings: 142,  adr: 125, occ: 54, revpar: 68,  grade: "D", profile: "summer",  peak: "August",  tags: ["Mittelalter","zweisprachig"], cat: "Stadt" },
  { name: "Schaffhausen",   canton: "SH",                listings: 195,  adr: 145, occ: 60, revpar: 87,  grade: "C", profile: "summer",  peak: "Juli",    tags: ["Rheinfall","Altstadt"], cat: "Stadt" },
  { name: "Sion",           canton: "VS",                listings: 178,  adr: 132, occ: 56, revpar: 74,  grade: "D", profile: "dual",    peak: "Aug+Feb", tags: ["Wallis","Wein","Hauptort"], cat: "Stadt" },
  { name: "Chur",           canton: "GR",                listings: 198,  adr: 145, occ: 58, revpar: 84,  grade: "C", profile: "dual",    peak: "Aug+Feb", tags: ["Älteste Stadt CH","Bündnerland"], cat: "Stadt" },
  { name: "Bellinzona",     canton: "TI",                listings: 122,  adr: 128, occ: 54, revpar: 69,  grade: "D", profile: "summer",  peak: "August",  tags: ["UNESCO","drei Burgen"], cat: "Stadt" },
  { name: "Lugano",         canton: "TI", x: 480, y: 380, listings: 1362, adr: 142, occ: 56, revpar: 80,  grade: "C", profile: "summer",  peak: "August",  tags: ["See","Mediterran"], cat: "Stadt" },

  // ====== ALPINE WINTER RESORTS ======
  { name: "Zermatt",        canton: "VS", x: 350, y: 320, listings: 836, adr: 325, occ: 73, revpar: 237, grade: "A", profile: "winter", peak: "Februar", tags: ["Ski","Matterhorn","Auto-frei","Zweitwohnungs-Cap"], cat: "Alpen" },
  { name: "Verbier",        canton: "VS", x: 250, y: 330, listings: 720, adr: 480, occ: 60, revpar: 288, grade: "A", profile: "winter", peak: "Februar", tags: ["Ski","4 Vallées","Premium"], cat: "Alpen" },
  { name: "St. Moritz",     canton: "GR", x: 580, y: 295, listings: 620, adr: 410, occ: 58, revpar: 238, grade: "A", profile: "winter", peak: "Januar",  tags: ["Ski","Luxus","White Turf","Engadin"], cat: "Alpen" },
  { name: "Davos",          canton: "GR", x: 555, y: 240, listings: 540, adr: 290, occ: 55, revpar: 160, grade: "B", profile: "winter", peak: "Januar",  tags: ["Ski","WEF","Kongress"], cat: "Alpen" },
  { name: "Andermatt",      canton: "UR", x: 440, y: 270, listings: 310, adr: 395, occ: 58, revpar: 229, grade: "A", profile: "winter", peak: "Februar", tags: ["Ski","Resort-Expansion","Vail"], cat: "Alpen" },
  { name: "Saas-Fee",       canton: "VS",                listings: 480, adr: 295, occ: 65, revpar: 192, grade: "A", profile: "winter", peak: "Februar", tags: ["Ski","Gletscher","Auto-frei"], cat: "Alpen" },
  { name: "Gstaad",         canton: "BE",                listings: 410, adr: 580, occ: 55, revpar: 319, grade: "A", profile: "winter", peak: "Februar", tags: ["Ski","Luxus","Promis"], cat: "Alpen" },
  { name: "Klosters",       canton: "GR",                listings: 290, adr: 360, occ: 56, revpar: 202, grade: "B", profile: "winter", peak: "Februar", tags: ["Ski","Royals"], cat: "Alpen" },
  { name: "Arosa",          canton: "GR",                listings: 320, adr: 280, occ: 58, revpar: 162, grade: "B", profile: "winter", peak: "Februar", tags: ["Ski","Familien"], cat: "Alpen" },
  { name: "Lenzerheide",    canton: "GR",                listings: 285, adr: 265, occ: 56, revpar: 148, grade: "B", profile: "dual",   peak: "Feb+Aug", tags: ["Ski","Bike","Schweizermeile"], cat: "Alpen" },
  { name: "Flims",          canton: "GR",                listings: 340, adr: 240, occ: 60, revpar: 144, grade: "B", profile: "dual",   peak: "Aug+Feb", tags: ["Ski","Caumasee","Wandern"], cat: "Alpen" },
  { name: "Laax",           canton: "GR",                listings: 295, adr: 235, occ: 62, revpar: 146, grade: "B", profile: "winter", peak: "Februar", tags: ["Ski","Snowboard-Mekka","Freestyle"], cat: "Alpen" },
  { name: "Adelboden",      canton: "BE",                listings: 365, adr: 250, occ: 58, revpar: 145, grade: "B", profile: "winter", peak: "Februar", tags: ["Ski","Weltcup-Slalom"], cat: "Alpen" },
  { name: "Engelberg",      canton: "OW",                listings: 420, adr: 245, occ: 64, revpar: 157, grade: "B", profile: "winter", peak: "Februar", tags: ["Ski","Titlis","Asien-Tourismus"], cat: "Alpen" },
  { name: "Wengen",         canton: "BE",                listings: 285, adr: 295, occ: 62, revpar: 183, grade: "A", profile: "dual",   peak: "Aug+Jan", tags: ["Ski","Lauberhorn","Auto-frei"], cat: "Alpen" },
  { name: "Mürren",         canton: "BE",                listings: 165, adr: 285, occ: 60, revpar: 171, grade: "B", profile: "dual",   peak: "Aug+Feb", tags: ["Ski","Schilthorn","Auto-frei"], cat: "Alpen" },
  { name: "Champéry",       canton: "VS",                listings: 240, adr: 285, occ: 56, revpar: 160, grade: "B", profile: "winter", peak: "Februar", tags: ["Ski","Portes du Soleil"], cat: "Alpen" },
  { name: "Crans-Montana",  canton: "VS", x: 280, y: 320, listings: 480, adr: 310, occ: 54, revpar: 167, grade: "B", profile: "dual",   peak: "Feb+Jul", tags: ["Ski","Golf","Plateau"], cat: "Alpen" },
  { name: "Leukerbad",      canton: "VS",                listings: 220, adr: 195, occ: 60, revpar: 117, grade: "C", profile: "winter", peak: "Februar", tags: ["Ski","Thermalbad"], cat: "Alpen" },
  { name: "Pontresina",     canton: "GR",                listings: 175, adr: 295, occ: 56, revpar: 165, grade: "B", profile: "winter", peak: "Februar", tags: ["Ski","Engadin","Langlauf"], cat: "Alpen" },
  { name: "Celerina",       canton: "GR",                listings: 165, adr: 285, occ: 55, revpar: 157, grade: "B", profile: "winter", peak: "Februar", tags: ["Ski","Engadin","ruhig"], cat: "Alpen" },
  { name: "Scuol",          canton: "GR",                listings: 195, adr: 215, occ: 56, revpar: 120, grade: "C", profile: "dual",   peak: "Aug+Feb", tags: ["Ski","Thermalbad","Unterengadin"], cat: "Alpen" },
  { name: "Samnaun",        canton: "GR",                listings: 145, adr: 265, occ: 58, revpar: 154, grade: "B", profile: "winter", peak: "Februar", tags: ["Ski","Zollfrei","Ischgl-Anschluss"], cat: "Alpen" },

  // ====== ALPINE SUMMER / BERNESE OBERLAND ======
  { name: "Interlaken",     canton: "BE", x: 360, y: 260, listings: 780, adr: 340, occ: 68, revpar: 231, grade: "A", profile: "summer", peak: "August",  tags: ["See","Asien","US-Tourismus"], cat: "Alpen" },
  { name: "Lauterbrunnen",  canton: "BE", x: 380, y: 285, listings: 542, adr: 440, occ: 52, revpar: 230, grade: "A", profile: "summer", peak: "Juli",    tags: ["Wasserfälle","Instagram","Tal"], cat: "Alpen" },
  { name: "Grindelwald",    canton: "BE", x: 395, y: 275, listings: 610, adr: 360, occ: 64, revpar: 230, grade: "A", profile: "dual",   peak: "Aug+Feb", tags: ["Eiger","Ski","Wandern","First"], cat: "Alpen" },
  { name: "Brienz",         canton: "BE",                listings: 195, adr: 245, occ: 58, revpar: 142, grade: "B", profile: "summer", peak: "Juli",    tags: ["See","Holzschnitzerei","Rothorn"], cat: "See" },
  { name: "Spiez",          canton: "BE",                listings: 145, adr: 198, occ: 60, revpar: 119, grade: "C", profile: "summer", peak: "August",  tags: ["Thunersee","Schloss"], cat: "See" },
  { name: "Thun",           canton: "BE",                listings: 240, adr: 175, occ: 62, revpar: 109, grade: "C", profile: "summer", peak: "Juli",    tags: ["See","Schloss"], cat: "See" },
  { name: "Meiringen",      canton: "BE",                listings: 165, adr: 195, occ: 56, revpar: 109, grade: "C", profile: "summer", peak: "Juli",    tags: ["Sherlock Holmes","Reichenbachfall"], cat: "Alpen" },
  { name: "Riederalp",      canton: "VS",                listings: 195, adr: 235, occ: 58, revpar: 136, grade: "B", profile: "dual",   peak: "Aug+Feb", tags: ["UNESCO Aletsch","Gletscher","Auto-frei"], cat: "Alpen" },
  { name: "Bettmeralp",     canton: "VS",                listings: 175, adr: 245, occ: 58, revpar: 142, grade: "B", profile: "dual",   peak: "Aug+Feb", tags: ["Auto-frei","Aletsch","Bergsee"], cat: "Alpen" },

  // ====== LAKES / TICINO ======
  { name: "Locarno",        canton: "TI",                listings: 480, adr: 165, occ: 60, revpar: 99,  grade: "C", profile: "summer", peak: "August",  tags: ["Lago Maggiore","Filmfestival"], cat: "See" },
  { name: "Ascona",         canton: "TI",                listings: 320, adr: 215, occ: 62, revpar: 133, grade: "B", profile: "summer", peak: "August",  tags: ["Lago Maggiore","Premium"], cat: "See" },
  { name: "Mendrisio",      canton: "TI",                listings: 95,  adr: 138, occ: 52, revpar: 72,  grade: "D", profile: "summer", peak: "August",  tags: ["Designer Outlet"], cat: "Stadt" },
  { name: "Montreux",       canton: "VD",                listings: 425, adr: 195, occ: 64, revpar: 125, grade: "B", profile: "summer", peak: "Juli",    tags: ["Jazz Festival","Lac Léman","Riviera"], cat: "See" },
  { name: "Vevey",          canton: "VD",                listings: 215, adr: 168, occ: 62, revpar: 104, grade: "C", profile: "summer", peak: "Juli",    tags: ["Chaplin","Lac Léman","Nestlé"], cat: "See" },
  { name: "Nyon",           canton: "VD",                listings: 125, adr: 158, occ: 60, revpar: 95,  grade: "C", profile: "summer", peak: "Juli",    tags: ["Lac Léman","UEFA"], cat: "See" },
  { name: "Morges",         canton: "VD",                listings: 98,  adr: 152, occ: 58, revpar: 88,  grade: "C", profile: "summer", peak: "Juli",    tags: ["Lac Léman","Tulpenfest"], cat: "See" },
  { name: "Vitznau",        canton: "LU",                listings: 88,  adr: 245, occ: 60, revpar: 147, grade: "B", profile: "summer", peak: "Juli",    tags: ["Vierwaldstättersee","Premium","Park Hotel"], cat: "See" },
  { name: "Weggis",         canton: "LU",                listings: 145, adr: 198, occ: 60, revpar: 119, grade: "C", profile: "summer", peak: "Juli",    tags: ["Vierwaldstättersee","Rigi"], cat: "See" },
  { name: "Brunnen",        canton: "SZ",                listings: 122, adr: 178, occ: 58, revpar: 103, grade: "C", profile: "summer", peak: "Juli",    tags: ["Vierwaldstättersee","Mythen"], cat: "See" },
  { name: "Rapperswil",     canton: "SG",                listings: 95,  adr: 168, occ: 60, revpar: 101, grade: "C", profile: "summer", peak: "Juli",    tags: ["Zürichsee","Schloss","Rosen"], cat: "See" },
  { name: "Stein am Rhein", canton: "SH",                listings: 78,  adr: 178, occ: 58, revpar: 103, grade: "C", profile: "summer", peak: "Juli",    tags: ["Mittelalter","Rhein","Fassadenmalerei"], cat: "Stadt" },
  { name: "Appenzell",      canton: "AI",                listings: 145, adr: 165, occ: 60, revpar: 99,  grade: "C", profile: "dual",   peak: "Aug+Feb", tags: ["Folklore","Säntis","Käse"], cat: "Alpen" },

  // ====== KLEINERE STÄDTE / REGIONEN ======
  { name: "Baden",          canton: "AG",                listings: 165, adr: 148, occ: 60, revpar: 89,  grade: "C", profile: "city",   peak: "Juli",    tags: ["Thermalbad","Bäderquartier","S-Bahn ZH"], cat: "Stadt" },
  { name: "Aarau",          canton: "AG",                listings: 110, adr: 135, occ: 56, revpar: 76,  grade: "D", profile: "city",   peak: "Juni",    tags: ["Hauptort AG","Altstadt"], cat: "Stadt" },
  { name: "Zug",            canton: "ZG",                listings: 145, adr: 215, occ: 64, revpar: 138, grade: "B", profile: "city",   peak: "Juni",    tags: ["Steueroase","Crypto Valley","Zugersee"], cat: "Stadt" },
  { name: "Solothurn",      canton: "SO",                listings: 105, adr: 142, occ: 58, revpar: 82,  grade: "D", profile: "city",   peak: "Juli",    tags: ["Barockstadt","Aare"], cat: "Stadt" },
  { name: "Olten",          canton: "SO",                listings: 75,  adr: 122, occ: 54, revpar: 66,  grade: "D", profile: "city",   peak: "Juni",    tags: ["Bahnknoten"], cat: "Stadt" },
  { name: "Lenk",           canton: "BE",                listings: 195, adr: 235, occ: 56, revpar: 132, grade: "B", profile: "dual",   peak: "Feb+Aug", tags: ["Ski","Wellness","Simmental"], cat: "Alpen" },
  { name: "Frutigen",       canton: "BE",                listings: 95,  adr: 175, occ: 54, revpar: 95,  grade: "C", profile: "summer", peak: "August",  tags: ["Tropenhaus","Kandertal"], cat: "Alpen" },
  { name: "Disentis",       canton: "GR",                listings: 165, adr: 215, occ: 56, revpar: 120, grade: "C", profile: "winter", peak: "Februar", tags: ["Ski","Kloster","Surselva"], cat: "Alpen" },
  { name: "Sörenberg",      canton: "LU",                listings: 145, adr: 195, occ: 54, revpar: 105, grade: "C", profile: "winter", peak: "Februar", tags: ["Ski","Entlebuch","Familie"], cat: "Alpen" },
  { name: "Wildhaus",       canton: "SG",                listings: 125, adr: 198, occ: 55, revpar: 109, grade: "C", profile: "winter", peak: "Februar", tags: ["Ski","Toggenburg","Säntis"], cat: "Alpen" },
  { name: "Beatenberg",     canton: "BE",                listings: 145, adr: 215, occ: 58, revpar: 125, grade: "B", profile: "summer", peak: "August",  tags: ["Thunersee-Sicht","Niederhorn"], cat: "Alpen" },
  { name: "Beckenried",     canton: "NW",                listings: 78,  adr: 178, occ: 58, revpar: 103, grade: "C", profile: "summer", peak: "Juli",    tags: ["Vierwaldstättersee","Klewenalp"], cat: "See" },
  { name: "Romanshorn",     canton: "TG",                listings: 85,  adr: 132, occ: 56, revpar: 74,  grade: "D", profile: "summer", peak: "August",  tags: ["Bodensee","Hafen"], cat: "See" },
  { name: "Kreuzlingen",    canton: "TG",                listings: 95,  adr: 128, occ: 54, revpar: 69,  grade: "D", profile: "summer", peak: "Juli",    tags: ["Bodensee","Konstanz"], cat: "See" },
  { name: "Frauenfeld",     canton: "TG",                listings: 65,  adr: 118, occ: 52, revpar: 61,  grade: "D", profile: "city",   peak: "Juli",    tags: ["Hauptort TG"], cat: "Stadt" },
  { name: "Glarus",         canton: "GL",                listings: 95,  adr: 158, occ: 54, revpar: 85,  grade: "D", profile: "dual",   peak: "Aug+Feb", tags: ["Linthal","Berge"], cat: "Alpen" },
  { name: "Altdorf",        canton: "UR",                listings: 78,  adr: 142, occ: 56, revpar: 80,  grade: "D", profile: "summer", peak: "August",  tags: ["Tell","Gotthard"], cat: "Stadt" },
  { name: "Brig",           canton: "VS",                listings: 145, adr: 165, occ: 58, revpar: 96,  grade: "C", profile: "dual",   peak: "Aug+Feb", tags: ["Simplon","Stockalper"], cat: "Stadt" },
  { name: "Sierre",         canton: "VS",                listings: 95,  adr: 138, occ: 56, revpar: 77,  grade: "D", profile: "summer", peak: "Juli",    tags: ["Wein","Sonnenstadt"], cat: "Stadt" },
  { name: "Martigny",       canton: "VS",                listings: 88,  adr: 142, occ: 58, revpar: 82,  grade: "D", profile: "summer", peak: "Juli",    tags: ["Wein","Fondation Gianadda"], cat: "Stadt" },
  { name: "Yverdon",        canton: "VD",                listings: 95,  adr: 132, occ: 56, revpar: 74,  grade: "D", profile: "summer", peak: "Juli",    tags: ["Thermalbad","See"], cat: "See" },
];

// Seasonal multipliers (12 months × profile). Mean ≈ 1.0.
// Real BFS seasonality is preferred at runtime (m.bfs.seasonality), this is the fallback.
const profiles = {
  winter: [1.32, 1.50, 1.27, 0.75, 0.54, 0.65, 0.86, 0.91, 0.74, 0.53, 0.44, 1.22],
  summer: [0.56, 0.62, 0.71, 0.87, 1.06, 1.24, 1.50, 1.59, 1.25, 0.94, 0.63, 0.71],
  dual:   [1.18, 1.32, 1.05, 0.72, 0.78, 0.90, 1.20, 1.30, 0.98, 0.70, 0.65, 1.10],
  city:   [0.91, 0.98, 1.02, 1.07, 1.12, 1.19, 1.26, 1.23, 1.16, 1.07, 0.91, 1.00],
  events: [0.85, 0.87, 1.00, 1.78, 0.95, 0.92, 0.88, 0.92, 1.04, 0.95, 1.15, 0.92],
};

const cantonNames = {
  ZH: "Zürich", BE: "Bern", LU: "Luzern", UR: "Uri", SZ: "Schwyz",
  OW: "Obwalden", NW: "Nidwalden", GL: "Glarus", ZG: "Zug", FR: "Freiburg",
  SO: "Solothurn", BS: "Basel-Stadt", BL: "Basel-Land", SH: "Schaffhausen",
  AR: "Appenzell-A.", AI: "Appenzell-I.", SG: "St. Gallen", GR: "Graubünden",
  AG: "Aargau", TG: "Thurgau", TI: "Tessin", VD: "Waadt", VS: "Wallis",
  NE: "Neuenburg", GE: "Genf", JU: "Jura",
};
