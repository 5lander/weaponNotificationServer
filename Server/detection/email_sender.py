"""
Sistema de envío de emails usando SendGrid API HTTP (no SMTP)
SMTP está bloqueado en Render - usamos HTTP API que funciona perfectamente
"""
from threading import Thread
from django.template.loader import render_to_string
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

# Intentar importar sendgrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
    logger.info("✅ SendGrid API disponible")
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("⚠️ SendGrid no instalado - pip install sendgrid")


def send_email_async(subject, text_content, to_email, html_content=None, from_email=None):
    """
    Envía un email usando SendGrid API HTTP (no SMTP bloqueado por Render)
    Se ejecuta en un thread separado para no bloquear la respuesta
    """
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    def _send():
        try:
            if not SENDGRID_AVAILABLE:
                logger.error("❌ SendGrid no instalado")
                logger.error("   Ejecuta: pip install sendgrid")
                return False
            
            # Obtener API Key
            api_key = os.environ.get('SENDGRID_API_KEY', settings.EMAIL_HOST_PASSWORD)
            
            if not api_key or not api_key.startswith('SG.'):
                logger.error("❌ SENDGRID_API_KEY no configurado o inválido")
                logger.error(f"   API Key actual: {api_key[:20] if api_key else 'None'}...")
                return False
            
            logger.info(f"📧 Enviando email a {to_email} vía SendGrid API HTTP...")
            
            # Crear mensaje con SendGrid API
            message = Mail(
                from_email=Email(from_email),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content("text/plain", text_content)
            )
            
            # Agregar HTML si existe
            if html_content:
                message.add_content(Content("text/html", html_content))
            
            # Enviar vía API HTTP (puerto 443 - NO bloqueado por Render)
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            
            # SendGrid API retorna 202 si fue aceptado
            if response.status_code == 202:
                logger.info(f"✅ Email enviado exitosamente a {to_email}")
                logger.info(f"   Status: {response.status_code} (Accepted)")
                return True
            else:
                logger.warning(f"⚠️ SendGrid retornó status inesperado: {response.status_code}")
                logger.warning(f"   Body: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando email vía SendGrid API: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    # Lanzar en thread daemon (muere con el proceso principal)
    thread = Thread(target=_send, daemon=True)
    thread.start()
    
    logger.info(f"🚀 Email encolado para {to_email} vía API HTTP")
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