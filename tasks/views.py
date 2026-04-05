import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone, encoding, http
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site

# Importación de modelos y formularios locales
from .models import Task, RegistroEntrega, ObjetoPerdido, PrendaRopa, BajaBalon
from .forms import TaskForm, CustomUserCreationForm
from .tokens import account_activation_token

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
            print(f"Error de base de datos ocultado: {e}")
            
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
        # QUITAMOS: user.is_active = True 
        # El usuario sigue inactivo, pero el token ya fue validado.
        return render(request, 'confirmar_cuenta.html') # Este HTML debe decir "Correo verificado, espera a Rosita"
    return render(request, 'confirmar_fallido.html')
    
@login_required
def tipos(request): return render(request, 'tipos.html')
def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': CustomUserCreationForm()})
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # 1. INTENTO DE GUARDADO (Aquí es donde ocurre el 502)
                user = form.save(commit=False)
                user.first_name = request.POST.get('rol', 'Sin Rol')
                user.is_active = False 
                
                print("DEBUG: Intentando guardar en MongoDB...")
                user.save() 
                print("DEBUG: Usuario guardado exitosamente.")

                # 2. GENERACIÓN DE TOKEN Y CORREO
                try:
                    current_site = get_current_site(request)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = account_activation_token.make_token(user)
                    
                    context = {
                        'user': user,
                        'domain': current_site.domain,
                        'uid': uid,
                        'token': token,
                    }

                    html_content = render_to_string('confirmacion_email.html', context)
                    text_content = strip_tags(html_content)

                    msg = EmailMultiAlternatives(
                        'Activa tu cuenta - Live Fútbol',
                        text_content,
                        'Live Fútbol <saebra581@gmail.com>',
                        [user.email]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    
                    print("DEBUG: Intentando enviar correo...")
                    msg.send(fail_silently=True)
                    print("DEBUG: Correo enviado (o falló silenciosamente).")

                except Exception as mail_error:
                    print(f"DEBUG: Error enviando correo: {mail_error}")
                    # No detenemos el proceso si falla el correo, el usuario ya se creó.

                return render(request, 'signup.html', {
                    'form': CustomUserCreationForm(), 
                    'success': 'Registro exitoso. Revisa tu correo (si no llega, contacta a Rosita).'
                })

            except Exception as e:
                # SI ESTO SE EJECUTA, VERÁS EL ERROR EN LA PÁGINA EN VEZ DEL 502
                print(f"DEBUG: ERROR CRÍTICO EN BASE DE DATOS: {e}")
                return render(request, 'signup.html', {
                    'form': form, 
                    'error': f"Error de conexión con la base de datos: {str(e)}"
                })
        else:
            return render(request, 'signup.html', {'form': form, 'error': "Datos inválidos en el formulario."})


# --- CORRECCIÓN AQUÍ: SE SEPARÓ SIGNIN ---
def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': AuthenticationForm()})
        
    user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
    
    if user is not None:
        if not user.is_active: 
            return render(request, 'signin.html', {'form': AuthenticationForm(), 'error': 'Cuenta pendiente de activación.'})
        
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
    usuarios_qs = User.objects.exclude(username__in=['rosita', 'rosita1'])
    usuarios = [u for u in usuarios_qs if not u.is_superuser]

    data = [
        {
            'id': u.id,
            'nombre': u.username,
            'email': u.email,
            'rol': u.first_name,
            'estado': 'activo' if u.is_active else 'pendiente',
            'grupo_asignado': u.groups.first().name if u.groups.exists() else 'Sin Grupo'
        }
        for u in usuarios
    ]
    return JsonResponse(data, safe=False)

@user_passes_test(es_coordinacion)
def api_eliminar_usuario(request, user_id):
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=user_id)
        usuario.delete()
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'status': 'error'}, status=405)

