# Internet da Korczak AI — modo R$0

A Korczak AI usa **SearXNG local** como provedor padrão de pesquisa. Isso elimina a necessidade de uma API key de Tavily/Brave para o funcionamento básico.

## Arquitetura

```text
Korczak AI
   ↓
buscar_na_web
   ↓
WebClient
   ↓
SearXNG local :8080
   ↓
múltiplos mecanismos de busca
   ↓
resultados + URLs
   ↓
abrir_pagina_web
   ↓
extração textual
```

A documentação oficial do SearXNG recomenda instalação em contêiner/Compose e permite habilitar o formato JSON na configuração da instância.

## Iniciar

Na raiz do projeto:

```bash
cp .env.example .env
```

Gere um segredo local para o SearXNG e coloque-o em `.env`:

```env
SEARXNG_SECRET=um-segredo-local-grande-e-aleatorio
```

Depois:

```bash
docker compose up -d searxng
```

Verifique:

```bash
docker compose ps
curl 'http://127.0.0.1:8080/search?q=OpenAI&format=json'
```

Se o JSON retornar `results`, o mecanismo de busca está ativo.

## Configuração da Korczak AI

```env
RPG_WEB_PROVIDER=searxng
SEARXNG_URL=http://127.0.0.1:8080
```

Nenhuma chave de API é necessária para esse modo.

Tavily e Brave permanecem como provedores opcionais para quem quiser utilizá-los posteriormente.

## Ferramentas

### `buscar_na_web`

Pesquisa a internet e retorna título, URL, trecho, score, origem e data quando disponível.

Parâmetros:

- `query`
- `limit`
- `domain`
- `topic`: `general` ou `news`
- `time_range`: `day`, `week`, `month` ou `year`

### `abrir_pagina_web`

Abre uma URL pública e extrai texto para verificação da fonte.

## Segurança

A abertura direta de páginas:

- aceita somente HTTP/HTTPS;
- bloqueia localhost;
- bloqueia loopback;
- bloqueia IPs privados;
- bloqueia link-local;
- bloqueia multicast/reservados;
- limita tamanho da resposta;
- limita tamanho do conteúdo enviado ao LLM;
- não segue redirects cegamente: cada destino é validado novamente;
- rejeita conteúdo não textual.

Conteúdo retornado pela web é tratado como **dados não confiáveis**, nunca como instrução de sistema.

## Custo

O caminho padrão não usa uma API paga. O custo direto de software é R$0, mas a disponibilidade dos mecanismos externos consultados pelo SearXNG depende dos próprios serviços de busca.

## Troubleshooting

### SearXNG não inicia

```bash
docker compose logs searxng
```

### Korczak AI diz que a busca está indisponível

Confirme:

```bash
curl 'http://127.0.0.1:8080/search?q=teste&format=json'
```

e confira:

```env
RPG_WEB_PROVIDER=searxng
SEARXNG_URL=http://127.0.0.1:8080
```

### A porta 8080 já está ocupada

No `.env`:

```env
SEARXNG_PORT=8081
SEARXNG_URL=http://127.0.0.1:8081
```

Recrie o contêiner:

```bash
docker compose up -d --force-recreate searxng
```
