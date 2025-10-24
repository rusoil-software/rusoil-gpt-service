# Test templates (concise)

Purpose: provide tiny, copy-paste test templates for contributors. Keep tests fast and focused (happy path + 1 edge case). See `doc/conventions.md` for test policy and `doc/vision.md` for architecture context — do not duplicate those files here.

Where to put tests
- Prefer `tests/` at repository root for general-purpose code.
- For scoped directories use: `backend/tests/`, `frontend/__tests__/` or `frontend/tests/`.

Naming patterns our CI looks for
- `tests/` folder
- `__tests__/` folders
- `*.test.*` or `*.spec.*` (e.g., `example.test.ts`, `module.spec.js`)

Python (pytest) — minimal example

```python
# tests/example_pytest.py
def test_example_happy_path():
    assert 1 + 1 == 2

def test_example_edge_case():
    assert 0 == 0
```

Jest + TypeScript — minimal example

```ts
// tests/example.test.ts
import { describe, test, expect } from '@jest/globals';

describe('example suite', () => {
  test('happy path', () => {
    expect(1 + 2).toBe(3);
  });
});
```

Quick run hints
- Python: run `pytest -q` (install via your preferred env manager).
- JS/TS: run `npm test` or `pnpm test` (ensure `jest` is installed in devDependencies).

Guidance (KISS)
- Keep tests small and deterministic. Avoid network calls, long-running steps, or heavy models in unit tests.
- Each PR that changes code should include a fast unit test (happy path + one edge case) — the CI will check for this.
- If tests require fixtures or setup, prefer small fixtures or use mocks to keep tests fast.

If you need more examples (UI testing, E2E, performance), add them to `doc/vision.md` or create a separate `doc/test-examples.md` — keep this file the quick copy/paste reference.
