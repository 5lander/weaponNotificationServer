"""
Vistas para Web Push (VAPID):
  - public_key:  entrega la clave pública VAPID al navegador.
  - subscribe:   guarda/actualiza la suscripción del usuario autenticado.
  - unsubscribe: elimina la suscripción por su endpoint.
  - service_worker: sirve /sw.js desde la raíz, con scope global.

Las suscripciones quedan ligadas a request.user (sesión web), por lo que
solo el dueño de la cuenta recibe sus alertas.
"""
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from .models import PushSubscription

logger = logging.getLogger(__name__)


@require_GET
def public_key(request):
    """Devuelve la clave pública VAPID (applicationServerKey) al cliente."""
    return JsonResponse({'public_key': settings.VAPID_PUBLIC_KEY})


@login_required(login_url='login')
@require_POST
def subscribe(request):
    """Registra la suscripción push del usuario autenticado."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        endpoint = data['endpoint']
        keys = data['keys']
        p256dh = keys['p256dh']
        auth = keys['auth']
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'error': 'Suscripción inválida'}, status=400)

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            'user': request.user,
            'p256dh': p256dh,
            'auth': auth,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:300],
        },
    )
    logger.info("🔔 Suscripción push registrada para %s", request.user.username)
    return JsonResponse({'ok': True})


@login_required(login_url='login')
@require_POST
def unsubscribe(request):
    """Elimina la suscripción push por su endpoint."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        endpoint = data['endpoint']
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'error': 'Petición inválida'}, status=400)

    PushSubscription.objects.filter(endpoint=endpoint, user=request.user).delete()
    return JsonResponse({'ok': True})


@require_GET
def service_worker(request):
    """
    Sirve el Service Worker desde la raíz (/sw.js) para que su scope sea '/'.
    La cabecera Service-Worker-Allowed permite controlar todo el sitio.
    """
    body = render_to_string('detection/sw.js')
    response = HttpResponse(body, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response
