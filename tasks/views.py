from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.http import JsonResponse
import json

from .models import Task, RegistroEntrega, ObjetoPerdido, PrendaRopa, BajaBalon
from .forms import TaskForm, CustomUserCreationForm
from .tokens import account_activation_token

# --- VISTAS PÚBLICAS ---
def home(request): return render(request, 'home.html')
def soporte(request): return render(request, 'soporte.html')
def condiciones(request): return render(request, 'condiciones.html')

# --- AUTENTICACIÓN ---
def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)
        if user.username == 'rosita':
            return redirect('formulario')
        elif user.username == 'asistente_bienestar1':
            return redirect('radar')
        else:
            return redirect('tipos')
    else:
        return render(request, 'signin.html', {
            'form': AuthenticationForm(),
            'error': 'Usuario o contraseña incorrectos'
        })

def signout(request):
    logout(request)
    return redirect('home')

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': CustomUserCreationForm()})
    form = CustomUserCreationForm(request.POST)
    if form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        # Lógica de envío de email (abreviada para brevedad)
        return render(request, 'confirmacion_enviada.html')
    return render(request, 'signup.html', {'form': form, 'error': 'Datos inválidos.'})

# --- INVENTARIOS Y APIs (Ejemplos base) ---
@login_required
def tipos(request): return render(request, 'tipos.html')

@login_required
def formulario(request): return render(request, 'formulario.html')

@login_required
def radar(request): return render(request, 'radar.html')

@login_required
def videos(request): return render(request, 'videos.html')

@login_required
def voz(request): return render(request, 'voz.html')

@login_required
def tasks(request):
    tasks_list = Task.objects.filter(user=request.user, diaCompletado__isnull=True)
    return render(request, 'tasks.html', {'tasks': tasks_list})