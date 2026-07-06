import re
import unicodedata


def _normaliza(texto: str) -> str:
    """minúsculas, sem acento, sem espaços nas bordas."""
    t = unicodedata.normalize("NFKD", texto.strip().lower())
    return "".join(c for c in t if not unicodedata.combining(c))


class InputInterpreter:
    """Normaliza qualquer entrada digitada para uma Opcao do estado atual.

    No protótipo cobre B0 (toque/número) e B1 (palavra-chave simples). STT e
    LLM (B2/B3) entram na fase de Aceleração — mas o motor não muda, porque
    eles também só devolvem um id de opção ou dado estruturado para confirmar.
    """

    def interpretar(self, texto: str, opcoes: tuple) -> object | None:
        alvo = _normaliza(texto)
        if not alvo or not opcoes:
            return None

        # 1) número 1-based ("1", "2", ...)
        if alvo.isdigit():
            idx = int(alvo) - 1
            return opcoes[idx] if 0 <= idx < len(opcoes) else None

        # 2) id exato ou rótulo exato
        for op in opcoes:
            if alvo == op.id or alvo == _normaliza(op.rotulo):
                return op

        # 3) rótulo ou palavra-chave como token/frase INTEIRA.
        #    Fronteira de palavra (\b) evita casar 'mei' dentro de 'primeiro'
        #    — substring cru rotearia fala livre para a opção errada.
        #    Desempate por ESPECIFICIDADE (reviews Codex): se os termos casados
        #    das outras opções são substrings de um termo casado da melhor
        #    ("tenho" ⊂ "nao tenho"), a mais específica vence. Ambiguidade real
        #    ("nao" × "confirmar") não decide: None e o motor reapresenta —
        #    primeira-opção-vence gravaria uma negação.
        casadas: dict = {}  # op -> termos que casaram
        for op in opcoes:
            termos = (_normaliza(op.rotulo), *(_normaliza(p) for p in op.palavras))
            achados = [t for t in termos
                       if t and re.search(rf"\b{re.escape(t)}\b", alvo)]
            if achados:
                casadas[op] = achados

        if not casadas:
            return None
        if len(casadas) == 1:
            return next(iter(casadas))
        melhor = max(casadas, key=lambda op: max(len(t) for t in casadas[op]))
        outras_sao_subfrases = all(
            any(t in t_melhor for t_melhor in casadas[melhor])
            for op, ts in casadas.items() if op is not melhor
            for t in ts
        )
        return melhor if outras_sao_subfrases else None
