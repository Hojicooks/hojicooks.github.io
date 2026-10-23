// Cabine Miroir : réseau d'abord pour l'app, copie locale si le téléphone est hors ligne.
// Change le numéro de version après une mise à jour pour vider l'ancienne copie.
const CACHE = 'cabine-v6-2';
// Bibliothèques et modèles en version figée (client Gradio, détection du corps) :
// gardés dans un cache à part, qui survit aux mises à jour, pour ne pas les retélécharger.
const CDN_CACHE = 'cabine-cdn-v1';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './icon-maskable-512.png',
  './apple-touch-icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE && k !== CDN_CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function isPinnedCdn(url) {
  if (url.hostname === 'cdn.jsdelivr.net') return /@\d+\.\d+\.\d+/.test(url.pathname);
  return url.hostname === 'storage.googleapis.com' && url.pathname.startsWith('/mediapipe-models/');
}

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  if (isPinnedCdn(url)) {
    event.respondWith(
      caches.open(CDN_CACHE).then(cache =>
        cache.match(req).then(hit => hit || fetch(req).then(res => {
          if (res && res.ok) cache.put(req, res.clone()).catch(() => {});
          return res;
        }))
      )
    );
    return;
  }

  const isFont = url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com';
  if (url.origin !== self.location.origin && !isFont) return;

  event.respondWith(
    fetch(req)
      .then(res => {
        if (res && (res.ok || res.type === 'opaque')) {
          const copy = res.clone();
          caches.open(CACHE).then(cache => cache.put(req, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() =>
        caches.match(req).then(hit => {
          if (hit) return hit;
          if (req.mode === 'navigate') return caches.match('./index.html').then(r => r || Response.error());
          return Response.error();
        })
      )
  );
});
