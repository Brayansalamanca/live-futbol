from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Task

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')

    class Meta:
        model = User
        fields = ('username', 'email') # password1 y password2 los maneja UserCreationForm automáticamente

    # ESTO ES LO QUE SOLUCIONA EL ERROR:
    # Sobrescribimos la validación para evitar que Django use el comando iLIKE
    def clean_username(self):
        username = self.cleaned_data.get("username")
        # Usamos filter().exists() que Djongo traduce a un comando compatible con MongoDB
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")
        return username

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['titulo', 'descripcion', 'importante']
        # Añadimos widgets para que se vea mejor en el HTML
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escribe un título'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe la tarea'}),
            'importante': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EmailForm(forms.Form):
    email = forms.EmailField(label="Correo de destino", required=True)