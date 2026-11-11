
"""
Django settings for Miyabi E-commerce.

Local development:
- SQLite database
- Local media storage
- Console email backend

Production:
- PostgreSQL database (Neon)
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


# ==========================================================
# ENVIRONMENT DETECTION
# ==========================================================

IS_HOSTED = (
    "RENDER" in os.environ
    or "VERCEL" in os.environ
    or os.environ.get("ENVIRONMENT") == "production"
)


# ==========================================================
# SECURITY
# ==========================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-local-development-key-change-before-production"
)

DEBUG = os.environ.get(
    "DEBUG",
    "False" if IS_HOSTED else "True"
).lower() == "true"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".onrender.com",
    ".vercel.app",
]

# Add custom domain through environment variable if needed.
CUSTOM_DOMAIN = os.environ.get("CUSTOM_DOMAIN")

if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)

CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
    "https://*.vercel.app",
]

if CUSTOM_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(
        f"https://{CUSTOM_DOMAIN}"
    )

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
    and os.environ.get("CLOUDINARY_API_KEY")
    and os.environ.get("CLOUDINARY_API_SECRET")
)


# ==========================================================
# INSTALLED APPLICATIONS
# ==========================================================

INSTALLED_APPS = [
    # Django built-in applications
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Miyabi applications
    "app.apps.AppConfig",
    "pos",
]

# Cloudinary applications
if USE_CLOUDINARY:
    INSTALLED_APPS += [
        "cloudinary",
        "cloudinary_storage",
    ]


# ==========================================================
# CART SETTINGS
# ==========================================================

# Your cart uses Django sessions.
# Do not add 'cart' to INSTALLED_APPS because
# your project does not contain a separate cart app.

CART_SESSION_ID = "cart"


# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==========================================================
# URL CONFIGURATION
# ==========================================================

ROOT_URLCONF = "ECommerce.urls"


# ==========================================================
# TEMPLATES
# ==========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ==========================================================
# WSGI
# ==========================================================

WSGI_APPLICATION = "ECommerce.wsgi.application"


# ==========================================================
# DATABASE
# ==========================================================

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    # Local development database
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ==========================================================
# PASSWORD VALIDATION
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ==========================================================
# INTERNATIONALIZATION
# ==========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ==========================================================
# STATIC FILES
# ==========================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# WhiteNoise compressed static files
STORAGES = {
    "default": {
        "BACKEND": (
            "cloudinary_storage.storage.MediaCloudinaryStorage"
            if USE_CLOUDINARY
            else "django.core.files.storage.FileSystemStorage"
        ),
    },

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}


# ==========================================================
# MEDIA FILES
# ==========================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

if USE_CLOUDINARY:
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME"),
        "API_KEY": os.environ.get("CLOUDINARY_API_KEY"),
        "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET"),
    }


# ==========================================================
# DEFAULT PRIMARY KEY
# ==========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==========================================================
# EMAIL CONFIGURATION
# ==========================================================

EMAIL_HOST_USER = os.environ.get(
    "EMAIL_HOST_USER",
    ""
)

EMAIL_HOST_PASSWORD = os.environ.get(
    "EMAIL_HOST_PASSWORD",
    ""
)

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:

    EMAIL_BACKEND = (
        "django.core.mail.backends.smtp.EmailBackend"
    )

    EMAIL_USE_TLS = True

    EMAIL_HOST = "smtp.gmail.com"

    EMAIL_PORT = 587

else:

    EMAIL_BACKEND = (
        "django.core.mail.backends.console.EmailBackend"
    )


# ==========================================================
# AUTHENTICATION REDIRECTS
# ==========================================================

LOGIN_REDIRECT_URL = "index"

LOGOUT_REDIRECT_URL = "index"

LOGIN_URL = "/accounts/login/"
