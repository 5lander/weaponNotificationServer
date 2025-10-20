import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webdev.settings')
django.setup()

from detection.email_utils import (
    send_email_async,
    wait_for_queue_empty,
    get_queue_status,
    print_status
)

print("\n🧪 TEST DEL SISTEMA DE EMAILS ASÍNCRONO")
print("="*60)

# Test 1: Enviar email simple
print("\n1️⃣ Enviando email de prueba...")
success = send_email_async(
    subject='Test Email Asíncrono',
    text_content='Este es un email de prueba del sistema asíncrono.',
    to_emails='landerchicaiza@gmail.com',  # Cambia esto
    html_content='<h1>¡Funciona!</h1><p>Email asíncrono exitoso</p>'
)

if success:
    print("✅ Email encolado")
else:
    print("❌ Error encolando email")

# Test 2: Verificar estado
print("\n2️⃣ Estado de la cola:")
print_status()

# Test 3: Esperar a que se procese
print("\n3️⃣ Esperando a que se envíe el email...")
if wait_for_queue_empty(timeout=30):
    print("✅ Email procesado exitosamente")
else:
    print("⚠️ Timeout esperando - revisa los logs")

# Test 4: Estado final
print("\n4️⃣ Estado final:")
print_status()

print("\n" + "="*60)
print("✅ Test completado - Revisa tu email")
print("="*60 + "\n")