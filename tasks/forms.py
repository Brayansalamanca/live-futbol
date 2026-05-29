from django import forms
from .models import Task


class CustomUserCreationForm(forms.Form):

    nombre_real = forms.CharField(
        max_length=255,
        required=True,
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: Juan David Pérez'
        })
    )

    email = forms.EmailField(
        required=False,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'placeholder': 'correo@ejemplo.com'
        })
    )

    ROLES = [
        ('asistente bienestar', 'Asistente de Bienestar'),
        ('coordinacion', 'Coordinación / Administrativo'),
        ('profesores', 'Profesor'),
    ]

    rol = forms.ChoiceField(
        choices=ROLES,
        required=True
    )


class TaskForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = ['titulo', 'descripcion', 'importante']

        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Escribe un título'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe la tarea'
            }),

            'importante': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class EmailForm(forms.Form):

    email = forms.EmailField(
        label="Correo de destino",
        required=True
    )