import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone, encoding, http
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
from .models import ReservaPrenda

# Importación de modelos y formularios locales
from .models import Task, RegistroEntrega, ObjetoPerdido, PrendaRopa, BajaBalon
from .forms import TaskForm, CustomUserCreationForm
from .tokens import account_activation_token
import socket
# Forzar a que use IPv4 para evitar el error 101
socket.getaddrinfo = lambda *args: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))]
import requests
from requests.exceptions import RequestException


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
                    msg.send(fail_silently=False)
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

# Al final de tasks/views.py
def lista_profesores(request):
    import requests
    from requests.exceptions import RequestException

    url = "https://jsonplaceholder.typicode.com/users"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        profesores = response.json()
    except RequestException as e:
        print(f"Error de conexión: {e}")
        profesores = []

    return render(request, 'profesores.html', {'profesores': profesores})

@login_required
def horarios(request):
    return render(request, 'horarios.html')
    
# ==========================================
# 🍽️ MÓDULO ASISTENCIA ALIMENTOS (RADAR)
# ==========================================

from .models import AsistenciaAlimento

@user_passes_test(es_asistente)
def api_guardar_asistencia(request):
    if request.method == "POST":
        data = json.loads(request.body)

        AsistenciaAlimento.objects.create(
            nombre=data.get('nombre'),
            grado=data.get('grado'),
            seccion=data.get('seccion'),
            pago=data.get('pago', True),
            estado=data.get('estado', 'normal')
        )

        return JsonResponse({"status": "ok"})
    


@user_passes_test(es_asistente)
def api_listar_asistencia(request):
    tipo = request.GET.get('tipo')

    if tipo == "no_pagan":
        personas = AsistenciaAlimento.objects.filter(pago=False)
    else:
        personas = AsistenciaAlimento.objects.filter(estado=tipo)

    data = []
    for p in personas:
        data.append({
            "id": p.id,
            "nombre": p.nombre,
            "grado": p.grado,
            "seccion": p.seccion,
            "estado": p.estado,
            "pago": p.pago
        })

    return JsonResponse(data, safe=False)

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
    

# === En views.py ===



@login_required
def liberar_reserva(request, reserva_id):
    reserva = get_object_or_404(ReservaPrenda, id=reserva_id)

    prenda = reserva.prenda

    prenda.cantidad += reserva.cantidad
    prenda.cantidad_apartada -= reserva.cantidad

    if prenda.cantidad_apartada == 0:
        prenda.estado = 'Disponible'

    prenda.save()

    reserva.entregado = True
    reserva.save()

    return JsonResponse({"status": "ok"})

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
def api_obtener_prendas(request):
    prendas = list(PrendaRopa.objects.all())
    prendas.reverse()

    todas_reservas = list(ReservaPrenda.objects.all())

    result = []

    for p in prendas:
        reservas = []

        for r in todas_reservas:
            if str(r.prenda_id) == str(p.id) and r.entregado is False:
                reservas.append({
                    "id": r.id,
                    "nombre": r.nombre,
                    "curso": r.curso,
                    "evento": r.evento,
                    "cantidad": r.cantidad,
                    "fecha_uso": r.fecha_uso.strftime('%d/%m/%Y')
                })

        result.append({
            "id": p.id,
            "nombre": p.objeto,
            "cantidad": p.cantidad,
            "cantidad_apartada": p.cantidad_apartada,
            "talla": p.talla,
            "estado": p.estado,
            "imagen": p.imagen,
            "reservas": reservas
        })

    return JsonResponse(result, safe=False)
