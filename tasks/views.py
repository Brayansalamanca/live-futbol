from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test # <--- CAMBIO AQUÍ
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

# Función de verificación (Añadir después de los imports)
def es_rosita(user):
    return user.is_authenticated and user.username == 'rosita'

# ============================
# 🏠 VISTAS PÚBLICAS
# ============================
def home(request): return render(request, 'home.html')
def soporte(request): return render(request, 'soporte.html')
def tipos(request): return render(request, 'tipos.html')
def formulario(request): return render(request, 'formulario.html')
def ranking(request): return render(request, 'ranking.html')
def condiciones(request): return render(request, 'condiciones.html')

# ============================
# 🔐 AUTENTICACIÓN Y GESTIÓN
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
            # CAPTURAMOS EL ROL: Importante para que Rosita lo vea en el Ranking
            user.first_name = request.POST.get('rol', 'Usuario')
            user.is_active = False 
            user.save()
            
            return render(request, 'signup.html', {
                'form': CustomUserCreationForm(),
                'success': '¡Solicitud enviada! Rosita debe aprobar tu acceso.'
            })
        except Exception as e:
            return render(request, 'signup.html', {'form': form, 'error': f'Error en BD: {e}'})
    
    # --- CAMBIO CLAVE AQUÍ ---
    # Esto extraerá el error específico (ej: "Contraseña muy corta")
    errores = form.errors.as_data()
    msg_error = "Datos inválidos: "
    for campo, detalles in errores.items():
        # detalles[0].message suele traer el texto del error de Django
        msg_error += f"[{campo}: {detalles[0].message}] "

    return render(request, 'signup.html', {'form': form, 'error': msg_error})

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
                'error': 'Tu cuenta está pendiente de aprobación por Rosita.'
            })
        login(request, user)
        # Redirección por roles
        if user.username == 'rosita': return redirect('formulario')
        elif user.username == 'asistente_bienestar1': return redirect('radar')
        return redirect('tipos')
    else:
        return render(request, 'signin.html', {
            'form': AuthenticationForm(),
            'error': 'Usuario o contraseña incorrectos'
        })
# ==========================================
# 🏆 GESTIÓN DE USUARIOS (RANKING - ROSITA)
# ==========================================

@user_passes_test(es_rosita)
def api_obtener_usuarios_gestion(request):
    """API: Retorna la lista con rol capturado desde first_name"""
    usuarios_db = User.objects.exclude(username='rosita').exclude(is_superuser=True)
    data = []
    for u in usuarios_db:
        data.append({
            'id': u.id,
            'nombre': u.username,
            'email': u.email,
            'rol': u.first_name, # El rol que guardamos en signup
            'estado': 'activo' if u.is_active else 'pendiente'
        })
    return JsonResponse(data, safe=False)

@user_passes_test(es_rosita)
def api_cambiar_estado_usuario(request, user_id):
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=user_id)
        usuario.is_active = not usuario.is_active
        usuario.save()
        return JsonResponse({'status': 'ok', 'nuevo_estado': usuario.is_active})

@user_passes_test(es_rosita)
def api_eliminar_usuario(request, user_id):
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=user_id)
        usuario.delete()
        return JsonResponse({'status': 'deleted'})
def signout(request):
    logout(request)
    return redirect('home')



# ============================
# 📦 INVENTARIO ROPA
# ============================
@login_required
def radar(request): return render(request, 'radar.html')

