"""Quadro de interesses da compra coletiva. Append-only, sem edição.

NÃO reusa o Ledger de propósito: interesse de compra não é lançamento
financeiro — não tem sinal (+/−) nem estorno compensatório. Reusar a
estrutura "porque já é append-only" resemantizaria a classe.
"""
from dataclasses import dataclass

from core import catalogo


@dataclass(frozen=True)
class Interesse:
    id: int
    sessao_id: str
    produto: str
    quantidade: int


class QuadroInteresses:
    def __init__(self) -> None:
        self._interesses: list[Interesse] = []

    def registrar(self, sessao_id: str, produto: str, quantidade: int) -> Interesse:
        # fail-secure: valida na escrita, mesmo que a trilha já tenha validado
        if produto not in catalogo.PRODUTOS:
            raise ValueError(f"produto fora da lista curada: {produto}")
        # isinstance barra float/NaN (NaN passaria: nan <= 0 é False) — review Codex
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise ValueError(f"quantidade deve ser um inteiro positivo: {quantidade}")
        interesse = Interesse(id=len(self._interesses) + 1, sessao_id=sessao_id,
                              produto=produto, quantidade=quantidade)
        self._interesses.append(interesse)
        return interesse

    def agregado(self) -> list[tuple[str, int, int]]:
        """(produto, nº de feirantes distintos, total de unidades), mais feirantes primeiro."""
        feirantes: dict[str, set[str]] = {}
        totais: dict[str, int] = {}
        for i in self._interesses:
            feirantes.setdefault(i.produto, set()).add(i.sessao_id)
            totais[i.produto] = totais.get(i.produto, 0) + i.quantidade
        linhas = [(p, len(feirantes[p]), totais[p]) for p in totais]
        # desempate canônico por nome: mesma entrada => mesma saída, sempre
        return sorted(linhas, key=lambda linha: (-linha[1], linha[0]))

    def interesses(self) -> tuple[Interesse, ...]:
        return tuple(self._interesses)
