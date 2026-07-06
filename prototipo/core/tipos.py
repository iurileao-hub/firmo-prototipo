from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Sessao:
    id: str
    estado: str = "inicio"
    slots: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Opcao:
    id: str
    rotulo: str
    destino: str
    palavras: tuple[str, ...] = ()


@dataclass(frozen=True)
class Captura:
    slot: str            # onde guardar o valor capturado (em sessao.slots)
    tipo: str            # "valor" (único tipo no protótipo)
    destino: str         # estado para o qual ir após captura bem-sucedida
    erro_chave: str      # chave do catálogo quando o parse falha


@dataclass(frozen=True)
class Mensagem:
    texto: str
    opcoes: tuple[Opcao, ...] = ()
    audio_ref: Optional[str] = None


@dataclass(frozen=True)
class Estado:
    id: str
    mensagens: tuple[str, ...] = ()      # chaves do catálogo emitidas ao entrar
    opcoes: tuple[Opcao, ...] = ()
    captura: Optional[Captura] = None    # se setado, o estado lê entrada estruturada
    render: Optional[str] = None         # handler PURO: mensagens dinâmicas de display
    #   (idempotente — roda em toda exibição, inclusive re-render e recuperação de erro)
    acao: Optional[str] = None           # handler de EFEITO: roda 1x na transição de
    #   entrada; NUNCA em display-only; pode redirecionar a sessão para um estado de repouso


@dataclass
class Resposta:
    sessao: Sessao
    mensagens: list  # list[Mensagem]