@login_required
def api_apartar_prenda(request, prenda_id):
    prenda = get_object_or_404(PrendaRopa, id=prenda_id)
    if request.method != 'POST': 
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        
    accion = data.get('accion', 'apartar')

    if accion == 'apartar':
        cant = int(data.get('cantidad_alquilada', 1))
        # Usamos el nombre que viene en el payload (o el usuario actual si no viene)
        nombre_persona = data.get('nombre') or request.user.username
        
        if cant > prenda.cantidad: 
            return JsonResponse({'status': 'error', 'message': 'Sin stock suficiente'}, status=400)

        prenda.cantidad -= cant
        prenda.cantidad_apartada += cant
        prenda.estado = 'Agotado' if prenda.cantidad == 0 else 'Parcialmente Apartado'
        
        # Datos de la ÚLTIMA persona que apartó (para compatibilidad con tu código actual)
        prenda.nombre_apartado = nombre_persona
        prenda.curso_apartado = data.get('curso', '')
        prenda.evento_apartado = data.get('evento', '')
        
        # AGREGAR AL HISTORIAL PLANO en detalle_defecto
        # Formato: "Nombre - Cantidad prendas - Curso/Evento;"
        nuevo_registro_historial = f"{nombre_persona} - {cant} prenda(s) - {data.get('curso', 'S/C')}/{data.get('evento', 'S/E')};"
        
        if prenda.detalle_defecto:
            prenda.detalle_defecto += " " + nuevo_registro_historial
        else:
            prenda.detalle_defecto = nuevo_registro_historial

        # Guardamos la fecha de uso correctamente
        fecha_str = data.get('fecha')
        if fecha_str:
            try:
                prenda.fecha_uso = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        prenda.save()
        return JsonResponse({'status': 'ok', 'message': f'Prenda apartada para {nombre_persona}'})

    elif accion == 'liberar':
        # NUEVO: Rosita especifica cuántas prendas se devuelven
        cantidad_a_devolver = int(data.get('cantidad_devolucion', 0))
        
        if cantidad_a_devolver <= 0:
             return JsonResponse({'status': 'error', 'message': 'Cantidad de devolución inválida'}, status=400)
             
        if cantidad_a_devolver > prenda.cantidad_apartada:
             return JsonResponse({'status': 'error', 'message': 'No puedes devolver más prendas de las apartadas'}, status=400)

        # Actualizamos stock
        prenda.cantidad += cantidad_a_devolver
        prenda.cantidad_apartada -= cantidad_a_devolver
        
        # Si se devolvió TODO, limpiamos todo
        if prenda.cantidad_apartada == 0:
            prenda.estado = 'Disponible'
            prenda.nombre_apartado = ''
            prenda.curso_apartado = ''
            prenda.evento_apartado = ''
            prenda.fecha_uso = None
            prenda.detalle_defecto = '' # Limpiamos el historial plano
        else:
            # Si es devolución parcial, solo actualizamos estado
            prenda.estado = 'Parcialmente Apartado'
            # Mantenemos el historial crudo, pero podrías intentar editarlo recursivamente (complejo sin SQL)
            # Por simplicidad, mantenemos el historial como "quiénes han alquilado históricamente"
            
        prenda.save()
        return JsonResponse({'status': 'ok', 'message': f'Se devolvieron {cantidad_a_devolver} prenda(s)'})

    return JsonResponse({'status': 'error', 'message': 'Acción no reconocida'}, status=400)

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
# ==========================================
# 👗 NUEVO MÓDULO: HALLAZGOS Y PERTENENCIAS (V2)
# ==========================================

@login_required
def hallazgo_v2_guardar(request):
    """ Guarda objetos encontrados con nombres de función únicos """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # Usamos los campos exactos de tu modelo ObjetoPerdido
            ObjetoPerdido.objects.create(
                nombre_reporta=data.get('nombre', 'Anónimo'),
                tipo_objeto=data.get('tipo', 'Sin especificar'),
                descripcion=data.get('color', 'Sin descripción'),
                entregado=False
            )
            return JsonResponse({"status": "success", "message": "Objeto registrado en V2"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error"}, status=405)

@login_required
def hallazgo_v2_listar(request):
    """ Lista objetos no entregados sin interferir con otras APIs """
    # Intentamos usar el campo de fecha que tengas disponible
    objetos = ObjetoPerdido.objects.filter(entregado=False).order_by('-id')
    
    data = []
    for o in objetos:
        # Formateo de fecha seguro
        fecha_txt = "S/F"
        if hasattr(o, 'fecha_registro') and o.fecha_registro:
            fecha_txt = o.fecha_registro.strftime('%d/%m/%Y')
        elif hasattr(o, 'fecha') and o.fecha:
            fecha_txt = o.fecha.strftime('%d/%m/%Y')

        data.append({
            "id": o.id,
            "nombre": o.nombre_reporta,
            "tipo": o.tipo_objeto,
            "color": o.descripcion,
            "fecha": fecha_txt
        })
    return JsonResponse(data, safe=False)

@login_required
def hallazgo_v2_eliminar(request, item_id):
    """ Borrado físico del objeto por ID """
    if request.method == "POST":
        objeto = get_object_or_404(ObjetoPerdido, id=item_id)
        objeto.delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=405)