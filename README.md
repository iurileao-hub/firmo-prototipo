# Firmô — protótipo funcional (CPSI Formaliza Feira)

Protótipo do núcleo do **Firmô**, assistente digital de formalização, gestão e compras
coletivas para o empreendedor popular, por WhatsApp e por voz — solução proposta pela
**CLÍNICA DE PSICOLOGIA ELOS LTDA** ao desafio **Formaliza Feira** (CPSI — Licitação
39-2026-14L / CP Eletrônica 40-2026-CP, Prefeitura de Feira de Santana/BA, via
Plataforma Desafios Gov.br/Enap).

Este repositório é a **evidência técnica citada na §4.4.1 da Proposta de Solução
Inovadora** (Anexo V): o núcleo demonstrável da solução, com as três trilhas do desafio
implementadas sobre um motor de conversa determinístico, **84 testes automatizados** e
uma interface de demonstração estilo WhatsApp.

## O que está implementado

| Trilha | O que demonstra |
|---|---|
| **Formalizar** | Jornada MEI-first com a orientação sobre benefícios sociais (Bolsa Família) **antes** de qualquer passo de cadastro — a causa nº 1 da informalidade tratada no centro do fluxo |
| **Gerir** | Registro de vendas/despesas por confirmação explícita → livro-caixa **append-only** (correção = estorno, nunca edição) + retrato do negócio (entrou/saiu/sobrou) |
| **Comprar Junto** | Registro de interesse de compra coletiva (produto × quantidade, confirmado) → **quadro agregado da feira** (nº de feirantes e unidades por produto) |

## Invariantes de segurança (testadas)

- **Conteúdo 100% curado** — todo texto exibido vem de catálogo (`core/catalogo.py`);
  nada é gerado por IA. Chave ausente no catálogo é erro, não fallback.
- **Nada é gravado sem confirmação explícita** — e um refresh/reenvio não regrava
  (efeitos rodam uma única vez, na transição de estado).
- **Append-only** — livro-caixa e quadro de interesses não têm edição; correção é
  estorno compensatório.
- **Entrada ambígua não decide** — fala que casa mais de uma opção ("não confirmar")
  é reapresentada, nunca interpretada a favor de uma ação com efeito.

A arquitetura completa da solução (canal WhatsApp Cloud API, voz STT/TTS, persistência,
painel SETTDEC, LGPD by design) está em [`docs/arquitetura.md`](docs/arquitetura.md) —
o protótipo implementa o núcleo dela (decisões 1, 4 e 5); as demais camadas são o
próximo marco (§4.4.2 da proposta).

## Rodar

```bash
cd prototipo
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q                        # 84 passed
cd web && python manage.py migrate && python manage.py runserver
# abrir http://localhost:8000
# demo com ritmo de conversa real: DEMO_DELAY_MS=350 python manage.py runserver
```

`prototipo/evidencia/` contém 6 cenas capturadas do fluxo (regeneráveis por
`scripts_smoke.py`, Playwright). O quadro da feira da demonstração parte de **dados de
demonstração declarados** (`web/chat/demo.py`) — não são registros reais.

## Estrutura

```
prototipo/core/   motor determinístico (Python puro, zero Django): catálogo · tipos ·
                  interpreter · confirmação · ledger · quadro · motor · 3 trilhas
prototipo/tests/  84 testes (invariantes, trilhas, integração, adaptador web)
prototipo/web/    adaptador Django + HTMX (chat estilo WhatsApp para demonstração)
docs/             arquitetura da solução completa
```

O `core/` não importa Django (ports & adapters): na fase de Aceleração, o webhook do
WhatsApp substitui o adaptador web sem tocar no motor.

## Licença e uso

Código disponibilizado publicamente para fins de **avaliação no âmbito do CPSI
Formaliza Feira**. Todos os direitos reservados © 2026 CLÍNICA DE PSICOLOGIA ELOS LTDA.
