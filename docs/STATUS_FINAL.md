# Status técnico — mega fase

## Objetivo
Levar a plataforma ao maior nível funcional possível em uma única rodada, com piso de 80%, meta de 90% e objetivo de 99%.

## Entregas integradas
- aplicação Flask preservada e ampliada;
- persistência JSON e compatibilidade legada;
- memória persistente e recuperação;
- runtime determinístico e simulação autônoma;
- decisões de NPC baseadas em necessidades, objetivos e rotina;
- eventos, agenda e ledger causal;
- auditoria de invariantes do mundo;
- população e demografia básica;
- economia, preços, produção, estoque e transações;
- clima;
- sociedade, relações e diplomacia;
- combate baseado em atributos observáveis;
- snapshots e backups com hashes/manifestos;
- RAG por fontes, chunks, busca e citações;
- ingestão de PDF/DOCX/TXT/MD/HTML/JSON/CSV;
- camadas de memória;
- guard e ferramentas nativas do agente;
- APIs v2 integradas;
- testes unitários, integração e longa duração;
- Docker/Gunicorn;
- CI com compilação, testes, smoke import e build do container.

## Gate de qualidade
O percentual final não é aumentado apenas por quantidade de código. Uma capacidade conta quando está implementada, integrada e coberta por teste/verificação.

## Riscos residuais
- a execução efetiva da CI precisa ser observada pelo GitHub;
- um provedor LLM depende de configuração local e modelo disponível;
- embeddings densos/reranking podem ser aprimorados além do índice lexical atual;
- mapas, editor e painéis administrativos ainda precisam de refinamento de produto;
- autenticação/autorização e hardening adicional são necessários para exposição pública;
- testes de carga e recuperação de falhas em escala ainda precisam de execução real.
