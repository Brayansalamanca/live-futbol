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
import json

# Importación de modelos y formularios
from .models import Task, RegistroEntrega, ObjetoPerdido, PrendaRopa, BajaBalon
from .forms import TaskForm, CustomUserCreationForm
from .tokens import account_activation_token
from django.contrib.sites.shortcuts import get_current_site 

# ==========================================
# 🔐 RECUPERACIÓN DE CONTRASEÑA
# ==========================================
class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    template_name = 'recuperar_contraseña.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    success_message = "Instrucciones enviadas al correo."
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        try:
            usuarios = list(User.objects.filter(email=email, is_active=True))
            if usuarios:
                form.save(
                    email_template_name=self.email_template_name,
                    subject_template_name=self.subject_template_name,
                    request=self.request,
                    use_https=self.request.is_secure(),
                )
        except Exception as e:
            print(f"Error de base de datos: {e}")
        return redirect(self.success_url)

# ==========================================
# 🔐 FUNCIONES DE VERIFICACIÓN
# ==========================================
def es_coordinacion(user):
    return user.is_authenticated and (user.groups.filter(name='coordinacion').exists() or user.username in ['rosita', 'rosita1'])

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
        username = form.cleaned_data.get('username')
        email = form.cleaned_data.get('email')

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'form': form, 'error': 'El usuario ya existe.'})
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'form': form, 'error': 'El correo ya está registrado.'})

        try:
            user = form.save(commit=False)
            user.first_name = request.POST.get('rol', 'Sin Rol')
            user.is_active = False 
            user.save()

            current_site = get_current_site(request)
            domain = current_site.domain
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            
            link = f"https://{domain}/activar/{uid}/{token}/"
            mensaje = f"Hola {user.username},\n\nActiva tu cuenta aquí: {link}"

            send_mail('Activa tu cuenta', mensaje, 'saebra581@gmail.com', [user.email])

            return render(request, 'signup.html', {'form': CustomUserCreationForm(), 'success': '¡Revisa tu correo!'})
        except Exception as e:
            return render(request, 'signup.html', {'form': form, 'error': f"Error: {e}"})
            
    return render(request, 'signup.html', {'form': form, 'error': "Datos inválidos"})

def signin(request):
    if request.method == 'GET': 
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    
    user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
    if user is not None:
        if not user.is_active: 
            return render(request, 'signin.html', {'form': AuthenticationForm(), 'error': 'Cuenta no activada.'})
        login(request, user)
        if es_coordinacion(user): return redirect('formulario')
        if es_asistente(user): return redirect('radar')
        return redirect('tipos')
    return render(request, 'signin.html', {'form': AuthenticationForm(), 'error': 'Datos incorrectos'})

def signout(request):
    logout(request)
    return redirect('home')

# ==========================================
# ⚽ APIs Y GESTIÓN
# ==========================================
@user_passes_test(es_coordinacion)
def ranking(request): return render(request, 'ranking.html')

@user_passes_test(es_coordinacion)
def api_obtener_usuarios_gestion(request):
    usuarios = [u for u in User.objects.exclude(username__in=['rosita', 'rosita1']) if not u.is_superuser]
    data = [{'id': u.id, 'nombre': u.username, 'email': u.email, 'rol': u.first_name, 'estado': 'activo' if u.is_active else 'pendiente'} for u in usuarios]
    return JsonResponse(data, safe=False)

@user_passes_test(es_coordinacion)
def api_eliminar_usuario(request, user_id):
    if request.method == 'POST':
        get_object_or_404(User, id=user_id).delete()
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'status': 'error'}, status=405)

@user_passes_test(es_asistente)
def radar(request): return render(request, 'radar.html')

@user_passes_test(es_asistente)
def api_guardar_entrega(request):
    if request.method == "POST":
        data = json.loads(request.body)
        RegistroEntrega.objects.create(nombre=data.get('recibido_por'), objeto=data.get('balon'), curso=data.get('curso'), lugar=data.get('lugar'))
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_entregas(request):
    entregas = RegistroEntrega.objects.all().order_by('-fecha')
    data = [{"id": e.id, "nombre": e.nombre, "objeto": e.objeto, "curso": e.curso, "lugar": e.lugar, "fecha": e.fecha.isoformat()} for e in entregas]
    return JsonResponse(data, safe=False)

@user_passes_test(es_asistente)
def api_eliminar_entrega(request, entrega_id):
    if request.method == "POST":
        get_object_or_404(RegistroEntrega, pk=entrega_id).delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

@user_passes_test(es_asistente)
def api_editar_entrega(request, entrega_id):
    if request.method == "POST":
        data = json.loads(request.body)
        e = get_object_or_404(RegistroEntrega, pk=entrega_id)
        e.nombre = data.get('nombre')
        e.objeto = data.get('objeto')
        e.curso = data.get('curso')
        e.lugar = data.get('lugar')
        e.save()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

