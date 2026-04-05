from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from datetime import datetime, timedelta
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site 
import json

# Importación de modelos y formularios propios del proyecto
from .models import Task, RegistroEntrega, ObjetoPerdido, PrendaRopa, BajaBalon
from .forms import TaskForm, CustomUserCreationForm
from .tokens import account_activation_token

# =================================================================
# 🔐 GESTIÓN DE AUTENTICACIÓN Y ROLES
# =================================================================

def es_coordinacion(user):
    """Verifica si el usuario pertenece al grupo de coordinación o es admin manual."""
    if not user.is_authenticated:
        return False
    es_admin_manual = user.username in ['rosita', 'rosita1']
    pertenece_grupo = user.groups.filter(name='coordinacion').exists()
    return es_admin_manual or pertenece_grupo

def es_asistente(user):
    """Verifica si el usuario es asistente de bienestar."""
    return user.is_authenticated and user.groups.filter(name='asistente bienestar').exists()

def signup(request):
    """Registro de nuevos usuarios con validación manual para MongoDB."""
    if request.method == 'GET':
        form = CustomUserCreationForm()
        return render(request, 'signup.html', {'form': form})
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Validación de duplicados para evitar el error 500 de Djongo/MongoDB
            if User.objects.filter(username=username).exists():
                return render(request, 'signup.html', {
                    'form': form, 
                    'error': 'Lo sentimos, ese nombre de usuario ya está ocupado.'
                })
            
            if User.objects.filter(email=email).exists():
                return render(request, 'signup.html', {
                    'form': form, 
                    'error': 'Este correo electrónico ya tiene una cuenta asociada.'
                })

            try:
                # Crear usuario inactivo hasta que confirme correo
                user = form.save(commit=False)
                user.first_name = request.POST.get('rol', 'Sin Rol')
                user.is_active = False 
                user.save()

                # Preparación del link de activación
                current_site = get_current_site(request)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = account_activation_token.make_token(user)
                protocol = 'https' if request.is_secure() else 'http'
                
                activation_link = f"{protocol}://{current_site.domain}/activar/{uid}/{token}/"
                
                subject = 'Activa tu cuenta en Live Fútbol'
                message = (
                    f"Hola {user.username},\n\n"
                    f"Gracias por unirte a Live Fútbol. Para empezar a usar la plataforma, "
                    f"por favor activa tu cuenta haciendo clic en el siguiente enlace:\n\n"
                    f"{activation_link}\n\n"
                    f"Si no solicitaste este registro, puedes ignorar este correo.\n\n"
                    f"Atentamente,\nEl equipo de Live Fútbol"
                )

                # Envío de correo seguro
                send_mail(
                    subject, 
                    message, 
                    'saebra581@gmail.com', 
                    [user.email], 
                    fail_silently=True
                )

                return render(request, 'signup.html', {
                    'form': CustomUserCreationForm(), 
                    'success': '¡Registro exitoso! Por favor revisa tu correo para activar tu cuenta.'
                })

            except Exception as e:
                return render(request, 'signup.html', {
                    'form': form, 
                    'error': f"Ocurrió un error inesperado: {str(e)}"
                })
                
        return render(request, 'signup.html', {
            'form': form, 
            'error': 'La información ingresada no es válida. Revisa los campos.'
        })

def signin(request):
    """Inicio de sesión con redirección por roles."""
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if not user.is_active:
                    return render(request, 'signin.html', {
                        'form': form, 
                        'error': 'Tu cuenta aún no ha sido activada por correo o por un administrador.'
                    })
                
                login(request, user)
                
                # Redirección según privilegios
                if es_coordinacion(user):
                    return redirect('formulario')
                elif es_asistente(user):
                    return redirect('radar')
                else:
                    return redirect('tipos')
            
        return render(request, 'signin.html', {
            'form': form, 
            'error': 'Usuario o contraseña incorrectos.'
        })

def signout(request):
    """Cierre de sesión seguro."""
    logout(request)
    return redirect('home')

