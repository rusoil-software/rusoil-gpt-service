# Embeddings

This document describes the embedding-generation endpoints, examples, and usage.

## Endpoints

- POST /embeddings
  - Single-text embedding
  - Request: {"input": "some text"}
  - Response: {"embedding": [float, ...]}

- POST /embeddings/batch
  - Batch embeddings
  - Request: {"inputs": ["text1", "text2"]}
  - Response: {"embeddings": [[float,...],[float,...]]}

- POST /embeddings/chunk
  - Chunk a long text and create embeddings for each chunk
  - Query params: chunk_size (default 512), overlap (default 64)
  - Request: {"input": "long text..."}
  - Response: {"embeddings": [[float,...], ...]}

## Examples

### Python (single)

```python
import requests
r = requests.post('http://localhost:8000/embeddings', json={'input': 'Hello world'})
print(r.json())
```

### Curl (batch)

```bash
curl -X POST -H "Content-Type: application/json" -d '{"inputs": ["a","b"]}' http://localhost:8000/embeddings/batch
```

## Metrics

When `METRICS_ENABLED` is true, the following Prometheus metrics are exposed on `/metrics`:

- embedding_requests_total{type="single|batch|chunk",status="ok|error"}
- embedding_latency_seconds{type="single|batch|chunk"}
- embedding_batch_size_distribution (histogram)
- embedding_chunk_count (counter)

These metrics help monitor throughput, latency and batch sizes.
