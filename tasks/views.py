from django.db import transaction
import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone, encoding, http
from django.utils.http import (
    urlsafe_base64_encode,
    urlsafe_base64_decode
)
from django.utils.encoding import (
    force_bytes,
    force_str
)
from .models import ObjetoPerdido
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings

from pymongo import MongoClient

# Importación de modelos y formularios locales
from .models import (
    Task,
    RegistroEntrega,
    ObjetoPerdido,
    PrendaRopa,
    BajaBalon,
    ReservaPrenda
)

from .forms import (
    TaskForm,
    CustomUserCreationForm
)

from .tokens import account_activation_token

import socket

# Forzar IPv4
socket.getaddrinfo = lambda *args: [
    (socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))
]

import requests
from requests.exceptions import RequestException

from django.contrib.auth.tokens import default_token_generator
from pymongo import MongoClient
from django.conf import settings


# ==========================================
# 🔐 RECUPERACIÓN DE CONTRASEÑA
# ==========================================
class CustomPasswordResetView(
    SuccessMessageMixin,
    PasswordResetView
):

    template_name = 'recuperar_contraseña.html'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):

        email = form.cleaned_data.get('email')

        try:

            # ==========================================
            # CONEXIÓN DIRECTA A MONGODB
            # ==========================================
            mongo_host = settings.DATABASES['default']['CLIENT']['host']

            client = MongoClient(mongo_host)

            db_name = settings.DATABASES['default']['NAME']

            db = client[db_name]

            usuarios = list(
                db.auth_user.find({
                    "email": email,
                    "is_active": True
                })
            )

            print("Usuarios encontrados:", usuarios)

            for user_data in usuarios:

                user = User.objects.get(
                    pk=user_data['id']
                )

                uid = urlsafe_base64_encode(
                    force_bytes(user.pk)
                )

                token = default_token_generator.make_token(user)

                current_site = get_current_site(self.request)

                context = {
                    'email': user.email,
                    'domain': current_site.domain,
                    'site_name': current_site.name,
                    'uid': uid,
                    'user': user,
                    'token': token,
                    'protocol': (
                        'https'
                        if self.request.is_secure()
                        else 'http'
                    ),
                }

                # Asunto manual
                asunto = "Recuperación de contraseña - Live Futbol"

                # Template HTML
                mensaje = render_to_string(
                    'email_reset_password.html',
                    context
                )

                # Enviar correo
                send_mail(
                    asunto,
                    mensaje,
                    'saebra581@gmail.com',
                    [user.email],
                    fail_silently=False,
                )

                print("Correo enviado:", user.email)

        except Exception as e:

            import traceback

            print("ERROR REAL:")
            traceback.print_exc()

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
        from .models import HistorialEntrega
        from django.utils import timezone
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
        try:
            data = json.loads(request.body)
            PrendaRopa.objects.create(
                objeto=data.get('nombre'),
                cantidad=int(data.get('cantidad', 1)),
                cantidad_apartada=0, # <-- Agregado por seguridad
                talla=data.get('talla', ''),
                imagen=data.get('imagen', ''),
                estado='Disponible'
            )
            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error"}, status=405)
    
# ==========================================
# 🍽️ COMEDOR NFC - VIEWS COMPLETOS
# ==========================================

import json
import pandas as pd

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .models import UsuarioComedor


# ==========================================
# 🏠 PÁGINAS HTML
# ==========================================

@login_required
def mis_suscripciones(request):

    return render(
        request,
        'mis_suscripciones.html'
    )


@login_required
def subir_excel_comedor(request):

    return render(
        request,
        'subir_excel_comedor.html'
    )


@login_required
def registrar_entrega_comedor(request):

    return render(
        request,
        'registrar_entrega_comedor.html'
    )


# ==========================================
# 📤 SUBIR EXCEL
# ==========================================

