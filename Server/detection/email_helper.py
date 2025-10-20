"""
Sistema de envío de emails asíncrono SIMPLE
Un solo thread por email, sin colas ni workers complejos
"""
from threading import Thread
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_email_in_thread(subject, text_content, to_email, html_content=None):
    """
    Envía un email en un thread separado para no bloquear la respuesta HTTP
    Método simple y directo - un thread por email
    """
    def _send():
        try:
            logger.info(f"📧 Enviando email a {to_email}...")
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            
            if html_content:
                email.attach_alternative(html_content, "text/html")
            
            result = email.send(fail_silently=False)
            
            if result == 1:
                logger.info(f"✅ Email enviado exitosamente a {to_email}")
            else:
                logger.error(f"❌ Email.send() retornó {result}")
                
        except Exception as e:
            logger.error(f"❌ Error enviando email a {to_email}: {e}")
    
    # Crear y lanzar thread (daemon=True para que muera con el proceso)
    thread = Thread(target=_send, daemon=True)
    thread.start()
    
    logger.info(f"🚀 Email encolado para {to_email} (respuesta inmediata)")


def send_password_reset_email_async(user, uid, token, domain, protocol='https'):
    """
    Envía email de password reset de forma asíncrona
    Retorna inmediatamente sin esperar
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

---
Sistema de Detección de Armas
        """.strip()
        html_content = None
    
    # Asunto
    subject = '🔐 Restablecimiento de Contraseña - Sistema de Detección de Armas'
    
    # Enviar en thread (no bloquea)
    send_email_in_thread(subject, text_content, user.email, html_content)
    
    return True