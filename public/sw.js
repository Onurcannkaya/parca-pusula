const CACHE_NAME = 'parcapusula-v1';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
    // Eğer offline olduğumuzda gösterilecek bir sayfa yaparsak buraya eklenir
];

// Install Event
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log('[SW] Caching Static Assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate Event
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.filter(name => name !== CACHE_NAME).map(name => {
                    console.log('[SW] Deleting Old Cache:', name);
                    return caches.delete(name);
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch Event (KRİTİK: /api/ aramalarını asla önbellekleme)
self.addEventListener('fetch', event => {
    // API isteklerinde her zaman ağdan (network) çek, cache kullanma!
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request).catch(error => {
                console.error('[SW] API isteği başarısız (Offline olabilir):', error);

                // Offline durumunda API bir JSON hatası yollamalı
                return new Response(
                    JSON.stringify({
                        status: 'error',
                        message: 'İnternet bağlantınız koptu. Lütfen bağlanıp tekrar deneyin.'
                    }),
                    { headers: { 'Content-Type': 'application/json' } }
                );
            })
        );
        return; // Api isteği bitti, statik kısımlara inme.
    }

    // Statik dosyalar için: Önce önbelleğe (,cache'e) bak, yoksa ağdan (network) çek.
    event.respondWith(
        caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
                return cachedResponse;
            }
            return fetch(event.request).then(response => {
                // Sadece başarılı ağ yanıtlarını cache'e al
                if (!response || response.status !== 200 || response.type !== 'basic') {
                    return response;
                }
                const responseToCache = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, responseToCache);
                });
                return response;
            });
        }).catch(() => {
            // Tamamen koptuysa ve HTML isteniyorsa cached index'e dön (SPA mantığı)
            if (event.request.headers.get('accept').includes('text/html')) {
                return caches.match('/index.html');
            }
        })
    );
});
