# Plano de implementação — Assistente Virtual do Residencial Aurora

> Baseado em [specs.md](specs.md) e [contract.md](contract.md). Define decisões de arquitetura e a sequência de construção. Ajustar conforme descobertas durante o desenvolvimento (especialmente a retomada de confirmações via ADK, ponto que o enunciado marca como além das aulas).

## 1. Decisões de arquitetura

### 1.1 Stack
- Python 3.12+, gerenciado por `uv`.
- Google ADK série 2, fixar versão exata (`>=2.2.0,<3` travado no `uv.lock`; começar em `2.2.0` ou a mais nova disponível na série 2).
- Gemini via Google AI Studio (`GOOGLE_API_KEY` no `.env`).
- FastAPI como framework web.
- Persistência:
  - **Sessões ADK**: `DatabaseSessionService` do ADK sobre **SQLite** (arquivo local) — satisfaz Garantia 3 (nada se perde no reinício) e é a combinação citada no enunciado como testada com sucesso para retomada de confirmação.
  - **Dados do condomínio (reservas/visitantes)**: mesmo banco SQLite, tabelas próprias (`reservas`, `visitantes`), carregadas a partir de `dados/*.json` na restauração. `dados/*.json` permanecem intocados (fonte, não destino).

### 1.2 Agentes
- **Agente principal (orquestrador)**: recebe a mensagem do morador, decide para qual especialista rotear. **Não** recebe o regulamento nas instruções (Garantia 4).
- **Especialista de Reservas**: cria/cancela reservas, consulta agenda de área (retorna só livre/ocupada), calcula se há cobrança.
- **Especialista de Visitantes**: autoriza visitantes, consulta autorizações do próprio apartamento.
- **Especialista de Regulamento**: consulta `dados/regulamento.md` sob demanda (por tópico/capítulo) e devolve só o trecho relevante — nunca o documento completo.
- Todos os especialistas recebem o `apartamento` via contexto de sessão (`session.state`), nunca por argumento de tool preenchido livremente pelo modelo.

### 1.3 Tools (contrato interno)
Todas as tools que tocam dados de reserva/visitante recebem o apartamento **do contexto de execução da tool** (`tool_context.state["apartamento"]` ou equivalente do ADK), nunca como parâmetro que o LLM escolhe:
- `consultar_disponibilidade(area, data) -> "livre" | "ocupada"` — nunca revela de quem é a reserva.
- `criar_reserva(area, data)` — lê apartamento da sessão; se `taxa(area) > 0`, marca a ação como exigindo confirmação (Garantia 1) antes de gravar.
- `cancelar_reserva(codigo_ou_area_data)` — só cancela reserva pertencente ao apartamento da sessão.
- `autorizar_visitante(nome, data)` — sempre exige confirmação (libera acesso).
- `listar_minhas_reservas()`, `listar_meus_visitantes()` — escopo travado no apartamento da sessão.
- `buscar_regulamento(pergunta_ou_topico) -> trecho` — retorna apenas o(s) parágrafo(s)/capítulo(s) relevante(s).

### 1.4 Garantia 1 — confirmação (ponto crítico de pesquisa)
- Usar o mecanismo de confirmação de tools do ADK (`tool_confirmation` / `RequestConfirmation` conforme a doc oficial da versão fixada).
- A API precisa: (a) detectar quando o `Runner` pausa esperando confirmação e expor isso em `confirmacoes_pendentes`; (b) ao receber `POST /sessoes/{id}/confirmacoes`, injetar a resposta de volta no ponto exato da execução pausada e retomar via `Runner`.
- Guardar, por sessão, um mapa `confirmation_id -> (invocation pendente, já respondida?)` para implementar o 409 (id não pendente ou já respondido nessa sessão).
- Testar a retomada **com sessão persistida em SQLite e após reiniciar o processo**, não só em memória/`adk web` — o enunciado avisa que essa combinação já quebrou entre versões do ADK.

