# Firmô — Protótipo do Core (fase de Pré-seleção)

Protótipo funcional do núcleo determinístico do Firmô: máquina de estados,
`InputInterpreter`, ledger append-only e quadro de compra coletiva, cobrindo
as **três trilhas do desafio — Formalizar, Gerir e Comprar Junto**, com uma
interface web estilo WhatsApp.

## Rodar

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -v                       # suíte do core (evidência de "protótipo funcional")
cd web && python manage.py migrate && python manage.py runserver
# abrir http://localhost:8000
# vídeo/demo: DEMO_DELAY_MS=350 python manage.py runserver  (resposta com "digitando…")
```

**84 testes automatizados** passando (`pytest -q`).

## O que este protótipo demonstra

- **Determinismo no conteúdo:** todo texto exibido vem de catálogo curado
  (`core/catalogo.py`) — nunca gerado. Conteúdo sensível (benefícios sociais)
  aparece **antes** de qualquer passo de cadastro (`tests/test_trilha_formalizar.py`).
- **Invariante de confirmação:** nenhum lançamento entra no ledger sem "Confirmar"
  (`tests/test_trilha_gerir.py::test_fluxo_venda_so_grava_apos_confirmar`), e um
  refresh não regrava (`test_confirmar_venda_nao_regrava_em_refresh`).
- **Ledger append-only:** correção é estorno compensatório, nunca edição
  (`tests/test_ledger.py`); o retrato do negócio (entradas/saídas/saldo) deriva
  só do livro (`Ledger.retrato()`).
- **Compra coletiva com quadro agregado:** interesse só entra no quadro após
  confirmação explícita (`tests/test_trilha_comprar.py`); o quadro da demo
  parte de **dados de demonstração declarados** (`web/chat/demo.py`) — não são
  registros reais.
- **Entrada ambígua não decide:** "não confirmar" casa termos de Confirmar E
  de Corrigir — o interpreter exige match único e o motor reapresenta
  (`tests/test_interpreter.py::test_entrada_ambigua_retorna_none`).
- **Ports & adapters:** o `core/` não importa Django; a web é só um adaptador
  (`web/chat/views.py`), como será o webhook do WhatsApp na Aceleração.

## Estrutura

```
core/    catalogo · tipos · interpreter · confirmacao · ledger · quadro · motor
         · trilha_formalizar · trilha_gerir · trilha_comprar · app
tests/   84 testes (catálogo, interpreter, ledger, quadro, motor, 3 trilhas, integração, web)
web/     adaptador Django + HTMX (chat estilo WhatsApp; demo.py = seed do quadro)
evidencia/  6 cenas do fluxo (para o vídeo e a evidência da 4.4.1)
scripts_smoke.py  dirige o fluxo no navegador (Playwright) e regenera as cenas
```

## Fora do escopo do protótipo (na proposta como roadmap)

Voz (STT/TTS), WhatsApp Cloud API, persistência em Postgres/Supabase, painel
SETTDEC, rateio/fechamento de grupo na Comprar Junto. Ver a arquitetura completa
em [`../docs/arquitetura.md`](../docs/arquitetura.md).

> **Nota:** o estado de sessão do adaptador web é em memória de processo
> (*prototype-only*). Na Aceleração vira `SessaoConversa` + `Ledger` persistidos.
