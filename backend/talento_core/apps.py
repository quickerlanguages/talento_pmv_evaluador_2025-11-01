# Shim para mantener el nombre convencional de Django
# Reexporta el AppConfig definido en core_apps.py
from .core_apps import *  # noqa: F401,F403
