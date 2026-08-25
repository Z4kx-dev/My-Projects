# Internet da Korczak AI

A Korczak AI usa ferramentas do agente para pesquisar e abrir páginas da internet. O backend suporta dois provedores:

- `Tavily`: recomendado para agentes; oferece Search e Extract.
- `Brave Search API`: alternativa para busca web.

## Configuração

Copie `.env.example` para `.env` e configure pelo menos uma chave:

```env
RPG_WEB_PROVIDER=tavily
TAVILY_API_KEY=...
```

Ou:

```env
RPG_WEB_PROVIDER=brave
BRAVE_SEARCH_API_KEY=...
```

Nunca coloque a chave no código ou no frontend.

## Ferramentas do agente

`buscar_na_web`
- recebe `query`, `limit` e opcionalmente `domain`;
- retorna URL, título, trecho, score e origem.

`abrir_pagina_web`
- recebe uma URL HTTP/HTTPS;
- usa extração Tavily quando disponível;
- pode usar abertura direta como fallback;
- limita tamanho e timeout.

## Diagnóstico

```text
GET /api/web/status
```

Exemplo:

```json
{
  "enabled": true,
  "provider": "tavily",
  "tavily": true,
  "brave": false
}
```

`GET /api/health` também inclui o estado web.

## Comportamento esperado

A IA deve pesquisar quando a solicitação exigir informação atual, externa ou verificável. Para conhecimento estável, memória local e documentos do Notebook, a busca web não deve ser usada desnecessariamente.

Conteúdo obtido da web é tratado como dado externo, não como instrução de sistema. Páginas podem conter prompt injection e nunca devem alterar a hierarquia de instruções da Korczak AI.
