"""Testes do adaptador web. O pytest-django configura o Django via pytest.ini
(DJANGO_SETTINGS_MODULE=config.settings). O fixture `client` é o test client.
"""
import pytest

from chat.views import _demora_ms

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _delay_off(settings):
    """Demo liga o delay por padrão; nos testes web mantemos instantâneo.
    Testes que exercitam o próprio delay re-ligam com settings.DEMO_DELAY = True."""
    settings.DEMO_DELAY = False


# --- ritmo de "digitação" proporcional ao tamanho da resposta (demo/vídeo) ---

def test_demora_desligada_e_instantanea(settings):
    settings.DEMO_DELAY = False
    assert _demora_ms(500) == 0


def test_demora_curta_usa_base_mais_por_char(settings):
    settings.DEMO_DELAY = True
    settings.DEMO_DELAY_BASE_MS = 250
    settings.DEMO_DELAY_PER_CHAR_MS = 8
    settings.DEMO_DELAY_CAP_MS = 1200
    assert _demora_ms(10) == 250 + 8 * 10


def test_demora_longa_bate_no_teto(settings):
    settings.DEMO_DELAY = True
    settings.DEMO_DELAY_BASE_MS = 250
    settings.DEMO_DELAY_PER_CHAR_MS = 8
    settings.DEMO_DELAY_CAP_MS = 1200
    assert _demora_ms(10_000) == 1200


def test_demora_cresce_com_o_tamanho(settings):
    settings.DEMO_DELAY = True
    assert _demora_ms(200) >= _demora_ms(20)


def test_enviar_aplica_a_demora(client, settings, monkeypatch):
    settings.DEMO_DELAY = True
    dormidas = []
    monkeypatch.setattr("chat.views.time.sleep", lambda s: dormidas.append(s))
    client.get("/")
    client.post("/enviar/", {"texto": "cuidar das contas"})
    assert dormidas and dormidas[-1] > 0     # dormiu proporcional à resposta


def test_index_responde_com_saudacao(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Firmô".encode() in resp.content


def test_enviar_venda_confirmada_grava(client):
    client.get("/")                                    # inicia a sessão
    client.post("/enviar/", {"texto": "cuidar das contas"})
    client.post("/enviar/", {"texto": "1"})            # registrar venda
    client.post("/enviar/", {"texto": "300"})          # valor
    resp = client.post("/enviar/", {"texto": "confirmar"})
    assert "Firmô ✅".encode() in resp.content


def test_quadro_da_feira_mostra_seed_de_demo(client):
    client.get("/")
    client.post("/enviar/", {"texto": "comprar junto"})
    resp = client.post("/enviar/", {"texto": "ver quadro"})
    assert "Embalagens".encode() in resp.content
    assert "feirante".encode() in resp.content


def test_reiniciar_volta_para_saudacao(client):
    client.get("/")
    client.post("/enviar/", {"texto": "cuidar das contas"})
    resp = client.post("/reiniciar/", follow=True)     # zera a conversa
    assert resp.status_code == 200
    assert "O que você quer fazer".encode() in resp.content
