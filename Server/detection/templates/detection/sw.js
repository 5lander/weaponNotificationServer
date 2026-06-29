/* Service Worker - Weapon Detection System (Web Push)
 * Servido desde /sw.js (scope raíz) por detection.push_views.service_worker.
 */

// Recibe un mensaje push y muestra la notificación del sistema.
self.addEventListener('push', function (event) {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { title: 'Alerta de seguridad', body: event.data ? event.data.text() : '' };
  }

  const title = data.title || '🚨 Alerta de seguridad';
  const options = {
    body: data.body || 'Se ha detectado un arma en el sistema de vigilancia.',
    icon: data.icon || '/static/img/icon.png',
    badge: data.badge || '/static/img/badge.png',
    tag: data.tag || 'weapon-alert',
    requireInteraction: true,
    data: { url: data.url || '/' }
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

// Al hacer clic en la notificación, enfoca o abre la pestaña de la alerta.
self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (windowClients) {
      for (const client of windowClients) {
        if (client.url.indexOf(targetUrl) !== -1 && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
