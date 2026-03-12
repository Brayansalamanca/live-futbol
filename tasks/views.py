from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
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

# ==========================================
# 🔐 FUNCIONES DE VERIFICACIÓN (GRUPOS)
# ==========================================

def es_coordinacion(user):
    return user.is_authenticated and (user.groups.filter(name='coordinacion').exists() or user.username == 'rosita')

def es_asistente(user):
    return user.is_authenticated and user.groups.filter(name='asistente bienestar').exists()

def es_profesor(user):
    return user.is_authenticated and user.groups.filter(name='profesores').exists()

# ==========================================
# 🏠 VISTAS PÚBLICAS Y BASE
# ==========================================

def home(request): return render(request, 'home.html')
def soporte(request): return render(request, 'soporte.html')
def condiciones(request): return render(request, 'condiciones.html')

@login_required
def tipos(request): return render(request, 'tipos.html')

@user_passes_test(es_coordinacion)
def formulario(request): return render(request, 'formulario.html')

@user_passes_test(es_coordinacion)
def ranking(request): return render(request, 'ranking.html')

# ==========================================
# 🔐 AUTENTICACIÓN Y REGISTRO
# ==========================================

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
            # Guardamos el rol seleccionado en el campo first_name para usarlo luego
            user.first_name = request.POST.get('rol', 'Sin Rol')
            user.is_active = False 
            user.save()
            
            return render(request, 'signup.html', {
                'form': CustomUserCreationForm(),
                'success': '¡Solicitud enviada! Un administrador debe aprobar tu acceso.'
            })
        except Exception as e:
            return render(request, 'signup.html', {'form': form, 'error': f'Error en el registro: {e}'})
    
    # Diagnóstico de errores para el usuario
    errors = form.errors.as_data()
    error_msg = "Datos inválidos: "
    for field, detail in errors.items():
        error_msg += f"[{field}: {detail[0].message}] "
    return render(request, 'signup.html', {'form': form, 'error': error_msg})

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
    return render(request, 'confirmar_fallido.html')

def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        if not user.is_active:
            return render(request, 'signin.html', {
                'form': AuthenticationForm(),
                'error': 'Tu cuenta está pendiente de aprobación.'
            })
        login(request, user)
        # Redirección inteligente por grupo
        if es_coordinacion(user): return redirect('formulario')
        if es_asistente(user): return redirect('radar')
        return redirect('tipos')
    
    return render(request, 'signin.html', {'form': AuthenticationForm(), 'error': 'Usuario o contraseña incorrectos'})

def signout(request):
    logout(request)
    return redirect('home')

# ==========================================
# 🏆 GESTIÓN DE USUARIOS (GRUPOS AUTOMÁTICOS)
# ==========================================

@user_passes_test(es_coordinacion)
def api_obtener_usuarios_gestion(request):
    usuarios_db = User.objects.exclude(username='rosita').exclude(is_superuser=True)
    data = []
    for u in usuarios_db:
        # Obtenemos el nombre del grupo principal si existe
        grupo = u.groups.first().name if u.groups.exists() else "Sin Grupo"
        data.append({
            'id': u.id,
            'nombre': u.username,
            'email': u.email,
            'rol': u.first_name, 
            'grupo_asignado': grupo,
            'estado': 'activo' if u.is_active else 'pendiente'
        })
    return JsonResponse(data, safe=False)

@user_passes_test(es_coordinacion)
def api_cambiar_estado_usuario(request, user_id):
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=user_id)
        usuario.is_active = not usuario.is_active
        
        # Asignación automática de grupo al activar
        if usuario.is_active:
            rol = usuario.first_name.lower()
            nombre_grupo = ""
            if "profesor" in rol: nombre_grupo = 'profesores'
            elif "coordinacion" in rol: nombre_grupo = 'coordinacion'
            elif "asistente" in rol: nombre_grupo = 'asistente bienestar'
            
            if nombre_grupo:
                grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
                usuario.groups.add(grupo)
        
        usuario.save()
        return JsonResponse({'status': 'ok', 'nuevo_estado': usuario.is_active})

@user_passes_test(es_coordinacion)
def api_eliminar_usuario(request, user_id):
    if request.method == 'POST':
        get_object_or_404(User, id=user_id).delete()
        return JsonResponse({'status': 'deleted'})

# ==========================================
# ⚽ MÓDULOS DE INVENTARIO Y BALONES
# ==========================================