@user_passes_test(es_asistente)
def api_guardar_baja(request):
    if request.method == "POST":
        data = json.loads(request.body)
        BajaBalon.objects.create(
            tipo_balon=data.get('tipo'), 
            causa=data.get('causa'), 
            responsable=data.get('usuario'), 
            marca=data.get('lugar'), 
            alquilado_por=data.get('alquilado_por'), 
            foto=data.get('imagen', '/static/sin evidencia.webp')
        )
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_bajas(request):
    bajas = BajaBalon.objects.all().order_by('-fecha')
    data = [{"id": b.id, "tipo": b.tipo_balon, "causa": b.causa, "responsable": b.responsable, "lugar": b.marca, "alquilado_por": b.alquilado_por, "imagen": b.foto, "fecha": b.fecha.isoformat()} for b in bajas]
    return JsonResponse(data, safe=False)

@user_passes_test(es_asistente)
def api_eliminar_baja(request, baja_id):
    if request.method == "POST":
        get_object_or_404(BajaBalon, pk=baja_id).delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

@user_passes_test(es_coordinacion)
def api_guardar_prenda(request):
    if request.method == "POST":
        data = json.loads(request.body)
        PrendaRopa.objects.create(objeto=data.get('nombre'), cantidad=int(data.get('cantidad', 1)), talla=data.get('talla', ''), imagen=data.get('imagen', ''), estado='Disponible')
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=405)

@login_required
def api_obtener_prendas(request):
    talla = request.GET.get('talla')
    prendas = PrendaRopa.objects.filter(talla__iexact=talla) if talla else PrendaRopa.objects.all()
    result = []
    for p in prendas.order_by('-fecha_registro'):
        result.append({'id': p.id, 'nombre': p.objeto, 'cantidad': p.cantidad, 'talla': p.talla, 'estado': p.estado, 'imagen': p.imagen})
    return JsonResponse(result, safe=False)

@login_required
def tasks(request):
    return render(request, 'tasks.html', {'tasks': Task.objects.filter(user=request.user, diaCompletado__isnull=True)})

@login_required
def api_guardar_objeto(request):
    if request.method == "POST":
        data = json.loads(request.body)
        ObjetoPerdido.objects.create(nombre_reporta=data.get('nombre'), tipo_objeto=data.get('tipo'), descripcion=data.get('dif'))
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

@login_required
def api_obtener_objetos(request):
    objetos = ObjetoPerdido.objects.all().order_by('-fecha')
    data = [{"id": o.id, "nombre": o.nombre_reporta, "tipo": o.tipo_objeto, "descripcion": o.descripcion, "fecha": o.fecha.strftime('%d/%m/%Y') if o.fecha else "Sin fecha"} for o in objetos]
    return JsonResponse(data, safe=False)

@user_passes_test(es_coordinacion)
def api_cambiar_estado_usuario(request, user_id):
    if request.method == 'POST':
        u = get_object_or_404(User, id=user_id)
        u.is_active = not u.is_active
        if u.is_active:
            rol = (u.first_name or "").lower()
            nombre_grupo = ''
            if 'profesor' in rol: nombre_grupo = 'profesores'
            elif 'coordinacion' in rol: nombre_grupo = 'coordinacion'
            elif 'asistente' in rol: nombre_grupo = 'asistente bienestar'
            
            if nombre_grupo:
                g, _ = Group.objects.get_or_create(name=nombre_grupo)
                u.groups.add(g)
            try: send_mail('Cuenta Activa', f'Hola {u.username}, ya puedes entrar.', 'saebra581@gmail.com', [u.email])
            except: pass
        u.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=405)

@user_passes_test(es_coordinacion)
def formulario(request): return render(request, 'formulario.html')

@login_required
def api_apartar_prenda(request, prenda_id):
    prenda = get_object_or_404(PrendaRopa, id=prenda_id)
    if request.method != 'POST': return JsonResponse({'status': 'error'}, status=405)
    data = json.loads(request.body)
    if data.get('accion') == 'apartar':
        cant = int(data.get('cantidad_alquilada', 1))
        prenda.cantidad -= cant
        prenda.cantidad_apartada += cant
        prenda.estado = 'Apartado' if prenda.cantidad == 0 else 'Parcialmente Apartado'
        prenda.save()
    return JsonResponse({'status': 'ok'})

@user_passes_test(es_coordinacion)
def api_eliminar_prenda(request, prenda_id):
    if request.method == 'POST':
        get_object_or_404(PrendaRopa, id=prenda_id).delete()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=405)

@user_passes_test(es_asistente)
def videos(request): return render(request, 'videos.html')

@login_required
def create_task(request):
    if request.method == 'GET': return render(request, 'create_task.html', {'form': TaskForm()})
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.user = request.user
        task.save()
        return redirect('tasks')
    return render(request, 'create_task.html', {'form': form})

@login_required
def lista(request, task_id):
    return render(request, 'task_detail.html', {'task': get_object_or_404(Task, pk=task_id, user=request.user)})

@login_required
def completar(request, task_id):
    t = get_object_or_404(Task, pk=task_id, user=request.user)
    t.diaCompletado = timezone.now()
    t.save()
    return redirect('tasks')

@login_required
def eliminar_tarea(request, task_id):
    get_object_or_404(Task, pk=task_id, user=request.user).delete()
    return redirect('tasks')