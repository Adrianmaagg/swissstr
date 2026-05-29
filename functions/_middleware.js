// functions/_middleware.js — Passwort-Schutz fuer SwissSTR auf Cloudflare Pages.
//
// Identische Logik wie bei DiplomAI: alle Requests durchlaufen Basic Auth,
// das Passwort wird aus der Cloudflare-Pages-Env-Variable ACCESS_PASSWORD
// gelesen.
//
// Konfiguration:
//   - Cloudflare Pages -> swissstr -> Settings -> Variables and Secrets
//   - Variable: ACCESS_PASSWORD, Type: Secret, Value: <dein-passwort>
//
// Verhalten:
//   - Ohne ACCESS_PASSWORD: zeigt Setup-Hinweis-Page (App ist gesperrt).
//   - Mit ACCESS_PASSWORD: HTTP Basic Auth, Browser fragt 1x nach Login.

const REALM = 'SwissSTR';

export async function onRequest(context) {
  const { request, env, next } = context;
  const expectedPassword = env.ACCESS_PASSWORD;

  if (!expectedPassword) {
    return new Response(_setupPage(), {
      status: 503,
      headers: { 'content-type': 'text/html; charset=utf-8' }
    });
  }

  const auth = request.headers.get('Authorization') || '';
  if (!auth.startsWith('Basic ')) {
    return _challenge();
  }

  let decoded;
  try {
    decoded = atob(auth.slice(6));
  } catch (_) {
    return _challenge();
  }
  const idx = decoded.indexOf(':');
  if (idx < 0) return _challenge();
  const password = decoded.slice(idx + 1);

  if (!_safeEqual(password, expectedPassword)) {
    return _challenge();
  }

  return next();
}

function _challenge() {
  return new Response('Authentication required.', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="' + REALM + '", charset="UTF-8"',
      'content-type': 'text/plain; charset=utf-8'
    }
  });
}

function _safeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}

function _setupPage() {
  return '<!DOCTYPE html><html lang="de"><head>' +
    '<meta charset="utf-8"><title>SwissSTR - Setup noetig</title>' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<style>body{font-family:-apple-system,sans-serif;max-width:560px;margin:60px auto;padding:0 24px;color:#222;line-height:1.55}' +
    'h1{color:#DA291C}code{background:#f0f0f0;padding:2px 6px;border-radius:4px}ol li{margin:8px 0}</style>' +
    '</head><body>' +
    '<h1>SwissSTR - Passwort fehlt</h1>' +
    '<p>Diese App ist passwort-geschuetzt, aber das Passwort wurde noch nicht gesetzt.</p>' +
    '<ol>' +
    '<li>Cloudflare-Dashboard oeffnen.</li>' +
    '<li>Pages -> <strong>swissstr</strong> -> <strong>Settings</strong>.</li>' +
    '<li><strong>Variables and Secrets</strong> -> <strong>Add</strong>.</li>' +
    '<li>Variable name: <code>ACCESS_PASSWORD</code>, Type: <strong>Secret</strong>, Value: dein-passwort.</li>' +
    '<li>Auf <strong>Save</strong> klicken, dann neuen Deploy triggern.</li>' +
    '</ol>' +
    '</body></html>';
}
