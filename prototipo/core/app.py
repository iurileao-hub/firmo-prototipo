"""Composição do motor completo: menu raiz + trilhas Formalizar, Gerir e Comprar Junto."""
from core.motor import Motor
from core.tipos import Estado, Opcao, Sessao
from core.trilha_comprar import ESTADOS_COMPRAR, construir_handlers_comprar
from core.trilha_formalizar import ESTADOS_FORMALIZAR, HANDLERS_FORMALIZAR
from core.trilha_gerir import ESTADOS_GERIR, construir_handlers_gerir

_INICIO = {
    "inicio": Estado(
        id="inicio",
        mensagens=("saudacao", "menu_raiz"),
        opcoes=(
            Opcao(id="ir_formalizar", rotulo="Abrir/organizar minha firma",
                  destino="form_intro", palavras=("formalizar", "cnpj", "mei", "firma", "abrir")),
            Opcao(id="ir_gerir", rotulo="Cuidar das contas",
                  destino="ger_menu", palavras=("contas", "conta", "venda", "despesa", "caixa", "gerir")),
            Opcao(id="ir_comprar", rotulo="Comprar junto com a feira",
                  destino="cj_menu", palavras=("comprar", "junto", "coletiva", "grupo")),
        ),
    ),
}


def _checar_colisao(*mapas) -> None:
    vistos: set[str] = set()
    for mapa in mapas:
        for chave in mapa:
            if chave in vistos:
                raise ValueError(f"colisão de id de estado: {chave}")
            vistos.add(chave)


def montar_motor(ledger, quadro) -> Motor:
    _checar_colisao(_INICIO, ESTADOS_FORMALIZAR, ESTADOS_GERIR, ESTADOS_COMPRAR)
    estados = {**_INICIO, **ESTADOS_FORMALIZAR, **ESTADOS_GERIR, **ESTADOS_COMPRAR}
    handlers = {**HANDLERS_FORMALIZAR, **construir_handlers_gerir(ledger),
                **construir_handlers_comprar(quadro)}
    return Motor(estados=estados, handlers=handlers)


def nova_sessao(id: str) -> Sessao:
    return Sessao(id=id, estado="inicio")
