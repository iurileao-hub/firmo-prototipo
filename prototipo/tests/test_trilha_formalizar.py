from core.tipos import Sessao
from core.motor import Motor
from core.trilha_formalizar import ESTADOS_FORMALIZAR, HANDLERS_FORMALIZAR


def _motor():
    return Motor(estados=ESTADOS_FORMALIZAR, handlers=HANDLERS_FORMALIZAR)


def test_intro_oferece_situacoes():
    r = _motor().processar(Sessao(id="s", estado="form_intro"), None)
    ids = [o.id for o in r.mensagens[-1].opcoes]
    assert "form_nao_tem" in ids and "form_ja_tem" in ids


def test_quem_nao_tem_recebe_beneficios_antes_dos_passos():
    m = _motor()
    s = Sessao(id="s", estado="form_intro")
    # escolhe "ainda não tenho CNPJ"
    r = m.processar(s, "ainda não")
    texto_beneficios = " ".join(msg.texto for msg in r.mensagens)
    assert "Bolsa Família" in texto_beneficios
    assert "CRAS" in texto_beneficios  # orientação conservadora: encaminhar
    # avança para os passos só depois
    r2 = m.processar(s, "1")
    assert any("Portal do Empreendedor" in msg.texto for msg in r2.mensagens)


def test_quem_ja_tem_vai_para_beneficios_pj():
    m = _motor()
    s = Sessao(id="s", estado="form_intro")
    r = m.processar(s, "já tenho")
    assert any("grupos de compra" in msg.texto for msg in r.mensagens)
