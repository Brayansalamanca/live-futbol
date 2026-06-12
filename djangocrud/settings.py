import os
from pathlib import Path
from dotenv import load_dotenv

# ==========================================
# CARGAR VARIABLES .ENV
# ==========================================
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================
# SEGURIDAD
# ==========================================
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-z$!j#aip6tr)!7=l#1&=_*=jc4s*2@tve06#i&hwg&p5na7z2'
)

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '.onrender.com',
    '.app.github.dev'
]

# ==========================================
# APPS
# ==========================================
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

# ==========================================
# MIDDLEWARE
# ==========================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'djangocrud.urls'

# ==========================================
# TEMPLATES
# ==========================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'tasks' / 'templates'
        ],

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

# ==========================================
# BASE DE DATOS MONGODB
# ==========================================
MONGO_URL = os.getenv(
    'MONGO_URL',
    'mongodb+srv://brayan:3143401305@cluster0.uuxqot8.mongodb.net/livefutbol_db?retryWrites=true&w=majority'
)

DATABASES = {
    'default': {
        'ENGINE': 'djongo',

        'NAME': 'livefutbol_db',

        'ENFORCE_SCHEMA': False,

        'CLIENT': {
            'host': MONGO_URL,

            'authMechanism': 'SCRAM-SHA-1',

            'serverSelectionTimeoutMS': 5000,

            'connectTimeoutMS': 5000,

            'retryWrites': True,
        }
    }
}

# ==========================================
# VALIDADORES
# ==========================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },

    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'
    },

    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'
    },

    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]

# ==========================================
# REGIÓN
# ==========================================
LANGUAGE_CODE = 'es-es'

TIME_ZONE = 'America/Bogota'
USE_TZ = True

USE_I18N = True



# ==========================================
# STATIC FILES
# ==========================================
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'tasks' / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

if not DEBUG:

    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

    WHITENOISE_MANIFEST_STRICT = False

# ==========================================
# LOGIN
# ==========================================
LOGIN_URL = 'signin'

LOGIN_REDIRECT_URL = 'tipos'

LOGOUT_REDIRECT_URL = 'signin'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# EMAIL GMAIL
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'

EMAIL_PORT = 587

EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')

EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

EMAIL_TIMEOUT = 20
EMAIL_SSL_KEYFILE = None
EMAIL_SSL_CERTFILE = None

# ==========================================
# CORS
# ==========================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",

    "http://127.0.0.1:5173",

    "http://localhost:3000",

    "http://127.0.0.1:8000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",

    "http://127.0.0.1:5173",

    "https://django2-xo79.onrender.com",

    "https://*.onrender.com",

    "https://*.app.github.dev"
]

# ==========================================
# MEDIA
# ==========================================
MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'