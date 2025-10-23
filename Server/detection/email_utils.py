"""
Sistema de envío de emails asíncrono optimizado para SendGrid SMTP
Evita bloqueos y timeouts en el servidor
SendGrid es más rápido y confiable que Gmail
"""
from threading import Thread, Lock
from queue import Queue, Empty
import time
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

# Cola global thread-safe para emails
email_queue = Queue(maxsize=100)  # Máximo 100 emails en cola

# Lock para operaciones críticas
queue_lock = Lock()

# Estadísticas
stats = {
    'sent': 0,
    'failed': 0,
    'queued': 0,
    'processing': False
}


class EmailWorker(Thread):
    """
    Worker dedicado que procesa emails de forma asíncrona con SendGrid
    Corre en un thread separado sin bloquear el servidor
    """
    
    def __init__(self, max_retries=3, retry_delay=1):
        Thread.__init__(self)
        self.daemon = True  # Se cierra automáticamente
        self._running = True
        self.max_retries = max_retries
        self.retry_delay = retry_delay  # SendGrid es rápido, menos delay
        stats['processing'] = True
    
    def run(self):
        """Loop principal que procesa emails continuamente"""
        logger.info("🚀 SendGrid Email Worker iniciado y listo")
        
        while self._running:
            try:
                # Espera máximo 1 segundo por un email en la cola
                email_data = email_queue.get(timeout=1)
                
                if email_data:
                    success = self._send_email_with_retry(email_data)
                    
                    if success:
                        with queue_lock:
                            stats['sent'] += 1
                    else:
                        with queue_lock:
                            stats['failed'] += 1
                
                email_queue.task_done()
                
            except Empty:
                # Es normal, la cola está vacía
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error inesperado en Email Worker: {e}")
                time.sleep(1)
    
    def _send_email_with_retry(self, email_data):
        """
        Envía un email con sistema de reintentos
        Retorna True si se envió exitosamente
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                success = self._send_email(email_data, attempt)
                if success:
                    return True
                    
            except Exception as e:
                logger.warning(f"⚠️ Intento {attempt}/{self.max_retries} falló: {e}")
                
                if attempt < self.max_retries:
                    # Esperar antes de reintentar (exponential backoff)
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"⏳ Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
        
        logger.error(f"❌ Email falló después de {self.max_retries} intentos")
        return False
    
    def _send_email(self, email_data, attempt=1):
        """Envía un email individual usando SendGrid"""
        start_time = time.time()
        
        logger.info(f"📧 [Intento {attempt}] Enviando vía SendGrid a {email_data['to']}")
        
        try:
            # Crear email multipart
            email = EmailMultiAlternatives(
                subject=email_data['subject'],
                body=email_data['text_content'],
                from_email=email_data['from_email'],
                to=email_data['to'],
            )
            
            # Adjuntar HTML si existe
            if email_data.get('html_content'):
                email.attach_alternative(email_data['html_content'], "text/html")
            
            # Enviar con timeout (SendGrid suele responder en 1-3 segundos)
            result = email.send(fail_silently=False)
            
            elapsed = time.time() - start_time
            
            if result == 1:
                logger.info(f"✅ Email enviado vía SendGrid en {elapsed:.2f}s a {email_data['to']}")
                return True
            else:
                logger.warning(f"⚠️ Email.send() retornó {result}")
                return False
                
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ Error enviando email vía SendGrid después de {elapsed:.2f}s: {e}")
            raise
    
    def stop(self):
        """Detiene el worker de forma ordenada"""
        logger.info("🛑 Deteniendo Email Worker...")
        self._running = False
        stats['processing'] = False


# Iniciar el worker automáticamente al importar el módulo
_email_worker = None

def start_email_worker():
    """Inicia el worker si no está corriendo"""
    global _email_worker
    
    if _email_worker is None or not _email_worker.is_alive():
        _email_worker = EmailWorker(max_retries=3, retry_delay=1)
        _email_worker.start()
        logger.info("✅ SendGrid Email Worker iniciado")
    
    return _email_worker

# Iniciar automáticamente
start_email_worker()


def send_email_async(subject, text_content, to_emails, html_content=None, from_email=None):
    """
    Encola un email para envío asíncrono vía SendGrid
    
    Args:
        subject (str): Asunto del email
        text_content (str): Contenido en texto plano
        to_emails (list or str): Destinatario(s)
        html_content (str, optional): Contenido HTML
        from_email (str, optional): Email del remitente
    
    Returns:
        bool: True si se encoló exitosamente
    """
    # Validaciones
    if not to_emails:
        logger.error("❌ No se proporcionaron destinatarios")
        return False
    
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    # Convertir a lista si es string
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    
    # Preparar datos del email
    email_data = {
        'subject': subject,
        'text_content': text_content,
        'html_content': html_content,
        'to': to_emails,
        'from_email': from_email,
        'timestamp': time.time()
    }
    
    try:
        # Verificar que el worker esté vivo
        if not _email_worker or not _email_worker.is_alive():
            logger.warning("⚠️ Email Worker no está corriendo, reiniciando...")
            start_email_worker()
        
        # Agregar a la cola
        email_queue.put(email_data, block=False)
        
        with queue_lock:
            stats['queued'] += 1
        
        queue_size = email_queue.qsize()
        logger.info(f"📨 Email encolado para SendGrid: {to_emails} (cola: {queue_size})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error encolando email: {e}")
        return False


def send_password_reset_email(user, uid, token, domain, protocol='https'):
    """
    Envía email de restablecimiento de contraseña de forma asíncrona vía SendGrid
    
    Args:
        user: Usuario de Django
        uid: UID codificado en base64
        token: Token de reset
        domain: Dominio del sitio
        protocol: 'http' o 'https'
    
    Returns:
        bool: True si se encoló exitosamente
    """
    # Validar que el usuario tenga email
    if not user.email:
        logger.error(f"❌ Usuario {user.username} no tiene email")
        return False
    
    # Construir URL completa de reset
    reset_url = f"{protocol}://{domain}/reset/{uid}/{token}/"
    
    # Contexto para renderizar templates
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
        # Renderizar templates HTML y texto
        html_content = render_to_string('detection/password_reset_email.html', context)
        text_content = render_to_string('detection/password_reset_email.txt', context)
        
    except Exception as e:
        logger.error(f"❌ Error renderizando templates: {e}")
        
        # Fallback a texto simple
        text_content = f"""
