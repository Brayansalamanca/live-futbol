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

# Importación de modelos y formularios
from .models import Task, RegistroEntrega, ObjetoPerdido, PrendaRopa, BajaBalon
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
        return render(request, 'signup.html', {'form': CustomUserCreationForm()})
    
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
        except Exception as e:
            return render(request, 'signup.html', {'form': form, 'error': 'Error en el registro.'})
    return render(request, 'signup.html', {'form': form, 'error': 'Datos inválidos.'})

def activar(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.filter(pk=uid).first()
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
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)
        return redirect('formulario')
    else:
        return render(request, 'signin.html', {
            'form': AuthenticationForm(),
            'error': 'Usuario o contraseña incorrectos'
        })

def signout(request):
    logout(request)
    return redirect('home')

# ============================
# 📦 INVENTARIO ROPA (radar.html)
# ============================

@login_required
def radar(request):
    return render(request, 'radar.html')

@login_required
def api_guardar_prenda(request):
    if request.method == "POST":
        data = json.loads(request.body)
        prenda = PrendaRopa.objects.create(
            objeto=data.get('objeto'),
            talla=data.get('talla'),
            condicion=data.get('condicion'),
            detalle_defecto=data.get('detalle_defecto', ''),
            imagen=data.get('imagen'),
            estado='Disponible'
        )
        return JsonResponse({"status": "success", "id": prenda.id})

@login_required
def api_obtener_prendas(request):
    prendas = list(PrendaRopa.objects.all().values().order_by('-fecha_registro'))
    return JsonResponse(prendas, safe=False)

@login_required
def api_apartar_prenda(request, prenda_id):
    if request.method == "POST":
        data = json.loads(request.body)
        prenda = get_object_or_404(PrendaRopa, pk=prenda_id)
        if data.get('accion') == 'liberar':
            prenda.estado = "Disponible"
            prenda.nombre_apartado = ""
        else:
            prenda.estado = "Apartado"
            prenda.nombre_apartado = data.get('nombre', request.user.username)
        prenda.save()
        return JsonResponse({"status": "success"})

@login_required
def api_eliminar_prenda(request, prenda_id):
    if request.method == "POST":
        prenda = get_object_or_404(PrendaRopa, pk=prenda_id)
        prenda.delete()
        return JsonResponse({"status": "success"})

# ============================
# ⚽ ENTREGAS BALONES (videos.html)
# ============================

@login_required
def videos(request):
    return render(request, 'videos.html')

@login_required
def api_guardar_entrega(request):
    if request.method == "POST":
        data = json.loads(request.body)
        RegistroEntrega.objects.create(
            nombre=data.get('recibido_por'),
            curso=data.get('curso', 'N/A'),
            objeto=data.get('balon'),
            lugar=data.get('lugar', 'Cancha')
        )
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_entregas(request):
    entregas = list(RegistroEntrega.objects.all().values().order_by('-fecha'))
    return JsonResponse(entregas, safe=False)

@login_required
def api_eliminar_entrega(request, entrega_id):
    if request.method == "POST":
        entrega = get_object_or_404(RegistroEntrega, pk=entrega_id)
        entrega.delete()
        return JsonResponse({"status": "success"})

# ============================
# 🔍 OBJETOS PERDIDOS (voz.html)
# ============================

@login_required
def voz(request):
    return render(request, 'voz.html')

@login_required
def api_guardar_objeto(request):
    if request.method == "POST":
        data = json.loads(request.body)
        ObjetoPerdido.objects.create(
            nombre_reporta=data.get('nombre'),
            curso=data.get('curso'),
            tipo_objeto=data.get('tipo'),
            color=data.get('color'),
            descripcion=data.get('dif')
        )
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_objetos(request):
    objetos = list(ObjetoPerdido.objects.all().values().order_by('-fecha'))
    return JsonResponse(objetos, safe=False)

@login_required
def api_eliminar_objeto(request, obj_id):
    if request.method == "POST":
        objeto = get_object_or_404(ObjetoPerdido, pk=obj_id)
        objeto.delete()
        return JsonResponse({"status": "success"})

# ============================
# 📉 BAJAS BALONES (voz.html)
# ============================

@login_required
def api_guardar_baja(request):
    if request.method == "POST":
        data = json.loads(request.body)
        BajaBalon.objects.create(
            tipo_balon=data.get('tipo'),
            causa=data.get('causa'),
            marca=data.get('marca'),
            responsable=data.get('responsable', 'Anonimo'),
            foto=data.get('foto')
        )
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_bajas(request):
    bajas = list(BajaBalon.objects.all().values().order_by('-fecha'))
    return JsonResponse(bajas, safe=False)

@login_required
def api_eliminar_baja(request, baja_id):
    if request.method == "POST":
        baja = get_object_or_404(BajaBalon, pk=baja_id)
        baja.delete()
        return JsonResponse({"status": "success"})

# ============================
# 📧 EXTRAS (Correos)
# ============================

@login_required
def enviar_rutina_correo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            rutina = data.get('rutina', {})
            contenido_html = f"<h2>Rutina de {request.user.username}</h2><p>{rutina}</p>"
            email = EmailMessage('🏋️ Tu Rutina', contenido_html, to=[request.user.email])
            email.content_subtype = "html"
            email.send()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ============================
# ✅ GESTIÓN DE TAREAS
# ============================

@login_required
def tasks(request):
    tasks_list = Task.objects.filter(user=request.user, diaCompletado__isnull=True)
    return render(request, 'tasks.html', {'tasks': tasks_list})

@login_required
def create_task(request):
    if request.method == 'GET':
        return render(request, 'create_task.html', {'form': TaskForm()})
    form = TaskForm(request.POST)
    if form.is_valid():
        new_task = form.save(commit=False)
        new_task.user = request.user
        new_task.save()
        return redirect('tasks')
    return render(request, 'create_task.html', {'form': form, 'error': 'Datos inválidos'})

@login_required
def lista(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'GET':
        form = TaskForm(instance=task)
        return render(request, 'lista.html', {'task': task, 'form': form})
    form = TaskForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
        return redirect('tasks')
    return render(request, 'lista.html', {'task': task, 'form': form})

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