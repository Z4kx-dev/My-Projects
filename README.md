# RPG Simulator

Simulador de RPG persistente para ChromeOS/Codespaces, com Flask, Ollama/Llama 3.1 e Carmilla.

## Arquitetura

```text
backend/                 API Flask e integração com Ollama
frontend/                interface web
guardian/                Carmilla, guardião da memória
data/mundos/             estado persistente dos mundos
tests/                   testes de fumaça
.github/workflows/       validação automática
```

Cada mundo possui um ID independente e seus próprios chats:

```text
data/mundos/
├── 001/                  # mundo real 001 (compatibilidade)
│   ├── mundo.json
│   ├── chat/             # chats 001, 002, ...
│   ├── personagem/
│   ├── npcs/
│   ├── politica/
│   ├── economia/
│   ├── diario/
│   └── eventos/
└── fantasia/
    └── 001/              # fantasia 001
```

IDs são usados como identidade; nomes são apenas apresentação.

## Rodar no Codespace

```bash
cd /workspaces/My-Projects
pip install -r backend/requirements.txt
ollama serve
ollama pull llama3.1
python3 backend/app.py
```

Abra a porta `8000` no navegador.

Se Ollama estiver em outro endereço:

```bash
export OLLAMA_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=llama3.1
```

## Memória

```text
mensagem → Flask → estado/memória/documento → Ollama → resposta
                                      ↓
                                   Carmilla
                                      ↓
                          memória persistente estruturada
```

A Carmilla valida as alterações antes de gravá-las e bloqueia caminhos fora das categorias autorizadas.

## API principal

- `GET /api/health`
- `GET /api/carmilla`
- `GET /api/worlds`
- `POST /api/worlds`
- `GET /api/worlds/<id>`
- `GET /api/worlds/<id>/chats`
- `POST /api/worlds/<id>/chats`
- `GET /api/worlds/<id>/chats/<chat>`
- `GET /api/worlds/<id>/memory`
- `GET /api/worlds/<id>/files`
- `POST /api/chat`

## Persistência futura

A memória fica separada do histórico e a arquitetura não acopla o frontend ao provedor do modelo. Isso permite migrar posteriormente a memória para Google Drive, banco de dados ou outro armazenamento sem reescrever a interface.
