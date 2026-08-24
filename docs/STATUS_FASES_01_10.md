# Status — Fases 01 a 10

> Estado: **implementadas na branch `feature/rpg-ai-foundation`**. A conclusão funcional final depende da execução da CI no GitHub e dos testes de integração com um servidor Ollama disponível.

## Fase 01 — Fundação
- Arquitetura, requisitos, ambiente, CI, `.env.example` e plano de 250 etapas.
- Baseline preservada; sem reescrita destrutiva da aplicação original.

## Fase 02 — Contratos e persistência base
- Modelos Python para mundo, mensagem, memória e evento.
- `JsonStore` com escrita atômica, fsync e proteção contra path traversal.
- Repositories de mundos/chats.
- Compatibilidade de leitura com a pasta legada `chat/`.

## Fase 03 — Memória
- Memórias persistentes em JSON.
- Importância, tags, origem, validade e timestamps.
- Deduplicação por hash.
- Recuperação lexical.
- Construção de contexto com orçamento de caracteres.

## Fase 04 — Motor temporal e eventos
- Relógio monotônico.
- Avanço temporal sem retrocesso.
- Eventos persistentes no estado do mundo.
- Versionamento do estado após mutações do motor.

## Fase 05 — Entidades e NPCs
- Entidades persistentes.
- Atributos, estado, relações, objetivos, rotina e memória.
- Seleção de ação de NPC limitada às ações realmente disponíveis.

## Fase 06 — Sociedade e economia
- Recursos finitos.
- Estoques e preços.
- Transações com verificação de saldo.
- Relações direcionais.
- Grupos/facções iniciais.

## Fase 07 — Orquestração da IA
- Cliente LLM isolado.
- Ollama configurável por ambiente.
- Orquestrador separado do motor de simulação.
- Contexto persistente antes da inferência.

## Fase 08 — Ferramentas
- Registro tipado de ferramentas.
- Schemas de parâmetros.
- Ferramentas nativas de avanço temporal e memória.
- Endpoint administrativo para inspeção/execução.

## Fase 09 — Recuperação híbrida
- Ranking lexical local.
- Importância de memória integrada ao ranking.
- Interface preparada para adicionar embeddings sem tornar embeddings obrigatórios.

## Fase 10 — Interface e integração
- Interface slim existente preservada.
- Seletor de mundos/chats conectado ao backend.
- Painel de memória conectado à persistência.
- Streaming SSE da resposta do LLM.
- Cancelamento de geração.
- Atalhos e preferências locais.
- Tratamento de estados vazios/erros.

## Auditoria de encerramento das 10 fases

### Passagem 1 — Estrutura
Verificados módulos, responsabilidades, imports e separação entre API, memória, engine, IA e tools.

### Passagem 2 — Dados
Verificados IDs, JSON, escrita atômica, compatibilidade legada e persistência de mensagens/memórias.

### Passagem 3 — Causalidade
Verificados avanço temporal monotônico, eventos, recursos finitos e separação entre LLM e estado do mundo.

### Passagem 4 — Integração
Verificados endpoints, streaming, frontend, memória, repositories e ferramentas.

### Passagem 5 — Regressão e segurança básica
Verificados validação de IDs, path traversal no storage, erros de API, saldo/estoque e suíte de testes.

## Pendências deliberadas
Estas fases estabelecem a fundação. Ainda não são consideradas completas as capacidades avançadas previstas nas etapas 101–250, como combate físico detalhado, clima, famílias, governos, RAG vetorial real, planner multi-tool, snapshots/rollback, mapas e editores completos. Elas permanecem no plano para as fases seguintes.
