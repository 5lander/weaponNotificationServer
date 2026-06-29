"""
Envío de notificaciones Web Push (VAPID) con pywebpush.

send_push_to_user(user, payload) recorre todas las suscripciones del usuario y
les entrega el mensaje. Las suscripciones caducadas (404/410) se eliminan.
"""
import json
import logging

from django.conf import settings

from .models import PushSubscription

logger = logging.getLogger(__name__)


def send_push_to_user(user, payload: dict) -> int:
    """
    Envía una notificación push a todas las suscripciones de `user`.
    Devuelve el número de envíos correctos.
    """
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        logger.warning("⚠️ VAPID no configurado: se omite el envío de push.")
        return 0

    # Import diferido para no romper el arranque si la librería no está instalada.
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.error("❌ pywebpush no está instalado; no se envían notificaciones push.")
        return 0

    subscriptions = PushSubscription.objects.filter(user=user)
    sent = 0

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_ADMIN_EMAIL},
            )
            sent += 1
        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None)
            if status in (404, 410):
                # Suscripción muerta: eliminar.
                logger.info("🧹 Suscripción push caducada eliminada (%s).", status)
                sub.delete()
            else:
                logger.error("❌ Error enviando push: %s", exc)
        except Exception as exc:  # noqa: BLE001 - no debe interrumpir la alerta
            logger.error("❌ Error inesperado enviando push: %s", exc)

    logger.info("🔔 Push enviadas a %s: %s/%s", user.username, sent, subscriptions.count())
    return sent


def notify_alert_owner(alert_instance):
    """
    Envía una push al dueño de la alerta (UploadAlert.userID -> Token -> User).
    Se llama desde el flujo de subida de alertas.
    """
    try:
        token = alert_instance.userID            # FK a authtoken.Token
        user = token.user
    except Exception as exc:  # noqa: BLE001
        logger.error("❌ No se pudo resolver el dueño de la alerta para push: %s", exc)
        return 0

    # Construir la URL de la alerta a partir del nombre de imagen (uuid.jpg).
    image_name = getattr(alert_instance.image, "name", "") or ""
    alert_id = image_name.split("/")[-1].rsplit(".", 1)[0] if image_name else ""
    url = f"/alert/{alert_id}/" if alert_id else "/"

    payload = {
        "title": "🚨 Arma detectada",
        "body": f"Ubicación: {alert_instance.location}",
        "url": url,
        "tag": f"weapon-alert-{alert_id or 'na'}",
    }
    return send_push_to_user(user, payload)
