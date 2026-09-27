# Stack técnica — Assistente Virtual do Residencial Aurora

> Consolida as escolhas de tecnologia derivadas de [specs.md §6](specs.md#6-tecnologias-obrigatórias-e-restrições) (obrigações do enunciado) e de [plan.md §1](plan.md#1-decisões-de-arquitetura) (decisões de projeto). Serve como referência única para `pyproject.toml`, `.env.example` e para a seção **Como rodar** do README final.

## 1. Linguagem e gerenciador de pacotes

| Item | Escolha | Motivo |
|---|---|---|
| Linguagem | Python **3.12+** | Exigência do enunciado |
| Gerenciador | **uv** (`pyproject.toml` + `uv.lock` versionados) | Exigência do enunciado |

Comandos-base:
```bash
uv sync            # instala dependências a partir de pyproject.toml/uv.lock
uv run <comando>   # executa dentro do venv gerenciado pelo uv
```

## 2. IA / Agentes

| Item | Escolha | Motivo |
|---|---|---|
| Framework de agentes | **Google ADK**, série 2, `>=2.2.0` | Exigência do enunciado; fixar versão exata no `pyproject.toml` |
| Modelo de linguagem | **Gemini** (Google AI Studio) | Exigência do enunciado; modelo por agente é decisão livre — escolher conforme limites vigentes no AI Studio |
| Chave de API | `GOOGLE_API_KEY` (ou variável equivalente exigida pelo ADK) | Nunca versionada — só em `.env`, listada sem valor em `.env.example` |
| Ferramenta de depuração | `adk web` | Melhor lugar para observar transferências entre agentes, tool calls e pedidos de confirmação durante o desenvolvimento (ver [plan.md §4](plan.md#4-riscos-e-pontos-de-atenção)) |

## 3. Framework web

| Item | Escolha | Motivo |
|---|---|---|
| Framework | **FastAPI** | Livre por enunciado; usado no curso, integra bem com `async`/`Runner` do ADK |
| Servidor ASGI | **uvicorn** | Padrão para servir FastAPI |
| Padrão de execução | `async` end-to-end nas rotas de conversa | Exigido pela integração com `Runner`/`App` do ADK |

## 4. Persistência

| Item | Escolha | Motivo |
|---|---|---|
| Sessões do ADK (eventos, state) | `DatabaseSessionService` do ADK sobre **SQLite** | Satisfaz Garantia 3 (nada se perde no reinício); combinação citada no enunciado como testada com sucesso para retomada de confirmação |
| Dados do condomínio (reservas/visitantes) | Tabelas próprias no **mesmo SQLite** (`reservas`, `visitantes`) | Simplicidade (um único arquivo de banco); permite `UNIQUE(area, data)` para Garantia 5 |
| Dados de referência (apartamentos/áreas) | Lidos direto de `dados/apartamentos.json` e `dados/areas.json` | Arquivos imutáveis do repositório base — não precisam de tabela própria |
| Regulamento | `dados/regulamento.md`, indexado em memória/por seção na inicialização | Base para a tool de busca da Garantia 4; nunca persistido no histórico da sessão |

Observação: `dados/*.json` e `dados/regulamento.md` **nunca são escritos** pela aplicação — são só fonte de carga inicial e de restauração.

## 5. Concorrência e idempotência (Garantia 5)

- Constraint de unicidade no SQLite: `UNIQUE(area, data)` sobre reservas ativas (ex.: índice parcial filtrando `cancelada = 0`, ou coluna de status na chave).
- Gravação via `INSERT` atômico dentro de transação; conflito de unicidade tratado como recusa normal (sem 500).
- SQLite em modo padrão já serializa escritas por conexão/arquivo, o que favorece esse padrão de "insert e trata conflito" sem precisar de lock externo.

## 6. Variáveis de ambiente (`.env.example`)

| Variável | Descrição |
|---|---|
| `GOOGLE_API_KEY` | Chave do Google AI Studio para os modelos Gemini |
| `DATABASE_URL` (ou caminho fixo, ex. `sqlite:///./data/aurora.db`) | Localização do arquivo SQLite usado por sessões + dados do condomínio |
| `PORT` (opcional, default `8000`) | Porta da API, deve responder em `http://localhost:8000` |

`.env` fica fora do Git (`.gitignore` já herdado do repositório base); `.env.example` versiona só os nomes.

## 7. Comandos de operação (a documentar no README final)

| Comando | Função |
|---|---|
| `uv sync` | Instala dependências |
| `uv run scripts/restaurar_dados.py` (nome ilustrativo) | Restaura reservas/visitantes ao estado de `dados/*.json` |
| `uv run uvicorn src.api.main:app --port 8000` (nome ilustrativo) | Sobe a API em `http://localhost:8000` |

Nomes exatos de módulos/scripts serão ajustados durante a implementação (ver estrutura de pastas em [plan.md §2](plan.md#2-estrutura-de-projeto-proposta)); esta tabela documenta a **intenção** de cada comando para orientar o README final.

## 8. Fora do escopo da stack

- Containers/serviços externos: não são necessários com SQLite local; se algo mudar durante a implementação (ex.: adotar Postgres em container), documentar o comando de subida no README, conforme permitido pelo enunciado.
- Frontend/UI: fora de escopo (entrega é só a API).
- Testes automatizados e deploy: fora de escopo do desafio.