@user_passes_test(es_asistente)
def radar(request): return render(request, 'radar.html')

@user_passes_test(es_asistente)
def videos(request): return render(request, 'videos.html')

@user_passes_test(es_asistente)
def voz(request): return render(request, 'voz.html')

# --- APIS DE ROPA ---
@user_passes_test(es_coordinacion)
def api_eliminar_prenda(request, prenda_id):
    if request.method == "POST":
        prenda = get_object_or_404(PrendaRopa, pk=prenda_id)
        prenda.delete()
        return JsonResponse({"status": "success", "message": "Prenda eliminada correctamente"})
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
@user_passes_test(es_coordinacion)
def api_guardar_prenda(request):
    if request.method == "POST":
        data = json.loads(request.body)
        prenda = PrendaRopa.objects.create(
            objeto=data.get('nombre'),
            cantidad=int(data.get('cantidad', 1)),
            talla=data.get('talla', 'N/A'),
            imagen=data.get('imagen'),
            estado='Disponible'
        )
        return JsonResponse({"status": "ok", "id": prenda.id})

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
            prenda.estado, prenda.nombre_apartado = "Disponible", ""
        else:
            prenda.estado, prenda.nombre_apartado = "Apartado", data.get('nombre')
        prenda.save()
        return JsonResponse({"status": "success"})

# --- APIS DE BALONES ---
@user_passes_test(es_profesor)
def api_guardar_entrega(request):
    if request.method == "POST":
        data = json.loads(request.body)
        RegistroEntrega.objects.create(nombre=data.get('recibido_por'), objeto=data.get('balon'), curso=data.get('curso'))
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_entregas(request):
    entregas = list(RegistroEntrega.objects.all().values().order_by('-fecha'))
    return JsonResponse(entregas, safe=False)

@user_passes_test(es_asistente)
def api_eliminar_entrega(request, entrega_id):
    if request.method == "POST":
        get_object_or_404(RegistroEntrega, pk=entrega_id).delete()
        return JsonResponse({"status": "success"})

@user_passes_test(es_asistente)
def api_guardar_baja(request):
    if request.method == "POST":
        data = json.loads(request.body)
        BajaBalon.objects.create(tipo_balon=data.get('tipo'), causa=data.get('causa'), responsable=data.get('usuario'))
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_bajas(request):
    bajas = list(BajaBalon.objects.all().values().order_by('-fecha'))
    return JsonResponse(bajas, safe=False)

# ==========================================
# ✅ TAREAS Y OBJETOS PERDIDOS
# ==========================================

@login_required
def tasks(request):
    tasks_list = Task.objects.filter(user=request.user, diaCompletado__isnull=True)
    return render(request, 'tasks.html', {'tasks': tasks_list})

@login_required
def create_task(request):
    if request.method == 'GET': return render(request, 'create_task.html', {'form': TaskForm()})
    form = TaskForm(request.POST)
    if form.is_valid():
        new_task = form.save(commit=False); new_task.user = request.user; new_task.save()
        return redirect('tasks')
    return render(request, 'create_task.html', {'form': form})

@login_required
def api_guardar_objeto(request):
    if request.method == "POST":
        data = json.loads(request.body)
        ObjetoPerdido.objects.create(nombre_reporta=data.get('nombre'), tipo_objeto=data.get('tipo'), descripcion=data.get('dif'))
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_objetos(request):
    return JsonResponse(list(ObjetoPerdido.objects.all().values().order_by('-fecha')), safe=False)
    # --- FUNCIONES FALTANTES PARA OBJETOS PERDIDOS Y TAREAS ---

@login_required
def api_eliminar_objeto(request, obj_id):
    if request.method == "POST":
        objeto = get_object_or_404(ObjetoPerdido, pk=obj_id)
        objeto.delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

@login_required
def lista(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'GET':
        form = TaskForm(instance=task)
        return render(request, 'task_detail.html', {'task': task, 'form': form})
    else:
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('tasks')
        return render(request, 'task_detail.html', {'task': task, 'form': form})

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
@user_passes_test(es_asistente)
def api_eliminar_baja(request, baja_id):
    if request.method == "POST":
        baja = get_object_or_404(BajaBalon, pk=baja_id)
        baja.delete()
        return JsonResponse({"status": "success", "message": "Registro de baja eliminado"})
    return JsonResponse({"status": "error"}, status=405)