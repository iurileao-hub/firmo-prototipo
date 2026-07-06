import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# core/ é irmão de web/ — adiciona o pai ao path para importar `core`
sys.path.insert(0, str(BASE_DIR.parent))

SECRET_KEY = "proto-inseguro-nao-usar-em-prod"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "chat",
]
# CSRF omitido de propósito: protótipo local sem autenticação. Na Aceleração,
# o webhook do WhatsApp substitui estas views e a segurança é do canal Meta.
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "APP_DIRS": True, "DIRS": [], "OPTIONS": {},
}]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3",
                         "NAME": BASE_DIR / "db.sqlite3"}}
STATIC_URL = "static/"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Delay artificial da resposta (ms) para a DEMO/vídeo parecer uma conversa
# real e o indicador "digitando…" ficar visível. 0 = desligado (testes/CI).
DEMO_DELAY_MS = int(os.environ.get("DEMO_DELAY_MS", "0"))
