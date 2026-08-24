# Arquitetura da IA de RPG

## Objetivo
Construir uma IA de simulação persistente para RPG, com experiência inspirada em produtos de chat e pesquisa por fontes, mas especializada em mundos, memória, causalidade e continuidade.

## Camadas
1. **Interface** — chat, mundos, chats, painel de estado, memória, configurações, anexos, pesquisa, ferramentas e acessibilidade.
2. **API** — autenticação futura, sessões, streaming, CRUD de mundos/chats, uploads, exportação e observabilidade.
3. **Orquestrador** — recebe intenção, recupera contexto, seleciona ferramentas, executa simulação, valida fatos e persiste mudanças.
4. **Motor de mundo** — tempo, entidades, NPCs, economia, geografia, clima, relações, combate, saúde, produção, eventos e causalidade.
5. **Memória** — memória de curto prazo, episódica, semântica, factual, estado atual, histórico imutável e índices de recuperação.
6. **LLM** — camada abstrata para Ollama/local e provedores externos; modelo não é a fonte de verdade do mundo.
7. **Persistência** — JSON inicialmente; camada de repositório preparada para SQLite/PostgreSQL e armazenamento vetorial.
8. **Validação** — schemas, invariantes, versionamento, migrações, testes e auditoria.

## Princípio central
O LLM propõe ações e linguagem. O estado persistente do mundo decide o que é verdadeiro. Toda alteração de estado deve passar pelo motor e ser registrada como evento.

## Fluxo de uma ação
`entrada -> classificação -> recuperação -> regras -> simulação -> validação -> evento -> persistência -> resposta -> atualização de memória`

## Contratos fundamentais
- IDs estáveis para mundo, personagem, NPC, local, item, evento e chat.
- Datas em ISO 8601 internamente; calendário do mundo separado do relógio do sistema.
- Eventos append-only; correções geram novos eventos.
- Estado derivado pode ser reconstruído do histórico.
- JSON deve obedecer schemas versionados.
- Contexto enviado ao modelo deve ser mínimo, relevante e rastreável.
- Nenhum dado privado de NPC deve ser exposto ao jogador sem justificativa perceptiva.

## Módulos planejados
`core/`, `engine/`, `memory/`, `llm/`, `tools/`, `world/`, `storage/`, `schemas/`, `api/`, `tests/`, `frontend/`.

## Estratégia de evolução
A base atual continuará funcional durante a migração. Cada fase deve produzir um incremento executável, com testes e revisão antes da seguinte. Nenhuma grande reescrita será feita sem uma camada de compatibilidade.