from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.http import JsonResponse
import json

# Importación de modelos y formularios
from .models import Task, RegistroEntrega, ObjetoPerdido, PrendaRopa, BajaBalon
from .forms import TaskForm, CustomUserCreationForm
from .tokens import account_activation_token

# ==========================================
# 🔐 FUNCIONES DE VERIFICACIÓN
# ==========================================
def es_coordinacion(user):
    return user.is_authenticated and (user.groups.filter(name='coordinacion').exists() or user.username == 'rosita')

def es_asistente(user):
    return user.is_authenticated and user.groups.filter(name='asistente bienestar').exists()

# ==========================================
# 🏠 VISTAS PÚBLICAS Y AUTENTICACIÓN
# ==========================================
def home(request): return render(request, 'home.html')
def soporte(request): return render(request, 'soporte.html')
def condiciones(request): return render(request, 'condiciones.html')
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

@login_required
def tipos(request): return render(request, 'tipos.html')

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': CustomUserCreationForm()})
    form = CustomUserCreationForm(request.POST)
    if form.is_valid():
        try:
            user = form.save(commit=False)
            user.first_name = request.POST.get('rol', 'Sin Rol')
            user.is_active = False 
            user.save()
            return render(request, 'signup.html', {'form': CustomUserCreationForm(), 'success': '¡Solicitud enviada!'})
        except Exception as e:
            return render(request, 'signup.html', {'form': form, 'error': str(e)})
    return render(request, 'signup.html', {'form': form, 'error': "Datos inválidos"})

def signin(request):
    if request.method == 'GET': return render(request, 'signin.html', {'form': AuthenticationForm()})
    user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
    if user is not None:
        if not user.is_active: return render(request, 'signin.html', {'form': AuthenticationForm(), 'error': 'Cuenta pendiente.'})
        login(request, user)
        if es_coordinacion(user): return redirect('formulario')
        if es_asistente(user): return redirect('radar')
        return redirect('tipos')
    return render(request, 'signin.html', {'form': AuthenticationForm(), 'error': 'Credenciales incorrectas'})

def signout(request):
    logout(request)
    return redirect('home')

# ==========================================
# 🏆 GESTIÓN (RANKING)
# ==========================================
@user_passes_test(es_coordinacion)
def ranking(request): return render(request, 'ranking.html')

@user_passes_test(es_coordinacion)
def api_obtener_usuarios_gestion(request):
    usuarios = User.objects.exclude(username='rosita').exclude(is_superuser=True)
    data = [{'id': u.id, 'nombre': u.username, 'email': u.email, 'rol': u.first_name, 'estado': 'activo' if u.is_active else 'pendiente'} for u in usuarios]
    return JsonResponse(data, safe=False)

@user_passes_test(es_coordinacion)
def api_eliminar_usuario(request, user_id):
    """Elimina un usuario de la base de datos (Solo Coordinación)"""
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=user_id)
        usuario.delete()
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

# ==========================================
# ⚽ MÓDULO BALONES (SOLO ASISTENTE)
# ==========================================
@user_passes_test(es_asistente)
def radar(request): return render(request, 'radar.html')

@user_passes_test(es_asistente)
def api_guardar_entrega(request):
    if request.method == "POST":
        data = json.loads(request.body)
        RegistroEntrega.objects.create(nombre=data.get('recibido_por'), objeto=data.get('balon'), curso=data.get('curso'))
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_entregas(request):
    entregas = RegistroEntrega.objects.all().order_by('-fecha')
    data = [{"id": e.id, "nombre": e.nombre, "objeto": e.objeto, "curso": e.curso, "fecha": e.fecha.strftime('%d/%m/%Y %H:%M')} for e in entregas]
    return JsonResponse(data, safe=False)

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
    bajas = BajaBalon.objects.all().order_by('-fecha')
    data = [{"id": b.id, "tipo": b.tipo_balon, "causa": b.causa, "responsable": b.responsable, "fecha": b.fecha.strftime('%d/%m/%Y %H:%M')} for b in bajas]
    return JsonResponse(data, safe=False)

@user_passes_test(es_asistente)
def api_eliminar_baja(request, baja_id):
    if request.method == "POST":
        get_object_or_404(BajaBalon, pk=baja_id).delete()
        return JsonResponse({"status": "success"})

# ==========================================
# 👗 MÓDULO ROPA Y OTROS
# ==========================================
@user_passes_test(es_coordinacion)
def api_guardar_prenda(request):
    if request.method == "POST":
        data = json.loads(request.body)
        PrendaRopa.objects.create(objeto=data.get('nombre'), cantidad=int(data.get('cantidad', 1)), talla=data.get('talla', 'N/A'), estado='Disponible')
        return JsonResponse({"status": "ok"})

@login_required
def api_obtener_prendas(request):
    return JsonResponse(list(PrendaRopa.objects.all().values().order_by('-fecha_registro')), safe=False)

@login_required
def tasks(request):
    tasks_list = Task.objects.filter(user=request.user, diaCompletado__isnull=True)
    return render(request, 'tasks.html', {'tasks': tasks_list})

@login_required
def api_guardar_objeto(request):
    """Guarda un nuevo objeto perdido"""
    if request.method == "POST":
        data = json.loads(request.body)
        ObjetoPerdido.objects.create(
            nombre_reporta=data.get('nombre'), 
            tipo_objeto=data.get('tipo'), 
            descripcion=data.get('dif')
        )
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_objetos(request):
    """Lista de objetos perdidos con formato de fecha seguro"""
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

@login_required
def api_eliminar_objeto(request, obj_id):
    """Elimina un objeto perdido de la lista"""
    if request.method == "POST":
        get_object_or_404(ObjetoPerdido, pk=obj_id).delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)