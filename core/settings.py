# settings.py

from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de archivos estáticos para producción con WhiteNoise
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# Configuración de seguridad y entorno
SECRET_KEY = config('SECRET_KEY')

# En producción, DEBUG debe ser False y ALLOWED_HOSTS debe contener los dominios permitidos
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
# En Render, el dominio del servicio llega solo en esta variable, así no hay que escribirlo a mano
RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default='')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Aplicaciones instaladas, middleware, configuración de base de datos, autenticación, internacionalización, etc. se definen a continuación
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_spectacular',
    # Terceros
    'rest_framework',
    'corsheaders',
    # Apps propias
    'apis',
    'users',
]
# Middleware, incluyendo CORS para permitir peticiones del frontend al backend
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

ROOT_URLCONF = 'core.urls'
# Configuración de plantillas, apuntando a la carpeta de templates del frontend
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'frontend.context_processors.modo_demo',
            ],
        },
    },
]

# Configuración de WSGI para despliegue
WSGI_APPLICATION = 'core.wsgi.application'

import dj_database_url

# Configuración de base de datos, usando dj_database_url para facilitar la configuración en diferentes entornos (desarrollo con SQLite y producción con PostgreSQL)
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
    )
}

# Validadores de contraseña para mejorar la seguridad de las cuentas de usuario
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'frontend' / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    # Paginación para limitar resultados y mejorar rendimiento
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 6,
    # Throttling para limitar peticiones y evitar abusos
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '60/minute',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# CORS: el frontend se sirve desde el mismo dominio que la API, así que no necesita CORS.
# Solo se permiten los orígenes que se indiquen en la variable de entorno (por defecto, ninguno).
CORS_ALLOWED_ORIGINS = [o.strip() for o in config('CORS_ALLOWED_ORIGINS', default='').split(',') if o.strip()]

# Caducidad del enlace de verificación de email (en horas)
VERIFICACION_HORAS = config('VERIFICACION_HORAS', default=24, cast=int)

# Modo demo (versión pública del portfolio): todos usan una cuenta compartida,
# así que se bloquean el registro y los cambios en la cuenta para que nadie la estropee.
MODO_DEMO = config('MODO_DEMO', default=False, cast=bool)
DEMO_USUARIO = config('DEMO_USUARIO', default='demo')
DEMO_PASSWORD = config('DEMO_PASSWORD', default='')

# Email — en desarrollo sale por terminal
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

# Fuerza HTTPS en las URLs generadas por DRF para railway (paginación, etc.)
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Al pedir recursos a otros sitios (como los mapas de OpenStreetMap), el navegador envía solo el dominio
# de la web en la cabecera Referer. Django por defecto no la envía, y OpenStreetMap bloquea esas peticiones.
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'