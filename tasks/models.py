from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    titulo = models.CharField(
        max_length=100,
        verbose_name='Título',
        help_text='Ingresa un título breve para la tarea'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Describe los detalles de la tarea'
    )

    f_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    diaCompletado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de finalización'
    )

    importante = models.BooleanField(
        default=False,
        verbose_name='¿Es importante?'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )

    def __str__(self):
        return f'{self.titulo} - by {self.user.username}'


