"""Catálogo curado de mensagens do Firmô. Linguagem simples, PT-BR.

Conteúdo sobre benefícios sociais é conservador por decisão de arquitetura:
na dúvida, encaminhar ao atendimento oficial. Nunca gerar resposta automática
sobre caso concreto.
"""

CATALOGO: dict[str, str] = {
    "saudacao": (
        "Oi! Eu sou o Firmô 👋 Seu ajudante aqui do Shopping Popular.\n"
        "Posso te ajudar a abrir sua firma, cuidar das contas do dia a dia "
        "e comprar junto com outros lojistas."
    ),
    "menu_raiz": "O que você quer fazer agora?",
    # --- Formalizar ---
    "formalizar_intro": (
        "Vamos ver sua situação. Me conta: você já tem CNPJ (a sua firma)?"
    ),
    "formalizar_beneficios": (
        "Antes de tudo, uma coisa importante sobre o Bolsa Família e outros "
        "benefícios: abrir o MEI *não cancela automaticamente* o seu benefício. "
        "O que conta é a renda da sua família, não o CNPJ em si.\n"
        "Como cada caso é um caso, o certo é confirmar no CRAS ou no Bolsa "
        "Família antes de decidir. Eu te mostro o caminho — quem decide é você, "
        "com a informação certa."
    ),
    "formalizar_passos": (
        "Abrir o MEI é de graça e dá pra fazer pelo celular. São 3 passos:\n"
        "1) Ter em mãos seu CPF e um endereço;\n"
        "2) Escolher a atividade (o que você vende);\n"
        "3) Fazer o cadastro no Portal do Empreendedor.\n"
        "Quer que eu te acompanhe passo a passo?"
    ),
    "formalizar_ja_pj": (
        "Boa, você já é formalizado! Então você já pode entrar nos grupos de "
        "compra coletiva e usar todos os benefícios de quem tem CNPJ."
    ),
    "formalizar_concluido": (
        "Fechou! Quando você terminar o cadastro do MEI, me avisa aqui que eu "
        "marco sua jornada como concluída. Firmô ✅"
    ),
    # --- Gerir ---
    "gerir_menu": "Vamos cuidar das contas. O que você quer registrar?",
    "gerir_pede_valor_venda": "Quanto foi a venda? Escreve só o valor (ex.: 300).",
    "gerir_pede_valor_despesa": "Quanto foi a despesa? Escreve só o valor (ex.: 50).",
    "gerir_valor_invalido": (
        "Não entendi o valor. Escreve só o número, tipo 300 ou 45,50."
    ),
    "gerir_confirmar_venda": "Entendi: venda de R$ {valor}. Tá certo?",
    "gerir_confirmar_despesa": "Entendi: despesa de R$ {valor}. Tá certo?",
    "gerir_venda_gravada": "Firmô ✅ Venda de R$ {valor} registrada.",
    "gerir_despesa_gravada": "Firmô ✅ Despesa de R$ {valor} registrada.",
    "gerir_retrato": (
        "Seu retrato até agora 📒\n"
        "Entrou: R$ {entradas}\n"
        "Saiu: R$ {saidas}\n"
        "Sobrou: R$ {saldo}\n"
        "São {n} registros no seu caderno."
    ),
    # --- Comprar Junto ---
    "comprar_intro": (
        "Comprando junto, a feira paga menos 💪\n"
        "Funciona assim: você marca o que precisa, eu junto os pedidos de "
        "vários lojistas e o grupo negocia preço melhor com o fornecedor.\n"
        "Marcar interesse não custa nada e não te obriga a comprar."
    ),
    "comprar_pede_produto": "O que você precisa comprar? Toca numa opção 👇",
    "comprar_pede_qtd": (
        "Quantas unidades de {produto} você precisa? Escreve só o número (ex.: 50)."
    ),
    "comprar_confirmar": "Entendi: {quantidade} unidade(s) de {produto}. Tá certo?",
    "comprar_interesse_gravado": (
        "Firmô ✅ Seu interesse em {quantidade} unidade(s) de {produto} "
        "tá no quadro da feira."
    ),
    "comprar_quadro_titulo": "Quadro da feira até agora 📋",
    "comprar_quadro_vazio": (
        "O quadro tá vazio por enquanto. Marca teu interesse que eu aviso a feira!"
    ),
    # --- genéricos ---
    "comprar_qtd_invalida": "Não entendi a quantidade. Escreve só o número inteiro, tipo 50.",
    "comprar_produto_invalido": "Não achei esse produto na lista. Toca numa das opções 👇",
    "nao_entendi": "Desculpa, não entendi. Toca numa das opções abaixo 👇",
    "voltar_menu": "Voltamos pro início. O que você quer fazer?",
}


# Produtos elegíveis para compra coletiva no protótipo (lista curada).
PRODUTOS: tuple[str, ...] = ("Embalagens", "Sacolas", "Fita adesiva")


def render(chave: str, **kwargs) -> str:
    """Retorna o texto curado da `chave`, interpolando `kwargs`.

    Chave ausente levanta KeyError de propósito: no protótipo determinístico,
    toda mensagem exibida tem que existir no catálogo.
    """
    return CATALOGO[chave].format(**kwargs)
