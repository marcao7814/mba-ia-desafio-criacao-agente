# Assistente Virtual do Residencial Aurora

Assistente do condomínio Residencial Aurora, construído com [Google ADK](https://google.github.io/adk-docs/) e exposto por uma API HTTP em Python (FastAPI). Pelo chat, o morador reserva áreas comuns, cancela as próprias reservas, autoriza visitantes e tira dúvidas sobre o regulamento interno — sempre respeitando as regras do condomínio no código, não no prompt.

O enunciado original do desafio está em [`documentacao/solcitacao.md`](documentacao/solcitacao.md); a documentação de planejamento (contrato de API, especificação, plano de implementação e stack) está em [`documentacao/`](documentacao/).

## Arquitetura

O assistente é dividido em um agente principal e três especialistas, todos definidos em [`src/aurora_assistente/agents/`](src/aurora_assistente/agents/):

| Agente | Arquivo | Responsabilidade | Como é acionado |
|---|---|---|---|
| **`assistente_aurora`** (principal) | [`agents/principal.py`](src/aurora_assistente/agents/principal.py) | Conversa com o morador, entende a intenção e distribui o trabalho. Nunca executa reserva, cancelamento, autorização ou consulta ao regulamento diretamente. | Recebe toda mensagem do morador via `POST /sessoes/{id}/mensagens`. |
| **`especialista_reservas`** | [`agents/especialistas.py`](src/aurora_assistente/agents/especialistas.py) | Consulta disponibilidade, cria e cancela reservas de área comum. | Sub-agent do principal (transferência automática do ADK, `sub_agents=[...]`) quando o assunto é reserva. |
| **`especialista_visitantes`** | [`agents/especialistas.py`](src/aurora_assistente/agents/especialistas.py) | Autoriza visitantes e lista autorizações existentes. | Sub-agent do principal, acionado para assuntos de visitante. |
| **`especialista_regulamento`** | [`agents/especialistas.py`](src/aurora_assistente/agents/especialistas.py) | Responde dúvidas sobre o regulamento interno. | Sub-agent do principal, acionado para dúvidas sobre regras do condomínio. |

**Por que essa divisão:** o enunciado exige um agente principal e no mínimo dois especialistas. Três especialistas fazem sentido aqui porque são três domínios de dados/regras genuinamente diferentes (reservas, visitantes, regulamento), cada um com suas próprias tools e sua própria razão para pedir ou não confirmação — separá-los mantém a instrução de cada agente pequena e focada, e é o que permite ao principal nunca precisar do regulamento nas instruções (Garantia 4). A transferência (`sub_agents`) foi escolhida em vez de `AgentTool` porque é o padrão ensinado no curso e o mais direto de raciocinar sobre para quem deve receber a retomada de uma confirmação pendente.

Reservas e visitantes nunca são "lembrados" pelo modelo: toda leitura e escrita passa por tools em [`src/aurora_assistente/agents/tools_reservas.py`](src/aurora_assistente/agents/tools_reservas.py) e [`tools_visitantes.py`](src/aurora_assistente/agents/tools_visitantes.py), que leem e gravam direto no SQLite (`src/aurora_assistente/storage/`).

## Garantias

### Garantia 1 — cobrança ou acesso só com confirmação

- [`agents/tools_reservas.py:36-37`](src/aurora_assistente/agents/tools_reservas.py#L36-L37) define `area_tem_taxa`, e [`agents/especialistas.py:38`](src/aurora_assistente/agents/especialistas.py#L38) registra `FunctionTool(criar_reserva, require_confirmation=area_tem_taxa)` — só pede confirmação quando a área reservada tem taxa (regra de negócio 2).
- [`agents/especialistas.py:57`](src/aurora_assistente/agents/especialistas.py#L57) registra `FunctionTool(autorizar_visitante, require_confirmation=True)` — **sempre** pede confirmação, porque autorizar visitante sempre libera acesso.
- Essas duas linhas usam o mecanismo nativo de confirmação de tools do ADK: quando `require_confirmation` é satisfeito e o morador ainda não respondeu, o ADK interrompe a tool **antes** de ela gravar qualquer coisa e gera um evento de confirmação pendente — a gravação em si (o `INSERT`/`UPDATE` dentro de `criar_reserva`/`autorizar_visitante`) só é alcançada depois que essa confirmação chega aprovada. Isso não depende do que o modelo decide dizer na conversa: mesmo que o morador escreva "já estou confirmando aqui", nada nas instruções dos agentes pode pular esse mecanismo, porque ele é aplicado pelo framework antes do corpo da tool rodar.
- [`api/conversa.py:28-64`](src/aurora_assistente/api/conversa.py#L28-L64) (`confirmacoes_pendentes`) varre o histórico completo da sessão e lista toda chamada sintética `adk_request_confirmation` que ainda não tem uma resposta do morador com o mesmo id — é dessa função que vem a lista `confirmacoes_pendentes` da API.
- [`api/routes_sessoes.py:76-80`](src/aurora_assistente/api/routes_sessoes.py#L76-L80) checa se o `id` recebido em `POST /sessoes/{id}/confirmacoes` está nessa lista **antes** de repassar qualquer coisa ao `Runner`; se não estiver (id desconhecido ou já respondido), devolve `409` sem executar nada — a validação acontece no código da rota, não em uma instrução para o modelo obedecer.

### Garantia 2 — cada sessão pertence a um apartamento

- [`api/routes_sessoes.py:26-35`](src/aurora_assistente/api/routes_sessoes.py#L26-L35) (`criar_sessao`) grava o apartamento em `state={"apartamento": ...}` uma única vez, no momento em que a sessão é criada pelo `DatabaseSessionService` do ADK.
- Toda tool que toca reserva ou visitante lê `tool_context.state["apartamento"]` — nunca recebe apartamento como argumento que o modelo preenche. Ver [`tools_reservas.py:47`](src/aurora_assistente/agents/tools_reservas.py#L47) (`criar_reserva`), [`tools_reservas.py:76`](src/aurora_assistente/agents/tools_reservas.py#L76) (`cancelar_reserva`, cuja cláusula `WHERE apartamento = ?` usa esse valor), [`tools_reservas.py:91`](src/aurora_assistente/agents/tools_reservas.py#L91) (`listar_minhas_reservas`) e o mesmo padrão em [`tools_visitantes.py`](src/aurora_assistente/agents/tools_visitantes.py). Nenhuma assinatura de tool tem um parâmetro `apartamento` que o modelo possa escolher.
- [`tools_reservas.py:19-33`](src/aurora_assistente/agents/tools_reservas.py#L19-L33) (`consultar_disponibilidade`) só devolve `"livre"` ou `"ocupada"` — a query lê a linha da reserva, mas o retorno da tool nunca inclui o apartamento de quem já reservou, então esse dado não tem como chegar à conversa.
- Como a checagem de apartamento está na cláusula SQL da tool e não em uma instrução de prompt, nenhuma mensagem do morador ("sou do 302", "isso é reserva do 302 também") consegue alterar qual apartamento é usado: o valor já foi fixado no `state` da sessão antes da primeira mensagem.

### Garantia 3 — nada se perde no reinício

- [`api/deps.py`](src/aurora_assistente/api/deps.py) configura o `DatabaseSessionService` do ADK sobre um arquivo SQLite persistido em disco (`DATABASE_PATH`, resolvido a partir de `DATABASE_URL` em [`config.py`](src/aurora_assistente/config.py)) — não é o serviço de sessão em memória, então os eventos de cada sessão sobrevivem ao processo terminar.
- Reservas e visitantes ficam no mesmo arquivo SQLite ([`storage/database.py`](src/aurora_assistente/storage/database.py)), fora do processo da API.
- Testado manualmente (Fase 3 do plano): criada uma sessão e uma reserva, o processo da API foi encerrado e religado sem rodar a restauração, e tanto `GET /sessoes/{id}/eventos` quanto `GET /apartamentos/{numero}/reservas` continuaram consistentes com o estado anterior ao reinício.

### Garantia 4 — o regulamento é consultado, não carregado

- [`agents/principal.py`](src/aurora_assistente/agents/principal.py) — a instrução do agente principal não contém nenhum trecho do regulamento; o comentário no topo do arquivo marca essa omissão como intencional.
- [`storage/regulamento.py`](src/aurora_assistente/storage/regulamento.py) (`carregar_capitulos`/`buscar_capitulo`) divide `dados/regulamento.md` em capítulos pelos cabeçalhos `## Capítulo ...` e escolhe **um único capítulo** por sobreposição de palavras com a pergunta.
- [`agents/tools_regulamento.py`](src/aurora_assistente/agents/tools_regulamento.py) (`buscar_regulamento`) é a única forma de qualquer agente tocar o texto do regulamento, e devolve só esse capítulo — nunca o documento inteiro. Só o `especialista_regulamento` tem essa tool; o principal e os outros especialistas nunca a veem.
- Como a tool devolve no máximo um capítulo por chamada, o evento de `function_response` que entra no histórico da sessão nunca acumula texto de capítulos sobre assuntos diferentes do que foi perguntado.

### Garantia 5 — dois moradores, uma reserva

- [`storage/database.py`](src/aurora_assistente/storage/database.py) cria `idx_reserva_ativa_area_data`, um índice **único parcial** — `CREATE UNIQUE INDEX ... ON reservas (area, data) WHERE cancelada = 0`. É o próprio SQLite que rejeita, no instante do `INSERT`, uma segunda reserva ativa para a mesma área e data — não uma checagem prévia feita em Python.
- [`agents/tools_reservas.py:40-66`](src/aurora_assistente/agents/tools_reservas.py#L40-L66) (`criar_reserva`) faz o `INSERT` dentro de uma transação e trata `aiosqlite.IntegrityError`: se a violação for do índice de área+data, devolve uma recusa normal (`{"erro": "Já existe uma reserva ativa..."}`), sem gerar erro 500; se for colisão de código (regra de negócio 5, que também nunca repete mesmo cancelado, pois `codigo` é chave primária), tenta outro código.
- Testado manualmente contra o SQLite direto: duas inserções concorrentes na mesma área e data resultam em uma bem-sucedida e uma bloqueada por `IntegrityError`; uma reserva cancelada na mesma área/data não conflita, porque o índice é parcial (`WHERE cancelada = 0`).

## Como rodar

### Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Uma chave de API do [Google AI Studio](https://aistudio.google.com/) para os modelos Gemini

### Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

| Variável | Descrição |
|---|---|
| `GOOGLE_API_KEY` | Chave do Google AI Studio (obrigatória) |
| `GEMINI_MODEL` | Modelo Gemini usado por todos os agentes (padrão: `gemini-2.5-flash`; ajuste conforme os modelos disponíveis no seu projeto) |
| `DATABASE_URL` | Caminho do SQLite que guarda sessões, reservas e visitantes (padrão: `sqlite:///./data/aurora.db`) |
| `PORT` | Porta da API (padrão: `8000`) |

### Instalar dependências

```bash
uv sync
```

### Restaurar os dados iniciais

```bash
uv run restaurar-dados
```

Recarrega as tabelas de reservas e visitantes a partir de `dados/reservas.json` e `dados/visitantes.json`. Não apaga sessões existentes.

### Subir a API

```bash
uv run subir-api
```

A API responde em `http://localhost:8000`.
