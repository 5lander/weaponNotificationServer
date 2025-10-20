from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import CreateUserForm
from .filters import DetectionFilter
from .models import UploadAlert

from rest_framework.authtoken.models import Token
from django.conf import settings
from django.core.paginator import Paginator

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse
from .email_utils import send_password_reset_email, get_queue_status
import logging


logger = logging.getLogger(__name__)

def loginPage(request):
	if request.user.is_authenticated:
		return redirect('home')
	else:
		if request.method == 'POST':
			username = request.POST.get('username')
			password =request.POST.get('password')

			user = authenticate(request, username=username, password=password)

			if user is not None:
				login(request, user) 
				return redirect('home')
			else:
				messages.info(request, 'El nombre de usuario O la contraseña es incorrecta')

		context = {}
		return render(request, 'detection/login.html', context)

def registerPage(request):

	if request.user.is_authenticated:
		return redirect('home')
	else:
		form = CreateUserForm()
		if request.method == 'POST':
			form = CreateUserForm(request.POST)
			if form.is_valid():
				form.save()
				user = form.cleaned_data.get('username')
				messages.success(request, 'La cuenta fue creada exitosamente para ' + user)

				return redirect('login')

		context = {'form':form}
		return render(request, 'detection/register.html', context)

def logoutUser(request):
	logout(request)
	return redirect('login')

@login_required(login_url='login')
def home(request):
    # Obtener el token del usuario
    token = Token.objects.get(user=request.user)
    
    # Obtener todas las alertas del usuario ordenadas por fecha (más reciente primero)
    uploadAlert = UploadAlert.objects.filter(userID=token).order_by('-dateCreated')
    
    # Aplicar filtros
    myFilter = DetectionFilter(request.GET, queryset=uploadAlert)
    uploadAlert = myFilter.qs
    
    # Configurar paginación
    per_page = request.GET.get('per_page', 10)  # 10 elementos por página por defecto
    try:
        per_page = int(per_page)
        # Validar que per_page esté en los valores permitidos
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    # Crear el paginador
    paginator = Paginator(uploadAlert, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Contexto para el template
    context = {
        'myFilter': myFilter,
        'uploadAlert': page_obj,  # Ahora es un objeto paginado
        'total_results': paginator.count,  # Total de resultados
    }
    
    return render(request, 'detection/dashboard.html', context)


def alert(request, pk):

	uploadAlert = UploadAlert.objects.filter(image = str(pk) + ".jpg")

	myFilter = DetectionFilter(request.GET, queryset=uploadAlert)
	uploadAlert = myFilter.qs 

	context = {'myFilter':myFilter, 'uploadAlert':uploadAlert}

	return render(request, 'detection/alert.html', context)



class FastPasswordResetView(PasswordResetView):
    """
    Vista de Password Reset con envío SÍNCRONO directo (sin cola)
    Volvemos al método simple que funcionaba antes
    """
    
    def form_valid(self, form):
        """
        Procesa el formulario y envía emails de forma SÍNCRONA
        """
        email = form.cleaned_data.get('email', '').strip()
        
        if not email:
            logger.warning("⚠️ Intento de reset sin email")
            return HttpResponseRedirect(reverse('password_reset_done'))
        
        User = get_user_model()
        
        # Buscar usuarios activos con ese email
        active_users = User.objects.filter(
            email__iexact=email,
            is_active=True
        )
        
        num_users = active_users.count()
        
        if num_users == 0:
            logger.info(f"🔍 Reset solicitado para email no registrado: {email}")
        else:
            logger.info(f"🔐 Reset solicitado para {num_users} usuario(s) con email: {email}")
        
        # ✅ Obtener dominio desde settings (no del request)
        domain = settings.SITE_DOMAIN
        protocol = settings.SITE_PROTOCOL
        
        logger.info(f"🌐 Usando dominio: {protocol}://{domain}")
        
        # Procesar cada usuario encontrado
        emails_enviados = 0
        
        for user in active_users:
            try:
                # Generar token único de reset
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # ✅ ENVÍO DIRECTO (SÍNCRONO) - como antes
                success = self.send_reset_email_sync(
                    user=user,
                    uid=uid,
                    token=token,
                    domain=domain,
                    protocol=protocol
                )
                
                if success:
                    emails_enviados += 1
                    logger.info(f"✅ Email enviado a: {user.username}")
                else:
                    logger.error(f"❌ Error enviando email a: {user.username}")
                    
            except Exception as e:
                logger.error(f"❌ Error procesando reset para {user.username}: {e}")
        
        logger.info(f"📊 Reset completado. Emails enviados: {emails_enviados}")
        
        # Redirigir inmediatamente
        return HttpResponseRedirect(reverse('password_reset_done'))
    
    def send_reset_email_sync(self, user, uid, token, domain, protocol):
        """
        Envía email de reset de forma SÍNCRONA (directa)
        Este es el método simple que funcionaba antes
        """
        # Validar email
        if not user.email:
            logger.error(f"❌ Usuario {user.username} no tiene email")
            return False
        
        # Construir URL de reset
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

Recibimos una solicitud para restablecer tu contraseña.

Para continuar, haz clic en el siguiente enlace:
{reset_url}

Este enlace expira en 24 horas.

Si no solicitaste este cambio, ignora este email.

---
Sistema de Detección de Armas
            """.strip()
            
            html_content = None
        
        # Asunto
        subject = '🔐 Restablecimiento de Contraseña - Sistema de Detección de Armas'
        
        try:
            # ✅ ENVÍO DIRECTO con EmailMultiAlternatives
            logger.info(f"📧 Enviando email a {user.email}...")
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            
            if html_content:
                email.attach_alternative(html_content, "text/html")
            
            # Enviar directamente (sin threads, sin cola)
            result = email.send(fail_silently=False)
            
            if result == 1:
                logger.info(f"✅ Email enviado exitosamente a {user.email}")
                return True
            else:
                logger.error(f"❌ Email.send() retornó {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando email a {user.email}: {e}")
            return False