/* push.js - Suscripción a Web Push (VAPID) desde el dashboard.
 * Registra el Service Worker, pide permiso y envía la suscripción al servidor.
 */
(function () {
  'use strict';

  // --- utilidades ---------------------------------------------------------
  function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const raw = window.atob(base64);
    const output = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; ++i) {
      output[i] = raw.charCodeAt(i);
    }
    return output;
  }

  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? match.pop() : '';
  }

  function setButtonState(btn, text, disabled) {
    if (!btn) return;
    btn.textContent = text;
    btn.disabled = !!disabled;
  }

  // --- flujo principal ----------------------------------------------------
  async function subscribeUser(btn) {
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        alert('Tu navegador no soporta notificaciones push.');
        return;
      }

      setButtonState(btn, 'Activando…', true);

      const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
      await navigator.serviceWorker.ready;

      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        alert('Permiso de notificaciones denegado.');
        setButtonState(btn, '🔔 Activar notificaciones', false);
        return;
      }

      // Obtener la clave pública VAPID del servidor.
      const keyResp = await fetch('/push/public_key/');
      const keyData = await keyResp.json();
      if (!keyData.public_key) {
        alert('El servidor no tiene configurada la clave VAPID.');
        setButtonState(btn, '🔔 Activar notificaciones', false);
        return;
      }

      // Reutilizar suscripción existente o crear una nueva.
      let subscription = await registration.pushManager.getSubscription();
      if (!subscription) {
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(keyData.public_key)
        });
      }

      // Enviar la suscripción al servidor.
      const resp = await fetch('/push/subscribe/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(subscription)
      });

      if (resp.ok) {
        setButtonState(btn, '✅ Notificaciones activas', true);
      } else {
        setButtonState(btn, '🔔 Activar notificaciones', false);
        alert('No se pudo registrar la suscripción en el servidor.');
      }
    } catch (err) {
      console.error('Error al activar notificaciones push:', err);
      setButtonState(btn, '🔔 Activar notificaciones', false);
      alert('Ocurrió un error al activar las notificaciones.');
    }
  }

  // Si ya está suscrito, refleja el estado en el botón al cargar.
  async function refreshButton(btn) {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      setButtonState(btn, 'Push no soportado', true);
      return;
    }
    try {
      const registration = await navigator.serviceWorker.getRegistration('/');
      if (registration) {
        const sub = await registration.pushManager.getSubscription();
        if (sub && Notification.permission === 'granted') {
          setButtonState(btn, '✅ Notificaciones activas', true);
        }
      }
    } catch (e) {
      // silencioso
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('enablePushBtn');
    if (!btn) return;
    refreshButton(btn);
    btn.addEventListener('click', function () { subscribeUser(btn); });
  });
})();
