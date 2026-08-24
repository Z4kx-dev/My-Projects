# Status técnico — plataforma RPG AI

## Objetivo
Construir uma plataforma de RPG persistente inspirada na experiência de chat + notebook de fontes, com o LLM separado do estado determinístico do mundo.

## Implementado nesta branch

- aplicação Flask existente preservada;
- persistência JSON e compatibilidade com dados legados;
- memória persistente e recuperação lexical existente;
- runtime determinístico para entidades e passagem de tempo;
- eventos e agenda futura;
- ledger causal;
- invariantes de estado;
- necessidades biológicas básicas;
- economia de oferta/demanda e transação;
- combate baseado em atributos observáveis;
- população;
- clima;
- geografia e cálculo de viagem;
- sociedade;
- diplomacia e pressão de guerra;
- missões;
- snapshots com hash SHA-256;
- RAG local por chunking e índice lexical;
- camadas de memória episódica, semântica, procedural, social, estado e mundial;
- guard de ferramentas e detector de contradições;
- API v2 integrada ao Flask;
- testes unitários das novas camadas.

## Limitações declaradas

Esta branch não deve ser chamada de produto 100% concluído enquanto não houver:

1. execução comprovada da CI;
2. ingestão de PDF/DOCX com extração de páginas;
3. embeddings e índice vetorial persistente;
4. reranking híbrido real;
5. autenticação/autorização;
6. UI completa para fontes, entidades, mapas e estado;
7. simulação populacional de longa duração validada;
8. sistema de arquivos seguro e uploads;
9. observabilidade e métricas;
10. testes de carga e recuperação após falhas;
11. empacotamento e instalação reproduzível.

## Regra de qualidade
Nenhuma funcionalidade deve ser marcada como concluída apenas por possuir uma classe ou endpoint. Ela precisa estar integrada, testada e documentada.

## Próximo gate
Executar a suíte completa, corrigir todas as regressões, depois validar um mundo por 1 dia, 1 mês, 1 ano e 10 anos simulados.
