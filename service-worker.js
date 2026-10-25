const CACHE='pragati-static-v1';
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/manifest.webmanifest','/static/icon.svg']))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
// Do not cache authenticated pages or API responses: prevents private study data
// from being stored in a shared-device cache. App functions require connectivity.
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;const u=new URL(e.request.url);if(u.origin!==location.origin||u.pathname.startsWith('/api/')||u.pathname.startsWith('/auth/'))return;if(u.pathname.startsWith('/static/')||u.pathname==='/manifest.webmanifest'){e.respondWith(caches.match(e.request).then(c=>c||fetch(e.request)));}});
