/* Service worker do Escola Sabatina Kids: deixa o app abrir sem internet.
   - Páginas e ícones: guardados na instalação.
   - Dados (data/): rede primeiro (pega lições novas); sem internet usa a cópia guardada.
   - Imagens: guardadas na primeira vez que aparecem. */
const SHELL = "kids-shell-v1";
const ASSETS = ["./", "./index.html", "./manifest.webmanifest", "./config.js", "./icon.svg",
  "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png", "./icon-maskable-512.png", "./data/infantil/index.json"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(SHELL).then(c => Promise.all(ASSETS.map(a => c.add(a).catch(() => {})))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("kids-shell-") && k !== SHELL).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const isImg = /\.(png|jpe?g|webp|gif|svg)$/i.test(url.pathname);
  if (url.origin !== self.location.origin) {
    if (isImg) e.respondWith(caches.open("kids-img-v1").then(c => c.match(req).then(hit => hit || fetch(req).then(r => { if (r && (r.ok || r.type === "opaque")) c.put(req, r.clone()); return r; }).catch(() => hit))));
    return;
  }
  if (url.pathname.includes("/data/") || url.pathname.endsWith("/config.js")) {
    e.respondWith(fetch(req).then(r => { const cp = r.clone(); caches.open(SHELL).then(c => c.put(req, cp)); return r; }).catch(() => caches.match(req)));
    return;
  }
  if (isImg && url.pathname.includes("/img/")) {
    e.respondWith(caches.open("kids-img-v1").then(c => c.match(req).then(hit => hit || fetch(req).then(r => { if (r.ok) c.put(req, r.clone()); return r; }))));
    return;
  }
  e.respondWith(caches.match(req, { ignoreSearch: true }).then(hit => hit || fetch(req).catch(() => caches.match("./index.html"))));
});
