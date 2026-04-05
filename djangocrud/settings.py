import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Cargar variables de entorno (Localmente usa un archivo .env)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Seguridad
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-z$!j#aip6tr)!7=l#1&=_*=jc4s*2@tve06#i&hwg&p5na7z2')

# 3. DEBUG
DEBUG = False

# Permitir localhost y la URL de Render
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.onrender.com']

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tasks',
    'api',
    'rest_framework',
    'corsheaders',
    'djongo',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'djangocrud.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'tasks' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'djangocrud.wsgi.application'

# 4. CONFIGURACIÓN BASE DE DATOS
MONGO_URL = os.getenv('MONGO_URL', 'mongodb+srv://brayan:3143401305@cluster0.uuxqot8.mongodb.net/livefutbol_db?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true')

DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'livefutbol_db',
        'ENFORCE_SCHEMA': False,
        'CLIENT': {
            'host': MONGO_URL,
            'authMechanism': 'SCRAM-SHA-1', # Ayuda a la compatibilidad con Atlas
            'serverSelectionTimeoutMS': 5000, # Si en 5 segundos no conecta, falla (evita el 502)
            'connectTimeoutMS': 5000,
            'retryWrites': True,
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Configuración Regional
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# 5. Archivos Estáticos (CSS, JS, Imágenes)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'tasks' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Optimización para Render
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    WHITENOISE_MANIFEST_STRICT = False

# ==========================================
# 🔑 CONFIGURACIÓN DE ACCESO Y REDIRECCIÓN
# ==========================================
# Esto evita el error de "/accounts/login/"
LOGIN_URL = 'signin' 

# Redirección por defecto si la lógica de views.py no encuentra un rol
LOGIN_REDIRECT_URL = 'tipos' 

LOGOUT_REDIRECT_URL = 'signin'
# ==========================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 6. Configuración de Correo (Gmail)
# Asegúrate de que estas líneas estén ASÍ exactamente
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'saebra581@gmail.com'
EMAIL_HOST_PASSWORD = 'lhuukgqvmxfoxaju' # Tu nueva clave sin espacios

# AÑADE ESTO para evitar problemas de conexión colgada
EMAIL_TIMEOUT = 10

# 7. Seguridad CORS y CSRF
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://*.onrender.com"
]

# Fotos y Medios
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'