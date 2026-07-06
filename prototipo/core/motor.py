from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Callable, Optional

from core import catalogo
from core.interpreter import InputInterpreter, _normaliza
from core.tipos import Estado, Mensagem, Resposta, Sessao

Handler = Callable[[Sessao], list]


def _parse_valor_br(texto: str) -> Optional[str]:
    """'300' / '45,50' / 'R$ 1.200,00' -> '300,00' (string BR) ou None."""
    limpo = (
        texto.strip().lower().replace("r$", "").replace(" ", "")
        .replace(".", "").replace(",", ".")
    )
    try:
        valor = Decimal(limpo)
        # is_finite() barra NaN/Infinity ANTES de qualquer comparação (que, com
        # NaN, levantaria InvalidOperation e abortaria a conversa).
        if not valor.is_finite():
            return None
        valor = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None
    # quantiza para centavos ANTES de checar > 0: valores sub-centavo (0,004)
    # arredondam para 0,00 e devem ser rejeitados aqui, não no ledger (crash).
    if valor <= 0:
        return None
    return f"{valor:.2f}".replace(".", ",")


def _parse_quantidade(texto: str) -> Optional[str]:
    """'50' / ' 10 ' -> '50'/'10' (int positivo canônico) ou None."""
    limpo = texto.strip()
    # isdigit() aceita '²'/'①', que int() rejeita (review Codex): o try/except
    # é a barreira real; o isdigit() só barra sinais/decimais/expoentes antes.
    if not limpo.isdigit():
        return None
    try:
        n = int(limpo)
    except ValueError:
        return None
    return str(n) if n > 0 else None


def _parse_produto(texto: str) -> Optional[str]:
    """Casa a entrada (acento/caixa-insensível) com um produto curado."""
    alvo = _normaliza(texto)
    for produto in catalogo.PRODUTOS:
        if alvo == _normaliza(produto):
            return produto
    return None


class Motor:
    """Aplica transições sobre a máquina de estados declarativa.

    Não sabe nem precisa saber como a entrada chegou (toque, número, voz):
    recebe texto normalizado do adaptador e o InputInterpreter faz o resto.

    Dois papéis de handler, deliberadamente separados:
    - `render` é PURO e idempotente: computa mensagens de display a partir da
      sessão. Roda em toda exibição do estado (transição, re-render, erro).
    - `acao` tem EFEITO colateral (ex.: gravar no ledger): roda UMA vez, só na
      transição de entrada, nunca em display-only. Assim um refresh de página
      jamais regrava um lançamento.
    """

    def __init__(self, estados: dict[str, Estado], handlers: Optional[dict[str, Handler]] = None):
        self.estados = estados
        self.handlers = handlers or {}
        self.interpreter = InputInterpreter()

    def _mensagens_do_estado(self, estado: Estado, sessao: Sessao) -> list:
        msgs = [Mensagem(texto=catalogo.render(ch)) for ch in estado.mensagens]
        if estado.render:  # handler puro de display
            msgs += self.handlers[estado.render](sessao)
        return msgs

    def _emitir(self, estado: Estado, sessao: Sessao, prefixo: Optional[list] = None) -> list:
        """Monta as mensagens de display do estado; `prefixo` são avisos (ex.: nao_entendi).

        Os botões do estado grudam na ÚLTIMA mensagem (o prompt), não no aviso.
        """
        msgs = list(prefixo or [])
        msgs += self._mensagens_do_estado(estado, sessao)
        if estado.opcoes:
            if msgs:
                base = msgs[-1]
                msgs[-1] = Mensagem(texto=base.texto, opcoes=estado.opcoes,
                                    audio_ref=base.audio_ref)
            else:
                msgs = [Mensagem(texto=catalogo.render("menu_raiz"), opcoes=estado.opcoes)]
        return msgs

    def _exibir(self, sessao: Sessao) -> Resposta:
        """Display-only: mostra o estado atual SEM rodar `acao` (idempotente)."""
        estado = self.estados[sessao.estado]
        return Resposta(sessao=sessao, mensagens=self._emitir(estado, sessao))

    def _transicionar(self, sessao: Sessao, estado_id: str) -> Resposta:
        """Entra em `estado_id` via transição real: roda `acao` (1x), que pode redirecionar."""
        sessao.estado = estado_id
        estado = self.estados[estado_id]
        prefixo: list = []
        if estado.acao:
            prefixo = self.handlers[estado.acao](sessao)
            if sessao.estado != estado_id:  # o efeito redirecionou para um estado de repouso
                estado = self.estados[sessao.estado]
        return Resposta(sessao=sessao, mensagens=self._emitir(estado, sessao, prefixo))

    def processar(self, sessao: Sessao, entrada: Optional[str]) -> Resposta:
        estado = self.estados[sessao.estado]

        if entrada is None:  # entrada no fluxo / re-render: só exibe (sem efeito)
            return self._exibir(sessao)

        # estado de captura de dado estruturado
        if estado.captura is not None:
            cap = estado.captura
            if cap.tipo == "valor":
                valor = _parse_valor_br(entrada)
            elif cap.tipo == "quantidade":
                valor = _parse_quantidade(entrada)
            elif cap.tipo == "produto":
                valor = _parse_produto(entrada)
            else:
                valor = entrada
            if valor is None:
                aviso = [Mensagem(texto=catalogo.render(cap.erro_chave))]
                return Resposta(sessao=sessao, mensagens=self._emitir(estado, sessao, aviso))
            sessao.slots[cap.slot] = valor
            return self._transicionar(sessao, cap.destino)

        # estado de menu: casa a entrada com uma opção
        opcao = self.interpreter.interpretar(entrada, estado.opcoes)
        if opcao is None:
            aviso = [Mensagem(texto=catalogo.render("nao_entendi"))]
            return Resposta(sessao=sessao, mensagens=self._emitir(estado, sessao, aviso))
        return self._transicionar(sessao, opcao.destino)
