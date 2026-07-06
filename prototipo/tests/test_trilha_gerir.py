import pytest
from decimal import Decimal
from core.tipos import Sessao
from core.motor import Motor
from core.ledger import Ledger
from core.trilha_gerir import ESTADOS_GERIR, construir_handlers_gerir


def _motor_e_ledger():
    ledger = Ledger()
    m = Motor(estados=ESTADOS_GERIR, handlers=construir_handlers_gerir(ledger))
    return m, ledger


def test_fluxo_venda_so_grava_apos_confirmar():
    m, ledger = _motor_e_ledger()
    s = Sessao(id="s", estado="ger_menu")
    m.processar(s, "1")               # escolhe "Registrar venda"
    m.processar(s, "300")             # digita o valor
    assert ledger.saldo() == Decimal("0")   # INVARIANTE: nada gravado ainda
    r = m.processar(s, "confirmar")   # confirma
    assert ledger.saldo() == Decimal("300")
    assert any("Firmô ✅" in msg.texto for msg in r.mensagens)


def test_corrigir_volta_a_pedir_valor_sem_gravar():
    m, ledger = _motor_e_ledger()
    s = Sessao(id="s", estado="ger_menu")
    m.processar(s, "1")
    m.processar(s, "300")
    m.processar(s, "corrigir")
    assert ledger.saldo() == Decimal("0")
    assert s.estado == "ger_venda_valor"   # voltou a pedir


def test_ver_saldo_reflete_ledger():
    m, ledger = _motor_e_ledger()
    ledger.registrar("venda", Decimal("500"))
    s = Sessao(id="s", estado="ger_menu")
    r = m.processar(s, "ver saldo")
    assert any("500,00" in msg.texto for msg in r.mensagens)


def test_retrato_mostra_entradas_saidas_saldo():
    m, ledger = _motor_e_ledger()
    ledger.registrar("venda", Decimal("500"))
    ledger.registrar("despesa", Decimal("120"))
    s = Sessao(id="s", estado="ger_menu")
    r = m.processar(s, "ver meu retrato")
    texto = " ".join(msg.texto for msg in r.mensagens)
    assert "500,00" in texto and "120,00" in texto and "380,00" in texto
    assert r.mensagens[-1].opcoes                # tem saída (↩ Voltar), não é beco


def test_negar_confirmacao_nao_grava():
    # review Codex: "não tá certo" não pode ser lido como Confirmar
    m, ledger = _motor_e_ledger()
    s = Sessao(id="s", estado="ger_menu")
    m.processar(s, "1")
    m.processar(s, "300")
    m.processar(s, "não tá certo")
    assert ledger.saldo() == Decimal("0")
    assert s.estado == "ger_venda_valor"   # tratado como correção


def test_nao_confirmar_reapresenta_sem_gravar():
    # review Codex: "não confirmar" casa termos de OK e de CORRIGE ao mesmo
    # tempo — o motor não pode escolher o OK por ordem; reapresenta sem gravar
    m, ledger = _motor_e_ledger()
    s = Sessao(id="s", estado="ger_menu")
    m.processar(s, "1")
    m.processar(s, "300")
    m.processar(s, "não confirmar")
    assert ledger.saldo() == Decimal("0")
    assert s.estado == "ger_venda_confirma"     # continua confirmando


def test_valor_sub_centavo_reprompt_sem_crashar():
    # review Codex: 0,004 arredonda p/ 0,00 — deve reperguntar, não crashar
    m, ledger = _motor_e_ledger()
    s = Sessao(id="s", estado="ger_menu")
    m.processar(s, "1")
    r = m.processar(s, "0,004")
    assert "valor" not in s.slots
    assert s.estado == "ger_venda_valor"
    assert "não entendi o valor" in r.mensagens[0].texto.lower()
    assert ledger.saldo() == Decimal("0")


def test_confirmar_venda_nao_regrava_em_refresh():
    # a invariante do motor (acao 1x) vale de ponta a ponta na trilha real
    m, ledger = _motor_e_ledger()
    s = Sessao(id="s", estado="ger_menu")
    m.processar(s, "1")
    m.processar(s, "300")
    m.processar(s, "confirmar")
    m.processar(s, None)              # refresh
    m.processar(s, None)
    assert ledger.saldo() == Decimal("300")


# ============================================================================
# Orientação em gestão básica + controle de fluxo de caixa (edital §3.1.1):
# afordâncias VISÍVEIS no WhatsApp para extrato consolidado e para as dicas
# curadas dos quatro fundamentos (fluxo de caixa, precificação, margem, giro).
# ============================================================================

def test_menu_gerir_expoe_extrato_e_dicas():
    # o edital §3.1.1 nomeia "orientação" e "controle de fluxo de caixa";
    # ambos precisam estar visíveis no menu (viram botões no WhatsApp)
    destinos = {op.destino for op in ESTADOS_GERIR["ger_menu"].opcoes}
    assert "ger_extrato" in destinos
    assert "ger_dicas_menu" in destinos


def test_extrato_lista_lancamentos_e_totais():
    m, ledger = _motor_e_ledger()
    ledger.registrar("venda", Decimal("500"))
    ledger.registrar("despesa", Decimal("120"))
    s = Sessao(id="s", estado="ger_menu")
    r = m.processar(s, "extrato")
    texto = " ".join(msg.texto for msg in r.mensagens)
    assert "500,00" in texto and "120,00" in texto   # os lançamentos aparecem
    assert "380,00" in texto                          # saldo consolidado
    assert r.mensagens[-1].opcoes                      # tem Voltar, não é beco


def test_extrato_vazio_responde_amigavel_sem_crashar():
    m, ledger = _motor_e_ledger()
    s = Sessao(id="s", estado="ger_menu")
    r = m.processar(s, "extrato")                      # ledger vazio
    assert s.estado == "ger_extrato"                   # chegou no extrato (não no fallback)
    assert r.mensagens and r.mensagens[0].texto.strip()
    assert r.mensagens[-1].opcoes                      # tem saída


def test_dicas_menu_cobre_os_quatro_fundamentos():
    # a §4.2 da proposta afirma os "quatro fundamentos"; o protótipo tem de
    # demonstrá-los, não só afirmá-los
    destinos = {op.destino for op in ESTADOS_GERIR["ger_dicas_menu"].opcoes}
    assert {"ger_dica_fluxo", "ger_dica_preco",
            "ger_dica_margem", "ger_dica_giro"} <= destinos


@pytest.mark.parametrize("palavra,estado_dica", [
    ("fluxo", "ger_dica_fluxo"),
    ("precificação", "ger_dica_preco"),
    ("margem", "ger_dica_margem"),
    ("giro", "ger_dica_giro"),
])
def test_cada_dica_orienta_e_tem_voltar(palavra, estado_dica):
    m, ledger = _motor_e_ledger()
    s = Sessao(id="s", estado="ger_dicas_menu")
    r = m.processar(s, palavra)
    assert s.estado == estado_dica                     # navegou pro tópico
    assert any(len(msg.texto.strip()) > 20 for msg in r.mensagens)  # conteúdo curado
    assert r.mensagens[-1].opcoes                        # Voltar (não é beco)
