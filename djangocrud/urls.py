from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from tasks import views

# Función de seguridad: Solo permite el paso si el usuario es "rosita"
def es_rosita(user):
    return user.is_authenticated and user.username == 'rosita'

urlpatterns = [
    # -----------------------------------------------------------
    # 🌍 RUTAS PÚBLICAS Y AUTENTICACIÓN
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
    # 🌸 MÓDULO EXCLUSIVO DE ROSITA (Ropa e Inventario)
    # -----------------------------------------------------------
    # Solo Rosita puede entrar a esta URL y usar sus APIs
    path('formulario/', user_passes_test(es_rosita)(views.formulario), name='formulario'),
    path('api/guardar-prenda/', user_passes_test(es_rosita)(views.api_guardar_prenda), name='api_guardar_prenda'),
    path('api/obtener-prendas/', user_passes_test(es_rosita)(views.api_obtener_prendas), name='api_obtener_prendas'),

    # -----------------------------------------------------------
    # ⚽ MÓDULO DE BALONES Y BAJAS (videos.html)
    # -----------------------------------------------------------
    path('videos/', login_required(views.videos), name='videos'),
    path('api/guardar-entrega/', login_required(views.api_guardar_entrega), name='api_guardar_entrega'),
    path('api/obtener-entregas/', login_required(views.api_obtener_entregas), name='api_obtener_entregas'),
    path('api/eliminar-entrega/<int:entrega_id>/', login_required(views.api_eliminar_entrega), name='api_eliminar_entrega'),
    
    path('api/guardar-baja/', login_required(views.api_guardar_baja), name='api_guardar_baja'),
    path('api/obtener-bajas/', login_required(views.api_obtener_bajas), name='api_obtener_bajas'),
    path('api/eliminar-baja/<int:baja_id>/', login_required(views.api_eliminar_baja), name='api_eliminar_baja'),

    # -----------------------------------------------------------
    # 🔍 MÓDULO DE OBJETOS PERDIDOS (voz.html)
    # -----------------------------------------------------------
    path('voz/', login_required(views.voz), name='voz'),
    path('api/guardar-objeto/', login_required(views.api_guardar_objeto), name='api_guardar_objeto'),
    path('api/obtener-objetos/', login_required(views.api_obtener_objetos), name='api_obtener_objetos'),
    path('api/eliminar-objeto/<int:obj_id>/', login_required(views.api_eliminar_objeto), name='api_eliminar_objeto'),

    # -----------------------------------------------------------
    # 📝 TAREAS Y RUTINAS
    # -----------------------------------------------------------
    path('tasks/create/', login_required(views.create_task), name='create_task'),
    path('tasks/<int:task_id>/', login_required(views.lista), name='lista'),
    path('tasks/<int:task_id>/completar/', login_required(views.completar), name='completar'),
    path('tasks/<int:task_id>/eliminar/', login_required(views.eliminar_tarea), name='eliminar_tarea'),
    path('enviar-rutina-correo/', login_required(views.enviar_rutina_correo), name='enviar_rutina_correo'),

    # -----------------------------------------------------------
    # 🔑 RECUPERACIÓN DE CONTRASEÑA
    # -----------------------------------------------------------
    path('recuperar/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='enlace_enviado.html'), name='password_reset_done'),
    path('recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='restablecer_password.html'), name='password_reset_confirm'),
    path('recuperar/completo/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]