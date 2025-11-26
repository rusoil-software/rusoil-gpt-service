Petra is a Dockerized GPT Service developed in Ufa State Petroleum Technological University

Short pointer:

- Conventions: see `doc/conventions.md` for the concise contributor checklist and rules.

See `doc/vision.md` for the living technical blueprint and rationale.

Embeddings
----------

This project exposes simple embedding endpoints for examples and unit tests.

- POST /embeddings — create a single embedding for text.
- POST /embeddings/batch — create embeddings for many texts.
- POST /embeddings/chunk — split a long text into chunks and embed each chunk.

See `docs/embeddings.md` for examples and Prometheus metric descriptions.
