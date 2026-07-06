# Arquitetura da Solução — Firmô (CPSI Formaliza Feira)

**Data:** 2026-07-03
**Contexto:** proposta ao CPSI Formaliza Feira (Licitação 39-2026-14L / CP Eletrônica 40-2026-CP,
Prefeitura de Feira de Santana/BA). Contrato: R$ 200.000 (subvenção), 12 meses,
MVP funcional em ≤6 meses (TR 3.4), operação com ≥900 empreendedores no período restante.
Proponente: CLÍNICA DE PSICOLOGIA ELOS LTDA.

Este documento registra a arquitetura da solução proposta. Ele é insumo direto para a
seção 4 do Anexo V (proposta) e para o plano de implementação do MVP (fase de Aceleração,
a partir de 27/07/2026). O protótipo do núcleo (`../prototipo/`) implementa as decisões
1, 4 e 5 e as invariantes de segurança descritas aqui.

---

## 1. Requisitos que dirigem o design

Derivados do edital (4.2.1), TR (3.1–3.5) e briefing (seções 3–6):

1. **Funcionais obrigatórios (checklist binário):** jornada de formalização MEI-first;
   orientação sobre benefícios sociais (causa estrutural nº 1: medo de perder Bolsa Família
   ao formalizar); gestão básica (receitas/despesas/fluxo de caixa, precificação, margem,
   giro de estoque); compras por atacado (verbos do TR 3.1.2: *orientar, promover a
   organização, instruir, integrar* — não é marketplace transacional); capacidade ≥900
   empreendedores.
2. **Não-funcionais obrigatórios:** acessibilidade (linguagem simples, **leitura por voz**
   = saída em áudio, mobile); LGPD *by design* com rastreabilidade, auditoria e controle
   de acesso **demonstráveis** (TR 3.1.4).
3. **Requisito de evidência:** os 5 eixos de KPI (briefing 6.2) são comprovados por
   "dados gerenciais da solução". Telemetria e histórico auditável são o mecanismo que
   destrava 60% do pagamento (30% relatório de validação + 30% final; TR 7.4).
4. **Restrições:** equipe enxuta com prazo duro; custo de infra ≈ zero em repouso; risco
   "MVP não testável em tempo hábil" classificado ALTO na matriz de riscos do edital.

## 2. Decisões estruturantes

| # | Decisão | Escolha | Alternativas descartadas |
|---|---|---|---|
| 1 | Motor de conversa | **Determinístico puro** — máquina de estados com catálogo curado; autoridade de conteúdo e de escrita 100% determinística | Conversa livre gerada por LLM |
| 1b | Entrada por voz *(revisado 2026-07-03)* | **Pacote completo B0–B3, faseado dentro do MVP:** botões/listas interativas + STT→navegação + classificador LLM restrito + lançamento por voz com confirmação determinística (ver §4.7) | Só menus digitados (fricção real para público que fala mais que digita); voz apenas pós-MVP (proposta perderia o diferencial) |
| 2 | Stack | **Django + HTMX (Fly.io + Supabase)**, motor de conversa como módulo Python puro sem imports de Django | Next.js/Vercel (reconstruiria admin/auth/audit à mão; Hobby proíbe uso comercial); Flask/FastAPI mínimo; SaaS de chatbot (custo recorrente, lock-in, PI enredada) |
| 3 | Voz de saída | **Híbrido:** catálogo de mensagens pré-gerado em build (Piper local; ElevenLabs se a qualidade pedir) + TTS on-demand com cache por hash para conteúdo dinâmico | Pré-gerado total (degrada UX nos números); on-demand total (API no caminho crítico); mínimo de conformidade (defesa fraca do requisito) |
| 4 | Histórico econômico | **Ledger append-only** para lançamentos (correção = estorno compensatório) + CRUD com AuditEvent para cadastros | Event sourcing completo com projeções (maquinaria demais para 6 meses); CRUD puro (edição retroativa corrompe KPIs) |
| 5 | Compras coletivas | **Agregação de demanda + formação de grupos + registro de desfecho.** Formalização é o critério habilitador de acesso aos grupos (TR 3.1.2). Dinheiro nunca passa pelo sistema | Só conteúdo orientativo (não gera KPI); marketplace transacional (risco fiscal/jurídico/LGPD, não pedido pelo edital) |
| 6 | Superfícies web | **Lojista 100% no WhatsApp** (relatórios visuais como PNG no chat) + **painel SETTDEC** = Django admin custom + views HTMX de KPI | Web-lite via magic link (superfície de segurança nova; citada na proposta como evolução); PWA completo (fase de escala) |
| 7 | Infra | **Fly.io GRU + Supabase São Paulo, org ELOS dedicada** (separada de projetos pessoais), staging + prod, Supabase Pro (PITR/backups) | VPS autogerida (ops recorrente para equipe enxuta); infra municipal TR 3.5 (dependência de terceiro; citada como portabilidade futura) |

