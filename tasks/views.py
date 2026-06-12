from django.db import transaction
import json
import traceback
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from .models import BalonNFC


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone, encoding, http
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import HorarioCurso, BloqueHorario
import json
from django.utils import timezone
from .models import (
    Task,
    RegistroEntrega,
    ObjetoPerdido,
    PrendaRopa,
    BajaBalon,
    ReservaPrenda,
    BalonNFC,
  
)


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
    ReservaPrenda,
    BalonNFC
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

def es_asistente_o_coordinacion(user):
    return (
        es_asistente(user)
        or es_coordinacion(user)
    )

@user_passes_test(es_asistente_o_coordinacion)
def nfc(request):

    return render(
        request,
        'nfc.html'
    )



def es_administracion(user):
    return user.is_authenticated and user.groups.filter(name='administracion').exists()


# ==========================================
# ⚽ SUBIR EXCEL BALONES NFC
# ==========================================
from django.views.decorators.http import require_POST

@require_POST

def borrar_registros_antiguos(request):

    hoy = timezone.now()

    if hoy.weekday() == 5:
        # sábado

        hace_7_dias = hoy - timedelta(days=7)

        RegistroEntrega.objects.filter(
            fecha__lt=hace_7_dias
        ).delete()

    return JsonResponse({
        "ok": True
    })

@csrf_exempt
@login_required
def api_subir_balones_excel(request):

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

        hoja = request.POST.get(
            "hoja",
            0
        )

        df = pd.read_excel(
            archivo,
            sheet_name=hoja
        )

        agregados = 0

        for _, fila in df.iterrows():

            nombre = str(
                fila.get("nombre_balon", "")
            ).strip()

            tipo = str(
                fila.get("tipo", "")
            ).strip()

            codigo = str(
                fila.get("codigo_nfc", "")
            ).strip()

            imagen = str(
                fila.get("imagen", "")
            ).strip()

            if not nombre or not codigo:

                continue

            BalonNFC.objects.update_or_create(

                codigo_nfc=codigo,

                defaults={

                    "nombre_balon": nombre,
                    "tipo": tipo,
                    "imagen": imagen,
                    "disponible": True
                }
            )

            agregados += 1

        return JsonResponse({

            "success": True,
            "mensaje": f"{agregados} balones cargados"

        })

    except Exception as e:

        return JsonResponse({

            "success": False,
            "error": str(e)

        })
    
    # ==========================================
# ⚽ REGISTRAR ENTREGA NFC
# ==========================================

@csrf_exempt
@login_required
def api_registrar_entrega_nfc(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False
        })

    try:

        data = json.loads(request.body)

        nombre = data.get("nombre")
        curso = data.get("curso")
        ciclo = data.get("ciclo")
        codigo_nfc = data.get("codigo_nfc")

        balon = BalonNFC.objects.filter(
            codigo_nfc=codigo_nfc
        ).first()

        if not balon:

            return JsonResponse({
                "success": False,
                "error": "Balón no encontrado"
            })

        if not balon.disponible:

            return JsonResponse({
                "success": False,
                "error": "Balón no disponible"
            })

        RegistroEntrega.objects.create(

            nombre=nombre,

            curso=f"{curso} - {ciclo}",

            objeto=balon.nombre_balon,

            lugar=balon.tipo
        )

        balon.disponible = False

        balon.save()

        return JsonResponse({

            "success": True,

            "balon": {

                "nombre": balon.nombre_balon,
                "tipo": balon.tipo,
                "imagen": balon.imagen
            }
        })

    except Exception as e:

        return JsonResponse({

            "success": False,
            "error": str(e)

        })
    # ==========================================
# ⚽ DEVOLVER BALÓN
# ==========================================

@csrf_exempt
@login_required
def api_devolver_balon(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False
        })

    try:

        data = json.loads(request.body)

        codigo_nfc = data.get(
            "codigo_nfc"
        )

        balon = BalonNFC.objects.filter(
            codigo_nfc=codigo_nfc
        ).first()

        if not balon:

            return JsonResponse({
                "success": False,
                "error": "Balón no encontrado"
            })

        balon.disponible = True

        balon.save()

        return JsonResponse({

            "success": True

        })

    except Exception as e:

        return JsonResponse({

            "success": False,
            "error": str(e)

        })
    
    # ==========================================
