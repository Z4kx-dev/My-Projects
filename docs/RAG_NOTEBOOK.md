# RAG e Notebook por mundo

## Objetivo

Cada mundo possui um workspace documental isolado em `data/notebooks/<world_id>`.
A fonte documental é persistida separadamente do chat e do estado do mundo.

## Pipeline

```text
arquivo/texto
  -> normalização
  -> chunks determinísticos
  -> índice vetorial local
  -> busca lexical/TF-IDF
  -> citações rastreáveis
  -> contexto para o LLM
```

## Formatos atuais

O núcleo aceita UTF-8 em TXT, Markdown, HTML, JSON e CSV. PDF/DOCX não são aceitos como texto bruto: devem receber adaptadores de extração específicos antes de entrarem no índice. Isso evita tratar binário como texto silenciosamente.

## API

- `GET /api/v2/worlds/<id>/rag/sources`
- `GET /api/v2/worlds/<id>/rag/search?q=...`
- `GET /api/v2/worlds/<id>/rag/context?q=...`
- `POST /api/v2/worlds/<id>/rag/source`
- `POST /api/v2/worlds/<id>/rag/upload`

## Isolamento

O índice, as fontes e os metadados são associados ao `world_id`. Um notebook não deve consultar documentos de outro mundo sem uma operação explícita de importação/cópia.

## Próxima evolução

A interface `VectorStore` deve permanecer estável quando o projeto receber embeddings densos, banco vetorial e reranking. O backend atual é deliberadamente local e determinístico para facilitar testes e recuperação offline.