## 3. Visão geral

Sistema de acompanhamento do lojista do Shopping Popular Cidade das Compras via WhatsApp,
com três trilhas integradas — **Formalizar**, **Gerir**, **Comprar Junto** — onde a
formalização destrava o acesso aos grupos de compra e todo uso alimenta o histórico
econômico auditável que gera os relatórios de KPI do contrato.

```
lojista ──WhatsApp──▶ Webhook (Django view, idempotente por wamid)
                          │
                          ▼
                 ┌─ core/ (Python puro) ─┐
                 │ InputInterpreter      │   catálogo de mensagens
                 │ Máquina de estados    │──▶ texto + áudio pré-gerado
                 │ Regras das trilhas    │   (+ TTS dinâmico c/ cache)
                 └───────────┬───────────┘
                             ▼
              domínio Django: Ledger (append-only) · Cadastros (CRUD+AuditEvent)
              JornadaFormalizacao · Grupos de compra · Outbox de envio
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
      Painel SETTDEC                relatórios do lojista
      (admin custom + views KPI)    (PNG matplotlib no chat)
```

## 4. Componentes

### 4.1 `core/` — motor de conversa (Python puro)

- Zero imports de Django. Ports & adapters: webhook, painel e testes são adaptadores.
- Máquina de estados **explícita e declarativa**: estados, transições e catálogo de
  mensagens definidos como dados Python (dataclasses — tipados, testáveis, refatoráveis);
  migração para YAML só se surgir necessidade de edição de conteúdo por não-dev.
- `InputInterpreter` como interface: a camada de entrada (toque em botão, número
  digitado, voz — ver §4.7) normaliza qualquer entrada para uma opção do estado atual
  ou para dados estruturados pendentes de confirmação. O motor não sabe nem precisa
  saber como a entrada chegou.
- **Invariante de segurança:** STT e LLM nunca geram conteúdo mostrado ao usuário e
  nunca escrevem no domínio. Só (a) selecionam uma opção do menu do estado atual, ou
  (b) propõem dados estruturados que exigem confirmação determinística antes de virar
  lançamento.
- Componente mais testado do sistema (ver §7).
- Conteúdo sensível (orientação sobre benefícios sociais) é **texto curado, nunca
  gerado**: erro aqui é dano real a pessoa vulnerável.

### 4.2 Adaptador WhatsApp

- WhatsApp Business Cloud API oficial (conta Meta Business da ELOS). Bibliotecas
  não-oficiais descartadas (banimento; indefensável em contrato público).
- **Webhook idempotente**: dedup pelo `wamid` (a Meta reenvia webhooks).
- **Outbox transacional**: mensagens de resposta são gravadas no banco na mesma
  transação da mutação de domínio; worker envia com retry exponencial. Crash entre
  gravar e enviar nunca perde nem duplica mensagem (princípio log-first).
- Falha persistente de envio alerta o operador (canal de ops).

### 4.3 Domínio (models Django)

