from core.tipos import Opcao
from core.interpreter import InputInterpreter

OPCOES = (
    Opcao(id="formalizar", rotulo="Abrir minha firma", destino="f1",
          palavras=("cnpj", "mei", "formalizar", "abrir firma")),
    Opcao(id="gerir", rotulo="Cuidar das contas", destino="g1",
          palavras=("conta", "venda", "despesa", "caixa")),
)


def test_casa_por_numero():
    assert InputInterpreter().interpretar("1", OPCOES).id == "formalizar"
    assert InputInterpreter().interpretar("2", OPCOES).id == "gerir"


def test_casa_por_palavra_chave_com_acento_e_caixa():
    assert InputInterpreter().interpretar("Quero abrir o CNPJ", OPCOES).id == "formalizar"
    assert InputInterpreter().interpretar("ver minha VENDA", OPCOES).id == "gerir"


def test_casa_por_rotulo():
    assert InputInterpreter().interpretar("cuidar das contas", OPCOES).id == "gerir"


def test_nao_casa_retorna_none():
    assert InputInterpreter().interpretar("bom dia tudo bem?", OPCOES) is None


def test_numero_fora_do_intervalo_retorna_none():
    assert InputInterpreter().interpretar("9", OPCOES) is None


def test_termo_mais_especifico_vence_o_generico():
    # review Codex (2ª rodada): "não tenho" casa 'nao tenho' (form_nao_tem) e
    # 'tenho' (form_ja_tem). 'tenho' é substring de 'nao tenho' — o termo mais
    # específico vence; não é ambiguidade real.
    ops = (
        Opcao(id="nao_tem", rotulo="Ainda não tenho CNPJ", destino="b",
              palavras=("nao", "ainda nao", "nao tenho")),
        Opcao(id="ja_tem", rotulo="Já tenho CNPJ", destino="p",
              palavras=("ja tenho", "tenho", "sim", "ja sou")),
    )
    assert InputInterpreter().interpretar("não tenho", ops).id == "nao_tem"
    assert InputInterpreter().interpretar("ainda não tenho CNPJ", ops).id == "nao_tem"


def test_entrada_ambigua_retorna_none():
    # review Codex: "não confirmar" casa termos de DUAS opções (confirmar/nao).
    # Na dúvida o interpreter não decide — devolve None e o motor reapresenta.
    ops = (
        Opcao(id="ok", rotulo="✅ Confirmar", destino="x", palavras=("confirmar", "sim")),
        Opcao(id="corrige", rotulo="✏️ Corrigir", destino="y", palavras=("corrigir", "nao")),
    )
    assert InputInterpreter().interpretar("não confirmar", ops) is None


def test_nao_casa_palavra_curta_dentro_de_outra_palavra():
    # regressão (review Codex): 'mei' está dentro de 'primeiro' — não pode
    # roubar o roteamento; 'cuidar das contas' (rótulo) deve vencer.
    assert (
        InputInterpreter().interpretar("primeiro quero cuidar das contas", OPCOES).id
        == "gerir"
    )
