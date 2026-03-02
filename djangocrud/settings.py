import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Cargar variables de entorno (Asegúrate de tener instalado: pip install python-dotenv)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Seguridad: Prioriza el .env
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-z$!j#aip6tr)!7=l#1&=_*=jc4s*2@tve06#i&hwg&#p5na7z2')

# 3. DEBUG dinámico
DEBUG = os.getenv('DEBUG', 'True') == 'True'
if os.environ.get('RENDER'):
    DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.onrender.com', '*']

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
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

# 4. CONFIGURACIÓN EXCLUSIVA MONGODB (DJONGO)
# No necesitas pymysql ni dj_database_url aquí
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'livefutbol_db',
        'ENFORCE_SCHEMA': False,
        'CLIENT': {
            'host': os.getenv('MONGO_URL', 'mongodb+srv://brayan:3143401305@cluster0.uuxqot8.mongodb.net/livefutbol_db?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true'),
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalización
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Archivos Estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'tasks' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

if os.environ.get('RENDER'):
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    WHITENOISE_MANIFEST_STRICT = False

# Redirecciones
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 5. Configuración de Correo (Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'saebra581@gmail.com'
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD', 'bfaslgsipjnpmnpd')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# 6. Seguridad CORS y CSRF
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.onrender.com"
]