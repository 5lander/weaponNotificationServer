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
				messages.info(request, 'Username OR password is incorrect')

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
				messages.success(request, 'Account was successfully created for ' + user)

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