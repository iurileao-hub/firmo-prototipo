"""Trilha Formalizar como dados. Benefícios sociais (causa nº 1) no centro:
quem ainda não é formalizado passa OBRIGATORIAMENTE pela orientação de
benefícios — curada e conservadora — antes de ver os passos do cadastro.
"""
from core.tipos import Estado, Opcao

ESTADOS_FORMALIZAR: dict[str, Estado] = {
    "form_intro": Estado(
        id="form_intro",
        mensagens=("formalizar_intro",),
        opcoes=(
            Opcao(id="form_nao_tem", rotulo="Ainda não tenho CNPJ",
                  destino="form_beneficios", palavras=("nao", "ainda nao", "nao tenho")),
            Opcao(id="form_ja_tem", rotulo="Já tenho CNPJ",
                  destino="form_ja_pj", palavras=("ja tenho", "tenho", "sim", "ja sou")),
        ),
    ),
    # benefícios sociais ANTES dos passos — invariante de conteúdo
    "form_beneficios": Estado(
        id="form_beneficios",
        mensagens=("formalizar_beneficios",),
        opcoes=(
            Opcao(id="form_seguir", rotulo="Entendi, quero ver como abrir",
                  destino="form_passos", palavras=("ok", "entendi", "seguir", "continuar")),
        ),
    ),
    "form_passos": Estado(
        id="form_passos",
        mensagens=("formalizar_passos",),
        opcoes=(
            Opcao(id="form_acompanhar", rotulo="Sim, me acompanha",
                  destino="form_concluido", palavras=("sim", "quero", "acompanha")),
        ),
    ),
    "form_ja_pj": Estado(id="form_ja_pj", mensagens=("formalizar_ja_pj",)),
    "form_concluido": Estado(id="form_concluido", mensagens=("formalizar_concluido",)),
}

HANDLERS_FORMALIZAR: dict = {}
