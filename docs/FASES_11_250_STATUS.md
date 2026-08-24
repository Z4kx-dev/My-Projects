# Fases 11–250 — implementação e critérios

Este documento é o contrato de conclusão das etapas restantes. Cada etapa só é marcada como concluída quando possui código integrado, teste/regra verificável e revisão de regressão.

## 11–40 — mundo persistente
- 11 migrações versionadas
- 12 validação de schema na escrita
- 13 snapshots
- 14 restauração segura
- 15 auditoria append-only
- 16 relógio persistente
- 17 agenda de eventos
- 18 grafo causal
- 19 locais e rotas
- 20 clima
- 21 necessidades biológicas
- 22 população
- 23 famílias
- 24 relações direcionais
- 25 governos
- 26 leis
- 27 tesouro
- 28 estoques
- 29 receitas de produção
- 30 profissões
- 31 preços
- 32 comércio
- 33 transporte
- 34 infraestrutura
- 35 saúde
- 36 educação
- 37 segurança
- 38 diplomacia
- 39 migração
- 40 ciclo diário

## 41–80 — NPCs e sociedade
Objetivos, memória episódica, personalidade, hábitos, rotinas, necessidades, vínculos, famílias, reputação, ocupação, patrimônio, aprendizado, envelhecimento, doença, morte, nascimento, conflitos, grupos, culturas, idiomas, religião, educação, crime, justiça e reação coletiva.

## 81–120 — simulação econômica e política
Mercados, oferta/demanda, salários, inflação, impostos, orçamento, dívida, comércio regional, produção, consumo, agricultura, mineração, manufatura, logística, estradas, preços locais, escassez, choques, guerras, sanções, tratados, sucessão, eleições quando aplicáveis, legislação e instituições.

## 121–150 — IA e memória avançada
Orquestração multi-etapa, planner, seleção de ferramentas, validação de argumentos, pós-validação, recuperação híbrida, embeddings substituíveis, sumarização hierárquica, memória episódica/semântica/procedural, consolidação, esquecimento controlado, detecção de contradição, fontes, citações internas, contexto por escopo, compressão e orçamento de tokens.

## 151–175 — Notebook/RPG workspace
Upload de documentos, extração de texto, indexação, coleções, fontes por mundo, pesquisa, perguntas sobre fontes, notas, citações, diário, linha do tempo, entidades, relações, busca global, importação/exportação e histórico.

## 176–205 — interface
Sidebar de mundos/chats, chat, composer, streaming, HUD, painel de estado, memória, fontes, NPCs, mapa, economia, política, diário, missões, inventário, configurações, atalhos, responsividade, acessibilidade, temas, estados de carregamento, erros e recuperação.

## 206–225 — segurança e operação
Segredos por ambiente, permissões, limites, validação de entrada, path traversal, auditoria, rate limiting, timeout, retries, circuit breaker, logs estruturados, métricas, health checks, backups, restauração, migrações e diagnóstico.

## 226–240 — qualidade
Testes unitários, integração, API, persistência, propriedade, simulação determinística, cenários de longa duração, concorrência, regressão de UI, testes de carga, fuzzing de schemas, consistência temporal, invariantes econômicas e auditoria de dados.

## 241–250 — lançamento
Empacotamento, documentação, configuração inicial, seed de mundo, instalação local, modo offline quando suportado, observabilidade, smoke test, teste de recuperação, revisão de segurança, revisão de performance, checklist de release, versão e conclusão.

> O estado deste documento é deliberadamente separado do plano: não declarar uma etapa como concluída apenas por existir um arquivo ou classe. A integração real precisa ser exercitada pelos testes e pela aplicação.
