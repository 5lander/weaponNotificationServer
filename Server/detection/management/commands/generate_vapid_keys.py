"""
Comando de gestión: generate_vapid_keys

Genera un par de claves VAPID (curva P-256) para Web Push y las imprime en el
formato que esperan tanto el navegador como `pywebpush`:

  - VAPID_PUBLIC_KEY  -> punto público sin comprimir, base64url (applicationServerKey)
  - VAPID_PRIVATE_KEY -> valor privado de 32 bytes, base64url

Copia ambos valores en tu .env (local) y en las variables de entorno de Render.
NO los subas al repositorio.

Uso:
    python manage.py generate_vapid_keys
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


def _b64url(data: bytes) -> str:
    """base64url sin relleno '=' (formato esperado por Web Push / VAPID)."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


class Command(BaseCommand):
    help = "Genera un par de claves VAPID para notificaciones Web Push."

    def handle(self, *args, **options):
        private_key = ec.generate_private_key(ec.SECP256R1())

        # Clave pública: punto sin comprimir (65 bytes) -> applicationServerKey
        public_bytes = private_key.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )
        public_b64 = _b64url(public_bytes)

        # Clave privada: valor escalar de 32 bytes (lo que acepta pywebpush)
        private_value = private_key.private_numbers().private_value
        private_b64 = _b64url(private_value.to_bytes(32, "big"))

        self.stdout.write(self.style.SUCCESS("\n✅ Par de claves VAPID generado.\n"))
        self.stdout.write("Añade estas líneas a tu .env (y a las env vars de Render):\n")
        self.stdout.write(self.style.HTTP_INFO(f"VAPID_PUBLIC_KEY={public_b64}"))
        self.stdout.write(self.style.HTTP_INFO(f"VAPID_PRIVATE_KEY={private_b64}"))
        self.stdout.write(self.style.HTTP_INFO("VAPID_ADMIN_EMAIL=mailto:tu-correo@dominio.com"))
        self.stdout.write(self.style.WARNING(
            "\n⚠️ Guarda la clave privada en secreto. No la subas al repositorio.\n"
        ))
