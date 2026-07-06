"""Trilha Gerir como dados + handlers que fecham sobre o Ledger da sessão.

Invariante de confirmação (spec §4.1): o valor é capturado por um estado de
captura, mostrado por um handler `render` (puro), e só vira lançamento quando o
usuário toca em "Confirmar" — que leva a um estado de `acao` (efeito único, que
grava e redireciona de volta ao menu). "Corrigir" volta a pedir o valor.
"""
from decimal import Decimal

from core import catalogo
from core.confirmacao import CORRIGE as _CORRIGE
from core.confirmacao import OK as _OK
from core.tipos import Captura, Estado, Mensagem, Opcao, Sessao

ESTADOS_GERIR: dict[str, Estado] = {
    "ger_menu": Estado(
        id="ger_menu",
        mensagens=("gerir_menu",),
        opcoes=(
            Opcao(id="ger_venda", rotulo="Registrar venda", destino="ger_venda_valor",
                  palavras=("venda", "vendi", "vender")),
            Opcao(id="ger_despesa", rotulo="Registrar despesa", destino="ger_despesa_valor",
                  palavras=("despesa", "gastei", "compra", "paguei")),
            Opcao(id="ger_saldo", rotulo="Ver meu retrato", destino="ger_saldo",
                  palavras=("saldo", "retrato", "quanto", "caixa")),
            Opcao(id="ger_extrato_op", rotulo="📄 Extrato do caixa", destino="ger_extrato",
                  palavras=("extrato", "extratos", "movimento")),
            Opcao(id="ger_dicas_op", rotulo="💡 Dicas de gestão", destino="ger_dicas_menu",
                  palavras=("dica", "dicas", "aprender", "orientacao", "ajuda")),
        ),
    ),
    # --- venda ---
    "ger_venda_valor": Estado(
        id="ger_venda_valor",
        mensagens=("gerir_pede_valor_venda",),
        captura=Captura(slot="valor", tipo="valor", destino="ger_venda_confirma",
                        erro_chave="gerir_valor_invalido"),
    ),
    "ger_venda_confirma": Estado(
        id="ger_venda_confirma",
        render="msg_confirma_venda",
        opcoes=(
            Opcao(id="ger_venda_ok", rotulo="✅ Confirmar", destino="ger_venda_gravou",
                  palavras=_OK),
            Opcao(id="ger_venda_corrige", rotulo="✏️ Corrigir", destino="ger_venda_valor",
                  palavras=_CORRIGE),
        ),
    ),
    "ger_venda_gravou": Estado(id="ger_venda_gravou", acao="gravar_venda"),
    # --- despesa ---
    "ger_despesa_valor": Estado(
        id="ger_despesa_valor",
        mensagens=("gerir_pede_valor_despesa",),
        captura=Captura(slot="valor", tipo="valor", destino="ger_despesa_confirma",
                        erro_chave="gerir_valor_invalido"),
    ),
    "ger_despesa_confirma": Estado(
        id="ger_despesa_confirma",
        render="msg_confirma_despesa",
        opcoes=(
            Opcao(id="ger_despesa_ok", rotulo="✅ Confirmar", destino="ger_despesa_gravou",
                  palavras=_OK),
            Opcao(id="ger_despesa_corrige", rotulo="✏️ Corrigir", destino="ger_despesa_valor",
                  palavras=_CORRIGE),
        ),
    ),
    "ger_despesa_gravou": Estado(id="ger_despesa_gravou", acao="gravar_despesa"),
    # --- retrato (display puro, com saída de volta ao menu) ---
    "ger_saldo": Estado(
        id="ger_saldo",
        render="mostrar_retrato",
        opcoes=(
            Opcao(id="ger_voltar", rotulo="↩ Voltar", destino="ger_menu",
                  palavras=("voltar", "menu")),
        ),
    ),
    # --- extrato consolidado (display puro, lê do ledger; edital §3.1.1) ---
    "ger_extrato": Estado(
        id="ger_extrato",
        render="mostrar_extrato",
        opcoes=(
            Opcao(id="ger_extrato_voltar", rotulo="↩ Voltar", destino="ger_menu",
                  palavras=("voltar", "menu")),
        ),
    ),
    # --- dicas de gestão: os quatro fundamentos do edital §3.1.1 ---
    "ger_dicas_menu": Estado(
        id="ger_dicas_menu",
        mensagens=("gerir_dicas_menu",),
        opcoes=(
            Opcao(id="ger_dica_fluxo_op", rotulo="💰 Fluxo de caixa",
                  destino="ger_dica_fluxo", palavras=("fluxo",)),
            Opcao(id="ger_dica_preco_op", rotulo="🏷️ Precificação",
                  destino="ger_dica_preco", palavras=("preco", "precificacao")),
            Opcao(id="ger_dica_margem_op", rotulo="📈 Margem",
                  destino="ger_dica_margem", palavras=("margem", "lucro")),
            Opcao(id="ger_dica_giro_op", rotulo="📦 Giro de estoque",
                  destino="ger_dica_giro", palavras=("giro", "estoque")),
            Opcao(id="ger_dicas_voltar", rotulo="↩ Voltar", destino="ger_menu",
                  palavras=("voltar", "menu")),
        ),
    ),
    # cada dica exibe texto curado e volta ao menu de dicas (não é beco).
    "ger_dica_fluxo": Estado(
        id="ger_dica_fluxo",
        mensagens=("gerir_dica_fluxo",),
        opcoes=(
            Opcao(id="ger_dica_fluxo_voltar", rotulo="↩ Voltar",
                  destino="ger_dicas_menu", palavras=("voltar", "menu")),
        ),
    ),
    "ger_dica_preco": Estado(
        id="ger_dica_preco",
        mensagens=("gerir_dica_preco",),
        opcoes=(
            Opcao(id="ger_dica_preco_voltar", rotulo="↩ Voltar",
                  destino="ger_dicas_menu", palavras=("voltar", "menu")),
        ),
    ),
    "ger_dica_margem": Estado(
        id="ger_dica_margem",
        mensagens=("gerir_dica_margem",),
        opcoes=(
            Opcao(id="ger_dica_margem_voltar", rotulo="↩ Voltar",
                  destino="ger_dicas_menu", palavras=("voltar", "menu")),
        ),
    ),
    "ger_dica_giro": Estado(
        id="ger_dica_giro",
        mensagens=("gerir_dica_giro",),
        opcoes=(
            Opcao(id="ger_dica_giro_voltar", rotulo="↩ Voltar",
                  destino="ger_dicas_menu", palavras=("voltar", "menu")),
        ),
    ),
}


