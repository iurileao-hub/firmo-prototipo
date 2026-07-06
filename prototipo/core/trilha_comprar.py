"""Trilha Comprar Junto como dados + handlers que fecham sobre o Quadro.

Mesmo padrão da Gerir: captura -> render confirma (puro) -> acao grava (1x).
Interesse de compra vai para o QuadroInteresses (append-only), NUNCA para o
ledger financeiro — são semânticas diferentes.
"""
from core import catalogo
from core.confirmacao import CORRIGE as _CORRIGE
from core.confirmacao import OK as _OK
from core.tipos import Captura, Estado, Mensagem, Opcao, Sessao

# Botões dos produtos: quem interpreta a entrada é a CAPTURA (tipo "produto");
# as opções aqui são só a superfície de toque (o destino delas não é usado,
# porque o motor trata a captura antes do menu — o botão posta o rótulo).
_BOTOES_PRODUTO = tuple(
    Opcao(id=f"cj_prod_{i}", rotulo=p, destino="cj_qtd")
    for i, p in enumerate(catalogo.PRODUTOS)
)

ESTADOS_COMPRAR: dict[str, Estado] = {
    "cj_menu": Estado(
        id="cj_menu",
        mensagens=("comprar_intro",),
        opcoes=(
            # "quero" NÃO é palavra de roteamento: verbo de desejo aparece em
            # qualquer fala livre e colidiria com todas as outras opções.
            Opcao(id="cj_participar", rotulo="Quero participar", destino="cj_produto",
                  palavras=("participar", "entrar")),
            Opcao(id="cj_ver_quadro", rotulo="Ver quadro da feira", destino="cj_quadro",
                  palavras=("quadro", "ver")),
            Opcao(id="cj_voltar", rotulo="↩ Voltar", destino="inicio",
                  palavras=("voltar", "menu", "inicio")),
        ),
    ),
    "cj_produto": Estado(
        id="cj_produto",
        mensagens=("comprar_pede_produto",),
        opcoes=_BOTOES_PRODUTO,
        captura=Captura(slot="produto", tipo="produto", destino="cj_qtd",
                        erro_chave="comprar_produto_invalido"),
    ),
    "cj_qtd": Estado(
        id="cj_qtd",
        render="msg_pede_qtd",
        captura=Captura(slot="quantidade", tipo="quantidade", destino="cj_confirma",
                        erro_chave="comprar_qtd_invalida"),
    ),
    "cj_confirma": Estado(
        id="cj_confirma",
        render="msg_confirma_interesse",
        opcoes=(
            Opcao(id="cj_ok", rotulo="✅ Confirmar", destino="cj_gravou", palavras=_OK),
            Opcao(id="cj_corrige", rotulo="✏️ Corrigir", destino="cj_qtd",
                  palavras=_CORRIGE),
        ),
    ),
    "cj_gravou": Estado(id="cj_gravou", acao="registrar_interesse"),
    "cj_quadro": Estado(
        id="cj_quadro",
        render="mostrar_quadro",
        opcoes=(
            Opcao(id="cj_q_participar", rotulo="Quero participar", destino="cj_produto",
                  palavras=("participar", "entrar")),
            Opcao(id="cj_q_voltar", rotulo="↩ Voltar", destino="cj_menu",
                  palavras=("voltar", "menu")),
        ),
    ),
}


def construir_handlers_comprar(quadro) -> dict:
    """Handlers fecham sobre `quadro`. `render` puros; `registrar_interesse`
    tem efeito, roda 1x e devolve a sessão ao repouso (cj_menu)."""

    def msg_pede_qtd(sessao: Sessao) -> list:
        return [Mensagem(texto=catalogo.render(
            "comprar_pede_qtd", produto=sessao.slots["produto"]))]

    def msg_confirma_interesse(sessao: Sessao) -> list:
        return [Mensagem(texto=catalogo.render(
            "comprar_confirmar", quantidade=sessao.slots["quantidade"],
            produto=sessao.slots["produto"]))]

    def registrar_interesse(sessao: Sessao) -> list:
        quadro.registrar(sessao.id, sessao.slots["produto"],
                         int(sessao.slots["quantidade"]))
        texto = catalogo.render("comprar_interesse_gravado",
                                quantidade=sessao.slots["quantidade"],
                                produto=sessao.slots["produto"])
        sessao.estado = "cj_menu"  # efeito roda 1x e volta ao repouso
        return [Mensagem(texto=texto)]

    def mostrar_quadro(sessao: Sessao) -> list:
        linhas = quadro.agregado()
        if not linhas:
            return [Mensagem(texto=catalogo.render("comprar_quadro_vazio"))]
        corpo = "\n".join(
            f"• {produto}: {n} feirante(s) · {total} unidades"
            for produto, n, total in linhas
        )
        titulo = catalogo.render("comprar_quadro_titulo")
        return [Mensagem(texto=f"{titulo}\n{corpo}")]

    return {
        "msg_pede_qtd": msg_pede_qtd,
        "msg_confirma_interesse": msg_confirma_interesse,
        "registrar_interesse": registrar_interesse,
        "mostrar_quadro": mostrar_quadro,
    }
