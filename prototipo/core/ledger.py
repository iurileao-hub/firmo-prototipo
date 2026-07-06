from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

_SINAL = {"venda": Decimal("1"), "despesa": Decimal("-1")}


@dataclass(frozen=True)
class Lancamento:
    id: int
    tipo: str                 # "venda" | "despesa" | "estorno"
    valor: Decimal            # magnitude, sempre positiva
    ref: Optional[int] = None # para estorno: id do lançamento revertido


class Ledger:
    """Livro append-only. Correção = estorno compensatório, nunca edição.

    Protótipo: em memória. Na Aceleração vira model Django com a mesma
    semântica (imutabilidade por convenção + AuditEvent).
    """

    def __init__(self) -> None:
        self._lancamentos: list[Lancamento] = []

    def _proximo_id(self) -> int:
        return len(self._lancamentos) + 1

    def registrar(self, tipo: str, valor: Decimal) -> Lancamento:
        if tipo not in _SINAL:
            raise ValueError(f"tipo inválido para registro: {tipo}")
        valor = Decimal(valor)
        if valor <= 0:
            raise ValueError(f"valor deve ser positivo (magnitude): {valor}")
        lanc = Lancamento(id=self._proximo_id(), tipo=tipo, valor=valor)
        self._lancamentos.append(lanc)
        return lanc

    def estornar(self, id_alvo: int) -> Lancamento:
        original = next((x for x in self._lancamentos if x.id == id_alvo), None)
        if original is None or original.tipo == "estorno":
            raise ValueError(f"não há lançamento estornável com id {id_alvo}")
        # um lançamento é estornável UMA vez só — dois estornos reverteriam
        # o efeito em dobro (retry/double-submit corromperia o saldo).
        if any(x.tipo == "estorno" and x.ref == id_alvo for x in self._lancamentos):
            raise ValueError(f"lançamento {id_alvo} já foi estornado")
        estorno = Lancamento(
            id=self._proximo_id(), tipo="estorno", valor=original.valor, ref=id_alvo
        )
        self._lancamentos.append(estorno)
        return estorno

    def saldo(self) -> Decimal:
        total = Decimal("0")
        for lanc in self._lancamentos:
            if lanc.tipo in _SINAL:
                total += _SINAL[lanc.tipo] * lanc.valor
            elif lanc.tipo == "estorno":
                alvo = next(x for x in self._lancamentos if x.id == lanc.ref)
                total -= _SINAL[alvo.tipo] * alvo.valor
        return total

    def retrato(self) -> dict:
        """Totais do caderno: entradas, saídas, saldo e nº de registros.
        Estorno abate o total do tipo estornado (coerente com saldo())."""
        entradas = saidas = Decimal("0")
        for lanc in self._lancamentos:
            if lanc.tipo == "venda":
                entradas += lanc.valor
            elif lanc.tipo == "despesa":
                saidas += lanc.valor
            else:  # estorno
                alvo = next(x for x in self._lancamentos if x.id == lanc.ref)
                if alvo.tipo == "venda":
                    entradas -= lanc.valor
                else:
                    saidas -= lanc.valor
        return {"entradas": entradas, "saidas": saidas,
                "saldo": entradas - saidas, "n_lancamentos": len(self._lancamentos)}

    def lancamentos(self) -> tuple[Lancamento, ...]:
        return tuple(self._lancamentos)
