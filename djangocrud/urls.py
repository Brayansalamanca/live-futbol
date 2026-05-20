from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from tasks import views

# ==========================================
# 🔐 FUNCIONES DE CONTROL DE ACCESO (GRUPOS)
# ==========================================

def es_coordinacion(user):
    """Permite el acceso a Rosita o a cualquier usuario del grupo 'coordinacion'"""
    return user.is_authenticated and (
        user.groups.filter(name='coordinacion').exists() or 
        user.username == 'rosita'
    )

def es_rosita(user):
    """Permite el acceso solo a Rosita"""
    return user.is_authenticated and user.username == 'rosita'

def es_asistente(user):
    """Permite el acceso a usuarios del grupo 'asistente bienestar'"""
    return user.is_authenticated and user.groups.filter(name='asistente bienestar').exists()

def es_profesor(user):
    """Permite el acceso a usuarios del grupo 'profesores'"""
    return user.is_authenticated and user.groups.filter(name='profesores').exists()

# ==========================================
# 📌 CONFIGURACIÓN DE RUTAS (URLS)
# ==========================================

urlpatterns = [
    # --- GESTIÓN DE CUENTA Y BASE ---
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.signout, name='logout'),
    path('activar/<uidb64>/<token>/', views.activar, name='activar'),
     path('restablecer_/', views.signup, name='signup'),
    path('condiciones/', views.condiciones, name='condiciones'),
    path('soporte/', views.soporte, name='soporte'),

   # ==========================================
# 🍽️ URLS NFC / COMEDOR
# ==========================================

# ==========================================
# PÁGINAS HTML
# ==========================================

path(
    'mis_suscripciones/',
    login_required(
        views.mis_suscripciones
    ),
    name='mis_suscripciones'
),

path(
    'subir_excel_comedor/',
    login_required(
        views.subir_excel_comedor
    ),
    name='subir_excel_comedor'
),

path(
    'registrar_entrega_comedor/',
    login_required(
        views.registrar_entrega_comedor
    ),
    name='registrar_entrega_comedor'
),

# ==========================================
# API NFC
# ==========================================

path(
    'api/nfc/subir/',
    login_required(
        views.api_nfc_subir
    ),
    name='api_nfc_subir'
),

path(
    'api/nfc/buscar/',
    login_required(
        views.api_nfc_buscar
    ),
    name='api_nfc_buscar'
),

