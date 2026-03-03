from django.db import models
from django.contrib.auth.models import User

# 1. TAREAS (Tu modelo original)
class Task(models.Model):
    titulo = models.CharField(max_length=100, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    f_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    diaCompletado = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de finalización')
    importante = models.BooleanField(default=False, verbose_name='¿Es importante?')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')

    def __str__(self):
        return f'{self.titulo} - by {self.user.username}'

# 2. REGISTRO DE ENTREGAS (Para el primer código que me pasaste)
class RegistroEntrega(models.Model):
    nombre = models.CharField(max_length=100)
    curso = models.CharField(max_length=20)
    objeto = models.CharField(max_length=50)
    lugar = models.CharField(max_length=100)
    marca = models.CharField(max_length=50, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Entrega"

# 3. OBJETOS PERDIDOS (Centro de reportes)
class ObjetoPerdido(models.Model):
    nombre_reporta = models.CharField(max_length=100)
    curso = models.CharField(max_length=20)
    tipo_objeto = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

# 4. INVENTARIO DE ROPA (Optimizado para 300+ prendas)
class PrendaRopa(models.Model):
    objeto = models.CharField(max_length=100) # Saco, Joger, Pantalón...
    talla = models.CharField(max_length=20)
    estado = models.CharField(max_length=20, default='Disponible') # Disponible / Apartado
    condicion = models.CharField(max_length=20, default='Óptimo') # Óptimo / Defecto
    detalle_defecto = models.TextField(blank=True, null=True)
    nombre_apartado = models.CharField(max_length=100, blank=True, null=True)
    imagen = models.TextField()  # Guardamos el Base64 (texto de la foto)
    fecha_registro = models.DateTimeField(auto_now_add=True)

# 5. GESTIÓN DE BALONES / BAJAS
class BajaBalon(models.Model):
    tipo_balon = models.CharField(max_length=50)
    causa = models.CharField(max_length=50)
    marca = models.CharField(max_length=50)
    responsable = models.CharField(max_length=100)
    foto = models.TextField() # Base64
    fecha = models.DateTimeField(auto_now_add=True)