@login_required
def api_guardar_prenda(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            prenda = PrendaRopa.objects.create(
                objeto=data.get('nombre'),
                cantidad=int(data.get('cantidad', 1)),
                talla=data.get('talla', 'N/A'),
                condicion=data.get('condicion', 'Óptimo'),
                detalle_defecto=data.get('detalle_defecto', ''),
                imagen=data.get('imagen'),
                estado='Disponible',
                devuelto=True
            )
            return JsonResponse({"status": "ok", "id": prenda.id})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

@login_required
def api_obtener_prendas(request):
    prendas_qs = PrendaRopa.objects.all().order_by('-fecha_registro')
    data = [{"id": p.id, "nombre": p.objeto, "cantidad": p.cantidad, "imagen": p.imagen, "estado": p.estado, "profesor": p.nombre_apartado or "Disponible", "curso": p.curso_apartado or "---", "evento": p.evento_apartado or "---", "fecha_uso": str(p.fecha_uso) if p.fecha_uso else "---", "devuelto": p.devuelto} for p in prendas_qs]
    return JsonResponse(data, safe=False)

@login_required
def api_apartar_prenda(request, prenda_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            prenda = get_object_or_404(PrendaRopa, pk=prenda_id)
            if data.get('accion') == 'liberar':
                prenda.estado, prenda.nombre_apartado, prenda.curso_apartado, prenda.evento_apartado, prenda.fecha_uso, prenda.devuelto = "Disponible", "", "", "", None, True
            else:
                prenda.estado, prenda.nombre_apartado, prenda.curso_apartado, prenda.evento_apartado, prenda.fecha_uso, prenda.devuelto = "Apartado", data.get('nombre', request.user.username), data.get('curso', 'N/A'), data.get('evento', 'N/A'), data.get('fecha'), False
            prenda.save()
            return JsonResponse({"status": "success"})
        except Exception as e: return JsonResponse({"status": "error", "message": str(e)}, status=400)

@login_required
def api_eliminar_prenda(request, prenda_id):
    if request.method == "POST":
        get_object_or_404(PrendaRopa, pk=prenda_id).delete()
        return JsonResponse({"status": "success"})

# ============================
# ⚽ ENTREGAS BALONES
# ============================
@login_required
def videos(request): return render(request, 'videos.html')

@login_required
def api_guardar_entrega(request):
    if request.method == "POST":
        data = json.loads(request.body)
        RegistroEntrega.objects.create(nombre=data.get('recibido_por'), curso=data.get('curso', 'N/A'), objeto=data.get('balon'), lugar=data.get('lugar', 'Cancha'))
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_entregas(request):
    entregas = list(RegistroEntrega.objects.all().values().order_by('-fecha'))
    return JsonResponse(entregas, safe=False)

@login_required
def api_eliminar_entrega(request, entrega_id):
    if request.method == "POST":
        get_object_or_404(RegistroEntrega, pk=entrega_id).delete()
        return JsonResponse({"status": "success"})

# ============================
# 📉 BAJAS BALONES
# ============================
@login_required
def api_guardar_baja(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            BajaBalon.objects.create(
                tipo_balon=data.get('tipo'),
                causa=data.get('causa'),
                marca=data.get('lugar', 'N/A'),
                responsable=data.get('usuario'), 
                alquilado_por=data.get('alquilado_por'),
                foto=data.get('imagen') 
            )
            return JsonResponse({"status": "success"})
        except Exception as e: return JsonResponse({"status": "error", "message": str(e)}, status=400)

@login_required
def api_obtener_bajas(request):
    bajas = [{"id": b.id, "tipo": b.tipo_balon, "causa": b.causa, "lugar": b.marca, "usuario": b.responsable, "alquilado_por": b.alquilado_por, "imagen": b.foto, "fecha": b.fecha} for b in BajaBalon.objects.all().order_by('-fecha')]
    return JsonResponse(bajas, safe=False)

@login_required
def api_eliminar_baja(request, baja_id):
    if request.method == "POST":
        try:
            get_object_or_404(BajaBalon, pk=baja_id).delete()
            return JsonResponse({"status": "success"})
        except Exception as e: return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error"}, status=405)

# ============================
# 🔍 OBJETOS PERDIDOS
# ============================
@login_required
def voz(request): return render(request, 'voz.html')

@login_required
def api_guardar_objeto(request):
    if request.method == "POST":
        data = json.loads(request.body)
        ObjetoPerdido.objects.create(nombre_reporta=data.get('nombre'), curso=data.get('curso'), tipo_objeto=data.get('tipo'), color=data.get('color'), descripcion=data.get('dif'))
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_objetos(request):
    return JsonResponse(list(ObjetoPerdido.objects.all().values().order_by('-fecha')), safe=False)

@login_required
def api_eliminar_objeto(request, obj_id):
    if request.method == "POST":
        get_object_or_404(ObjetoPerdido, pk=obj_id).delete()
        return JsonResponse({"status": "success"})

# ============================
# ✅ TAREAS
# ============================
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
def lista(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'GET': return render(request, 'lista.html', {'task': task, 'form': TaskForm(instance=task)})
    form = TaskForm(request.POST, instance=task)
    if form.is_valid(): form.save(); return redirect('tasks')
    return render(request, 'lista.html', {'task': task, 'form': form})

@login_required
def completar(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST': task.diaCompletado = timezone.now(); task.save()
    return redirect('tasks')

@login_required
def eliminar_tarea(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST': task.delete()
    return redirect('tasks')