from core.tipos import Sessao
from core.motor import Motor
from core.quadro import QuadroInteresses
from core.trilha_comprar import ESTADOS_COMPRAR, construir_handlers_comprar


def _motor_e_quadro():
    quadro = QuadroInteresses()
    m = Motor(estados=ESTADOS_COMPRAR, handlers=construir_handlers_comprar(quadro))
    return m, quadro


def _ate_confirmacao(m, s):
    m.processar(s, "quero participar")
    m.processar(s, "Embalagens")        # botão posta o rótulo; captura interpreta
    m.processar(s, "50")


def test_interesse_so_grava_apos_confirmar():
    m, quadro = _motor_e_quadro()
    s = Sessao(id="lojista-1", estado="cj_menu")
    _ate_confirmacao(m, s)
    assert quadro.interesses() == ()            # INVARIANTE: nada antes do Confirmar
    r = m.processar(s, "confirmar")
    i, = quadro.interesses()
    assert (i.sessao_id, i.produto, i.quantidade) == ("lojista-1", "Embalagens", 50)
    assert any("Firmô ✅" in msg.texto for msg in r.mensagens)
    assert s.estado == "cj_menu"                # voltou ao repouso


def test_corrigir_volta_a_pedir_quantidade_sem_gravar():
    m, quadro = _motor_e_quadro()
    s = Sessao(id="lojista-1", estado="cj_menu")
    _ate_confirmacao(m, s)
    m.processar(s, "corrigir")
    assert quadro.interesses() == ()
    assert s.estado == "cj_qtd"


def test_negar_confirmacao_nao_grava():
    m, quadro = _motor_e_quadro()
    s = Sessao(id="lojista-1", estado="cj_menu")
    _ate_confirmacao(m, s)
    m.processar(s, "não tá certo")
    assert quadro.interesses() == ()
    assert s.estado == "cj_qtd"


def test_nao_confirmar_reapresenta_sem_gravar():
    # review Codex: entrada ambígua (casa OK e CORRIGE) não pode gravar
    m, quadro = _motor_e_quadro()
    s = Sessao(id="lojista-1", estado="cj_menu")
    _ate_confirmacao(m, s)
    m.processar(s, "não confirmar")
    assert quadro.interesses() == ()
    assert s.estado == "cj_confirma"            # reapresentou, não decidiu


def test_refresh_nao_regrava_interesse():
    m, quadro = _motor_e_quadro()
    s = Sessao(id="lojista-1", estado="cj_menu")
    _ate_confirmacao(m, s)
    m.processar(s, "confirmar")
    m.processar(s, None)                        # refresh
    m.processar(s, None)
    assert len(quadro.interesses()) == 1


def test_quadro_reflete_gravacao_e_tem_saida():
    m, quadro = _motor_e_quadro()
    quadro.registrar("outro-lojista", "Sacolas", 200)
    s = Sessao(id="lojista-1", estado="cj_menu")
    _ate_confirmacao(m, s)
    m.processar(s, "confirmar")
    r = m.processar(s, "ver quadro")
    texto = " ".join(msg.texto for msg in r.mensagens)
    assert "Embalagens" in texto and "50" in texto
    assert "Sacolas" in texto and "200" in texto
    assert r.mensagens[-1].opcoes                # não é beco: dá pra participar/voltar


def test_fala_livre_quero_ver_o_quadro_roteia():
    # review Codex (3ª rodada): "quero" não pode ser palavra de roteamento —
    # "quero ver o quadro" tem que chegar no quadro, não virar ambiguidade
    m, _ = _motor_e_quadro()
    s = Sessao(id="lojista-1", estado="cj_menu")
    r = m.processar(s, "quero ver o quadro da feira")
    assert s.estado == "cj_quadro"
    assert any("vazio" in msg.texto.lower() for msg in r.mensagens)


def test_quadro_vazio_convida():
    m, _ = _motor_e_quadro()
    s = Sessao(id="lojista-1", estado="cj_menu")
    r = m.processar(s, "ver quadro")
    assert any("vazio" in msg.texto.lower() for msg in r.mensagens)
