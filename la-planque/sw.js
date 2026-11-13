/* La Planque : mode hors ligne simple. Réseau d'abord, copie locale si pas de connexion.
   Ne touche qu'aux pages du site (pas aux données Supabase) ; ses caches commencent par "planque-". */
const C = "planque-v1";
const LIB = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/";
self.addEventListener("install", e => {
  e.waitUntil(caches.open(C).then(c => c.addAll(["./", "./manifest.webmanifest", "./icon-192.png"])).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("planque-") && k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const r = e.request;
  if (r.method !== "GET") return;
  const u = new URL(r.url), scope = new URL(self.registration.scope);
  const mine = u.origin === scope.origin && u.pathname.startsWith(scope.pathname);
  if (!mine && !u.href.startsWith(LIB)) return;
  e.respondWith(fetch(r).then(res => {
    if (res.ok && (res.type === "basic" || res.type === "cors")) { const cp = res.clone(); caches.open(C).then(c => c.put(r, cp)); }
    return res;
  }).catch(() => caches.match(r, { ignoreSearch: true }).then(m => m || (r.mode === "navigate" ? caches.match("./") : Response.error()))));
});
