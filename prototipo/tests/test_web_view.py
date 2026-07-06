"""Testes do adaptador web. O pytest-django configura o Django via pytest.ini
(DJANGO_SETTINGS_MODULE=config.settings). O fixture `client` é o test client.
"""
import pytest

pytestmark = pytest.mark.django_db


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
