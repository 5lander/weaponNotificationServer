"""
Sistema de envío de emails SIMPLE para SendGrid en Render
Sin workers, sin colas, sin problemas
"""
from threading import Thread
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_email_async(subject, text_content, to_email, html_content=None, from_email=None):
    """
    Envía un email en un thread separado (no bloquea la respuesta HTTP)
    Simple, directo, confiable
    """
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    def _send():
        try:
            logger.info(f"📧 Enviando email a {to_email} vía SendGrid...")
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[to_email],
            )
            
            if html_content:
                email.attach_alternative(html_content, "text/html")
            
            # SendGrid responde en 1-3 segundos típicamente
            result = email.send(fail_silently=False)
            
            if result == 1:
                logger.info(f"✅ Email enviado exitosamente a {to_email}")
                return True
            else:
                logger.error(f"❌ Email.send() retornó {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando email: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    # Lanzar en thread daemon (muere con el proceso principal)
    thread = Thread(target=_send, daemon=True)
    thread.start()
    
    logger.info(f"🚀 Email encolado para {to_email} (respuesta inmediata)")
    return True


def send_password_reset_email(user, uid, token, domain, protocol='https'):
    """
    Envía email de password reset de forma asíncrona
    Retorna inmediatamente
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
        # Renderizar templates (estos existen en tu código)
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
    
    # Enviar (no bloquea)
    return send_email_async(
        subject=subject,
        text_content=text_content,
        to_email=user.email,
        html_content=html_content
    )


