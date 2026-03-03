from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from tasks import views

urlpatterns = [
    # 🌍 Rutas públicas
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),

    # Confirmación de correo
    path('activar/<uidb64>/<token>/', views.activar, name='activar'),

    # 🔒 Rutas protegidas (Secciones principales)
    path('logout/', views.signout, name='logout'),
    path('tasks/create/', login_required(views.create_task), name='create_task'),
    path('tasks/<int:task_id>/', login_required(views.lista), name='lista'),
    path('tasks/<int:task_id>/completar/', login_required(views.completar), name='completar'),
    path('tasks/<int:task_id>/eliminar/', login_required(views.eliminar_tarea), name='eliminar_tarea'),

    path('soporte/', views.soporte, name='soporte'),
    path('formulario/', login_required(views.formulario), name='formulario'),
    path('condiciones/', views.condiciones, name='condiciones'),
    path('enviar-rutina-correo/', views.enviar_rutina_correo, name='enviar_rutina_correo'),

    # ⚽ Sección BALONES (videos.html)
    path('videos/', login_required(views.videos), name='videos'),
    path('api/guardar-entrega/', views.api_guardar_entrega, name='api_guardar_entrega'),
    path('api/obtener-entregas/', views.api_obtener_entregas, name='api_obtener_entregas'),
    path('api/eliminar-entrega/<int:entrega_id>/', views.api_eliminar_entrega, name='api_eliminar_entrega'),

    # 📦 Sección ROPA (radar.html)
    path('radar/', login_required(views.radar), name='radar'),
    path('api/guardar-prenda/', views.api_guardar_prenda, name='api_guardar_prenda'),
    path('api/obtener-prendas/', views.api_obtener_prendas, name='api_obtener_prendas'),
    path('api/apartar-prenda/<int:prenda_id>/', views.api_apartar_prenda, name='api_apartar_prenda'),

    # 🔍 Sección OBJETOS PERDIDOS (voz.html)
    path('voz/', login_required(views.voz), name='voz'),
    # (Agregaremos las APIs de voz en el siguiente paso cuando arreglemos ese archivo)

    # 🔑 Recuperación de contraseña
    path('recuperar/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='enlace_enviado.html'), name='password_reset_done'),
    path('recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='restablecer_password.html'), name='password_reset_confirm'),
    path('recuperar/completo/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    # Rutas para Objetos Perdidos (voz.html)
    path('api/guardar-objeto/', views.api_guardar_objeto, name='api_guardar_objeto'),
    path('api/obtener-objetos/', views.api_obtener_objetos, name='api_obtener_objetos'),
    path('api/eliminar-objeto/<int:obj_id>/', views.api_eliminar_objeto, name='api_eliminar_objeto'),
    path('api/guardar-baja/', views.api_guardar_baja, name='api_guardar_baja'),
    path('api/obtener-bajas/', views.api_obtener_bajas, name='api_obtener_bajas'),
    path('api/eliminar-baja/<int:baja_id>/', views.api_eliminar_baja, name='api_eliminar_baja'),
]