# ⚽ LISTAR ENTREGAS NFC
# ==========================================

@login_required
def api_listar_entregas_nfc(request):

    entregas = RegistroEntrega.objects.all().order_by(
        '-fecha'
    )

    data = []

    for e in entregas:

        balon = BalonNFC.objects.filter(
            nombre_balon=e.objeto
        ).first()

        data.append({

            "id": e.id,

            "nombre": e.nombre,

            "curso": e.curso,

            "balon": e.objeto,

            "tipo": e.lugar,

            "imagen": balon.imagen if balon else "",

            "fecha": e.fecha.strftime(
                "%d/%m/%Y %H:%M"
            )
        })

    return JsonResponse(
        data,
        safe=False
    )
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
def tipos(request):

    # ADMINISTRACION
    if request.user.groups.filter(name='administracion').exists():
        return render(request, 'tipos.html')

    # COORDINACION
    if request.user.groups.filter(name='coordinacion').exists():
        return render(request, 'tipos.html')

    # PERMISO TEMPORAL
    if request.user.groups.filter(name='inventario_temporal').exists():
        return render(request, 'tipos.html')

    return redirect('home')

def toggle_permiso_prendas(request, id):

    if request.method == "POST":

        usuario = User.objects.get(id=id)

        perfil = usuario.perfil

        perfil.puede_apartar_prendas = not perfil.puede_apartar_prendas

        perfil.save()

        return JsonResponse({
            'success': True,
            'message': 'Permiso actualizado correctamente'
        })

    return JsonResponse({
        'success': False
    })

from django.utils.text import slugify
from .models import Perfil
import random


@user_passes_test(es_coordinacion)
def signup(request):

    if request.method == 'GET':

        return render(request, 'signup.html', {
            'form': CustomUserCreationForm()
        })

    form = CustomUserCreationForm(request.POST)

    if form.is_valid():

        try:

            nombre_real = form.cleaned_data['nombre_real']
            email = form.cleaned_data['email']
            rol = form.cleaned_data['rol']

            # ==========================================
            # USERNAME AUTOMÁTICO
            # ==========================================

            base_username = slugify(nombre_real).replace('-', '')

            username = base_username

            contador = 1

            while User.objects.filter(username=username).exists():

                username = f"{base_username}{contador}"

                contador += 1

            # ==========================================
            # PASSWORD AUTOMÁTICA
            # ==========================================

            numero = random.randint(1000, 9999)

            password_temporal = f"ColRosario{numero}"

            # ==========================================
            # CREAR USUARIO
            # ==========================================

            user = User.objects.create_user(

                username=username,

                password=password_temporal,

                email=email,

                first_name=rol
            )

            user.is_active = True

            user.save()

            # ==========================================
            # GRUPOS
            # ==========================================

            grupo, _ = Group.objects.get_or_create(
                name=rol
            )

            user.groups.add(grupo)

            # ==========================================
            # PERFIL
            # ==========================================

            Perfil.objects.create(

                user=user,

                nombre_real=nombre_real,

                debe_cambiar_password=True
            )

            return render(request, 'signup.html', {

                'form': CustomUserCreationForm(),

                'success': f'''
Usuario creado correctamente.

Usuario:
{username}

Contraseña temporal:
{password_temporal}
'''
            })

        except Exception as e:

            return render(request, 'signup.html', {

                'form': form,

                'error': str(e)

            })

    return render(request, 'signup.html', {

        'form': form

    })

@login_required
def cambiar_password_inicial(request):

    if request.method == 'POST':

        nueva_password = request.POST['password']

        user = request.user

        # CAMBIAR CONTRASEÑA
        user.set_password(nueva_password)
        user.save()

        # 🔐 DESACTIVAR CAMBIO OBLIGATORIO
        perfil = request.user.perfil
        perfil.debe_cambiar_password = False
        perfil.save()

        # VOLVER A LOGUEAR
        login(request, user)

        return redirect('home')

    return render(
        request,
        'cambiar_password_inicial.html'
    )




