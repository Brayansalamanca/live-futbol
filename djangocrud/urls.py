from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from tasks import views

urlpatterns = [
    # 🌍 Rutas públicas
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),

    # Confirmación de correo
    path('activar/<uidb64>/<token>/', views.activar, name='activar'),

    # 🔒 Rutas protegidas
    path('logout/', views.signout, name='logout'),
    path('tasks/create/', login_required(views.create_task), name='create_task'),
    path('tasks/<int:task_id>/', login_required(views.lista), name='lista'),
    path('tasks/<int:task_id>/completar/', login_required(views.completar), name='completar'),
    path('tasks/<int:task_id>/eliminar/', login_required(views.eliminar_tarea), name='eliminar_tarea'),

    path('soporte/', views.soporte, name='soporte'),
    path('radar/', login_required(views.radar), name='radar'),
    path('videos/', login_required(views.videos), name='videos'),
    path('voz/', login_required(views.voz), name='voz'),
    path('formulario/', login_required(views.formulario), name='formulario'),
    path('condiciones/', views.condiciones, name='condiciones'),
    path('enviar-rutina-correo/', views.enviar_rutina_correo, name='enviar_rutina_correo'),

    # 🔑 Recuperación de contraseña
    path('recuperar/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='enlace_enviado.html'), name='password_reset_done'),
    path('recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='restablecer_password.html'), name='password_reset_confirm'),
    path('recuperar/completo/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]
