
"""
Django settings for the Miyabi E-commerce project.

Local development:
- SQLite database
- Local media storage
- Console email backend

Render production:
- PostgreSQL database
- Cloudinary image storage
- Environment variables for secrets
- WhiteNoise static files
"""

import os
from pathlib import Path

import dj_database_url


# ==========================================================
# BASE DIRECTORY
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ON_RENDER = "RENDER" in os.environ


# ==========================================================
# SECURITY
# ==========================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "dev-only-insecure-key-change-me"
)

DEBUG = os.environ.get(
    "DEBUG",
    "False" if ON_RENDER else "True"
) == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
]

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# ==========================================================
# CLOUDINARY DETECTION
# ==========================================================

USE_CLOUDINARY = bool(
    os.environ.get("CLOUDINARY_CLOUD_NAME")
)


# ==========================================================
# INSTALLED APPS
# ==========================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Miyabi applications
    'app.apps.AppConfig',
    'cart',
    'pos',
]

if USE_CLOUDINARY:
    INSTALLED_APPS += [
        'cloudinary',
        'cloudinary_storage',
    ]


# ==========================================================
# CART SETTINGS
# ==========================================================

CART_SESSION_ID = 'cart'


# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ==========================================================
# URL CONFIGURATION
# ==========================================================

ROOT_URLCONF = 'ECommerce.urls'


# ==========================================================
# TEMPLATES
# ==========================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates',
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'cart.context_processor.cart_total_amount',
            ],
        },
    },
]


# ==========================================================
# WSGI
# ==========================================================

WSGI_APPLICATION = 'ECommerce.wsgi.application'


# ==========================================================
# DATABASE
# ==========================================================

# Local: SQLite
# Render: PostgreSQL through DATABASE_URL

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),

        conn_max_age=600,

        conn_health_checks=True,

        ssl_require=bool(os.environ.get('DATABASE_URL')),
    )
}


# ==========================================================
# PASSWORD VALIDATION
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },

    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },

    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },

    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]


# ==========================================================
# INTERNATIONALIZATION
# ==========================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# ==========================================================
# STATIC AND MEDIA FILES
# ==========================================================

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# ==========================================================
# CLOUDINARY CONFIGURATION
# ==========================================================

if USE_CLOUDINARY:

    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get(
            'CLOUDINARY_CLOUD_NAME'
        ),

        'API_KEY': os.environ.get(
            'CLOUDINARY_API_KEY'
        ),

        'API_SECRET': os.environ.get(
            'CLOUDINARY_API_SECRET'
        ),
    }

    DEFAULT_FILE_STORAGE_BACKEND = (
        'cloudinary_storage.storage.MediaCloudinaryStorage'
    )

else:

    # Local development media storage

    DEFAULT_FILE_STORAGE_BACKEND = (
        'django.core.files.storage.FileSystemStorage'
    )


# ==========================================================
# DJANGO STORAGE CONFIGURATION
# ==========================================================

STORAGES = {

    # Uploaded images

    "default": {
        "BACKEND": DEFAULT_FILE_STORAGE_BACKEND,
    },

    # Static files

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },

}


# ==========================================================
# DEFAULT PRIMARY KEY
# ==========================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==========================================================
# EMAIL CONFIGURATION
# ==========================================================

EMAIL_HOST_USER = os.environ.get(
    'EMAIL_HOST_USER',
    ''
)

EMAIL_HOST_PASSWORD = os.environ.get(
    'EMAIL_HOST_PASSWORD',
    ''
)

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:

    EMAIL_BACKEND = (
        'django.core.mail.backends.smtp.EmailBackend'
    )

    EMAIL_USE_TLS = True

    EMAIL_HOST = 'smtp.gmail.com'

    EMAIL_PORT = 587

else:

    EMAIL_BACKEND = (
        'django.core.mail.backends.console.EmailBackend'
    )


# ==========================================================
# AUTHENTICATION REDIRECTS
# ==========================================================

LOGIN_REDIRECT_URL = 'index'

LOGOUT_REDIRECT_URL = 'index'

LOGIN_URL = '/accounts/login/'