### 1.5 Garantia 2 — isolamento por apartamento
- `apartamento` gravado em `session.state` na criação da sessão (`POST /sessoes`), lido de lá em toda tool.
- Nenhuma tool deve ter um parâmetro `apartamento` livre; se precisar, validar contra `session.state` e ignorar/rejeitar divergência.
- Consulta de disponibilidade de agenda nunca deve devolver o apartamento/morador de outra reserva.

### 1.6 Garantia 3 — persistência
- `DatabaseSessionService` (SQLite) para eventos/estado de sessão.
- Tabelas `reservas`/`visitantes` no mesmo SQLite, fora do ciclo de vida do processo.
- Comando de restauração recria as tabelas de reservas/visitantes a partir dos JSON; decidir se apaga ou preserva sessões (documentar a escolha no README).

### 1.7 Garantia 4 — regulamento sob demanda
- Pré-processar `dados/regulamento.md` em capítulos/seções (split por cabeçalho markdown).
- Tool `buscar_regulamento` faz busca simples (palavra-chave/similaridade) e retorna só a seção pertinente.
- Agente principal não deve ter o regulamento no prompt/instruções; só o Especialista de Regulamento acessa a tool.
- Conferir manualmente que o evento de tool-result no histórico contém só a seção relevante (passo 12 do fluxo do avaliador).

### 1.8 Garantia 5 — concorrência na gravação
- Constraint `UNIQUE(area, data)` na tabela `reservas` (considerando só reservas ativas — ex.: `WHERE cancelada = 0` via índice parcial, ou coluna de status).
- `criar_reserva` faz `INSERT` dentro de uma transação; conflito de unicidade → captura exceção e devolve recusa "normal" (sem 500) através do fluxo de resposta do agente.
- Evitar "check then write": não fazer `SELECT` de disponibilidade seguido de `INSERT` sem que a unicidade do banco seja a fonte de verdade — o `SELECT` é só para dar feedback amigável antes de pedir confirmação; a garantia real é o `INSERT` atômico.

## 2. Estrutura de projeto (proposta)

```
.
├── pyproject.toml
├── uv.lock
├── .env.example
├── README.md
├── dados/                      # imutável, do repositório base
│   ├── apartamentos.json
│   ├── areas.json
│   ├── reservas.json
│   ├── visitantes.json
│   └── regulamento.md
├── documentacao/
│   ├── solcitacao.md
│   ├── contract.md
│   ├── specs.md
│   └── plan.md
└── src/
    ├── api/                    # FastAPI: rotas do contrato
    ├── agents/                 # agente principal + especialistas (ADK)
    ├── tools/                  # tools de reserva, visitante, regulamento
    ├── storage/                # acesso a SQLite (sessões ADK + dados do condomínio)
    └── scripts/                # subir API, restaurar dados
```

## 3. Fases de implementação

1. **Bootstrap do repositório**
   - Fork do repositório base; `uv init`; fixar Python 3.12+ e ADK (`>=2.2.0`) em `pyproject.toml`; `.env.example` com `GOOGLE_API_KEY` e demais variáveis necessárias.
2. **Camada de dados**
   - Modelos/loaders para `apartamentos.json`, `areas.json`.
   - Schema SQLite para `reservas` (com constraint de unicidade ativa) e `visitantes`.
   - Script de restauração: recarrega `reservas`/`visitantes` a partir dos JSON originais.
3. **API base (sem IA ainda)**
   - `POST /sessoes`, `GET /sessoes/{id}/eventos`, rotas de verificação (`GET /apartamentos/{n}/reservas|visitantes`) ligadas direto ao storage.
   - Validar 404 para sessão inexistente.
4. **Integração ADK — Runner + sessão persistida**
   - Configurar `DatabaseSessionService` (SQLite), `App`/`Runner`.
   - `POST /sessoes` cria sessão ADK com `apartamento` em `state`.
   - `POST /sessoes/{id}/mensagens` chama o `Runner` de forma assíncrona e traduz eventos para `resposta` + `confirmacoes_pendentes`.
