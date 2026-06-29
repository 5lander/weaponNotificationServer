"""
Comando de gestión: flush_all_sessions

Elimina TODAS las sesiones activas (logout global). Se ejecuta en el arranque
en frío del servidor para garantizar que un reinicio NO deje ninguna sesión
iniciada (evita el "auto-login" inseguro).

A diferencia del comando integrado `clearsessions` (que solo borra las sesiones
YA caducadas), este borra todas las filas de la tabla `django_session`.

Uso:
    python manage.py flush_all_sessions
"""
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Elimina TODAS las sesiones activas (logout global) en el arranque en frío."

    def handle(self, *args, **options):
        total = Session.objects.count()
        Session.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            f"🔒 Sesiones eliminadas: {total}. El servidor exigirá login manual."
        ))
