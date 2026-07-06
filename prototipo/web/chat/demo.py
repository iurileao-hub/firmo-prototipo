"""Seed de DEMONSTRAÇÃO do quadro da feira — não é dado real.

O quadro é coletivo (um por processo, compartilhado entre sessões): é isso
que a compra coletiva demonstra. O seed dá contexto visual à demo/vídeo e
está declarado como dado de demonstração no README.
"""
from core.quadro import QuadroInteresses

_SEEDS = (
    ("demo-1", "Embalagens", 50),
    ("demo-2", "Embalagens", 120),
    ("demo-3", "Embalagens", 150),
    ("demo-4", "Sacolas", 200),
    ("demo-5", "Sacolas", 300),
    ("demo-6", "Fita adesiva", 40),
)


def quadro_demo() -> QuadroInteresses:
    quadro = QuadroInteresses()
    for sessao_id, produto, quantidade in _SEEDS:
        quadro.registrar(sessao_id, produto, quantidade)
    return quadro