@csrf_exempt
@login_required
def api_nfc_subir(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "error": "Método inválido"
        })

    try:

        archivo = request.FILES.get("excel")

        if not archivo:

            return JsonResponse({
                "success": False,
                "error": "No se envió archivo"
            })

        hoja = request.POST.get("hoja")

        fila_inicio = int(
            request.POST.get("fila_inicio", 2)
        )

        columna_nombre = request.POST.get(
            "columna_nombre",
            "A"
        )

        columna_documento = request.POST.get(
            "columna_documento",
            "B"
        )

        columna_chip = request.POST.get(
            "columna_chip",
            "C"
        )

        # ======================================
        # LEER EXCEL
        # ======================================

        df = pd.read_excel(
            archivo,
            sheet_name=hoja
        )

        # ======================================
        # LETRAS -> INDICES
        # ======================================

        def letra_a_indice(letra):

            letra = letra.upper()

            resultado = 0

            for char in letra:

                resultado = (
                    resultado * 26
                    + ord(char)
                    - ord('A')
                    + 1
                )

            return resultado - 1

        idx_nombre = letra_a_indice(
            columna_nombre
        )

        idx_documento = letra_a_indice(
            columna_documento
        )

        idx_chip = letra_a_indice(
            columna_chip
        )

        # ======================================
        # RECORRER FILAS
        # ======================================

        agregados = 0

        for i in range(fila_inicio - 1, len(df)):

            fila = df.iloc[i]

            nombre = str(
                fila.iloc[idx_nombre]
            ).strip()

            documento = str(
                fila.iloc[idx_documento]
            ).strip()

            chip = str(
                fila.iloc[idx_chip]
            ).strip()

            if nombre == "nan":

                continue

            UsuarioComedor.objects.update_or_create(

                documento=documento,

                defaults={

                    "nombre": nombre,
                    "uid_nfc": chip
                }
            )

            agregados += 1

        return JsonResponse({

            "success": True,
            "mensaje": f"{agregados} usuarios cargados"

        })

    except Exception as e:

        return JsonResponse({

            "success": False,
            "error": str(e)

        })


# ==========================================
# 🔍 BUSCAR USUARIO
# ==========================================

@login_required
def api_nfc_buscar(request):

    q = request.GET.get("q", "").strip()

    if not q:

        return JsonResponse({

            "success": False,
            "error": "Sin búsqueda"

        })

    try:

        usuario = UsuarioComedor.objects.filter(
            documento=q
        ).first()

        if not usuario:

            usuario = UsuarioComedor.objects.filter(
                nombre__icontains=q
            ).first()

        if not usuario:

            usuario = UsuarioComedor.objects.filter(
                uid_nfc=q
            ).first()

        if not usuario:

            return JsonResponse({

                "success": False,
                "error": "No encontrado"

            })

        return JsonResponse({

            "success": True,

            "usuario": {

                "nombre": usuario.nombre,
                "documento": usuario.documento,
                "uid_nfc": usuario.uid_nfc,
                "entregado": usuario.entregado_hoy

            }

        })

    except Exception as e:

        return JsonResponse({

            "success": False,
            "error": str(e)

        })


# ==========================================
# 🍽️ REGISTRAR ENTREGA
# ==========================================

@csrf_exempt
@login_required
def buscar_usuario_comedor(request):

    if request.method != "POST":

        return JsonResponse({

            "success": False

        })

    try:

        data = json.loads(
            request.body
        )

        uid = data.get("uid")

        usuario = UsuarioComedor.objects.filter(
            uid_nfc=uid
        ).first()

        if not usuario:

            return JsonResponse({

                "success": False,
                "error": "Chip no registrado"

            })

        if usuario.entregado_hoy:

            return JsonResponse({

                "success": False,
                "error": "Ya reclamó alimento"

            })

        usuario.entregado_hoy = True

        usuario.save()

        return JsonResponse({

            "success": True,

            "usuario": {

                "nombre": usuario.nombre,
                "documento": usuario.documento,
                "uid_nfc": usuario.uid_nfc

            }

        })

    except Exception as e:

        return JsonResponse({

            "success": False,
            "error": str(e)

        })
# === En views.py ===
# ==========================================
# 🏆 API TORNEOS
# ==========================================

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .models import Torneo


# ===============================
# LISTAR TORNEOS
# ===============================
@login_required
def api_torneos(request):

    torneos = Torneo.objects.all()

    data = {}

    for t in torneos:

        data[t.nombre] = t.datos

    return JsonResponse(data)


