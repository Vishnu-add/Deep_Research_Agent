# Deep Research Agent — Frontend

Vue 3 chat UI for the FastAPI Deep Research Agent. Streams a LangGraph workflow's reasoning and final answer through an internal Nitro proxy.

## Stack

- Vue 3, Vite, Nuxt UI v4
- Nitro server routes
- AI SDK (`@ai-sdk/vue`)
- Drizzle ORM + SQLite
- Ollama for title generation and model listing

## Prerequisites

- Node.js 20+
- Backend on `:8001` (see `../backend/README.md`)
- Ollama with a chat model pulled:
  ```bash
  ollama pull qwen3:8b
  ```

## Setup

```bash
pnpm install   # or: npm install / bun install
```

Migrations auto-run on dev start (`server/plugins/migrations.ts`).

## Env

Copy `.env.example` to `.env` and set:

```
SESSION_SECRET                 # 32+ chars
GITHUB_OAUTH_CLIENT_ID
GITHUB_OAUTH_CLIENT_SECRET
```

Optional overrides:

```
RESEARCH_BACKEND_URL=http://localhost:8001/get_stream
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TITLE_MODEL=qwen3:8b
```

GitHub OAuth callback: `http://localhost:3000/auth/github`.

## Dev

```bash
pnpm dev    # or: npm run dev / bun run dev
```

Backend:

```bash
cd ../backend && poetry run uvicorn src.backend.app:app --port 8001 --reload
```

## Typecheck / lint

```bash
pnpm typecheck
pnpm lint
```

## Layout

- `server/routes/api/research/[id].post.ts` — proxy to FastAPI, maps `{thinking, final_answer}` events to AI SDK `reasoning-*` / `text-*` parts.
- `server/routes/api/models.get.ts` — proxies Ollama `/api/tags`.
- `src/components/chat/ReasoningSteps.vue` — emits `<step>` HTML.
- `src/components/chat/ReasoningComark.ts` — `defineComarkComponent({ step: ReasoningStep })`.
- `src/components/chat/RotatingIndicator.vue` — cycles gerunds while streaming.
