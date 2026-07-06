import pytest
from core.tipos import Estado, Opcao, Captura, Mensagem, Sessao
from core.motor import Motor

# --- máquina de estados mínima só para testar o Motor ---
# 'confirma' usa render (puro, mostra o valor); 'gravou' usa acao (efeito, redireciona).
ESTADOS = {
    "inicio": Estado(
        id="inicio",
        mensagens=("menu_raiz",),
        opcoes=(
            Opcao(id="ir_a", rotulo="Opção A", destino="a", palavras=("a",)),
            Opcao(id="captar", rotulo="Registrar valor", destino="pede_valor"),
        ),
    ),
    "a": Estado(id="a", mensagens=("menu_raiz",)),
    "pede_valor": Estado(
        id="pede_valor",
        mensagens=("gerir_pede_valor_venda",),
        captura=Captura(slot="valor", tipo="valor", destino="confirma",
                        erro_chave="gerir_valor_invalido"),
    ),
    "confirma": Estado(
        id="confirma",
        render="mostra_valor",
        opcoes=(
            Opcao(id="ok", rotulo="Confirmar", destino="gravou", palavras=("confirmar", "sim")),
            Opcao(id="corrige", rotulo="Corrigir", destino="pede_valor", palavras=("corrigir",)),
        ),
    ),
    "gravou": Estado(id="gravou", acao="grava"),
}


def _motor():
    """Motor com um contador de efeitos, para verificar idempotência."""
    contador = {"gravou": 0}

    def grava(sessao):
        contador["gravou"] += 1
        sessao.estado = "a"  # efeito roda 1x e redireciona para estado de repouso
        return [Mensagem(texto="gravei")]

    def mostra_valor(sessao):
        return [Mensagem(texto=f"confirmar {sessao.slots['valor']}")]

    m = Motor(estados=ESTADOS, handlers={"grava": grava, "mostra_valor": mostra_valor})
    return m, contador


def test_entrada_none_emite_estado_atual():
    m, _ = _motor()
    r = m.processar(Sessao(id="s1"), None)
    assert r.sessao.estado == "inicio"
    assert "O que você quer fazer" in r.mensagens[0].texto
    assert r.mensagens[0].opcoes[0].id == "ir_a"


def test_opcao_valida_transiciona():
    m, _ = _motor()
    r = m.processar(Sessao(id="s1", estado="inicio"), "1")
    assert r.sessao.estado == "a"


def test_entrada_nao_reconhecida_reapresenta_menu():
    m, _ = _motor()
    r = m.processar(Sessao(id="s1", estado="inicio"), "blá blá")
    assert r.sessao.estado == "inicio"          # não saiu do lugar
    assert "não entendi" in r.mensagens[0].texto.lower()
    assert r.mensagens[-1].opcoes                # remostrou as opções


def test_captura_valor_valido_avanca_e_mostra_via_render():
    m, _ = _motor()
    s = Sessao(id="s1", estado="pede_valor")
    r = m.processar(s, "300")
    assert s.slots["valor"] == "300,00"          # normalizado para exibição BR
    assert s.estado == "confirma"
    assert "confirmar 300,00" in r.mensagens[-1].texto


def test_captura_valor_invalido_reapresenta():
    m, _ = _motor()
    s = Sessao(id="s1", estado="pede_valor")
    r = m.processar(s, "abc")
    assert s.estado == "pede_valor"              # continua pedindo
    assert "não entendi o valor" in r.mensagens[0].texto.lower()


# --- capturas estruturadas "quantidade" e "produto" (trilha Comprar Junto) ---

ESTADOS_CAPTURAS = {
    "pede_qtd": Estado(
        id="pede_qtd", mensagens=("menu_raiz",),
        captura=Captura(slot="quantidade", tipo="quantidade", destino="fim",
                        erro_chave="comprar_qtd_invalida"),
    ),
    "pede_produto": Estado(
        id="pede_produto", mensagens=("menu_raiz",),
        captura=Captura(slot="produto", tipo="produto", destino="fim",
                        erro_chave="comprar_produto_invalido"),
    ),
    "fim": Estado(id="fim", mensagens=("menu_raiz",)),
}


@pytest.mark.parametrize("entrada,esperado", [("50", "50"), (" 10 ", "10"), ("007", "7")])
def test_captura_quantidade_valida(entrada, esperado):
    m = Motor(estados=ESTADOS_CAPTURAS)
    s = Sessao(id="s1", estado="pede_qtd")
    m.processar(s, entrada)
    assert s.slots["quantidade"] == esperado
    assert s.estado == "fim"


@pytest.mark.parametrize("ruim", ["0", "-3", "3,5", "abc", "", "1e3", "²", "①"])
def test_captura_quantidade_invalida_reapresenta(ruim):
    m = Motor(estados=ESTADOS_CAPTURAS)
    s = Sessao(id="s1", estado="pede_qtd")
    r = m.processar(s, ruim)
    assert s.estado == "pede_qtd" and "quantidade" not in s.slots
    assert "não entendi a quantidade" in r.mensagens[0].texto.lower()


@pytest.mark.parametrize("entrada", ["Embalagens", "embalagens", "FITA ADESIVA"])
def test_captura_produto_normaliza_para_canonico(entrada):
    m = Motor(estados=ESTADOS_CAPTURAS)
    s = Sessao(id="s1", estado="pede_produto")
    m.processar(s, entrada)
    assert s.slots["produto"] in ("Embalagens", "Fita adesiva")
    assert s.estado == "fim"


def test_captura_produto_fora_da_lista_reapresenta():
    m = Motor(estados=ESTADOS_CAPTURAS)
    s = Sessao(id="s1", estado="pede_produto")
    r = m.processar(s, "farinha")
    assert s.estado == "pede_produto" and "produto" not in s.slots
    assert "não achei esse produto" in r.mensagens[0].texto.lower()


# --- regressões dos 3 achados do review Codex ---

def test_acao_nao_reroda_em_display_only():
    # achado 1: refresh (entrada None) não pode regravar um efeito já executado
    m, contador = _motor()
    s = Sessao(id="s1", estado="pede_valor")
    m.processar(s, "300")        # -> confirma
    m.processar(s, "1")          # Confirmar -> gravou (acao 1x) -> redireciona p/ 'a'
    assert contador["gravou"] == 1
    assert s.estado == "a"
    m.processar(s, None)         # re-render
    m.processar(s, None)         # re-render de novo
    assert contador["gravou"] == 1


def test_render_reroda_ao_recuperar_de_entrada_invalida():
    # achado 2: num estado de confirmação, entrada inválida mantém o valor visível
    m, _ = _motor()
    s = Sessao(id="s1", estado="pede_valor")
    m.processar(s, "300")                    # -> confirma
    r = m.processar(s, "resposta bizarra")   # não casa nenhuma opção
    assert s.estado == "confirma"            # continua confirmando
    textos = " ".join(msg.texto for msg in r.mensagens)
    assert "não entendi" in textos.lower()
    assert "confirmar 300,00" in textos      # render re-rodou: valor ainda visível


@pytest.mark.parametrize("ruim", ["nan", "inf", "-inf", "abc", "1e", "", "0,004", "0,001"])
def test_captura_rejeita_nao_finitos_e_invalidos_sem_crashar(ruim):
    # achado 3: NaN/Infinity/lixo não podem crashar nem virar valor capturado
    m, _ = _motor()
    s = Sessao(id="s1", estado="pede_valor")
    r = m.processar(s, ruim)
    assert s.estado == "pede_valor"
    assert "valor" not in s.slots
    assert "não entendi o valor" in r.mensagens[0].texto.lower()