# --- CORRECCIÓN AQUÍ: SE SEPARÓ SIGNIN ---
def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': AuthenticationForm()})
        
    user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
    
    if user is not None:
        if not user.is_active: 
            return render(request, 'signin.html', {'form': AuthenticationForm(), 'error': 'Cuenta pendiente de activación.'})
        
        login(request, user)
        
    try:

        if user.perfil.debe_cambiar_password:

          return redirect('cambiar_password_inicial')
    except:
        pass
        if es_coordinacion(user): return redirect('tipos')
        if es_asistente(user): return redirect('radar')
        if es_administracion(user): return redirect('formulario')
        return redirect('tipos')
        
    return render(request, 'signin.html', {'form': AuthenticationForm(), 'error': 'Credenciales incorrectas'})

def signout(request):
    logout(request)
    return redirect('home')

# ==========================================
# 🏆 GESTIÓN (RANKING)
# ==========================================
@login_required
def ranking(request):

    usuarios = User.objects.all()

    return render(request, 'ranking.html', {
        'usuarios': usuarios
    })




@login_required
def cambiar_permiso_prendas(request, user_id):

    grupo, created = Group.objects.get_or_create(
        name='inventario_temporal'
    )

    usuario = get_object_or_404(User, id=user_id)

    if usuario.groups.filter(name='inventario_temporal').exists():

        usuario.groups.remove(grupo)

    else:

        usuario.groups.add(grupo)

    return redirect('ranking')

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
    
@csrf_exempt
@login_required
def guardar_bloque(request):

    if request.method == 'POST':

        data = json.loads(request.body)

        categoria = data.get('categoria')
        curso = data.get('curso')

        fila = data.get('fila')
        col = data.get('col')

        profesor = data.get('profesor')
        materia = data.get('materia')
        salon = data.get('salon')
        tipo = data.get('tipo')

        horario = HorarioCurso.objects.filter(
             categoria=categoria,
    curso=curso
        ).first()

        if not horario:

            horario = HorarioCurso.objects.create(
        categoria=categoria,
        curso=curso
    )

        BloqueHorario.objects.filter(
            horario=horario,
            fila=fila,
            col=col
        ).delete()

        BloqueHorario.objects.create(
            horario=horario,
            fila=fila,
            col=col,
            profesor=profesor,
            materia=materia,
            salon=salon,
            tipo=tipo
        )

        return JsonResponse({
            'success': True
        })
@login_required
def obtener_horario(request):

    categoria = request.GET.get('categoria')
    curso = request.GET.get('curso')

    try:

        horario = HorarioCurso.objects.filter(
    categoria=categoria,
    curso=curso
).first()

    except HorarioCurso.DoesNotExist:

        return JsonResponse({
            'bloques': []
        })

    bloques = []

    for b in horario.bloques.all():

        bloques.append({

            'fila': b.fila,
            'col': b.col,
            'profesor': b.profesor,
            'materia': b.materia,
            'salon': b.salon,
            'tipo': b.tipo

        })

    return JsonResponse({
        'bloques': bloques
    })
@csrf_exempt
@login_required
def eliminar_bloque(request):

    if request.method == 'POST':

        data = json.loads(request.body)

        categoria = data.get('categoria')
        curso = data.get('curso')

        fila = data.get('fila')
        col = data.get('col')

        horario = HorarioCurso.objects.filter(
            categoria=categoria,
            curso=curso
        ).first()

        if horario:

            BloqueHorario.objects.filter(
                horario=horario,
                fila=fila,
                col=col
            ).delete()

        return JsonResponse({
            'success': True
        })
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


@login_required
def api_obtener_historial(request):

    todas = RegistroEntrega.objects.all().order_by('-fecha')

    data = []

    for e in todas:

        # SOLO LOS ELIMINADOS
        if not getattr(e, 'eliminado', False):
            continue

        data.append({
            'id': e.id,
            'nombre': e.nombre,
            'curso': e.curso,
            'objeto': e.objeto,
            'fecha': e.fecha,
        })

    return JsonResponse(data, safe=False)
