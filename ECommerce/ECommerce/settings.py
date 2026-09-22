"""
Django settings for ECommerce project.

Miyabi Website
Mahathir Mohammad Siyam

Django 6.0.2
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env for local development
load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-5xmhvawk$%-+rreht6#_t&f0fu)+@ytj=*vtxiey65+5g0_*$x"
)

# Render automatically provides the RENDER environment variable
DEBUG = "RENDER" not in os.environ


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".onrender.com",
]

# Explicit Render hostname, if available
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# ============================================================
# CSRF
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
]


# ============================================================
# HTTPS / RENDER PROXY
# ============================================================

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [

    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Cloudinary
    "cloudinary_storage",
    "cloudinary",

    # Your applications
    "app.apps.AppConfig",
    "cart",
]


# ============================================================
# CART
# ============================================================

CART_SESSION_ID = "cart"


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "ECommerce.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [

                "django.template.context_processors.debug",

                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",

                # Cart
                "cart.context_processor.cart_total_amount",

                # Social links
                "app.social_context_processor.social_links",
            ],
        },
    },
]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "ECommerce.wsgi.application"


# ============================================================
# DATABASE - SQLITE
# ============================================================

# Local:
#     BASE_DIR / "db.sqlite3"
#
# Render:
#     /var/data/db.sqlite3
#
# Render environment variable:
#     SQLITE_DB_PATH=/var/data/db.sqlite3

SQLITE_DB_PATH = os.environ.get(
    "SQLITE_DB_PATH",
    str(BASE_DIR / "db.sqlite3"),
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": SQLITE_DB_PATH,
    }
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator",
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

# Folder containing your source static files
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# collectstatic output
STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================================================
# MEDIA FILES
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# CLOUDINARY
# ============================================================

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.environ.get(
        "CLOUDINARY_CLOUD_NAME",
        "",
    ),

    "API_KEY": os.environ.get(
        "CLOUDINARY_API_KEY",
        "",
    ),

    "API_SECRET": os.environ.get(
        "CLOUDINARY_API_SECRET",
        "",
    ),
}


# ============================================================
# STORAGE
# ============================================================

if DEBUG:

    # --------------------------------------------------------
    # LOCAL DEVELOPMENT
    # --------------------------------------------------------

    STORAGES = {

        "default": {
            "BACKEND":
                "django.core.files.storage.FileSystemStorage",
        },

        "staticfiles": {
            "BACKEND":
                "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

else:

    # --------------------------------------------------------
    # RENDER PRODUCTION
    # --------------------------------------------------------

    STORAGES = {

        # Product images -> Cloudinary
        "default": {
            "BACKEND":
                "cloudinary_storage.storage.MediaCloudinaryStorage",
        },

        # Static files -> WhiteNoise
        "staticfiles": {
            "BACKEND":
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage",
        },
    }


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# EMAIL
# ============================================================

EMAIL_USE_TLS = True

EMAIL_HOST = "smtp.gmail.com"

EMAIL_PORT = 587

EMAIL_HOST_USER = os.environ.get(
    "EMAIL_HOST_USER",
    "24101194@uap-bd.edu",
)

EMAIL_HOST_PASSWORD = os.environ.get(
    "EMAIL_HOST_PASSWORD",
)


# ============================================================
# LOGIN / LOGOUT
# ============================================================

LOGIN_REDIRECT_URL = "index"

LOGOUT_REDIRECT_URL = "index"

LOGIN_URL = "/accounts/login/"