¡Hola {user.username}!

Recibimos una solicitud para restablecer tu contraseña.

Para continuar, haz clic en el siguiente enlace:
{reset_url}

Este enlace expira en 24 horas.

Si no solicitaste este cambio, ignora este email.

---
Sistema de Detección de Armas
Este es un mensaje automático, por favor no respondas.
        """.strip()
        
        html_content = None
    
    # Asunto del email
    subject = '🔐 Restablecimiento de Contraseña - Sistema de Detección de Armas'
    
    # Enviar de forma asíncrona vía SendGrid
    success = send_email_async(
        subject=subject,
        text_content=text_content,
        html_content=html_content,
        to_emails=user.email,
    )
    
    if success:
        logger.info(f"✉️ Email de reset encolado para SendGrid: {user.email}")
    else:
        logger.error(f"❌ No se pudo encolar email para {user.email}")
    
    return success


def get_queue_status():
    """
    Retorna el estado actual del sistema de emails
    
    Returns:
        dict: Estadísticas del sistema
    """
    with queue_lock:
        return {
            'queue_size': email_queue.qsize(),
            'sent': stats['sent'],
            'failed': stats['failed'],
            'queued': stats['queued'],
            'worker_alive': _email_worker.is_alive() if _email_worker else False,
            'processing': stats['processing']
        }


def wait_for_queue_empty(timeout=30):
    """
    Espera hasta que la cola esté vacía (útil para tests)
    
    Args:
        timeout (int): Tiempo máximo de espera en segundos
    
    Returns:
        bool: True si la cola se vació, False si hubo timeout
    """
    start = time.time()
    
    while not email_queue.empty():
        if time.time() - start > timeout:
            logger.warning(f"⚠️ Timeout ({timeout}s) esperando cola vacía")
            return False
        time.sleep(0.1)
    
    # Esperar un poco más para asegurar que se procesó todo
    time.sleep(0.5)
    
    logger.info(f"✅ Cola vacía en {time.time() - start:.2f}s")
    return True


def reset_stats():
    """Reinicia las estadísticas (útil para tests)"""
    with queue_lock:
        stats['sent'] = 0
        stats['failed'] = 0
        stats['queued'] = 0
    logger.info("📊 Estadísticas reiniciadas")


# Función para debugging
def print_status():
    """Imprime el estado actual del sistema de SendGrid"""
    status = get_queue_status()
    print("\n" + "="*50)
    print("📊 ESTADO DEL SISTEMA DE EMAILS (SENDGRID)")
    print("="*50)
    print(f"Cola: {status['queue_size']} emails pendientes")
    print(f"Enviados: {status['sent']}")
    print(f"Fallidos: {status['failed']}")
    print(f"Encolados (total): {status['queued']}")
    print(f"Worker activo: {'✅ Sí' if status['worker_alive'] else '❌ No'}")
    print(f"Procesando: {'✅ Sí' if status['processing'] else '❌ No'}")
    print("="*50 + "\n")