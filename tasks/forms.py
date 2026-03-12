from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Task

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    
    # 1. Definimos los ROLES exactos que coinciden con los 'value' de tu HTML
    ROLES = [
        ('asistente bienestar', 'Asistente de Bienestar'),
        ('coordinacion', 'Coordinación / Administrativo'),
        ('profesores', 'Profesor'),
    ]
    
    rol = forms.ChoiceField(
        choices=ROLES, 
        required=True, 
        label='Rol solicitado',
        # El widget Select asegura que se renderice como una lista desplegable
        widget=forms.Select(attrs={'class': 'form-control'}) 
    )

    class Meta:
        model = User
        # Añadimos 'rol' a los campos del formulario para que Django lo procese
        fields = ('username', 'email', 'rol') 

    def clean_username(self):
        """Valida que el nombre de usuario sea único (útil para Djongo/MongoDB)"""
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def clean_email(self):
        """Valida que el correo sea único"""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está en uso.")
        return email

class TaskForm(forms.ModelForm):
    """Formulario para la creación de tareas personales"""
    class Meta:
        model = Task
        fields = ['titulo', 'descripcion', 'importante']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escribe un título'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe la tarea'}),
            'importante': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EmailForm(forms.Form):
    """Formulario simple para envío de correos"""
    email = forms.EmailField(label="Correo de destino", required=True)