# ===============================
# GUARDAR TORNEO
# ===============================
@csrf_exempt
@login_required
def api_guardar_torneo(request):

    if request.method == "POST":

        try:

            data = json.loads(request.body)

            nombre = data.get("nombre")
            datos = data.get("datos")

            if not nombre:
                return JsonResponse({
                    "success": False,
                    "error": "Nombre vacío"
                })

            torneo, created = Torneo.objects.update_or_create(
                nombre=nombre,
                defaults={
                    "datos": datos
                }
            )

            return JsonResponse({
                "success": True,
                "created": created
            })

        except Exception as e:

            return JsonResponse({
                "success": False,
                "error": str(e)
            })

    return JsonResponse({
        "success": False
    })


# ===============================
# ELIMINAR TORNEO
# ===============================
@csrf_exempt
@login_required
def api_eliminar_torneo(request, nombre):

    if request.method == "POST":

        Torneo.objects.filter(
            nombre=nombre
        ).delete()

        return JsonResponse({
            "success": True
        })

    return JsonResponse({
        "success": False
    })
# ==========================================
# API TORNEOS
# ==========================================

from .models import Torneo
from django.views.decorators.csrf import csrf_exempt


@login_required
def api_obtener_torneos(request):

    torneos = Torneo.objects.all()

    data = {}

    for t in torneos:

        data[t.nombre] = t.datos

    return JsonResponse(data)


@csrf_exempt
@login_required
def api_guardar_torneo(request):

    if request.method == "POST":

        data = json.loads(request.body)

        nombre = data.get("nombre")
        datos = data.get("datos")

        if not nombre:
            return JsonResponse({
                "success": False,
                "error": "Nombre requerido"
            })

        Torneo.objects.update_or_create(
            nombre=nombre,
            defaults={
                "datos": datos
            }
        )

        return JsonResponse({
            "success": True
        })

    return JsonResponse({
        "success": False
    })


@csrf_exempt
@login_required
def api_eliminar_torneo(request, nombre):

    if request.method == "POST":

        Torneo.objects.filter(
            nombre=nombre
        ).delete()

        return JsonResponse({
            "success": True
        })

    return JsonResponse({
        "success": False
    })

