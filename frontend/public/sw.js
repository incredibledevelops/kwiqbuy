// A minimal service worker to enable PWA installation
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Pass-through fetch for now (no offline caching yet)
  event.respondWith(fetch(event.request));
});