5. **Agentes e tools (fluxo feliz, sem confirmação)**
   - Agente principal + Especialista de Reservas + Especialista de Visitantes + Especialista de Regulamento.
   - Tools de leitura/gravação usando `session.state["apartamento"]`.
   - Reserva em área sem taxa e cancelamento funcionando ponta a ponta (passos 5 e 6 do fluxo do avaliador).
6. **Garantia 1 — confirmação**
   - Marcar tools de cobrança/acesso como exigindo confirmação.
   - Implementar `POST /sessoes/{id}/confirmacoes` com retomada real do `Runner` e 409 para id inválido/já respondido.
   - Validar passos 7, 8, 9, 11 do fluxo do avaliador, **incluindo após reinício do processo**.
7. **Garantia 5 — concorrência**
   - Implementar `INSERT` atômico com tratamento de conflito de unicidade.
   - Testar duas aprovações simultâneas (passo 14) com script de disparo paralelo (dois `curl` concorrentes).
8. **Garantia 4 — regulamento sob demanda**
   - Indexar `regulamento.md` por seção; tool de busca; garantir que o agente principal não tem o texto nas instruções.
   - Validar passo 12 (resposta correta + eventos sem trechos de outros capítulos).
9. **Garantia 2 — isolamento**
   - Auditoria de todas as tools: nenhuma aceita `apartamento` como argumento livre do modelo.
   - Testar passos 3, 4, 10 (tentativas de acessar/alterar dados de outro apartamento).
10. **Garantia 3 — reinício**
    - Testar parar/subir a API preservando sessões e dados (passo 13): eventos preservados, contagem cresce, dados persistem.
11. **Validação end-to-end**
    - Executar o roteiro completo de 15 passos do fluxo do avaliador manualmente (ou com script) antes de finalizar.
    - Revisar todos os critérios de aceite de [specs.md](specs.md#9-critérios-de-aceite).
12. **README final**
    - Seções **Arquitetura**, **Garantias** (apontando arquivo+trecho reais), **Como rodar** (pré-requisitos, `.env`, comando de subida, comando de restauração).
    - Remover/substituir o enunciado original na raiz.

## 4. Riscos e pontos de atenção

- **Retomada de confirmação via API própria** (não `adk web`): risco maior do desafio, e a armadilha é silenciosa — a rota de confirmações aceita a resposta, nenhum erro aparece, e a ação simplesmente não executa. A retomada só funciona quando a resposta chega ao **agente que pediu a confirmação**, e quem escolhe esse agente é o `Runner`. Segundo o enunciado, essa escolha mudou entre as versões 2.2.0 e 2.9.1 do ADK conforme a topologia dos agentes, os bloqueios de transferência, a configuração de retomada do `App` e o serviço de sessão — uma combinação que funcionava em memória já falhou com sessão persistida. A doc oficial avisa que alguns serviços de sessão não são suportados para confirmação, mas testes relatados no enunciado tiveram sucesso com sessão persistida em **SQLite** quando a resposta chegou ao agente certo. Por isso: testar a aprovação sempre com sessão persistida e **depois de reiniciar a API**, não só em memória e não só no `adk web`.
- **Ferramenta de desenvolvimento**: durante o desenvolvimento, usar o `adk web` para observar transferências entre agentes, chamadas de tool e pedidos de confirmação acontecendo — é o melhor lugar para depurar isso antes de validar via API própria.
- **Concorrência real**: testar com chamadas HTTP verdadeiramente paralelas (não sequenciais) para validar a constraint de unicidade sob contenção.
- **Vazamento de dados entre apartamentos**: qualquer tool que aceite `apartamento` como parâmetro do modelo é falha de Garantia 2 — revisar assinatura de todas as tools antes de entregar.
- **Regulamento no contexto**: revisar tanto as instruções do agente principal quanto o conteúdo de eventos de tool-call/tool-result para garantir que nenhum trecho fora do tópico perguntado aparece.