# ==========================================
# ⚽ MÓDULO BALONES (SOLO ASISTENTE)
# ==========================================
@csrf_exempt  # Evita problemas de CSRF temporalmente si haces la petición por fetch directo
@user_passes_test(es_asistente)
def api_registrar_nuevo_balon(request):
    if request.method == "POST":
        try:
            # Validamos que el cuerpo no esté vacío
            if not request.body:
                return JsonResponse({"error": "El cuerpo de la petición está vacío"}, status=400)
                
            data = json.loads(request.body)
            
            nombre = data.get('nombre')
            tipo = data.get('tipo', 'Fútbol')
            
            if not nombre:
                return JsonResponse({"error": "El campo 'nombre' es obligatorio"}, status=400)
            
            # Generamos un código temporal si no viene uno por NFC
            codigo_nfc = data.get('codigo_nfc', f"TEMP-{nombre.upper().replace(' ', '-')}")
            
            # Creamos el registro en tu base de datos
            nuevo_balon = BalonNFC.objects.create(
                nombre_balon=nombre,
                tipo=tipo,
                codigo_nfc=codigo_nfc,
                disponible=True
            )
            
            return JsonResponse({
                "status": "success",
                "message": f"Balón registrado con éxito.",
                "id": nuevo_balon.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido enviado al servidor"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Método no permitido"}, status=405)


# --- API 2: OBTENER BALONES DISPONIBLES ---


from .models import BalonInventario 

@user_passes_test(es_asistente)
def api_balones_disponibles(request):
    try:
        balones = BalonInventario.objects.all()
        data = list(balones.values('id', 'id_unico', 'marca', 'tipo', 'estado'))
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@user_passes_test(es_asistente)
def api_registrar_nuevo_balon(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            BalonInventario.objects.create(
                id_unico=data.get('id_unico'),
                marca=data.get('marca'),
                tipo=data.get('tipo', 'Balón Fútbol')
            )
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        require_POST # Solo permite peticiones POST por seguridad
@user_passes_test(es_asistente)
def api_eliminar_balon(request, id):
    balon = get_object_or_404(BalonInventario, id=id)
    balon.delete()
    return JsonResponse({"status": "success", "message": "Balón eliminado"})

@require_POST
@user_passes_test(es_asistente)
def api_editar_balon(request, id):
    balon = get_object_or_404(BalonInventario, id=id)
    data = json.loads(request.body)
    
    balon.id_unico = data.get('id_unico', balon.id_unico)
    balon.marca = data.get('marca', balon.marca)
    balon.tipo = data.get('tipo', balon.tipo)
    balon.save()
    
    return JsonResponse({"status": "success", "message": "Balón actualizado"})
    
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
            lugar=data.get('lugar'),
            # ✅ CORRECCIÓN 1: Forzamos que se guarde con la hora exacta local del servidor
            fecha=timezone.now() 
        )
        return JsonResponse({"status": "success"})

@login_required
def api_obtener_entregas(request):
    entregas = RegistroEntrega.objects.all().order_by('-fecha')
    data = []

    for e in entregas:
        # Ocultar registros eliminados
        if getattr(e, 'eliminado', False):
            continue

        # --- PROTECCIÓN CONTRA NAIVE DATETIME ---
        fecha_evaluar = e.fecha
        if fecha_evaluar:
            # Si la fecha no tiene zona horaria (naive), le asignamos la del sistema
            if not timezone.is_aware(fecha_evaluar):
                fecha_evaluar = timezone.make_aware(fecha_evaluar)
            
            # Ahora sí es seguro convertirla a la hora local de Colombia
            fecha_local = timezone.localtime(fecha_evaluar)
            fecha_formateada = fecha_local.strftime("%d/%m/%Y %I:%M %p")
            fecha_debug_str = str(fecha_local)
        else:
            fecha_formateada = "Sin fecha"
            fecha_debug_str = "None"

        data.append({
            'id': e.id,
            'nombre': e.nombre,
            'curso': e.curso,
            'objeto': e.objeto,
            'lugar': e.lugar,
            'marca': e.marca,
            # Cambia esto en views.py:
            'id_unico': e.marca if e.marca else "Sin ID",
            'fecha': fecha_formateada,
            'fecha_debug': fecha_debug_str,
            'eliminado': False
        })

    return JsonResponse(data, safe=False)

