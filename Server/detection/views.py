from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from rest_framework.authtoken.models import Token

from .forms import CreateUserForm
from .filters import DetectionFilter
from .models import UploadAlert

# ✅ Imports para password reset
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse
from .email_helper import send_password_reset_email_async
import logging

logger = logging.getLogger(__name__)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

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

        context = {'form': form}
        return render(request, 'detection/register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def home(request):
    token = Token.objects.get(user=request.user)
    uploadAlert = UploadAlert.objects.filter(userID=token).order_by('-dateCreated')
    
    myFilter = DetectionFilter(request.GET, queryset=uploadAlert)
    uploadAlert = myFilter.qs
    
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    paginator = Paginator(uploadAlert, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'myFilter': myFilter,
        'uploadAlert': page_obj,
        'total_results': paginator.count,
    }
    
    return render(request, 'detection/dashboard.html', context)


def alert(request, pk):
    uploadAlert = UploadAlert.objects.filter(image=str(pk) + ".jpg")
    myFilter = DetectionFilter(request.GET, queryset=uploadAlert)
    uploadAlert = myFilter.qs 

    context = {'myFilter': myFilter, 'uploadAlert': uploadAlert}
    return render(request, 'detection/alert.html', context)


# ✅ VISTA PERSONALIZADA RÁPIDA
class FastPasswordResetView(PasswordResetView):
    """
    Vista de Password Reset que responde INMEDIATAMENTE
    El email se envía en un thread separado (no bloquea)
    """
    
    def form_valid(self, form):
        """
        Procesa el formulario y retorna INMEDIATAMENTE
        Los emails se envían en threads separados (asíncrono simple)
        """
        email = form.cleaned_data.get('email', '').strip()
        
        if not email:
            logger.warning("⚠️ Intento de reset sin email")
            return HttpResponseRedirect(reverse('password_reset_done'))
        
        User = get_user_model()
        
        # Buscar usuarios activos
        active_users = User.objects.filter(
            email__iexact=email,
            is_active=True
        )
        
        num_users = active_users.count()
        
        if num_users == 0:
            logger.info(f"🔍 Reset solicitado para email no registrado: {email}")
        else:
            logger.info(f"🔐 Reset solicitado para {num_users} usuario(s) con email: {email}")
        
        # Obtener dominio desde settings
        domain = settings.SITE_DOMAIN
        protocol = settings.SITE_PROTOCOL
        
        logger.info(f"🌐 Dominio: {protocol}://{domain}")
        
        # Procesar usuarios
        for user in active_users:
            try:
                # Generar token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # ✅ ENVÍO ASÍNCRONO (no bloquea, retorna inmediatamente)
                send_password_reset_email_async(
                    user=user,
                    uid=uid,
                    token=token,
                    domain=domain,
                    protocol=protocol
                )
                
            except Exception as e:
                logger.error(f"❌ Error procesando reset para {user.username}: {e}")
        
        # ✅ RETORNAR INMEDIATAMENTE (emails se envían en background)
        logger.info("⚡ Respuesta enviada al usuario (emails procesándose en background)")
        return HttpResponseRedirect(reverse('password_reset_done'))