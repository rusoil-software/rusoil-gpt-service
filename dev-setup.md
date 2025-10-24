# Developer setup (minimal)

Quick instructions to run the provided unit tests locally. These commands are intentionally small and work on Windows PowerShell (the repository is local-first). If you use another shell, adapt the activate command for Python venv.

Node / Jest (TypeScript)

1. Ensure Node.js 18+ (Node 20 recommended) is installed. Check with:

```powershell
node --version
```

2. Install dependencies and run tests:

```powershell
npm install
npm test
```

If you prefer pnpm (recommended for faster installs):

```powershell
npm install -g pnpm
pnpm install
pnpm test
```

Python / pytest

1. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```

2. Install pytest and run tests:

```powershell
python -m pip install -U pip pytest
pytest -q
```

Notes
- The repo includes minimal templates for Jest/TS and pytest under `tests/` to help when adding tests. Keep unit tests fast and deterministic (no network calls, no heavy models).
- If you need Node version management, consider installing Volta (https://volta.sh/) or nvm for Windows.
