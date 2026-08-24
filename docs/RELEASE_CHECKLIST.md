# Checklist de release

## Gates obrigatórios
- [x] Compilação Python
- [x] Sintaxe JavaScript
- [x] Testes unitários
- [x] Contratos HTTP
- [x] Persistência JSON
- [x] RAG básico
- [x] CRUD de memória
- [x] CRUD de fontes
- [x] Pipeline E2E de contexto
- [x] Validação de identificadores
- [ ] Execução E2E com provedor Ollama real
- [ ] Cancelamento HTTP real verificado em runtime
- [ ] CI confirmado verde após o último commit
- [ ] Autenticação/autorização de produção
- [ ] Rate limiting de produção
- [ ] Observabilidade e métricas
- [ ] Backup/restore E2E
- [ ] Teste de simulação prolongada

## Critério de conclusão
O projeto só deve ser marcado como 100% quando todos os gates acima estiverem verdes e os testes de execução real forem reproduzíveis em CI ou ambiente de staging.
