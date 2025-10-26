# talento_backend_v2/settings.py
from pathlib import Path
import os

# ===============================
# 🔧 Carga de variables (.env)
# ===============================
BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    # Si no está instalado, seguimos con variables del entorno del proceso
    pass

def env_list(key: str, default: str = ""):
    return [x.strip() for x in os.getenv(key, default).split(",") if x.strip()]

# ===============================
# ⚙️ Core
# ===============================
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-unsafe-change-me")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")

# Host/puerto de desarrollo (no los usa Django internamente,
# pero son útiles para run.sh / documentación)
BIND_HOST = os.getenv("BIND_HOST", "127.0.0.1")
BIND_PORT = int(os.getenv("BIND_PORT", "8001"))
API_HOST  = os.getenv("API_HOST", f"http://{BIND_HOST}:{BIND_PORT}")

# Token para el Panel Orientador
PANEL_ORIENTADOR_TOKEN = os.getenv("PANEL_ORIENTADOR_TOKEN", "")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Raíz de artefactos (staticfiles/media) si quieres moverlos fuera del proyecto
TALENTO_CCP_ROOT = Path(os.getenv("TALENTO_CCP_ROOT", str(BASE_DIR)))

# ===============================
# 🗄️ Base de datos
# ===============================
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()

if DB_ENGINE == "sqlite":
    # Ruta relativa al BASE_DIR por defecto
    DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "talento_READY_2025-09-14.db"))
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": DB_PATH,
        }
    }
elif DB_ENGINE == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "talento"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
else:
    # Fallback mínimo a SQLite si el valor no es válido
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "talento_READY_2025-09-14.db"),
        }
    }

# ===============================
# 🧩 Apps / Middleware / WSGI
# ===============================
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Proyecto
    "talento_core",
    "ccp_vpm",
    "runtime",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "talento_backend_v2.urls"
WSGI_APPLICATION = "talento_backend_v2.wsgi.application"

# ===============================
# 🖼️ Templates
# ===============================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # templates/ a nivel de proyecto
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ===============================
# 🔐 Password Validators
# ===============================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ===============================
# 🌍 I18N / TZ
# ===============================
LANGUAGE_CODE = "es-es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ===============================
# 📦 Static & Media
# ===============================
STATIC_URL = "static/"
STATICFILES_DIRS = []
_proj_static = BASE_DIR / "static"
if _proj_static.exists():
    STATICFILES_DIRS.append(_proj_static)

STATIC_ROOT = TALENTO_CCP_ROOT / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = TALENTO_CCP_ROOT / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===============================
# 🛡️ CSRF / CORS (mínimo)
# ===============================
# Si defines CSRF_TRUSTED_ORIGINS en .env, se usa tal cual; si no, damos un default razonable
_env_csrf = env_list("CSRF_TRUSTED_ORIGINS", f"http://{BIND_HOST}:{BIND_PORT},http://localhost:{BIND_PORT}")
CSRF_TRUSTED_ORIGINS = _env_csrf
CSRF_COOKIE_SECURE = False  # dev (http)
SESSION_COOKIE_SECURE = False

# (Opcional) CORS si instalas django-cors-headers
# CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "")

# ===============================
# 📝 LOGGING
# ===============================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}

# Solo permitir token por cabecera fuera de DEBUG
PANEL_ALLOW_QUERYTOKEN = os.getenv("PANEL_ALLOW_QUERYTOKEN", "1" if DEBUG else "0") == "1"

