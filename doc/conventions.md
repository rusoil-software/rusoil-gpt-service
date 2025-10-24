Conventions — minimal rules for code assistants and contributors

These conventions are intentionally short and KISS. They point to the living technical blueprint in `doc/vision.md` for background and rationale; do not duplicate that file here. Follow these rules to keep code quality high and changes reviewable.

- Canonical source: `doc/vision.md` is the single source of architectural choices. When in doubt, follow it and link back to it in PRs.

- Small, incremental changes: prefer tiny, focused PRs (single concern). Each PR should be easy to review and revert.

- Tests: every new feature or bugfix must include fast unit tests (happy path + 1 edge case). CI must pass before merging.

- Types and linting:
  - Python: use type hints everywhere public (mypy-friendly). Keep function signatures explicit.
  - TypeScript: enable strict mode and prefer explicit types for exported shapes.
  - Keep formatting consistent (use repository formatters; run them in CI).

- Configuration: use the central Pydantic settings object (`backend/app/core/settings.py`) and environment-first configuration. Do not hard-code secrets or env-specific values in code.

- Logging & observability: emit structured JSON logs and include request_id/span when applicable. See `doc/vision.md` for logging and metrics guidance.

- Secret handling: never commit secrets. Use environment variables, secret manager, or CI secrets. Add `.env.example` for required keys (no real secrets).

- Dependencies:
  - Declare dependencies in the project manifest and keep a lockfile. Prefer reproducible installs (lock + pinned versions).
  - Upgrade dependencies in a dedicated PR with test verification.

- Docker & images: build multi-stage images, keep them minimal, do not bake secrets into images. Images must pass the deterministic smoke test in CI (see CI workflow in `doc/vision.md`).

- Local-first model handling: prefer quantized, pinned models for local dev. Record model versions/paths in configuration (see RAG & model guidance in `doc/vision.md`).

- Data & migrations: for dev prefer SQLite; for prod use a real RDBMS and migrations. Always add migrations and tests for schema changes.

- Infrastructure & CI:
  - CI must be deterministic and network-independent where possible (use the smoke server pattern described in `doc/vision.md`).
  - Keep build steps cached and fast; tests should be parallel-friendly.

- Commits and PRs: write clear, focused commit messages. PR description must explain why (link to `doc/vision.md` when relevant), list changes, and include review/merge checklist.

- Reviews & merging: require at least one approving reviewer and green CI. Prefer incremental releases; avoid breaking changes without explicit version bump and migration notes.

- Documentation: update `doc/vision.md` for architecture or policy changes; keep `doc/conventions.md` short and stable. Add usage notes in-line in the code when necessary.

- Safety & privacy: minimize PII in logs and indexes; follow retention and deletion rules described in `doc/vision.md`.

If a rule needs expansion, add details to `doc/vision.md` and reference it here. Keep `doc/conventions.md` as the concise checklist for contributors and automated assistants.
