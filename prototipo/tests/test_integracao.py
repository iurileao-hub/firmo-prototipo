from decimal import Decimal
from core.ledger import Ledger
from core.quadro import QuadroInteresses
from core.app import montar_motor, nova_sessao


def test_percurso_completo_formalizar_depois_gerir():
    ledger = Ledger()
    m = montar_motor(ledger, QuadroInteresses())
    s = nova_sessao("s1")

    # entra no fluxo
    r = m.processar(s, None)
    assert "Firmô" in r.mensagens[0].texto

    # vai para Formalizar, passa pelos benefícios
    m.processar(s, "1")                 # opção Formalizar (menu raiz)
    r = m.processar(s, "ainda não")     # não tem CNPJ
    assert any("Bolsa Família" in msg.texto for msg in r.mensagens)

    # volta ao início e vai para Gerir, registra e confirma uma venda
    s.estado = "inicio"                 # (o adaptador oferece "voltar"; simplificado no teste)
    m.processar(s, "cuidar das contas") # opção Gerir por palavra-chave
    m.processar(s, "1")                 # Registrar venda
    m.processar(s, "300")               # valor
    assert ledger.saldo() == Decimal("0")
    m.processar(s, "confirmar")
    assert ledger.saldo() == Decimal("300")


def test_ids_de_estado_sao_unicos():
    m = montar_motor(Ledger(), QuadroInteresses())
    # se houvesse colisão, o dict teria engolido estados; conferimos presença
    assert ("form_intro" in m.estados and "ger_menu" in m.estados
            and "inicio" in m.estados and "cj_menu" in m.estados)


def test_percurso_comprar_junto_e_voltar():
    ledger, quadro = Ledger(), QuadroInteresses()
    m = montar_motor(ledger, quadro)
    s = nova_sessao("s2")
    m.processar(s, None)
    m.processar(s, "comprar junto")     # menu raiz -> cj_menu (palavra-chave)
    m.processar(s, "quero participar")
    m.processar(s, "Sacolas")
    m.processar(s, "100")
    assert quadro.interesses() == ()
    m.processar(s, "confirmar")
    assert quadro.agregado() == [("Sacolas", 1, 100)]
    m.processar(s, "voltar")            # cj_menu -> inicio (a ponta que faltava)
    assert s.estado == "inicio"