- `Lancamento` — imutável; correção por estorno compensatório referenciando o original.
  Fluxo de caixa, margem e giro de estoque são queries com índice, não projeções.
- `Lojista`, `Produto` — CRUD com trilha AuditEvent (padrão AeroPed).
- `JornadaFormalizacao` — checklist de etapas com timestamps; vira KPI de formalização
  diretamente.
- `IntencaoCompra`, `GrupoCompra`, `DesfechoCompra` — agregação de demanda por categoria,
  massa crítica, registro do resultado (compra realizada, valor, economia estimada) para
  o KPI de competitividade econômica.
- `SessaoConversa` + log de eventos de sessão — estado da conversa e trilha de interação.

### 4.4 Voz (leitura por voz, TR 3.1.3)

- Comando de build gera áudio de **todo o catálogo** (finito porque o motor é
  determinístico). Piper TTS local (CPU ARM, batch); ElevenLabs como upgrade de
  qualidade se necessário.
- Mensagens com valores dinâmicos: TTS on-demand com **cache por hash do texto**.
  API externa fica fora do caminho crítico da conversa.
- Áudio entregue como mensagem de mídia do WhatsApp.

### 4.5 Entrada por voz (camada de normalização — revisado 2026-07-03)

Quatro níveis, faseados dentro do MVP (núcleo + B0 primeiro; B1→B3 na sequência).
O público-alvo usa nota de voz como modo primário de comunicação no WhatsApp;
recusar áudio ("digite o número") sangraria adoção — risco ALTO na matriz do edital.

- **B0 — Botões e listas interativas** (reply buttons ≤3, list messages ≤10 da Cloud
  API): tocar na opção substitui digitar número como caminho principal; digitação vira
  fallback. Determinismo intacto, custo zero. **~1 dia.**
- **B1 — STT → navegação por casamento simples:** nota de voz → transcrição →
  normalizador puro casa com o menu atual (números por extenso, palavras-chave dos
  rótulos, fuzzy match). Sem LLM. Sem casamento confiante → reapresenta o menu.
  **~1–2 dias.**
- **B2 — Classificador LLM restrito** (quando B1 falha): Claude Haiku recebe transcrição
  + opções do estado atual e só pode responder o id de uma opção ou "não sei" (saída
  estruturada). Robusto a fala natural. **+1 dia.**
- **B3 — Lançamento por voz com confirmação:** "vendi 300 reais hoje" → STT → extração
  estruturada (valor, tipo, categoria) → confirmação determinística (✅ Confirmar /
  ✏️ Corrigir) → só então grava no ledger. Caso de uso central da trilha Gerir e a
  cena mais forte do vídeo/Demoday. **+2–3 dias.**

**Total: ~5–7 dias ativos.** Custo de operação (900 usuários, ~30% ativos, ~10 áudios/
mês de ~15 s ≈ 700 min/mês): STT Groq Whisper large-v3-turbo ~US$0,0007/min (<US$1/mês;
alternativa OpenAI gpt-4o-mini-transcribe ~US$0,003/min) + classificação/extração Haiku
US$3–10/mês ⇒ **≈ US$5–12/mês**.

**LGPD do áudio:** voz é dado pessoal enviado a processador fora do Brasil. Tratamento:
DPA e cláusula de não-treinamento (default nas APIs pagas), **descarte do áudio após
transcrição** (retenção só do texto normalizado), transparência no aviso de privacidade
e registro no desenho de privacidade da proposta.

### 4.6 Painel SETTDEC

- Django admin custom — classe do AdminSite em módulo separado dos `@admin.register()`
  (lição LazyObject/AeroPed).
- Grupos de permissão: SETTDEC (read-only) e ELOS (operador). Controle de acesso da
  LGPD demonstrado por construção.
- Views HTMX de KPI agregado espelhando os 5 eixos do briefing 6.2.

### 4.7 Relatórios

