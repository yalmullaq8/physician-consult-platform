import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
USE_CLOUDINARY = os.getenv("USE_CLOUDINARY", "False").lower() == "true"


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'accounts',
    'physicians',
    'bookings',
    'payments',
    'notifications',
    'audit',
]

if USE_CLOUDINARY:
    INSTALLED_APPS += [
        'cloudinary_storage',
        'cloudinary',
    ]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
    )
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kuwait'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
if USE_CLOUDINARY:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', ''),
        'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
        'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
    }
    STORAGES = {
        'default': {
            'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
else:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        f"{FRONTEND_BASE_URL},{BACKEND_BASE_URL}",
    ).split(",")
    if origin.strip()
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", FRONTEND_BASE_URL).split(",")
    if origin.strip()
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost(:\d+)?$",
    r"^http://127\.0\.0\.1(:\d+)?$",
    r"^http://10\.\d+\.\d+\.\d+(:\d+)?$",
    r"^http://192\.168\.\d+\.\d+(:\d+)?$",
    r"^http://172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+(:\d+)?$",
]
CORS_ALLOW_CREDENTIALS = True

DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
PUBLIC_BOOKING_GUEST_EMAIL = os.getenv("PUBLIC_BOOKING_GUEST_EMAIL", "guest.requester@medconsult.local")
PUBLIC_BOOKING_GUEST_NAME = os.getenv("PUBLIC_BOOKING_GUEST_NAME", "Guest Requesting Physician")

MYFATOORAH_API_KEY = os.getenv("MYFATOORAH_API_KEY", "")
MYFATOORAH_BASE_URL = os.getenv("MYFATOORAH_BASE_URL", "")
_MYFATOORAH_PAYMENT_METHOD_ID_RAW = os.getenv("MYFATOORAH_PAYMENT_METHOD_ID", "").strip()
MYFATOORAH_PAYMENT_METHOD_ID = (
    int(_MYFATOORAH_PAYMENT_METHOD_ID_RAW)
    if _MYFATOORAH_PAYMENT_METHOD_ID_RAW
    else None
)
MYFATOORAH_CALLBACK_URL = os.getenv(
    "MYFATOORAH_CALLBACK_URL",
    f"{BACKEND_BASE_URL}/api/payments/myfatoorah/callback/",
)
MYFATOORAH_HOSTED_REDIRECTION_URL = os.getenv(
    "MYFATOORAH_HOSTED_REDIRECTION_URL",
    MYFATOORAH_CALLBACK_URL,
)
MYFATOORAH_ERROR_URL = os.getenv(
    "MYFATOORAH_ERROR_URL",
    f"{BACKEND_BASE_URL}/api/payments/myfatoorah/error/",
)
MYFATOORAH_REQUEST_TIMEOUT_SECONDS = int(os.getenv("MYFATOORAH_REQUEST_TIMEOUT_SECONDS", "10"))

EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp").strip().lower()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_API_URL = os.getenv("RESEND_API_URL", "https://api.resend.com/emails")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@physician-consult.local")

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() == "true"

REDIS_URL = os.environ.get("REDIS_URL")

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL or "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL or "redis://localhost:6379/0")

if not CELERY_BROKER_URL:
    raise RuntimeError("CELERY_BROKER_URL or REDIS_URL is not set")


CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Windows does not reliably support Celery's prefork worker pool.
# Use solo pool by default on Windows to avoid billiard permission errors.
if os.name == "nt":
    CELERY_WORKER_POOL = "solo"
    CELERY_WORKER_CONCURRENCY = 1

CELERY_BEAT_SCHEDULE = {
    "expire-unpaid-bookings-every-5-minutes": {
        "task": "bookings.tasks.expire_unpaid_bookings_task",
        "schedule": timedelta(minutes=5),
    },
    "mark-past-bookings-completed-every-10-minutes": {
        "task": "bookings.tasks.mark_past_bookings_ready_for_completion_task",
        "schedule": timedelta(minutes=10),
    },
    "send-24h-reminders-every-15-minutes": {
        "task": "notifications.tasks.send_24h_consultation_reminders_task",
        "schedule": timedelta(minutes=15),
    },
    "send-1h-reminders-every-5-minutes": {
        "task": "notifications.tasks.send_1h_consultation_reminders_task",
        "schedule": timedelta(minutes=5),
    },
}


print("SETTINGS CELERY_BROKER_URL repr:", repr(CELERY_BROKER_URL))
print("SETTINGS CELERY_RESULT_BACKEND repr:", repr(CELERY_RESULT_BACKEND))
print("SETTINGS REDIS_URL repr:", repr(REDIS_URL))