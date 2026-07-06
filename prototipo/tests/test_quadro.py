import pytest
from core.quadro import QuadroInteresses


def test_registrar_e_append_only():
    q = QuadroInteresses()
    i = q.registrar("lojista-1", "Embalagens", 50)
    assert (i.id, i.sessao_id, i.produto, i.quantidade) == (1, "lojista-1", "Embalagens", 50)
    assert len(q.interesses()) == 1


def test_agregado_conta_feirantes_distintos_e_soma_unidades():
    q = QuadroInteresses()
    q.registrar("a", "Embalagens", 50)
    q.registrar("b", "Embalagens", 100)
    q.registrar("a", "Embalagens", 30)      # mesmo feirante de novo: soma, não conta 2x
    q.registrar("c", "Sacolas", 200)
    assert q.agregado() == [("Embalagens", 2, 180), ("Sacolas", 1, 200)]


def test_agregado_ordena_por_feirantes_desc():
    q = QuadroInteresses()
    q.registrar("a", "Sacolas", 10)
    q.registrar("b", "Embalagens", 10)
    q.registrar("c", "Embalagens", 10)
    assert [linha[0] for linha in q.agregado()] == ["Embalagens", "Sacolas"]


@pytest.mark.parametrize("qtd", [0, -5, 1.5, float("nan")])
def test_quantidade_invalida_rejeitada(qtd):
    with pytest.raises(ValueError):
        QuadroInteresses().registrar("a", "Embalagens", qtd)


def test_agregado_desempata_por_nome():
    q = QuadroInteresses()
    q.registrar("a", "Sacolas", 10)         # inserida primeiro…
    q.registrar("b", "Embalagens", 10)      # …mas Embalagens vem antes no nome
    assert [linha[0] for linha in q.agregado()] == ["Embalagens", "Sacolas"]


def test_produto_fora_da_lista_rejeitado():
    # fail-secure: o quadro valida na ESCRITA, não confia só na trilha
    with pytest.raises(ValueError):
        QuadroInteresses().registrar("a", "farinha", 10)
