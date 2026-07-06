from decimal import Decimal
import pytest
from core.ledger import Ledger, Lancamento


def test_registrar_venda_e_despesa_afeta_saldo():
    L = Ledger()
    L.registrar("venda", Decimal("300"))
    L.registrar("despesa", Decimal("50"))
    assert L.saldo() == Decimal("250")


def test_lancamento_e_imutavel():
    lanc = Lancamento(id=1, tipo="venda", valor=Decimal("10"))
    with pytest.raises(Exception):  # FrozenInstanceError
        lanc.valor = Decimal("999")


def test_estorno_reverte_efeito_do_original_sem_apagar():
    L = Ledger()
    v = L.registrar("venda", Decimal("300"))
    L.estornar(v.id)
    assert L.saldo() == Decimal("0")
    # append-only: os dois lançamentos continuam no histórico
    assert len(L.lancamentos()) == 2
    assert L.lancamentos()[1].tipo == "estorno"
    assert L.lancamentos()[1].ref == v.id


def test_estornar_id_inexistente_levanta():
    L = Ledger()
    with pytest.raises(ValueError):
        L.estornar(999)


def test_registrar_valor_nao_positivo_levanta():
    # review Codex: valor negativo/zero viola a invariante de magnitude
    L = Ledger()
    with pytest.raises(ValueError):
        L.registrar("venda", Decimal("-50"))
    with pytest.raises(ValueError):
        L.registrar("despesa", Decimal("0"))


def test_retrato_totaliza_e_bate_com_saldo():
    led = Ledger()
    led.registrar("venda", Decimal("300"))
    led.registrar("despesa", Decimal("80"))
    extra = led.registrar("venda", Decimal("100"))
    led.estornar(extra.id)                      # estorno abate a venda
    r = led.retrato()
    assert r["entradas"] == Decimal("300")
    assert r["saidas"] == Decimal("80")
    assert r["saldo"] == led.saldo() == Decimal("220")
    assert r["n_lancamentos"] == 4              # estorno também é registro


def test_retrato_vazio_zera_tudo():
    r = Ledger().retrato()
    assert r == {"entradas": Decimal("0"), "saidas": Decimal("0"),
                 "saldo": Decimal("0"), "n_lancamentos": 0}


def test_nao_permite_estorno_duplicado():
    # review Codex: estorno duplicado reverteria o efeito em dobro
    L = Ledger()
    v = L.registrar("venda", Decimal("300"))
    L.estornar(v.id)
    with pytest.raises(ValueError):
        L.estornar(v.id)
    assert L.saldo() == Decimal("0")