def _decimal_br(valor_br: str) -> Decimal:
    return Decimal(valor_br.replace(".", "").replace(",", "."))


def construir_handlers_gerir(ledger) -> dict:
    """Handlers fecham sobre `ledger` (o da sessão). `render` são puros;
    `gravar_*` têm efeito e redirecionam de volta ao menu (repouso)."""

    def msg_confirma_venda(sessao: Sessao) -> list:
        return [Mensagem(texto=catalogo.render("gerir_confirmar_venda",
                                               valor=sessao.slots["valor"]))]

    def msg_confirma_despesa(sessao: Sessao) -> list:
        return [Mensagem(texto=catalogo.render("gerir_confirmar_despesa",
                                               valor=sessao.slots["valor"]))]

    def gravar_venda(sessao: Sessao) -> list:
        valor = sessao.slots["valor"]
        ledger.registrar("venda", _decimal_br(valor))
        sessao.estado = "ger_menu"  # efeito roda 1x e volta ao repouso
        return [Mensagem(texto=catalogo.render("gerir_venda_gravada", valor=valor))]

    def gravar_despesa(sessao: Sessao) -> list:
        valor = sessao.slots["valor"]
        ledger.registrar("despesa", _decimal_br(valor))
        sessao.estado = "ger_menu"
        return [Mensagem(texto=catalogo.render("gerir_despesa_gravada", valor=valor))]

    def mostrar_retrato(sessao: Sessao) -> list:
        def br(d: Decimal) -> str:
            return f"{d:.2f}".replace(".", ",")
        r = ledger.retrato()
        return [Mensagem(texto=catalogo.render(
            "gerir_retrato", entradas=br(r["entradas"]), saidas=br(r["saidas"]),
            saldo=br(r["saldo"]), n=r["n_lancamentos"]))]

    def mostrar_extrato(sessao: Sessao) -> list:
        """Extrato consolidado: lista cada lançamento do ledger + os totais.
        Caderno vazio devolve mensagem amigável (nunca crasha)."""
        def br(d: Decimal) -> str:
            return f"{d:.2f}".replace(".", ",")
        lancs = ledger.lancamentos()
        if not lancs:
            return [Mensagem(texto=catalogo.render("gerir_extrato_vazio"))]
        simbolo = {"venda": "＋", "despesa": "－", "estorno": "↩"}
        linhas = "\n".join(
            f"{simbolo.get(l.tipo, '•')} R$ {br(l.valor)} — {l.tipo}" for l in lancs
        )
        r = ledger.retrato()
        return [Mensagem(texto=catalogo.render(
            "gerir_extrato", linhas=linhas, entradas=br(r["entradas"]),
            saidas=br(r["saidas"]), saldo=br(r["saldo"])))]

    return {
        "msg_confirma_venda": msg_confirma_venda,
        "msg_confirma_despesa": msg_confirma_despesa,
        "gravar_venda": gravar_venda,
        "gravar_despesa": gravar_despesa,
        "mostrar_retrato": mostrar_retrato,
        "mostrar_extrato": mostrar_extrato,
    }
