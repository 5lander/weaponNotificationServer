"""
Sistema de envío de emails usando la API HTTP de Brevo (Sendinblue).
Render bloquea el SMTP saliente (puerto 587), por eso se usa la API HTTP
(https://api.brevo.com/v3/smtp/email, puerto 443) que NO está bloqueada.
"""
from threading import Thread
from django.template.loader import render_to_string
from django.conf import settings
import logging
import os
import requests

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _get_brevo_api_key():
    """API key de Brevo (empieza con 'xkeysib-')."""
    return os.environ.get('BREVO_API_KEY', getattr(settings, 'BREVO_API_KEY', '') or '')


def send_email_async(subject, text_content, to_email, html_content=None, from_email=None):
    """
    Envía un email usando la API HTTP de Brevo (no SMTP bloqueado por Render).
    Se ejecuta en un thread separado para no bloquear la respuesta HTTP.
    """
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL

    def _send():
        try:
            api_key = _get_brevo_api_key()
            if not api_key:
                logger.error("❌ BREVO_API_KEY no configurado (revisa .env / Render)")
                return False

            logger.info(f"📧 Enviando email a {to_email} vía Brevo API HTTP...")

            payload = {
                "sender": {"email": from_email, "name": "Weapon Detection System"},
                "to": [{"email": to_email}],
                "subject": subject,
                "textContent": text_content,
            }
            if html_content:
                payload["htmlContent"] = html_content

            headers = {
                "api-key": api_key,
                "Content-Type": "application/json",
                "accept": "application/json",
            }

            response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=15)

            # Brevo devuelve 201 (Created) cuando acepta el mensaje.
            if response.status_code in (200, 201):
                logger.info(f"✅ Email enviado exitosamente a {to_email} (status {response.status_code})")
                return True
            else:
                logger.warning(f"⚠️ Brevo devolvió status inesperado: {response.status_code}")
                logger.warning(f"   Body: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error enviando email vía Brevo API: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    thread = Thread(target=_send, daemon=True)
    thread.start()

    logger.info(f"🚀 Email encolado para {to_email} vía Brevo API HTTP")
    return True


def send_password_reset_email(user, uid, token, domain, protocol='https'):
    """
    Envía email de password reset usando SendGrid API
    Retorna inmediatamente sin bloquear
    """
    if not user.email:
        logger.error(f"❌ Usuario {user.username} no tiene email")
        return False
    
    # URL de reset
    reset_url = f"{protocol}://{domain}/reset/{uid}/{token}/"
    
    # Contexto para templates
    context = {
        'user': user,
        'email': user.email,
        'uid': uid,
        'token': token,
        'reset_url': reset_url,
        'protocol': protocol,
        'domain': domain,
    }
    
    try:
        # Renderizar templates
        html_content = render_to_string('detection/password_reset_email.html', context)
        text_content = render_to_string('detection/password_reset_email.txt', context)
        
    except Exception as e:
        logger.error(f"❌ Error renderizando templates: {e}")
        
        # Fallback a texto simple
        text_content = f"""
¡Hola {user.username}!

Para restablecer tu contraseña, haz clic en:
{reset_url}

Este enlace expira en 24 horas.

Si no solicitaste este cambio, ignora este email.

---
Sistema de Detección de Armas
        """.strip()
        
        html_content = None
    
    # Asunto
    subject = '🔐 Restablecimiento de Contraseña - Sistema de Detección de Armas'
    
    # Enviar usando API HTTP (no bloquea)
    return send_email_async(
        subject=subject,
        text_content=text_content,
        to_email=user.email,
        html_content=html_content
    )