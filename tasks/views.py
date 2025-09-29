from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import send_mail, EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.http import JsonResponse
import json

from .models import Task
from .forms import TaskForm, CustomUserCreationForm
from .tokens import account_activation_token

# ============================
# 🏠 VISTAS PÚBLICAS
# ============================

def home(request):
    return render(request, 'home.html')

def soporte(request):
    return render(request, 'soporte.html')

def tipos(request):
    return render(request, 'tipos.html')

def formulario(request):
    return render(request, 'formulario.html')

def ranking(request):
    return render(request, 'ranking.html')

def condiciones(request):
    return render(request, 'condiciones.html')

# ============================
# 🔐 AUTENTICACIÓN
# ============================

class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    template_name = 'recuperar_contraseña.html'
    email_template_name = 'email_reset_password.html'
    success_url = reverse_lazy('password_reset_done')
    success_message = "Te hemos enviado un enlace para restablecer tu contraseña"

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': CustomUserCreationForm()
        })
    else:
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_active = False
                user.save()

                current_site = request.get_host()
                subject = 'Confirma tu cuenta en Live Fútbol'
                message = render_to_string('confirmacion_email.html', {
                    'user': user,
                    'domain': current_site,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                email = EmailMessage(subject, message, to=[user.email])
                email.send()

                return render(request, 'confirmacion_enviada.html')
            except IntegrityError:
                return render(request, 'signup.html', {
                    'form': form,
                    'error': 'El usuario ya existe'
                })
        return render(request, 'signup.html', {
            'form': form,
            'error': 'Las contraseñas no coinciden o datos inválidos'
        })

def activar(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'confirmar_cuenta.html')
    else:
        return render(request, 'confirmar_fallido.html')

def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm()
        })
    else:
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('formulario')
        else:
            return render(request, 'signin.html', {
                'form': form,
                'error': 'Usuario o contraseña incorrectos'
            })

def signout(request):
    logout(request)
    return redirect('home')

# ============================
# 📝 VISTAS DE TAREAS
# ============================

@login_required
def tasks(request):
    tasks = Task.objects.filter(user=request.user, diaCompletado__isnull=True)
    return render(request, 'tasks.html', {'tasks': tasks})

@login_required
def create_task(request):
    if request.method == 'GET':
        return render(request, 'create_task.html', {
            'form': TaskForm()
        })
    else:
        try:
            form = TaskForm(request.POST)
            new_task = form.save(commit=False)
            new_task.user = request.user
            new_task.save()
            return redirect('tasks')
        except ValueError:
            return render(request, 'create_task.html', {
                'form': TaskForm(),
                'error': 'Por favor introduzca valores válidos'
            })

@login_required
def lista(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'GET':
        form = TaskForm(instance=task)
        return render(request, 'lista.html', {'task': task, 'form': form})
    else:
        try:
            form = TaskForm(request.POST, instance=task)
            form.save()
            return redirect('tasks')
        except ValueError:
            return render(request, 'lista.html', {
                'task': task,
                'form': form,
                'error': "Error al actualizar la tarea"
            })

@login_required
def completar(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        task.diaCompletado = timezone.now()
        task.save()
        return redirect('tasks')

@login_required
def eliminar_tarea(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('tasks')

# ============================
# 🎯 VISTAS ADICIONALES
# ============================

@login_required
def radar(request):
    return render(request, 'radar.html')

@login_required
def videos(request):
    return render(request, 'videos.html')

@login_required
def voz(request):
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                rutina = data.get('rutina', {})
                
                contenido_html = f"""
                <h2>🏋️ Tu Rutina Semanal Personalizada</h2>
                <p>Hola {request.user.username}, aquí tienes tu rutina:</p>
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr><th>Día</th><th>Rutina</th></tr>
                    <tr><td><strong>Lunes</strong></td><td>{rutina.get('lunes', 'Descanso')}</td></tr>
                    <tr><td><strong>Martes</strong></td><td>{rutina.get('martes', 'Descanso')}</td></tr>
                    <tr><td><strong>Miércoles</strong></td><td>{rutina.get('miercoles', 'Descanso')}</td></tr>
                    <tr><td><strong>Jueves</strong></td><td>{rutina.get('jueves', 'Descanso')}</td></tr>
                    <tr><td><strong>Viernes</strong></td><td>{rutina.get('viernes', 'Descanso')}</td></tr>
                    <tr><td><strong>Sábado</strong></td><td>{rutina.get('sabado', 'Descanso')}</td></tr>
                    <tr><td><strong>Domingo</strong></td><td>{rutina.get('domingo', 'Descanso')}</td></tr>
                </table>
                <p>¡Mucho éxito en tu entrenamiento! 💪</p>
                """
                
                email = EmailMessage(
                    subject='🏋️ Tu Rutina Semanal - Live Fútbol',
                    body=contenido_html,
                    from_email='noreply@livefutbol.com',
                    to=[request.user.email]
                )
                email.content_subtype = "html"
                email.send()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Rutina enviada correctamente a tu correo'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error al enviar el correo: {str(e)}'
                })
        
        mensaje = request.POST.get('mensaje', '')
        correo_destino = request.user.email

        if mensaje and correo_destino:
            send_mail(
                subject='Texto desde reconocimiento de voz',
                message=mensaje,
                from_email='noreply@livefutbol.com',
                recipient_list=[correo_destino],
                fail_silently=False,
            )
            return render(request, 'voz.html', {'enviado': True})

    return render(request, 'voz.html')

@login_required
def enviar_rutina_correo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            rutina = data.get('rutina', {})
            
            contenido_html = f"""
            <h2>🏋️ Tu Rutina Semanal Personalizada</h2>
            <p>Hola {request.user.username}, aquí tienes tu rutina:</p>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr><th>Día</th><th>Rutina</th></tr>
                <tr><td><strong>Lunes</strong></td><td>{rutina.get('lunes', 'Descanso')}</td></tr>
                <tr><td><strong>Martes</strong></td><td>{rutina.get('martes', 'Descanso')}</td></tr>
                <tr><td><strong>Miércoles</strong></td><td>{rutina.get('miercoles', 'Descanso')}</td></tr>
                <tr><td><strong>Jueves</strong></td><td>{rutina.get('jueves', 'Descanso')}</td></tr>
                <tr><td><strong>Viernes</strong></td><td>{rutina.get('viernes', 'Descanso')}</td></tr>
                <tr><td><strong>Sábado</strong></td><td>{rutina.get('sabado', 'Descanso')}</td></tr>
                <tr><td><strong>Domingo</strong></td><td>{rutina.get('domingo', 'Descanso')}</td></tr>
            </table>
            <p>¡Mucho éxito en tu entrenamiento! 💪</p>
            """
            
            email = EmailMessage(
                subject='🏋️ Tu Rutina Semanal - Live Fútbol',
                body=contenido_html,
                from_email='noreply@livefutbol.com',
                to=[request.user.email]
            )
            email.content_subtype = "html"
            email.send()
            
            return JsonResponse({
                'success': True,
                'message': 'Rutina enviada correctamente a tu correo electrónico'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al enviar el correo: {str(e)}'
            })