path(
    'api/nfc/entrega/',
    login_required(
        views.buscar_usuario_comedor
    ),
    name='buscar_usuario_comedor'
), 
    # --- 🏆 GESTIÓN DE USUARIOS (RANKING) ---
    # Solo Rosita gestiona quién entra a la plataforma
    path('ranking/', user_passes_test(es_coordinacion)(views.ranking), name='ranking'),
    path('api/usuarios/', user_passes_test(es_coordinacion)(views.api_obtener_usuarios_gestion), name='api_obtener_usuarios_gestion'),
    path('api/usuarios/estado/<int:user_id>/', user_passes_test(es_coordinacion)(views.api_cambiar_estado_usuario), name='api_cambiar_estado_usuario'),
    path('api/usuarios/eliminar/<int:user_id>/', user_passes_test(es_coordinacion)(views.api_eliminar_usuario), name='api_eliminar_usuario'),

    # --- 👕 MÓDULO ROPA ---
    path('formulario/', user_passes_test(es_coordinacion)(views.formulario), name='formulario'),
    path('tipos/', login_required(views.tipos), name='tipos'), 
    path('api/guardar-prenda/', user_passes_test(es_coordinacion)(views.api_guardar_prenda), name='api_guardar_prenda'),
    path('api/apartar-prenda/<int:prenda_id>/', login_required(views.api_apartar_prenda), name='api_apartar_prenda'),
    path(
    'liberar-reserva/<int:reserva_id>/',
    login_required(views.liberar_reserva),
    name='liberar_reserva'
),
    path('api/obtener-prendas/', login_required(views.api_obtener_prendas), name='api_obtener_prendas'),
    path('api/eliminar-prenda/<int:prenda_id>/', user_passes_test(es_coordinacion)(views.api_eliminar_prenda), name='api_eliminar_prenda'),

    path('api/editar-entrega/<int:entrega_id>/', user_passes_test(es_asistente)(views.api_editar_entrega), name='api_editar_entrega'),

    # --- ⚽ MÓDULO BALONES (Radar, Renta y Bajas) ---
    path('radar/', user_passes_test(es_asistente)(views.radar), name='radar'), 
    path('videos/', user_passes_test(es_asistente)(views.videos), name='videos'),
    path('voz/', user_passes_test(es_asistente)(views.voz), name='voz'),
    path('radar/', user_passes_test(es_asistente)(views.radar), name='radar'), 
    # --- 📅 MÓDULO INFORMACIÓN (Horarios y Profesores) ---
    path('horarios/', login_required(views.horarios), name='horarios'),
    path('profesores/', login_required(views.lista_profesores), name='profesores'),
    
    path('api/guardar-entrega/', user_passes_test(es_asistente)(views.api_guardar_entrega), name='api_guardar_entrega'),
    path('api/obtener-entregas/', login_required(views.api_obtener_entregas), name='api_obtener_entregas'),
    path('api/eliminar-entrega/<int:entrega_id>/', user_passes_test(es_asistente)(views.api_eliminar_entrega), name='api_eliminar_entrega'),
    path('api/guardar-baja/', user_passes_test(es_asistente)(views.api_guardar_baja), name='api_guardar_baja'),
    path('api/obtener-bajas/', login_required(views.api_obtener_bajas), name='api_obtener_bajas'),
    path('api/eliminar-baja/<int:baja_id>/', user_passes_test(es_asistente)(views.api_eliminar_baja), name='api_eliminar_baja'),

    # --- 🔍 OBJETOS PERDIDOS (CONVIVENCIA V1 y V2) ---
    
    # Versión Antigua (No la borres porque me dijiste que la usas para otra cosa)
    path('api/guardar-objeto/', login_required(views.api_guardar_objeto), name='api_guardar_objeto'),
    path('api/obtener-objetos/', login_required(views.api_obtener_objetos), name='api_obtener_objetos'),
    path('api/eliminar-objeto/<int:obj_id>/', login_required(views.api_eliminar_objeto), name='api_eliminar_objeto'),

    # NUEVA Versión V2 (La que creamos ahora con los nombres únicos)
    path('api/v2/hallazgos/guardar/', login_required(views.hallazgo_v2_guardar), name='hallazgo_v2_guardar'),
    path('api/v2/hallazgos/listar/', login_required(views.hallazgo_v2_listar), name='hallazgo_v2_listar'),
    path('api/v2/hallazgos/eliminar/<int:item_id>/', login_required(views.hallazgo_v2_eliminar), name='hallazgo_v2_eliminar'),
    # --- ✅ TAREAS ---
    path('tasks/', login_required(views.tasks), name='tasks'),
    path('tasks/create/', login_required(views.create_task), name='create_task'),
    path('tasks/<int:task_id>/', login_required(views.lista), name='lista'),
    path('tasks/<int:task_id>/completar/', login_required(views.completar), name='completar'),
    path('tasks/<int:task_id>/eliminar/', login_required(views.eliminar_tarea), name='eliminar_tarea'),

    # --- 🔑 RECUPERACIÓN DE CLAVE ---
 # --- 🔑 RECUPERACIÓN DE CLAVE ---
    # 1. El usuario pide recuperar (ingresa correo)
    path('recuperar/', views.CustomPasswordResetView.as_view(
        template_name='recuperar_contraseña.html' # <-- Aquí agregamos tu archivo
    ), name='password_reset'),

    # 2. Confirmación de que el correo se envió
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='enlace_enviado.html'
    ), name='password_reset_done'),

    # 3. El usuario hace clic en el link del correo y llega aquí
    path('recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='restablecer_password.html' # <-- Asegúrate que se llame así tu archivo
    ), name='password_reset_confirm'),

    # 4. Mensaje de éxito final
    path('recuperar/completo/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),
  path(
    'api/torneos/listar/', 
    login_required(views.api_obtener_torneos), 
    name='api_obtener_torneos'
),
path(
    'api/torneos/guardar/', 
    login_required(views.api_guardar_torneo), 
    name='api_guardar_torneo'
),

] 