def activar(request, uidb64, token):
    """Confirmación de cuenta mediante token enviado por correo."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.filter(pk=uid).first()
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'confirmar_cuenta.html')
    else:
        return render(request, 'confirmar_fallido.html')

# =================================================================
# 🏠 VISTAS DE NAVEGACIÓN GENERAL
# =================================================================

def home(request):
    return render(request, 'home.html')

def soporte(request):
    return render(request, 'soporte.html')

def condiciones(request):
    return render(request, 'condiciones.html')

@login_required
def tipos(request):
    return render(request, 'tipos.html')

# =================================================================
# 🏆 MÓDULO DE GESTIÓN (RANKING Y USUARIOS)
# =================================================================

@user_passes_test(es_coordinacion)
def ranking(request):
    """Vista principal para la gestión de usuarios."""
    return render(request, 'ranking.html')

@user_passes_test(es_coordinacion)
def api_obtener_usuarios_gestion(request):
    """API para listar usuarios excluyendo admins y cuentas de sistema."""
    usuarios_list = User.objects.exclude(username__in=['rosita', 'rosita1'])
    usuarios = [u for u in usuarios_list if not u.is_superuser]

    data = []
    for u in usuarios:
        data.append({
            'id': u.id,
            'nombre': u.username,
            'email': u.email,
            'rol': u.first_name,
            'estado': 'activo' if u.is_active else 'pendiente',
            'grupo_asignado': u.groups.first().name if u.groups.exists() else 'Sin Grupo'
        })
    return JsonResponse(data, safe=False)

@user_passes_test(es_coordinacion)
def api_cambiar_estado_usuario(request, user_id):
    """Activa o desactiva usuarios y les asigna grupo por su rol."""
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=user_id)
        usuario.is_active = not usuario.is_active
        
        if usuario.is_active:
            rol_texto = (usuario.first_name or "").lower()
            nombre_grupo = ''
            
            if 'profesor' in rol_texto:
                nombre_grupo = 'profesores'
            elif 'coordinacion' in rol_texto:
                nombre_grupo = 'coordinacion'
            elif 'asistente' in rol_texto:
                nombre_grupo = 'asistente bienestar'
            
            if nombre_grupo:
                grupo, created = Group.objects.get_or_create(name=nombre_grupo)
                usuario.groups.add(grupo)
            
            # Notificar al usuario por correo
            try:
                send_mail(
                    'Cuenta Activada - Live Fútbol',
                    f'Hola {usuario.username}, tu cuenta ha sido activada con éxito.',
                    'saebra581@gmail.com',
                    [usuario.email],
                    fail_silently=True
                )
            except:
                pass
                
        usuario.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=405)

@user_passes_test(es_coordinacion)
def api_eliminar_usuario(request, user_id):
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=user_id)
        usuario.delete()
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'status': 'error'}, status=405)

# =================================================================
# ⚽ MÓDULO DE BALONES (RADAR)
# =================================================================

@user_passes_test(es_asistente)
def radar(request):
    """Panel de control para entregas y bajas de balones."""
    return render(request, 'radar.html')

@user_passes_test(es_asistente)
def api_guardar_entrega(request):
    if request.method == "POST":
        data = json.loads(request.body)
        RegistroEntrega.objects.create(
            nombre=data.get('recibido_por'), 
            objeto=data.get('balon'), 
            curso=data.get('curso'),
            lugar=data.get('lugar')
        )
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

@login_required
def api_obtener_entregas(request):
    entregas = RegistroEntrega.objects.all().order_by('-fecha')
    data = []
    for e in entregas:
        data.append({
            "id": e.id, 
            "nombre": e.nombre, 
            "objeto": e.objeto, 
            "curso": e.curso, 
            "lugar": e.lugar, 
            "fecha": e.fecha.isoformat()
        })
    return JsonResponse(data, safe=False)

@user_passes_test(es_asistente)
def api_editar_entrega(request, entrega_id):
    if request.method == "POST":
        data = json.loads(request.body)
        entrega = get_object_or_404(RegistroEntrega, pk=entrega_id)
        entrega.nombre = data.get('nombre', entrega.nombre)
        entrega.objeto = data.get('objeto', entrega.objeto)
        entrega.curso = data.get('curso', entrega.curso)
        entrega.lugar = data.get('lugar', entrega.lugar)
        entrega.save()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

@user_passes_test(es_asistente)
def api_guardar_baja(request):
    if request.method == "POST":
        data = json.loads(request.body)
        imagen = data.get('imagen') or '/static/sin evidencia.webp'
        BajaBalon.objects.create(
            tipo_balon=data.get('tipo'), 
            causa=data.get('causa'), 
            responsable=data.get('usuario'),
            marca=data.get('lugar'),
            alquilado_por=data.get('alquilado_por'),
            foto=imagen
        )
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

@login_required
def api_obtener_bajas(request):
    bajas = BajaBalon.objects.all().order_by('-fecha')
    data = []
    for b in bajas:
        data.append({
            "id": b.id, 
            "tipo": b.tipo_balon, 
            "causa": b.causa, 
            "responsable": b.responsable, 
            "lugar": b.marca, 
            "alquilado_por": b.alquilado_por, 
            "imagen": b.foto, 
            "fecha": b.fecha.isoformat()
        })
    return JsonResponse(data, safe=False)

# =================================================================
# 👗 MÓDULO DE INDUMENTARIA (ROPA)
# =================================================================

@user_passes_test(es_coordinacion)
def formulario(request):
    """Vista de gestión de inventario de ropa para coordinación."""
    return render(request, 'formulario.html')

@user_passes_test(es_coordinacion)
def api_guardar_prenda(request):
    if request.method == "POST":
        data = json.loads(request.body)
        PrendaRopa.objects.create(
            objeto=data.get('nombre'),
            cantidad=int(data.get('cantidad', 1)),
            talla=data.get('talla', ''),
            imagen=data.get('imagen', ''),
            estado='Disponible'
        )
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=405)

@login_required
def api_obtener_prendas(request):
    talla_filtro = request.GET.get('talla')
    if talla_filtro:
        prendas = PrendaRopa.objects.filter(talla__iexact=talla_filtro).order_by('-fecha_registro')
    else:
        prendas = PrendaRopa.objects.all().order_by('-fecha_registro')
        
    result = []
    for p in prendas:
        try:
            dias = int(p.dias_alquiler) if p.dias_alquiler else 0
            fecha_devolucion = (p.fecha_uso + timedelta(days=dias)).strftime('%d/%m/%Y') if p.fecha_uso else ''
        except:
            fecha_devolucion = ''

        result.append({
            'id': p.id, 
            'nombre': p.objeto, 
            'cantidad': p.cantidad, 
            'cantidad_apartada': p.cantidad_apartada,
            'talla': p.talla, 
            'estado': p.estado, 
            'detalle_defecto': p.detalle_defecto,
            'profesor': p.nombre_apartado or '', 
            'curso': p.curso_apartado or '',
            'evento': p.evento_apartado or '', 
            'dias_alquiler': p.dias_alquiler,
            'fecha_uso': p.fecha_uso.strftime('%d/%m/%Y') if p.fecha_uso else '',
            'fecha_devolucion': fecha_devolucion, 
            'imagen': p.imagen
        })
    return JsonResponse(result, safe=False)

@login_required
def api_apartar_prenda(request, prenda_id):
    prenda = get_object_or_404(PrendaRopa, id=prenda_id)
    if request.method == 'POST':
        data = json.loads(request.body)
        accion = data.get('accion', 'apartar')

        if accion == 'apartar':
            cantidad_solicitada = int(data.get('cantidad_alquilada', 1))
            if cantidad_solicitada > prenda.cantidad:
                return JsonResponse({'status': 'error', 'message': 'No hay suficiente stock disponible.'}, status=400)
            
            prenda.cantidad -= cantidad_solicitada
            prenda.cantidad_apartada += cantidad_solicitada
            prenda.estado = 'Apartado' if prenda.cantidad == 0 else 'Parcialmente Apartado'
            prenda.nombre_apartado = data.get('nombre')
            prenda.save()
            return JsonResponse({'status': 'ok'})
            
        elif accion == 'liberar':
            prenda.cantidad += prenda.cantidad_apartada
            prenda.cantidad_apartada = 0
            prenda.estado = 'Disponible'
            prenda.save()
            return JsonResponse({'status': 'ok'})
            
    return JsonResponse({'status': 'error'}, status=405)

# =================================================================
# 🔍 MÓDULO DE OBJETOS PERDIDOS
# =================================================================

@login_required
def api_guardar_objeto(request):
    if request.method == "POST":
        data = json.loads(request.body)
        ObjetoPerdido.objects.create(
            nombre_reporta=data.get('nombre'), 
            tipo_objeto=data.get('tipo'), 
            descripcion=data.get('dif')
        )
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

@login_required
def api_obtener_objetos(request):
    objetos = ObjetoPerdido.objects.all().order_by('-fecha')
    data = []
    for o in objetos:
        data.append({
            "id": o.id, 
            "nombre": o.nombre_reporta, 
            "tipo": o.tipo_objeto, 
            "descripcion": o.descripcion, 
            "fecha": o.fecha.strftime('%d/%m/%Y') if o.fecha else "Sin fecha"
        })
    return JsonResponse(data, safe=False)

# =================================================================
# 📝 MÓDULO DE TAREAS PERSONALES (TASKS)
# =================================================================

@login_required
def tasks(request):
    """Lista de tareas pendientes del usuario logueado."""
    tasks_list = Task.objects.filter(user=request.user, diaCompletado__isnull=True)
    return render(request, 'tasks.html', {'tasks': tasks_list})

@login_required
def create_task(request):
    if request.method == 'GET':
        return render(request, 'create_task.html', {'form': TaskForm()})
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            nueva_tarea = form.save(commit=False)
            nueva_tarea.user = request.user
            nueva_tarea.save()
            return redirect('tasks')
        return render(request, 'create_task.html', {'form': form})

@login_required
def completar(request, task_id):
    tarea = get_object_or_404(Task, pk=task_id, user=request.user)
    tarea.diaCompletado = timezone.now()
    tarea.save()
    return redirect('tasks')

@login_required
def eliminar_tarea(request, task_id):
    tarea = get_object_or_404(Task, pk=task_id, user=request.user)
    tarea.delete()
    return redirect('tasks')

# =================================================================
# 🎥 VISTAS DE MULTIMEDIA
# =================================================================

@user_passes_test(es_asistente)
def videos(request):
    return render(request, 'videos.html')

@user_passes_test(es_asistente)
def voz(request):
    return render(request, 'voz.html')