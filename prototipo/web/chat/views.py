"""Adaptador web: a única lógica é traduzir HTTP <-> motor. Sem regra de negócio.

Estado de sessão em memória de processo — PROTOTYPE-ONLY. Na Aceleração isto
vira SessaoConversa + Ledger persistidos (models Django), e o webhook do
WhatsApp substitui estas views sem tocar no core.
"""
import time

from django.conf import settings
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.app import montar_motor, nova_sessao
from core.ledger import Ledger

from chat.demo import quadro_demo

_SESSOES: dict = {}  # session_key -> (Sessao, Ledger, Motor)
_QUADRO = quadro_demo()  # coletivo: um quadro por processo, compartilhado entre sessões


def _obter(request):
    if not request.session.session_key:
        request.session.create()
    chave = request.session.session_key
    if chave not in _SESSOES:
        ledger = Ledger()
        _SESSOES[chave] = (nova_sessao(chave), ledger, montar_motor(ledger, _QUADRO))
    return _SESSOES[chave]


def index(request):
    sessao, _, motor = _obter(request)
    resp = motor.processar(sessao, None)  # display-only: nunca dispara efeito
    return render(request, "chat/index.html", {"mensagens": resp.mensagens})


def _demora_ms(n_chars: int) -> int:
    """Ritmo de digitação da demo: base + por-caractere, com teto (ms).
    DEMO_DELAY desligado => 0 (instantâneo, p/ testes/CI)."""
    if not settings.DEMO_DELAY:
        return 0
    return min(settings.DEMO_DELAY_BASE_MS + settings.DEMO_DELAY_PER_CHAR_MS * n_chars,
               settings.DEMO_DELAY_CAP_MS)


@require_POST
def enviar(request):
    sessao, _, motor = _obter(request)
    texto = request.POST.get("texto", "")
    resp = motor.processar(sessao, texto)
    # espera proporcional ao tamanho da resposta => "digitando…" fica visível
    if (ms := _demora_ms(sum(len(m.texto) for m in resp.mensagens))):
        time.sleep(ms / 1000)
    return render(request, "chat/_baloes.html",
                  {"mensagens": resp.mensagens, "eco": texto})


@require_POST
def reiniciar(request):
    """Zera a conversa (útil na demo/vídeo). Descarta a sessão em memória."""
    if request.session.session_key:
        _SESSOES.pop(request.session.session_key, None)
    return redirect("index")
