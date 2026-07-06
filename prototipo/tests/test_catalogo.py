import pytest
from core import catalogo


def test_render_retorna_texto_simples():
    assert catalogo.render("saudacao").startswith("Oi! Eu sou o Firmô")


def test_render_interpola_valores():
    texto = catalogo.render("gerir_confirmar_venda", valor="300,00")
    assert "R$ 300,00" in texto


def test_chave_ausente_levanta_keyerror():
    with pytest.raises(KeyError):
        catalogo.render("chave_que_nao_existe")
