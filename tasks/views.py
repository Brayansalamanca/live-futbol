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

# Importación de tus modelos y formularios
from .models import Task, RegistroEntrega, ObjetoPerdido, PrendaRopa, BajaBalon
from .forms import TaskForm, CustomUserCreationForm
from .tokens import account_activation_token

# ============================
# 🏠 VISTAS DE NAVEGACIÓN
# ============================

def home(request): return render(request, 'home.html')
def soporte(request): return render(request, 'soporte.html')
def tipos(request): return render(request, 'tipos.html')
def formulario(request): return render(request, 'formulario.html')
def ranking(request): return render(request, 'ranking.html')
def condiciones(request): return render(request, 'condiciones.html')
def radar(request): return render(request, 'radar.html')
def videos(request): return render(request, 'videos.html')
def voz(request): return render(request, 'voz.html')

# ============================
# 🔐 AUTENTICACIÓN Y SEGURIDAD
# ============================

class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    template_name = 'recuperar_contraseña.html'
    email_template_name = 'email_reset_password.html'
    success_url = reverse_lazy('password_reset_done')
    success_message = "Instrucciones enviadas a tu correo."

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': CustomUserCreationForm()})
    
    form = CustomUserCreationForm(request.POST)
    if form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        
        domain = request.get_host()
        subject = 'Activa tu cuenta en Live Fútbol'
        message = render_to_string('confirmacion_email.html', {
            'user': user,
            'domain': domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        EmailMessage(subject, message, to=[user.email]).send()
        return render(request, 'confirmacion_enviada.html')
    return render(request, 'signup.html', {'form': form, 'error': 'Revisa los datos.'})

def activar(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except: user = None

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'confirmar_cuenta.html')
    return render(request, 'confirmar_fallido.html')

def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('formulario')
        return render(request, 'signin.html', {'form': form, 'error': 'Usuario o clave incorrectos'})
    return render(request, 'signin.html', {'form': AuthenticationForm()})

def signout(request):
    logout(request)
    return redirect('home')

# ============================
# 📦 API INVENTARIO (Rosita / Prendas)
# ============================

@login_required
def api_guardar_prenda(request):
    if request.method == "POST":
        data = json.loads(request.body)
        prenda = PrendaRopa.objects.create(
            objeto=data.get('nombre'),
            cantidad=int(data.get('cantidad', 1)),
            talla=data.get('talla', 'N/A'),
            condicion=data.get('condicion', 'Óptimo'),
            detalle_defecto=data.get('detalle_defecto', ''),
            imagen=data.get('imagen'),
            estado='Disponible'
        )
        return JsonResponse({"status": "ok", "id": prenda.id})

@login_required
def api_obtener_prendas(request):
    prendas_qs = PrendaRopa.objects.all().order_by('-fecha_registro')
    data = []
    for p in prendas_qs:
        data.append({
            "id": p.id,
            "nombre": p.objeto,
            "cantidad": p.cantidad,
            "imagen": p.imagen,
            "estado": p.estado,
            "profesor": p.nombre_apartado or "Disponible",
            "curso": p.curso_apartado or "---",
            "evento": p.evento_apartado or "---",
            "fecha_uso": str(p.fecha_uso) if p.fecha_uso else "---"
        })
    return JsonResponse(data, safe=False)

@login_required
def api_apartar_prenda(request, prenda_id):
    if request.method == "POST":
        data = json.loads(request.body)
        prenda = get_object_or_404(PrendaRopa, pk=prenda_id)
        if data.get('accion') == 'liberar':
            prenda.estado = "Disponible"
            prenda.nombre_apartado = ""
            prenda.curso_apartado = ""
            prenda.evento_apartado = ""
            prenda.fecha_uso = None
        else:
            prenda.estado = "Apartado"
            prenda.nombre_apartado = data.get('nombre')
            prenda.curso_apartado = data.get('curso')
            prenda.evento_apartado = data.get('evento')
            prenda.fecha_uso = data.get('fecha')
        prenda.save()
        return JsonResponse({"status": "success"})

@login_required
def api_eliminar_prenda(request, prenda_id):
    if request.method == "POST":
        get_object_or_404(PrendaRopa, pk=prenda_id).delete()
        return JsonResponse({"status": "success"})

# ============================
# ⚽ API BAJAS DEPORTIVAS
# ============================

@login_required
def api_guardar_baja(request):
    if request.method == "POST":
        data = json.loads(request.body)
        BajaBalon.objects.create(
            tipo_balon=data.get('tipo'),
            causa=data.get('causa'),
            marca=data.get('lugar', 'N/A'),
            responsable=data.get('usuario'),
            foto=data.get('imagen')
        )
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_bajas(request):
    bajas = BajaBalon.objects.all().order_by('-fecha')
    data = [{"id": b.id, "tipo": b.tipo_balon, "causa": b.causa, "lugar": b.marca,
             "usuario": b.responsable, "imagen": b.foto, "fecha": b.fecha} for b in bajas]
    return JsonResponse(data, safe=False)

@login_required
def api_eliminar_baja(request, baja_id):
    if request.method == "POST":
        get_object_or_404(BajaBalon, pk=baja_id).delete()
        return JsonResponse({"status": "success"})

# ============================
# 📋 API ENTREGAS Y OBJETOS
# ============================

@login_required
def api_guardar_entrega(request):
    if request.method == "POST":
        data = json.loads(request.body)
        RegistroEntrega.objects.create(
            nombre=data.get('recibido_por'),
            curso=data.get('curso'),
            objeto=data.get('balon'),
            lugar=data.get('lugar')
        )
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_entregas(request):
    entregas = list(RegistroEntrega.objects.all().values().order_by('-fecha'))
    return JsonResponse(entregas, safe=False)

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

# ============================
# ✅ GESTIÓN DE TAREAS
# ============================

@login_required
def tasks(request):
    tasks_list = Task.objects.filter(user=request.user, diaCompletado__isnull=True)
    return render(request, 'tasks.html', {'tasks': tasks_list})

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.user = request.user
            new_task.save()
            return redirect('tasks')
    return render(request, 'create_task.html', {'form': TaskForm()})

@login_required
def lista(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('tasks')
    return render(request, 'lista.html', {'task': task, 'form': TaskForm(instance=task)})

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