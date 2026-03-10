from django.urls import path
from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test
from . import views

# Funciones de validación de usuario
def es_rosita(user): return user.is_authenticated and user.username == 'rosita'
def es_asistente(user): return user.is_authenticated and user.username == 'asistente_bienestar1'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('soporte/', views.soporte, name='soporte'),
    path('condiciones/', views.condiciones, name='condiciones'),
    
    # Auth
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.signout, name='logout'), # Importante: name='logout'
    
    # Ropa
    path('formulario/', user_passes_test(es_rosita)(views.formulario), name='formulario'),
    path('tipos/', login_required(views.tipos), name='tipos'),
    
    # Balones
    path('radar/', user_passes_test(es_asistente)(views.radar), name='radar'),
    path('videos/', user_passes_test(es_asistente)(views.videos), name='videos'),
    path('voz/', user_passes_test(es_asistente)(views.voz), name='voz'),
    
    # Tareas
    path('tasks/', login_required(views.tasks), name='tasks'),
]