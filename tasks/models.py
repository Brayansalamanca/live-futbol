from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 1. GESTIÓN DE TAREAS
# ==========================================
class Task(models.Model):
    titulo = models.CharField(max_length=100, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    f_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    diaCompletado = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de finalización')
    importante = models.BooleanField(default=False, verbose_name='¿Es importante?')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')

    def __str__(self):
        return f'{self.titulo} - by {self.user.username}'

# ==========================================
# 2. REGISTRO DE ENTREGAS (BALONES ALQUILADOS)
# ==========================================
class RegistroEntrega(models.Model):
    nombre = models.CharField(max_length=100) # Quién recibe
    curso = models.CharField(max_length=20)
    objeto = models.CharField(max_length=50) # El balón entregado
    lugar = models.CharField(max_length=100)
    marca = models.CharField(max_length=50, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Entrega"

# ==========================================
# 3. OBJETOS PERDIDOS
# ==========================================
class ObjetoPerdido(models.Model):
    nombre_reporta = models.CharField(max_length=100)
    curso = models.CharField(max_length=20)
    tipo_objeto = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

# ==========================================
# 4. INVENTARIO DE ROPA (INDUMENTARIA)
# ==========================================
class PrendaRopa(models.Model):
    objeto = models.CharField(max_length=100)
    cantidad = models.IntegerField(default=1)
    cantidad_apartada = models.IntegerField(default=0)
    talla = models.CharField(max_length=20, blank=True, null=True)
    estado = models.CharField(max_length=20, default='Disponible')
    condicion = models.CharField(max_length=20, default='Óptimo')
    detalle_defecto = models.TextField(blank=True, null=True)
    
    # Datos de apartado
    nombre_apartado = models.CharField(max_length=100, blank=True, null=True)
    curso_apartado = models.CharField(max_length=50, blank=True, null=True)
    evento_apartado = models.CharField(max_length=100, blank=True, null=True)
    fecha_uso = models.DateField(blank=True, null=True)
    dias_alquiler = models.IntegerField(blank=True, null=True, default=0)
    
    imagen = models.TextField() # Base64 o URL
    devuelto = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.objeto} ({self.cantidad})"

# ==========================================
# 5. GESTIÓN DE BAJAS (BALONES PERDIDOS/DAÑADOS)
# ==========================================
class BajaBalon(models.Model):
    tipo_balon = models.CharField(max_length=50)
    causa = models.CharField(max_length=50)
    marca = models.CharField(max_length=50) # En tu vista se usa como 'Lugar'
    responsable = models.CharField(max_length=100) # Quién lo botó
    alquilado_por = models.CharField(max_length=100, null=True, blank=True) # Quién alquiló
    foto = models.TextField() # Base64
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Baja: {self.tipo_balon} - {self.causa}"
class AsistenciaAlimento(models.Model):
    nombre = models.CharField(max_length=100)
    grado = models.CharField(max_length=20)
    seccion = models.CharField(max_length=20)

    pago = models.BooleanField(default=True)

    estado = models.CharField(
        max_length=20,
        choices=[
            ('normal', 'Normal'),
            ('extra', 'Extra'),
            ('grave', 'Grave')
        ],
        default='normal'
    )

    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class ReservaPrenda(models.Model):
    prenda = models.ForeignKey(
        PrendaRopa,
        on_delete=models.CASCADE,
        related_name='reservas'
    )

    nombre = models.CharField(max_length=100)
    curso = models.CharField(max_length=50, blank=True)
    evento = models.CharField(max_length=100, blank=True)

    cantidad = models.IntegerField(default=1)

    fecha_uso = models.DateField()
    fecha_reserva = models.DateTimeField(auto_now_add=True)

    entregado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.prenda.objeto} - {self.nombre} - {self.fecha_uso}"