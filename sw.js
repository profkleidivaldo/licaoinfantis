/* Service worker — Escola Sabatina Kids
   - Página e ícones: guardados na instalação (abre sem internet).
   - data/ : rede primeiro (pega lições novas) e, sem internet, a cópia guardada.
   - kids/ : lições e imagens — usa o que está guardado e atualiza em segundo plano. */
const SHELL = "kids-shell-v1";
const ASSETS = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png", "./icon.svg", "./data/kids.json"];

self.addEventListener("install", e => e.waitUntil(caches.open(SHELL).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())));
self.addEventListener("activate", e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("kids-shell-") && k !== SHELL).map(k => caches.delete(k)))).then(() => self.clients.claim())
));

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (req.mode === "navigate") {
    event.respondWith(caches.match("./index.html").then(cached => {
      const refresh = fetch(req).then(res => { if (res && res.ok && !res.redirected) { const c = res.clone(); caches.open(SHELL).then(x => x.put("./index.html", c)); } return res; }).catch(() => cached);
      return cached || refresh;
    }));
    return;
  }
  if (url.pathname.includes("/data/")) {
    event.respondWith(fetch(req).then(res => { if (res && res.ok) { const c = res.clone(); caches.open(SHELL).then(x => x.put(req, c)); } return res; }).catch(() => caches.match(req)));
    return;
  }
  if (url.pathname.includes("/kids/")) {
    event.respondWith(caches.open("kids-conteudo-v1").then(c => c.match(req).then(hit => {
      const net = fetch(req).then(res => { if (res && res.ok) c.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    })));
    return;
  }
  event.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => { if (res && res.ok) { const c = res.clone(); caches.open(SHELL).then(x => x.put(req, c)); } return res; })));
});
