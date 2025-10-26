from .settings import *  # noqa
import os, shutil

DB_SRC = os.environ.get("TALENTO_TEST_DB_SRC")
DB_PATH = os.environ.get("TALENTO_TEST_DB_PATH", os.path.join(BASE_DIR, "test.sqlite3"))

if DB_SRC and os.path.exists(DB_SRC) and not os.path.exists(DB_PATH):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    shutil.copy(DB_SRC, DB_PATH)

DATABASES["default"]["NAME"] = DB_PATH

PANEL_ORIENTADOR_TOKEN = os.environ.get("PANEL_ORIENTADOR_TOKEN", "mi-token-local")

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

DATABASES["default"]["TEST"] = {"NAME": DATABASES["default"]["NAME"]}

MIGRATION_MODULES = {"runtime": None}