@user_passes_test(es_asistente_o_coordinacion)

@login_required
def api_eliminar_entrega(request, entrega_id):

    entrega = get_object_or_404(
        RegistroEntrega,
        id=entrega_id
    )

    entrega.eliminado = True
    entrega.fecha_eliminado = timezone.now()

    entrega.save()

    return JsonResponse({
        'success': True
    })

@require_POST
@user_passes_test(es_asistente_o_coordinacion)
def api_editar_entrega(request, entrega_id):
    entrega = get_object_or_404(RegistroEntrega, id=entrega_id)
    try:
        data = json.loads(request.body)
        entrega.nombre = data.get('nombre', entrega.nombre)
        entrega.curso = data.get('curso', entrega.curso)
        entrega.objeto = data.get('objeto', entrega.objeto)
        entrega.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

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
@user_passes_test(es_administracion)
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

@csrf_exempt # Necesario si no estás enviando el token CSRF desde el JS
def api_eliminar_torneo(request, nombre):
    if request.method == "POST":
        try:
            # LÓGICA DE ELIMINACIÓN
            # Opción A: Si usas un modelo de Django:
            # Torneo.objects.filter(nombre=nombre).delete()
            
            # Opción B: Si guardas en un JSON file o variable global (tipo persistencia):
            # Debes cargar tus torneos, eliminar la clave 'nombre' y guardar de nuevo.
            
            # Ejemplo simplificado de respuesta exitosa:
            return JsonResponse({"status": "success", "message": f"Torneo {nombre} eliminado"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
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

    if request.method == "POST":

        try:

            data = json.loads(request.body)

            ObjetoPerdido.objects.create(

                nombre_reporta=data.get('nombre', 'Anónimo'),

                curso=data.get('curso', ''),

                tipo_objeto=data.get('tipo', 'Sin especificar'),

                color=data.get('color', ''),

                descripcion=data.get('descripcion', '')

            )

            return JsonResponse({
                "status": "success"
            })

        except Exception as e:

            return JsonResponse({
                "status": "error",
                "message": str(e)
            })

    return JsonResponse({
        "status": "error"
    })
    

@login_required
def hallazgo_v2_listar(request):

    objetos = ObjetoPerdido.objects.all().order_by('-fecha')

    data = []

    for o in objetos:

        data.append({

            "id": o.id,

            "nombre": o.nombre_reporta,

            "curso": o.curso,

            "tipo": o.tipo_objeto,

            "color": o.color,

            "descripcion": o.descripcion,

            "fecha": o.fecha.strftime('%d/%m/%Y')

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



# ==========================================
# 📝 SOLICITUDES TEMPORALES
# ==========================================

solicitudes_temporales = []


# ==========================================
# 📥 OBTENER SOLICITUDES
# ==========================================

@login_required
def api_obtener_solicitudes(request):

    global solicitudes_temporales

    return JsonResponse(
        solicitudes_temporales,
        safe=False
    )


# ==========================================
# 📝 GUARDAR SOLICITUDES
# ==========================================

@csrf_exempt
@login_required
def api_guardar_solicitud(request):

    global solicitudes_temporales

    if request.method == "POST":

        try:

            data = json.loads(request.body)

            nueva = {
                "id": len(solicitudes_temporales) + 1,
                "nombre": data.get("nombre", ""),
                "curso": data.get("curso", ""),
                "descripcion": data.get("descripcion", ""),
                "fecha": timezone.now().strftime("%d/%m/%Y %H:%M")
            }

            solicitudes_temporales.append(nueva)

            return JsonResponse({
                "success": True,
                "solicitud": nueva
            })

        except Exception as e:

            return JsonResponse({
                "success": False,
                "error": str(e)
            })

    return JsonResponse({
        "success": False
    })
@login_required
def api_eliminar_solicitud(request, solicitud_id):

    global solicitudes_temporales

    if request.method == "DELETE":

        solicitudes_temporales = [

            s for s in solicitudes_temporales

            if str(s["id"]) != str(solicitud_id)

        ]

        return JsonResponse({
            "success": True
        })

    return JsonResponse({
        "success": False
    }, status=405)