- Job mensal: PNG (matplotlib) de fluxo de caixa/margem enviado ao lojista no chat —
  sem superfície de auth nova, demonstrável no vídeo de 5 min.
- Relatório de validação agregado (destrava pagamentos) exportável em PDF pelo painel.

## 5. Fluxo de dados e tratamento de erros

Mensagem entra → dedup por `wamid` → `InputInterpreter` → transição de estado →
mutações de domínio + mensagens de resposta gravadas **atomicamente** → worker de outbox
envia com retry. Entrada não reconhecida nunca é beco: reapresenta o menu em linguagem
simples. Toda mutação tem trilha: ledger por natureza, CRUD por AuditEvent, conversa por
log de sessão — a resposta LGPD (rastreabilidade/auditoria/controle de acesso) é
estrutural, não bolt-on.

LGPD complementar: orientação de privacidade em linguagem simples dentro do próprio
fluxo de conversa (requisito TR 3.1.4 "orientações claras e acessíveis"); plano de
resposta a incidentes documentado; dados em território brasileiro (Fly GRU + Supabase SP).

## 6. Infra e operação

- Org ELOS dedicada em Fly.io e Supabase, **separada de contas de projetos pessoais**.
- Ambientes staging + prod. Supabase Pro (PITR + backups diários — dado financeiro de
  terceiros).
- Portabilidade citada na proposta: Django+Postgres migra para infra municipal (TR 3.5)
  na fase de escala, se desejado.
- Custo estimado: Fly ~US$5 + Supabase Pro US$25 + WhatsApp Cloud API (conversas
  iniciadas pelo usuário: grátis; lembretes por template utility: centavos; estimado
  <US$30/mês a 900 usuários) + TTS saída ≈ 0 + voz de entrada (STT + LLM restrito,
  §4.5) ≈ US$5–12/mês. **Total ≈ R$400–450/mês ≈ 2,5% do contrato por ano.**

## 7. Estratégia de testes

- **Densa no que é crítico:** `core/` (centenas de testes unitários de fluxo: estado X +
  entrada Y → estado Z + mensagens W; sem banco, sem rede), idempotência do webhook,
  outbox, ledger (imutabilidade + estorno).
- Integração: adaptador WhatsApp com API mockada.
- E2E mínimo: um percurso completo por trilha.
- TDD como método de trabalho (padrão dos projetos ELOS em produção).

## 8. Fora de escopo do MVP (explícito)

- Marketplace transacional / pagamentos dentro do sistema.
- PWA offline-first e web-lite do lojista (roadmap declarado na proposta, não promessa
  do MVP).
- Conversa livre gerada por LLM (a IA só classifica/extrai com vocabulário fechado e
  confirmação determinística — ver invariante em §4.1; conteúdo exibido é 100% curado).
- Integrações automáticas com sistemas do Governo Federal (dados de formalização são
  registrados na jornada e cruzados manualmente/por exportação nos relatórios de KPI).

## 9. Riscos de arquitetura reconhecidos

| Risco | Mitigação |
|---|---|
| Fala natural fora do vocabulário dos menus | Camada B0–B3 (§4.5): botões como caminho principal, STT + classificador restrito absorvem fala livre; fallback sempre reapresenta o menu em linguagem simples; testes de usabilidade na aceleração (obrigação da matriz) |
| STT/LLM interpretam errado uma entrada | Invariante §4.1: nada grava sem confirmação determinística; erro de classificação degrada para reapresentação de menu, nunca para ação errada |
| Dependência da WhatsApp Cloud API (política/preço da Meta) | Motor puro independe do canal; adaptador é substituível (SMS/telegram/web) sem tocar no core |
| Adoção baixa (risco ALTO na matriz, alocado à CONTRATANTE) | Superfície única (WhatsApp já instalado), voz, linguagem simples; engajamento social é obrigação da prefeitura na matriz de riscos |
| Indisponibilidade da equipe (risco "questões internas da contratada", ALTO) | Arquitetura de superfície mínima; stack única dominada; documentação e testes desde o início |
