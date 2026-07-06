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

# Ritmo de "digitação" da DEMO/vídeo: a resposta espera um tempo proporcional
# ao seu tamanho, mantendo o indicador "digitando…" visível — parece uma conversa
# real. Ligado por padrão; DEMO_DELAY=0 desliga (testes/CI ou resposta instantânea).
DEMO_DELAY = os.environ.get("DEMO_DELAY", "1") != "0"
DEMO_DELAY_BASE_MS = 250       # piso: toda resposta "pensa" um instante
DEMO_DELAY_PER_CHAR_MS = 8     # quanto mais texto, mais tempo "digitando"
DEMO_DELAY_CAP_MS = 1200       # teto: espera nunca cansa
