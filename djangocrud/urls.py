from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from tasks import views  # Asegúrate que tu app se llame 'tasks'

# Funciones de permisos
def es_rosita(user):
    return user.is_authenticated and user.username == 'rosita'

def es_asistente_bienestar1(user):
    return user.is_authenticated and user.username == 'asistente_bienestar1'

urlpatterns = [
    # GESTIÓN DE CUENTA
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.signout, name='logout'), # Cambiado de signout a logout para base.html
    path('activar/<uidb64>/<token>/', views.activar, name='activar'),
    path('condiciones/', views.condiciones, name='condiciones'),
    path('soporte/', views.soporte, name='soporte'),

    # ROPA
    path('formulario/', user_passes_test(es_rosita)(views.formulario), name='formulario'),
    path('tipos/', login_required(views.tipos), name='tipos'), 
    
    # BALONES (Asegurando que los nombres coincidan con el menú)
    path('radar/', user_passes_test(es_asistente_bienestar1)(views.radar), name='radar'), 
    path('videos/', user_passes_test(es_asistente_bienestar1)(views.videos), name='videos'),
    path('voz/', user_passes_test(es_asistente_bienestar1)(views.voz), name='voz'),

    # TAREAS
    path('tasks/', login_required(views.tasks), name='tasks'),
    path('tasks/create/', login_required(views.create_task), name='create_task'),
    path('tasks/<int:task_id>/', login_required(views.lista), name='lista'),
    path('tasks/<int:task_id>/completar/', login_required(views.completar), name='completar'),
    path('tasks/<int:task_id>/eliminar/', login_required(views.eliminar_tarea), name='eliminar_tarea'),

    # RECUPERACIÓN DE CLAVE (Nombres estándar de Django)
    path('recuperar/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='enlace_enviado.html'), name='password_reset_done'),
    path('recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='restablecer_password.html'), name='password_reset_confirm'),
    path('recuperar/completo/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]