from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from tasks import views

def es_rosita(user):
    return user.is_authenticated and user.username == 'rosita'

def es_asistente_bienestar1(user):
    return user.is_authenticated and user.username == 'asistente_bienestar1'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.signout, name='logout'),
    path('activar/<uidb64>/<token>/', views.activar, name='activar'),
    path('condiciones/', views.condiciones, name='condiciones'),
    path('soporte/', views.soporte, name='soporte'),

    path('formulario/', user_passes_test(es_rosita)(views.formulario), name='formulario'),
    path('tipos/', login_required(views.tipos), name='tipos'), 

    path('radar/', user_passes_test(es_asistente_bienestar1)(views.radar), name='radar'), 
    path('videos/', user_passes_test(es_asistente_bienestar1)(views.videos), name='videos'),
    path('voz/', user_passes_test(es_asistente_bienestar1)(views.voz), name='voz'),

    path('tasks/', login_required(views.tasks), name='tasks'),
    path('tasks/create/', login_required(views.create_task), name='create_task'),
    path('tasks/<int:task_id>/', login_required(views.lista), name='lista'),
    path('tasks/<int:task_id>/completar/', login_required(views.completar), name='completar'),
    path('tasks/<int:task_id>/eliminar/', login_required(views.eliminar_tarea), name='eliminar_tarea'),
]