# ==========================================
# ⚽ MÓDULO BALONES (SOLO ASISTENTE)
# ==========================================
@user_passes_test(es_asistente)
def radar(request): return render(request, 'radar.html')

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
        imagen_defecto = data.get('imagen') or '/static/sin evidencia.webp'
        BajaBalon.objects.create(
            tipo_balon=data.get('tipo'), 
            causa=data.get('causa'), 
            responsable=data.get('usuario'),
            marca=data.get('lugar'),
            alquilado_por=data.get('alquilado_por'),
            foto=imagen_defecto
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

# ==========================================
# 👗 MÓDULO ROPA Y OTROS
# ==========================================
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
    prendas = PrendaRopa.objects.filter(talla__iexact=talla_filtro) if talla_filtro else PrendaRopa.objects.all()
    prendas = prendas.order_by('-fecha_registro')
    result = []
    for p in prendas:
        fecha_devolucion = (p.fecha_uso + timedelta(days=p.dias_alquiler)).strftime('%d/%m/%Y') if (p.fecha_uso and p.dias_alquiler) else ''
        result.append({
            'id': p.id, 'nombre': p.objeto, 'cantidad': p.cantidad, 'cantidad_apartada': p.cantidad_apartada,
            'talla': p.talla, 'estado': p.estado, 'detalle_defecto': p.detalle_defecto,
            'profesor': p.nombre_apartado or '', 'curso': p.curso_apartado or '',
            'evento': p.evento_apartado or '', 'dias_alquiler': p.dias_alquiler,
            'fecha_uso': p.fecha_uso.strftime('%d/%m/%Y') if p.fecha_uso else '',
            'fecha_devolucion': fecha_devolucion, 'imagen': p.imagen
        })
    return JsonResponse(result, safe=False)

@login_required
def tasks(request):
    tasks_list = Task.objects.filter(user=request.user, diaCompletado__isnull=True)
    return render(request, 'tasks.html', {'tasks': tasks_list})

@login_required
def api_guardar_objeto(request):
    if request.method == "POST":
        data = json.loads(request.body)
        ObjetoPerdido.objects.create(nombre_reporta=data.get('nombre'), tipo_objeto=data.get('tipo'), descripcion=data.get('dif'))
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_objetos(request):
    objetos = ObjetoPerdido.objects.all().order_by('-fecha')
    data = [{"id": o.id, "nombre": o.nombre_reporta, "tipo": o.tipo_objeto, "descripcion": o.descripcion, "fecha": o.fecha.strftime('%d/%m/%Y') if o.fecha else "Sin fecha"} for o in objetos]
    return JsonResponse(data, safe=False)

@login_required
def api_eliminar_objeto(request, obj_id):
    if request.method == "POST":
        get_object_or_404(ObjetoPerdido, pk=obj_id).delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)

@user_passes_test(es_coordinacion)
def api_cambiar_estado_usuario(request, user_id):
    if request.method == 'POST':
        u = get_object_or_404(User, id=user_id)
        u.is_active = not u.is_active
        if u.is_active:
            rol = u.first_name.lower()
            nombre_grupo = 'profesores' if 'profesor' in rol else 'coordinacion' if 'coordinacion' in rol else 'asistente bienestar' if 'asistente' in rol else ''
            if nombre_grupo:
                g, _ = Group.objects.get_or_create(name=nombre_grupo)
                u.groups.add(g)
            try:
                send_mail('Cuenta Activada', f'Hola {u.username}, tu cuenta está activa.', 'saebra581@gmail.com', [u.email])
            except: pass
        u.save()
        return JsonResponse({'status': 'ok'})

@user_passes_test(es_coordinacion)
def formulario(request): return render(request, 'formulario.html')

@login_required
def api_apartar_prenda(request, prenda_id):
    prenda = get_object_or_404(PrendaRopa, id=prenda_id)
    if request.method != 'POST': return JsonResponse({'status': 'error'}, status=405)
    data = json.loads(request.body)
    accion = data.get('accion', 'apartar')

    if accion == 'apartar':
        cant = int(data.get('cantidad_alquilada', 1))
        if cant > prenda.cantidad: return JsonResponse({'status': 'error'}, status=400)
        prenda.cantidad -= cant
        prenda.cantidad_apartada += cant
        prenda.estado = 'Apartado' if prenda.cantidad == 0 else 'Parcialmente Apartado'
        prenda.nombre_apartado = data.get('nombre')
        prenda.save()
    elif accion == 'liberar':
        prenda.cantidad += prenda.cantidad_apartada
        prenda.cantidad_apartada = 0
        prenda.estado = 'Disponible'
        prenda.save()
    return JsonResponse({'status': 'ok'})

@user_passes_test(es_coordinacion)
def api_eliminar_prenda(request, prenda_id):
    if request.method == 'POST':
        get_object_or_404(PrendaRopa, id=prenda_id).delete()
        return JsonResponse({'status': 'ok'})

@user_passes_test(es_asistente)
def videos(request): return render(request, 'videos.html')
@user_passes_test(es_asistente)
def voz(request): return render(request, 'voz.html')

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
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    return render(request, 'task_detail.html', {'task': task})

@login_required
def completar(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    task.diaCompletado = timezone.now()
    task.save()
    return redirect('tasks')

@login_required
def eliminar_tarea(request, task_id):
    get_object_or_404(Task, pk=task_id, user=request.user).delete()
    return redirect('tasks')