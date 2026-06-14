// BrainyBee Service Worker - intercepts manifest requests and returns BrainyBee branding
const BRAINYBEE_MANIFEST = {
  "name": "BrainyBee - Kids Learning",
  "short_name": "BrainyBee",
  "description": "Fun quiz app for kids powered by AI",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#667eea",
  "theme_color": "#667eea",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/app/static/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/app/static/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
};

self.addEventListener('install', function(event) {
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', function(event) {
  const url = event.request.url;
  // Intercept ALL manifest requests from Streamlit
  if (url.includes('manifest') || url.includes('_stcore/manifest')) {
    event.respondWith(
      new Response(JSON.stringify(BRAINYBEE_MANIFEST), {
        status: 200,
        headers: {
          'Content-Type': 'application/manifest+json',
          'Cache-Control': 'no-cache'
        }
      })
    );
  }
});
