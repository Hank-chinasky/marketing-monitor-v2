import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ["DJANGO_ALLOWED_HOSTS"].split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ["DJANGO_CSRF_TRUSTED_ORIGINS"].split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

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

ROOT_URLCONF = "marketing_monitor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "marketing_monitor.wsgi.application"
ASGI_APPLICATION = "marketing_monitor.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("SQLITE_PATH", str(BASE_DIR / "data" / "db.sqlite3")),
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "nl"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "operations-dashboard"
LOGOUT_REDIRECT_URL = "login"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "True").lower() == "true"
SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SESSION_COOKIE_SECURE", "True").lower() == "true"
CSRF_COOKIE_SECURE = os.environ.get("DJANGO_CSRF_COOKIE_SECURE", "True").lower() == "true"
SESSION_COOKIE_HTTPONLY = True

SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"