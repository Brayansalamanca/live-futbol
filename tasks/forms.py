from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Task

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    
    # Añadimos el campo de Rol con las opciones solicitadas
    ROLES = [
        ('Asistente', 'Asistente'),
        ('Coordinacion', 'Coordinación'),
    ]
    rol = forms.ChoiceField(
        choices=ROLES, 
        required=True, 
        label='Rol solicitado',
        widget=forms.Select(attrs={'class': 'form-control'}) # Mantiene consistencia visual
    )

    class Meta:
        model = User
        # Añadimos 'rol' a los campos del formulario
        fields = ('username', 'email', 'rol') 

    def clean_username(self):
        username = self.cleaned_data.get("username")
        # Mantenemos tu solución para Djongo/MongoDB
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")
        return username

    # Agregamos validación para el correo (opcional pero recomendado)
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está en uso.")
        return email

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['titulo', 'descripcion', 'importante']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escribe un título'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe la tarea'}),
            'importante': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EmailForm(forms.Form):
    email = forms.EmailField(label="Correo de destino", required=True)