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
# ⚽ INVENTARIO NFC DE BALONES
# ==========================================
class BalonNFC(models.Model):

    nombre_balon = models.CharField(max_length=100)

    tipo = models.CharField(max_length=50)

    codigo_nfc = models.CharField(
        max_length=100,
        unique=True
    )

    imagen = models.TextField(
        blank=True,
        null=True
    )

    disponible = models.BooleanField(default=True)

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.nombre_balon} - {self.tipo}"

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
# 🙋 SOLICITUDES DE OBJETOS PERDIDOS
# ==========================================

class SolicitudObjeto(models.Model):

    nombre = models.CharField(max_length=100)

    curso = models.CharField(max_length=20)

    prenda_buscada = models.CharField(max_length=100)

    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return f"{self.nombre} - {self.prenda_buscada}"
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
    # ==========================================
# HISTORIAL SEMANAL DE ENTREGAS
# ==========================================

class HistorialEntrega(models.Model):
    nombre = models.CharField(max_length=100)
    curso = models.CharField(max_length=20)
    objeto = models.CharField(max_length=50)
    lugar = models.CharField(max_length=100)

    fecha_entrega = models.DateTimeField()
    fecha_devolucion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.objeto}"
    

    from django.db import models


class UsuarioComedor(models.Model):

    nombre = models.CharField(
        max_length=255
    )

    documento = models.CharField(
        max_length=100,
        unique=True
    )

    uid_nfc = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    entregado_hoy = models.BooleanField(
        default=False
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return f"{self.nombre} - {self.documento}"

        # ==========================================
# 🏆 TORNEOS LIVE FUTBOL
# ==========================================

class Torneo(models.Model):

    nombre = models.CharField(
        max_length=200,
        unique=True
    )

    datos = models.JSONField(
        default=dict
    )

    fecha = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.nombre
    # ==========================================
# 📚 HORARIOS
# ==========================================

class HorarioCurso(models.Model):

    categoria = models.CharField(
        max_length=50
    )

    curso = models.CharField(
        max_length=50
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.categoria} - {self.curso}"


class BloqueHorario(models.Model):

    horario = models.ForeignKey(
        HorarioCurso,
        on_delete=models.CASCADE,
        related_name='bloques'
    )

    fila = models.IntegerField()

    col = models.IntegerField()

    profesor = models.CharField(
        max_length=100
    )

    materia = models.CharField(
        max_length=100
    )

    salon = models.CharField(
        max_length=100
    )

    tipo = models.CharField(
        max_length=30,
        default='clase'
    )

    def __str__(self):

        return f"{self.profesor} - {self.materia}"
    
    # ==========================================
# 👤 PERFIL DE USUARIO
# ==========================================

# ==========================================
# 👤 PERFIL DE USUARIO
# ==========================================

class Perfil(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    nombre_real = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    debe_cambiar_password = models.BooleanField(
        default=True
    )

    puede_apartar_prendas = models.BooleanField(
        default=False
    )

    def __str__(self):

        return self.user.username
    
    # ==========================================
# 💬 CHAT ESCOLAR
# ==========================================

class SalaChat(models.Model):

    nombre = models.CharField(
        max_length=255
    )

    creada = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.nombre


class MensajeChat(models.Model):

    sala = models.ForeignKey(
        SalaChat,
        on_delete=models.CASCADE,
        related_name='mensajes'
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    mensaje = models.TextField()

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    leido = models.BooleanField(
        default=False
    )

    def __str__(self):

        return f"{self.usuario.username}: {self.mensaje[:30]}"
    
    # ==========================================
# 🔔 NOTIFICACIONES
# ==========================================

class Notificacion(models.Model):

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )

    titulo = models.CharField(
        max_length=255
    )

    mensaje = models.TextField()

    leida = models.BooleanField(
        default=False
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.titulo
    
    # ==========================================
# 📜 HISTORIAL DEL SISTEMA
# ==========================================

class LogSistema(models.Model):

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    accion = models.CharField(
        max_length=255
    )

    modulo = models.CharField(
        max_length=100
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.usuario} - {self.accion}"
    
    