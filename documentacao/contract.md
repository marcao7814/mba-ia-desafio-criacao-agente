# Contrato da API — Assistente Residencial Aurora

> Fonte: `documentacao/solcitacao.md`. Este documento formaliza **apenas o contrato de API** que a correção usa. Nenhuma rota, campo, formato ou código de status aqui descrito pode ser alterado — a avaliação depende exatamente disto.

## Convenções gerais

- Todas as rotas recebem e devolvem **JSON**.
- Rotas com `{session_id}` no caminho devolvem **404** quando a sessão não existe.
- Datas nas rotas de verificação usam o formato **AAAA-MM-DD**.
- API responde em `http://localhost:8000`.

---

## 1. Criar sessão

```
POST /sessoes
```

**Request**
```json
{"apartamento": "101"}
```

**Response — 201**
```json
{"session_id": "..."}
```

Notas:
- O apartamento é definido **uma única vez**, na criação da sessão, e representa o morador autenticado (Garantia 2).
- Apartamento que não existe em `dados/apartamentos.json`: comportamento livre (fora de escopo).

---

## 2. Enviar mensagem

```
POST /sessoes/{session_id}/mensagens
```

**Request**
```json
{"texto": "Quero reservar o salão de festas para 2030-04-20"}
```

**Response — 200**
```json
{
  "resposta": "...",
  "confirmacoes_pendentes": [
    {
      "id": "...",
      "acao": "...",
      "detalhes": {"area": "salao-de-festas", "data": "2030-04-20"}
    }
  ]
}
```

Notas:
- `resposta` pode ser string vazia quando a execução parou esperando confirmação.
- `confirmacoes_pendentes` lista **todas** as confirmações pendentes da sessão no momento da resposta; lista vazia quando não há nenhuma.
- O conteúdo de `acao` e as chaves dentro de `detalhes` são livres — o exemplo é apenas ilustrativo.
- 404 se `session_id` não existir.
- Nova mensagem enviada enquanto existe confirmação pendente: comportamento livre, desde que nada execute sem confirmação.

---

## 3. Responder confirmação

```
POST /sessoes/{session_id}/confirmacoes
```

**Request**
```json
{"id": "...", "confirmado": true}
```

**Response — 200** (mesmo formato da rota de mensagens)

**Response — 409** — não existe confirmação pendente com esse `id` nesta sessão (inclui id de confirmação já respondida, ou id inexistente). Nada é executado.

Notas:
- Aprovar (`confirmado: true`) executa a ação **uma única vez**.
- Negar (`confirmado: false`) não altera nada.
- 404 se `session_id` não existir; 409 se o `id` não estiver pendente **nessa** sessão.

---

## 4. Ver eventos da sessão

```
GET /sessoes/{session_id}/eventos
```

**Response — 200**
```json
[ /* todos os eventos gravados na sessão, em ordem, com o conteúdo completo de cada um */ ]
```

404 se a sessão não existir.

---

## 5. Rotas de verificação

Leem os dados do condomínio **direto**, sem passar pelo modelo. Em produção ficariam atrás de acesso administrativo; aqui existem para o avaliador conferir efeitos de conversas.

```
GET /apartamentos/{numero}/reservas
```
**Response — 200**
```json
[{"codigo": "RSV-1377", "area": "quadra", "data": "2030-03-09"}]
```

```
GET /apartamentos/{numero}/visitantes
```
**Response — 200**
```json
[{"nome": "Marina Duarte", "data": "2030-03-16"}]
```

Notas:
- Apartamento que não existe em `dados/apartamentos.json`: comportamento livre.
- Datas no formato `AAAA-MM-DD`.

---

## Fora de escopo do contrato

- Interface visual (só API).
- Autenticação (o apartamento da criação de sessão já representa o morador autenticado).
- Pagamento/estorno.
- Regras de antecedência, datas passadas, horários de uso, capacidade das áreas.
- Duas respostas simultâneas para a mesma confirmação (comportamento livre; reenvio sequencial segue a Garantia 1).
- Tom/redação das respostas, fora dos pontos explicitamente conferidos no fluxo do avaliador.
