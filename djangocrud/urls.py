from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from tasks import views

# 🔐 Regla: Solo Rosita entra
def es_rosita(user):
    return user.is_authenticated and user.username == 'rosita'

urlpatterns = [
    # -----------------------------------------------------------
    # 🌍 SISTEMA BASE (LOGIN / REGISTRO)
    # -----------------------------------------------------------
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.signout, name='logout'),
    path('activar/<uidb64>/<token>/', views.activar, name='activar'),
    path('condiciones/', views.condiciones, name='condiciones'),
    path('soporte/', views.soporte, name='soporte'),

    # -----------------------------------------------------------
    # 👕 MÓDULO DE ROPA (INDUMENTARIA)
    # -----------------------------------------------------------
    # Rosita registra la ropa aquí
    path('formulario/', user_passes_test(es_rosita)(views.formulario), name='formulario'),
    
    # Profesores y Rosita ven el catálogo aquí para apartar
    path('tipos/', login_required(views.tipos), name='tipos'), 
    
    # APIs de Ropa (Estas deben coincidir con tu JavaScript)
    path('api/guardar-prenda/', user_passes_test(es_rosita)(views.api_guardar_prenda), name='api_guardar_prenda'),
    path('api/apartar-prenda/', login_required(views.api_apartar_prenda), name='api_apartar_prenda'),
    path('api/obtener-prendas/', login_required(views.api_obtener_prendas), name='api_obtener_prendas'),

    # -----------------------------------------------------------
    # ⚽ MÓDULO DE BALONES (RADAR Y RENTA)
    # -----------------------------------------------------------
    path('radar/', login_required(views.radar), name='radar'), 
    path('videos/', login_required(views.videos), name='videos'),
    
    # APIs de Balones
    path('api/guardar-entrega/', login_required(views.api_guardar_entrega), name='api_guardar_entrega'),
    path('api/obtener-entregas/', login_required(views.api_obtener_entregas), name='api_obtener_entregas'),
    path('api/eliminar-entrega/<int:entrega_id>/', login_required(views.api_eliminar_entrega), name='api_eliminar_entrega'),
    
    path('api/guardar-baja/', login_required(views.api_guardar_baja), name='api_guardar_baja'),
    path('api/obtener-bajas/', login_required(views.api_obtener_bajas), name='api_obtener_bajas'),

    # -----------------------------------------------------------
    # 🔍 OBJETOS PERDIDOS (VOZ)
    # -----------------------------------------------------------
    path('voz/', login_required(views.voz), name='voz'),
    path('api/guardar-objeto/', login_required(views.api_guardar_objeto), name='api_guardar_objeto'),
    path('api/obtener-objetos/', login_required(views.api_obtener_objetos), name='api_obtener_objetos'),

    # -----------------------------------------------------------
    # 📝 TAREAS Y RUTINAS
    # -----------------------------------------------------------
    path('tasks/create/', login_required(views.create_task), name='create_task'),
    path('tasks/<int:task_id>/', login_required(views.lista), name='lista'),
    path('tasks/<int:task_id>/completar/', login_required(views.completar), name='completar'),
    path('tasks/<int:task_id>/eliminar/', login_required(views.eliminar_tarea), name='eliminar_tarea'),

    # 🔑 CONTRASEÑAS
    path('recuperar/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='enlace_enviado.html'), name='password_reset_done'),
    path('recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='restablecer_password.html'), name='password_reset_confirm'),
    path('recuperar/completo/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]