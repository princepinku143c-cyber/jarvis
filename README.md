# JARVIS

A modular, self-hostable personal AI assistant designed for VPS deployment, real-time voice, browser automation, persistent memory, scheduled tasks, and safe tool orchestration.

## Design goals

- **Local-first runtime:** core orchestration runs on the user's VPS.
- **Provider-agnostic models:** OpenAI-compatible providers can be swapped without rewriting the assistant.
- **Real-time voice:** STT → agent → TTS pipeline with streaming-friendly interfaces.
- **Browser automation:** Playwright-based headless browser with screenshots and post-task evidence.
- **Persistent memory:** SQLite-backed durable memory with explicit importance and pruning.
- **Safety:** allowlisted tools, confirmation gates for risky actions, secret-free logs.
- **Observable:** health checks, structured events, task IDs, and deterministic tests.
- **Deployable:** Docker Compose for VPS; frontend can later be deployed to Vercel.

## Architecture

```text
                 ┌──────────────────────────┐
                 │ Web / Voice / Telegram UI │
                 └────────────┬─────────────┘
                              │
                       WebSocket / HTTP
                              │
                 ┌────────────▼─────────────┐
                 │      JARVIS Gateway      │
                 │ auth · sessions · events │
                 └────────────┬─────────────┘
                              │
              ┌───────────────┼────────────────┐
              │               │                │
        ┌─────▼─────┐   ┌────▼─────┐    ┌────▼─────┐
        │ Agent Core │   │  Memory  │    │ Scheduler │
        └─────┬─────┘   └──────────┘    └───────────┘
              │
       ┌──────┼───────────────┐
       │      │               │
 ┌─────▼──┐ ┌─▼────────┐ ┌────▼─────┐
 │ Models │ │ Browser  │ │ Tool Bus  │
 │ adapter│ │ Playwright│ │ allowlist │
 └────────┘ └──────────┘ └───────────┘
```

## Repository layout

- `apps/api` — FastAPI gateway and orchestration API
- `apps/web` — frontend shell (Vercel-ready later)
- `packages/jarvis_core` — agent, memory, models, browser, tools and events
- `tests` — unit/integration tests
- `deploy` — Docker/VPS deployment assets
- `.env.example` — documented configuration template; **never commit secrets**

## Quick start

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```

Health check: `GET /health`.

## Security

JARVIS intentionally does not contain real API keys. Put secrets in the deployment environment. Tool execution uses explicit allowlists and confirmation requirements for destructive/external actions.

## Status

This repository is the **foundation build**. External integrations (Composio, MCP, Gmail, GitHub SaaS actions, etc.) are intentionally adapters, not hard-coded into the core.
