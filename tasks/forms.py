from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Task  # ← AGREGAR esta importación

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['titulo', 'descripcion', 'importante']


class EmailForm(forms.Form):
    email = forms.EmailField(label="Correo de destino", required=True)