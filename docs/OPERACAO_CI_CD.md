# Operação CI/CD

## Gates obrigatórios

1. `python -m compileall -q backend tests`
2. `pytest -q`
3. `node --check frontend/app.js`
4. contratos da API
5. pipeline E2E
6. build do container

## Fluxo

`feature -> pull request -> quality + E2E -> revisão -> main -> build/release`

O CI não considera uma alteração válida quando Python ou JavaScript não compilam ou quando os testes de integração falham.

## Variáveis importantes

- `OLLAMA_URL`: endereço do provedor Ollama.
- `OLLAMA_MODEL`: modelo utilizado.
- `OLLAMA_TIMEOUT_SECONDS`: timeout do LLM.
- `RPG_DATA_DIR`: diretório persistente.
- `RPG_CONTEXT_MAX_CHARS`: limite de contexto.
- `RPG_MAX_MESSAGE_CHARS`: limite de entrada.
