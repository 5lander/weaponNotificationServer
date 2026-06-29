# Notificaciones Web Push (VAPID) y endurecimiento de sesiones

Este documento describe dos cambios en el servidor Django:

1. **Notificaciones Web Push** con el estándar VAPID.
2. **Corrección del auto-login** tras reiniciar el servidor (seguridad de sesiones).

---

## 1. Notificaciones Web Push (VAPID)

### Por qué VAPID y no FCM
- Estándar abierto (Web Push Protocol RFC 8030 + VAPID RFC 8292), soportado por
  Chrome, Edge, Firefox y Safari 16+.
- No requiere proyecto Firebase ni SDK externo: generas tu propio par de claves.
- Las librerías (`pywebpush`, `py-vapid`) ya estaban en `requirements.txt`.

### Arquitectura
- **Destino de la notificación:** el *dueño de la alerta*
  (`UploadAlert.userID` → `authtoken.Token` → `User`).
- Las suscripciones del navegador se guardan en el modelo `PushSubscription`,
  ligadas al usuario de la sesión web.
- El envío ocurre en el flujo de subida de alertas (`POST /api/images/`), en un
  hilo en segundo plano, junto al correo (SendGrid) ya existente.

### Componentes
| Componente | Ruta |
|-----------|------|
| Comando para generar claves | `detection/management/commands/generate_vapid_keys.py` |
| Modelo de suscripción | `detection/models.py` (`PushSubscription`) |
| Endpoints (clave pública / suscribir / desuscribir) | `detection/push_views.py` |
| Service Worker (servido en `/sw.js`, scope raíz) | `detection/templates/detection/sw.js` |
| Frontend (registro + suscripción) | `static/js/push.js` |
| Envío server-side | `detection/webpush_sender.py` |

### Rutas nuevas
- `GET  /sw.js` — Service Worker (cabecera `Service-Worker-Allowed: /`).
- `GET  /push/public_key/` — entrega la clave pública VAPID.
- `POST /push/subscribe/` — guarda la suscripción (requiere login + CSRF).
- `POST /push/unsubscribe/` — elimina la suscripción.

### Variables de entorno (NO se suben al repo)
Genera el par de claves:
```bash
cd Server
python manage.py generate_vapid_keys
```
Copia el resultado en `Server/.env` (local) y en las *Environment Variables* de Render:
```
VAPID_PUBLIC_KEY=<clave_publica_base64url>
VAPID_PRIVATE_KEY=<clave_privada_base64url>
VAPID_ADMIN_EMAIL=mailto:tu-correo@dominio.com
```
> Si `VAPID_*` está vacío, el envío de push se omite con un *warning*; el envío de
> alertas por correo (SendGrid) sigue funcionando.

### Migración
Se añade la tabla `PushSubscription`:
```bash
python manage.py migrate
```

### Cómo probar
1. Arranca el servidor e inicia sesión en el dashboard (HTTPS o `localhost`).
2. Pulsa **🔔 Activar notificaciones** y acepta el permiso del navegador.
3. Dispara una alerta (cliente PyQt o `POST /api/images/` con el token del usuario).
4. Llega la notificación del sistema aunque la pestaña esté en segundo plano; al
   hacer clic abre `/alert/<id>/`.

Ejemplo de prueba de la API:
```bash
curl -X POST https://<host>/api/images/ \
  -H "Authorization: Token <token_del_usuario>" \
  -F "userID=<token_del_usuario>" -F "alertReceiver=correo@dominio.com" \
  -F "location=Entrada" -F "image=@prueba.jpg"
```

---

## 2. Corrección del auto-login (seguridad de sesiones)

### Problema
Django usa por defecto **sesiones en base de datos** y una **cookie persistente**
(`SESSION_EXPIRE_AT_BROWSER_CLOSE=False`, edad por defecto de 2 semanas). Al
reiniciar el servidor, la sesión seguía viva en la BD y el navegador conservaba la
cookie → el usuario entraba **sin pedir credenciales**.

### Solución
- **`settings.py`**: la sesión termina al cerrar el navegador, caduca por
  inactividad (30 min, deslizante) y endurece la cookie:
  ```python
  SESSION_EXPIRE_AT_BROWSER_CLOSE = True
  SESSION_COOKIE_AGE = 1800
  SESSION_SAVE_EVERY_REQUEST = True
  SESSION_COOKIE_HTTPONLY = True
  SESSION_COOKIE_SAMESITE = 'Lax'
  SESSION_COOKIE_SECURE = os.environ.get('SECURE_COOKIES', 'False').lower() == 'true'
  CSRF_COOKIE_SECURE   = os.environ.get('SECURE_COOKIES', 'False').lower() == 'true'
  ```
- **Comando `flush_all_sessions`**: borra TODAS las sesiones activas (logout global).
- **Arranque en frío sin sesiones**:
  - *Producción/Render*: el hook `on_starting()` de `gunicorn_config.py` borra todas
    las sesiones una sola vez en el proceso maestro, antes de crear los workers.
  - *Local*: `start.ps1` / `start.sh` ejecutan `flush_all_sessions` y luego `runserver`.

### Variables de entorno (producción)
En Render, añade:
```
SECURE_COOKIES=true
```
para que las cookies de sesión y CSRF viajen solo por HTTPS.

### Cómo probar
1. Inicia sesión en la web.
2. Detén el servidor y vuelve a arrancarlo (`./start.ps1` en local).
3. Recarga: te redirige a `/login/` (ya no entra solo).

> Comando manual de verificación (servidor parado):
> ```bash
> python manage.py flush_all_sessions   # -> "🔒 Sesiones eliminadas: N"
> ```

### Nota sobre Render
Asegúrate de que el *Start Command* use el archivo de configuración para que el
hook de limpieza se ejecute:
```
gunicorn webdev.wsgi -c gunicorn_config.py
```