@login_required
def liberar_reserva(request, reserva_id):
    """
    Libera UNA sola reserva específica basada en su ID (reserva_id).
    """
    if request.method == "POST":
        try:
            # Buscamos la reserva INDIVIDUAL por su ID
            reserva = get_object_or_404(ReservaPrenda, id=reserva_id)

            if reserva.entregado:
                return JsonResponse({"status": "error", "message": "Esta reserva ya fue devuelta"}, status=400)

            prenda = reserva.prenda

            # Devolvemos el stock exacto que se llevó esa persona
            prenda.cantidad += reserva.cantidad
            prenda.cantidad_apartada -= reserva.cantidad

            if prenda.cantidad_apartada <= 0:
                prenda.cantidad_apartada = 0
                prenda.estado = 'Disponible'
            else:
                prenda.estado = 'Parcialmente Apartado'

            prenda.save()

            # Marcamos esta reserva específica como completada/entregada
            reserva.entregado = True
            reserva.save()

            return JsonResponse({"status": "ok", "message": "Prenda devuelta al inventario"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
            
    return JsonResponse({"status": "error"}, status=405)

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
    if request.method == 'DELETE':
        try:
            objeto = get_object_or_404(ObjetoPerdido, id=obj_id)
            objeto.delete()
            return JsonResponse({'message': 'Eliminado con éxito'}, status=200)
        except Exception as e:
            # ESTO MOSTRARÁ EL ERROR REAL EN LA RESPUESTA JSON
            return JsonResponse({'error_detalle': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

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
            # Filtramos las reservas vinculadas
            if r.prenda_id == p.id and not r.entregado:
                reservas.append({
                    "id": r.id,
                    "nombre": r.nombre, 
                    "curso": r.curso,
                    "evento": r.evento,
                    "cantidad": r.cantidad,
                    "fecha_uso": r.fecha_uso.strftime('%d/%m/%Y') if r.fecha_uso else None
                })

        # Formateo de fecha
        fecha_uso_formateada = p.fecha_uso.strftime('%d/%m/%Y') if getattr(p, 'fecha_uso', None) else None

        result.append({
            "id": p.id,
            "nombre": p.objeto, 
            "cantidad": p.cantidad,
            "cantidad_apartada": p.cantidad_apartada,
            "talla": p.talla,
            "estado": p.estado,
            # ✅ CORRECCIÓN: Quitamos .url porque tu campo 'imagen' ya es un texto/URL
            "imagen": p.imagen if p.imagen else None,
            "profesor": getattr(p, 'nombre_apartado', ''), 
            "curso": getattr(p, 'curso_apartado', ''),
            "evento": getattr(p, 'evento_apartado', ''),
            "fecha_uso": fecha_uso_formateada,
            "reservas": reservas
        })

    return JsonResponse(result, safe=False)
@login_required
@transaction.atomic
def api_apartar_prenda(request, prenda_id):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        accion = data.get('accion', 'apartar')
        prenda = get_object_or_404(PrendaRopa, id=prenda_id)

        if accion == 'apartar':
            cant = int(data.get('cantidad_alquilada', 1))
            nombre_persona = data.get('nombre') or request.user.username
            
            if cant > prenda.cantidad:
                return JsonResponse({'status': 'error', 'message': 'Sin stock suficiente'}, status=400)

            # 1. ACTUALIZAR SOLO EL STOCK EN LA PRENDA
            # No guardamos nombre ni fecha aquí para que no se sobreescriba "lo de Rosita"
            prenda.cantidad -= cant
            prenda.cantidad_apartada += cant
            prenda.estado = 'Agotado' if prenda.cantidad == 0 else 'Parcialmente Apartado'
            prenda.save()

            # 2. PROCESAR FECHA PARA LA RESERVA INDIVIDUAL
            fecha_str = data.get('fecha')
            fecha_uso_obj = None
            if fecha_str:
                from datetime import datetime
                try:
                    fecha_uso_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                except ValueError:
                    pass

            # 3. CREAR EL REGISTRO EN LA "HOJA DE ANOTACIÓN" (ReservaPrenda)
            # Esto es lo que garantiza que Rosita tenga 10 filas si apartó 10 veces
            ReservaPrenda.objects.create(
                prenda=prenda,
                nombre=nombre_persona,
                curso=data.get('curso', ''),
                evento=data.get('evento', ''),
                cantidad=cant,
                fecha_uso=fecha_uso_obj,
                entregado=False
            )

            return JsonResponse({'status': 'ok', 'message': f'Apartado registrado para {nombre_persona}'})

        elif accion == 'liberar':
            # Para liberar, lo ideal es que mandes el ID de la RESERVA, no de la prenda
            # Pero si lo haces por prenda, aquí devolvemos el stock general
            cantidad_a_devolver = int(data.get('cantidad_devolucion', 0))

            if cantidad_a_devolver <= 0 or cantidad_a_devolver > prenda.cantidad_apartada:
                return JsonResponse({'status': 'error', 'message': 'Cantidad inválida'}, status=400)

            prenda.cantidad += cantidad_a_devolver
            prenda.cantidad_apartada -= cantidad_a_devolver
            prenda.estado = 'Disponible' if prenda.cantidad_apartada == 0 else 'Parcialmente Apartado'
            prenda.save()
            
            return JsonResponse({'status': 'ok', 'message': 'Stock actualizado'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

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

from django.http import JsonResponse
# Si tienes un modelo para las solicitudes, impórtalo aquí arriba. Ejemplo:
# from .models import Solicitud

def api_obtener_solicitudes(request):
    """
    Endpoint para proveer los datos de solicitudes requeridos por el radar.
    Evita el error de sintaxis JSON y el 404 en el frontend.
    """
    try:
        # --- CONFIGURACIÓN CUANDO TENGAS EL MODELO ---
        # Si ya usas un modelo (por ejemplo, 'Solicitud'), descomenta las líneas de abajo
        # y ajusta los campos ('nombre', 'descripcion', etc.) a tu base de datos:
        
        # solicitudes = Solicitud.objects.all().order_by('-id')
        # data = [
        #     {
        #         'id': s.id,
        #         'usuario': s.usuario.username if s.usuario else "Anónimo",
        #         'descripcion': s.descripcion,
        #         'fecha': s.fecha.strftime('%Y-%m-%d') if s.fecha else ""
        #     }
        #     for s in solicitudes
        # ]
        # return JsonResponse(data, safe=False)

        # --- RETORNO TEMPORAL SEGURO ---
        # Mientras mapeas tus modelos, devolvemos un array vacío para que el JS no se rompa
        return JsonResponse([], safe=False)

    except Exception as e:
        # En caso de cualquier fallo en la consulta, responde con un JSON vacío limpio
        return JsonResponse([], safe=False)