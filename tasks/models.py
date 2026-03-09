from django.db import models
from django.contrib.auth.models import User

# ============================
# 1. GESTIÓN DE TAREAS
# ============================
class Task(models.Model):
    titulo = models.CharField(max_length=100, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    f_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    diaCompletado = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de finalización')
    importante = models.BooleanField(default=False, verbose_name='¿Es importante?')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')

    def __str__(self):
        return f'{self.titulo} - by {self.user.username}'

# ============================
# 2. REGISTRO DE ENTREGAS (Balones/Material)
# ============================
class RegistroEntrega(models.Model):
    nombre = models.CharField(max_length=100) # Quién recibe
    curso = models.CharField(max_length=20)
    objeto = models.CharField(max_length=50) # Qué balones
    lugar = models.CharField(max_length=100)
    marca = models.CharField(max_length=50, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Entrega"

# ============================
# 3. OBJETOS PERDIDOS
# ============================
class ObjetoPerdido(models.Model):
    nombre_reporta = models.CharField(max_length=100)
    curso = models.CharField(max_length=20)
    tipo_objeto = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

# ============================
# 4. INVENTARIO DE ROPA (Sincronizado para Rosita)
# ============================
class PrendaRopa(models.Model):
    # Datos básicos de la prenda
    objeto = models.CharField(max_length=100) # Nombre de la prenda
    cantidad = models.IntegerField(default=1)
    talla = models.CharField(max_length=20, blank=True, null=True)
    estado = models.CharField(max_length=20, default='Disponible') # Disponible/Apartado
    condicion = models.CharField(max_length=20, default='Óptimo')
    detalle_defecto = models.TextField(blank=True, null=True)
    
    # Datos del Apartado (Para Profesores)
    nombre_apartado = models.CharField(max_length=100, blank=True, null=True) # Nombre del Prof.
    curso_apartado = models.CharField(max_length=50, blank=True, null=True)
    evento_apartado = models.CharField(max_length=100, blank=True, null=True) # Para qué evento
    fecha_uso = models.DateField(blank=True, null=True)
    
    # Media y Control
    imagen = models.TextField()  # Guardamos la foto en Base64
    devuelto = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.objeto} ({self.cantidad})"

# ============================
# 5. GESTIÓN DE BAJAS (Bajas Deportivas)
# ============================
class BajaBalon(models.Model):
    tipo_balon = models.CharField(max_length=50)
    causa = models.CharField(max_length=50) # Perdido/Pinchado/Robo
    marca = models.CharField(max_length=50) # Usado como Marca o Lugar según tu JS
    responsable = models.CharField(max_length=100)
    foto = models.TextField() # Guardamos la evidencia en Base64
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Baja: {self.tipo_balon} - {self.causa}"