from django.db import models
from django.contrib.auth.models import User

# -----------------------------------------------------------
# 1. GESTIÓN DE USUARIOS Y TAREAS (Original)
# -----------------------------------------------------------
class Task(models.Model):
    titulo = models.CharField(max_length=100, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    f_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    diaCompletado = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de finalización')
    importante = models.BooleanField(default=False, verbose_name='¿Es importante?')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')

    def __str__(self):
        return f'{self.titulo} - by {self.user.username}'

# -----------------------------------------------------------
# 2. CONTROL DE BALONES Y EQUIPOS (Préstamos rápidos)
# -----------------------------------------------------------
class RegistroEntrega(models.Model):
    nombre = models.CharField(max_length=100) # Estudiante
    curso = models.CharField(max_length=20)
    objeto = models.CharField(max_length=50) # Balón, Cuerda, etc.
    lugar = models.CharField(max_length=100)
    marca = models.CharField(max_length=50, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Entrega"

# -----------------------------------------------------------
# 3. OBJETOS PERDIDOS
# -----------------------------------------------------------
class ObjetoPerdido(models.Model):
    nombre_reporta = models.CharField(max_length=100)
    curso = models.CharField(max_length=20)
    tipo_objeto = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

# -----------------------------------------------------------
# 4. INVENTARIO DE ROPA (Optimizado para Rosita y Profesores)
# -----------------------------------------------------------
class PrendaRopa(models.Model):
    # Datos básicos de la prenda
    objeto = models.CharField(max_length=100) # Nombre: "Uniforme Gala", "Peto", etc.
    cantidad = models.IntegerField(default=1) # Stock total en el colegio
    talla = models.CharField(max_length=20, blank=True)
    imagen = models.TextField() # Almacena el Base64 de la foto para MongoDB
    
    # Estado del inventario
    estado = models.CharField(
        max_length=20, 
        choices=[('Disponible', 'Disponible'), ('Apartado', 'Apartado'), ('En Lavandería', 'En Lavandería')],
        default='Disponible'
    )
    condicion = models.CharField(max_length=20, default='Óptimo') # Óptimo / Defecto
    detalle_defecto = models.TextField(blank=True, null=True)

    # Datos del Apartado (Para Profesores)
    nombre_apartado = models.CharField(max_length=100, blank=True, null=True) # Nombre del Profesor
    fecha_uso = models.DateField(blank=True, null=True) # Regla de los 10 días
    
    # Control de Paz y Salvo (Exclusivo Rosita)
    devuelto = models.BooleanField(default=True) # True = Paz y Salvo / False = Pendiente
    observaciones_entrega = models.TextField(blank=True, null=True)
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.objeto} - {self.cantidad} unidades"

# -----------------------------------------------------------
# 5. GESTIÓN DE BAJAS (Desechos de material)
# -----------------------------------------------------------
class BajaBalon(models.Model):
    tipo_balon = models.CharField(max_length=50)
    causa = models.CharField(max_length=50) # Pinchado, Perdido, Desgastado
    marca = models.CharField(max_length=50)
    responsable = models.CharField(max_length=100) # Quién reporta la baja
    foto = models.TextField() # Base64
    fecha = models.DateTimeField(auto_now_add=True)