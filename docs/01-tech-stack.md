# Document 1: Technology Stack

**Project:** Present Yourself — AI Slide Generation Platform
**Deployment Target:** Render
**Last Updated:** 2026-06-07

---

## 1. Stack Summary

| Layer | Choice | Why |
|---|---|---|
| Frontend framework | **Next.js 16 (App Router)** on React 19 | SSR/SSG, Server Components for fast first paint, mature ecosystem, Vercel/Render-friendly. |
| Language (FE) | **TypeScript 5.6** | Type safety across editor schema, IPC contracts, and API clients. |
| Styling | **Tailwind CSS v4 + shadcn/ui + Radix Primitives** | Speed of iteration, accessible primitives, design-token discipline. |
| Slide editor canvas | **Konva.js + react-konva** + **Zustand** (state) + **Immer** (immutable patches) | Konva handles GPU-accelerated 2D canvas; Zustand keeps editor state ergonomic without Redux ceremony. |
| Drag/drop | **dnd-kit** | Accessible, fast, supports slide reordering + asset dropping. |
| Rich text | **Tiptap (ProseMirror)** | Inline WYSIWYG inside slide text boxes with custom marks (color, font, list). |
| Forms / validation | **React Hook Form + Zod** | One schema (Zod) shared FE/BE for slide JSON + API payloads. |
| Backend framework | **FastAPI (Python 3.13)** | Async I/O for parallel research/AI/image fetches; Pydantic v2 matches the JSON schema spine. |
| Background workers | **Celery + Redis** (or **RQ** if simpler) | Generation jobs are long (10–45s) — must run off the request thread. |
| PPTX engine | **python-pptx** (server-side) | Battle-tested PPTX writer; full control over masters, layouts, shapes, themes. |
| PPTX parsing (template clone) | **python-pptx** + **lxml** | Read masters/layouts, extract theme XML, colors, fonts, logos. |
| LLM SDKs | **openai**, **anthropic**, **google-genai** behind an **LLMAdapter** interface | Adapter pattern → swap providers per-user-key. |
| Web research | **Tavily API** (primary) + **Brave Search API** (fallback) + **trafilatura** (extract) | Tavily returns LLM-ready snippets; trafilatura cleans HTML for deep dives. |
| Image search | **Unsplash API**, **Pexels API**, **Pixabay API** behind an **ImageAdapter** | Royalty-free, well-documented. |
| AI image gen (optional) | **Stability AI** / **OpenAI Images** via same adapter | User-provided key only. |
| Database | **PostgreSQL 16** (Render Managed) | Relational data + JSONB for slide blueprints; pgvector if we add semantic project search later. |
| Cache / queue broker | **Redis 7** (Render Managed) | Celery broker, rate-limit counters, generation progress pub/sub for SSE. |
| Object storage | **Cloudflare R2** (S3-compatible) — fallback **AWS S3** | Render has no native blob store; R2 is cheap with zero egress. Stores uploaded PPTX, exported PPTX, cached images. |
| File uploads | **boto3** (S3 client) + signed PUT URLs | Direct browser → R2 upload avoids API server bandwidth cost. |
| Auth | **Clerk** (or **Supabase Auth** if user prefers self-hosted) | Drop-in social/email auth, JWT for FastAPI, magic-link, MFA. |
| Secrets at rest | **AES-256-GCM via `cryptography`** with key from Render Secret Files | User API keys encrypted column-level in Postgres. |
| Realtime progress | **Server-Sent Events (SSE)** from FastAPI | Lighter than WebSockets, perfect for one-way job progress. |
| Telemetry | **OpenTelemetry → Grafana Cloud / Sentry** | Traces across research → LLM → render pipeline; Sentry for FE+BE errors. |
| Tests (BE) | **pytest + pytest-asyncio + httpx + respx** | Fast async tests; respx mocks LLM/image APIs deterministically. |
| Tests (FE) | **Vitest + React Testing Library + Playwright** | Unit + e2e (editor flows). |
| CI/CD | **GitHub Actions → Render Deploy Hooks** | Native Render integration, preview environments per PR. |
| Linting/format | **Ruff + Black** (Py), **ESLint + Prettier** (TS), **Biome** as alt | Consistent codebase. |

---

## 2. Render Service Topology

```
┌─────────────────────────────────────────────────────────────┐
│                     RENDER WORKSPACE                         │
│                                                              │
│  ┌────────────┐    ┌─────────────┐    ┌──────────────────┐  │
│  │ Web: FE    │    │ Web: API    │    │ Worker: jobs     │  │
│  │ Next.js 16 │───▶│ FastAPI     │───▶│ Celery x N       │  │
│  │ Node 24    │    │ Python 3.13 │    │ (auto-scale 1-4) │  │
│  └────────────┘    └─────────────┘    └──────────────────┘  │
│         │                 │                    │             │
│         └─────────────────┴────────────────────┘             │
│                           │                                  │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │  Render Managed Postgres 16    Render Managed Redis 7│   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
            External: R2, LLM APIs, Image APIs, Tavily
```

- **`frontend`** — Next.js standalone build, Node 24 runtime, served via Render Web Service.
- **`api`** — FastAPI/Uvicorn behind Gunicorn (`--workers 2 --worker-class uvicorn.workers.UvicornWorker`).
- **`worker`** — Celery worker pulling from Redis queues `research`, `generate`, `render`, `export`.
- **`scheduler`** (optional) — Celery beat for retention cleanup, signed-URL expiry, key-rotation audits.
- **`postgres`** — Render-managed; daily backups, point-in-time recovery on Pro plan.
- **`redis`** — Render-managed; persistence enabled (AOF every second).
- Secrets via Render **Environment Groups** + **Secret Files** for `MASTER_ENCRYPTION_KEY`.

---

## 3. Database Schema (Postgres)

```sql
-- Users handled by Clerk; we keep a profile row keyed by Clerk user_id.
CREATE TABLE app_user (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id   TEXT UNIQUE NOT NULL,
  email           CITEXT NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- User-provided API keys, encrypted column-level.
CREATE TABLE user_api_key (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES app_user(id) ON DELETE CASCADE,
  provider        TEXT NOT NULL,  -- 'openai' | 'anthropic' | 'gemini' | 'unsplash' | 'pexels' | 'pixabay' | 'stability' | 'tavily'
  key_ciphertext  BYTEA NOT NULL,
  key_nonce       BYTEA NOT NULL,
  key_fingerprint TEXT NOT NULL,  -- SHA-256 prefix, for display only
  created_at      TIMESTAMPTZ DEFAULT now(),
  UNIQUE (user_id, provider)
);

-- Reusable templates extracted from uploaded PPTX.
CREATE TABLE template (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES app_user(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  source_pptx_url TEXT NOT NULL,         -- R2 key
  design_tokens   JSONB NOT NULL,        -- colors, fonts, dimensions, masters
  thumbnail_url   TEXT,
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- A "project" is a topic+settings; it can have many decks (regenerations / variants).
CREATE TABLE project (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES app_user(id) ON DELETE CASCADE,
  title           TEXT NOT NULL,
  topic           TEXT NOT NULL,
  brief           TEXT,                  -- extra details, tone, audience
  language        TEXT DEFAULT 'en',
  template_id     UUID REFERENCES template(id),
  default_settings JSONB NOT NULL,       -- slide count, image prefs, model prefs
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- One generation = one deck. Multiple decks per project enable repeatability.
CREATE TABLE deck (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id      UUID REFERENCES project(id) ON DELETE CASCADE,
  status          TEXT NOT NULL,         -- 'queued'|'researching'|'writing'|'imaging'|'ready'|'failed'
  slide_count     INT NOT NULL,
  blueprint       JSONB NOT NULL,        -- the slide JSON (see schema doc)
  research_brief  JSONB,                 -- raw research output + citations
  generation_meta JSONB,                 -- model used, tokens, durations
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Version history per deck (non-destructive edits).
CREATE TABLE deck_version (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deck_id         UUID REFERENCES deck(id) ON DELETE CASCADE,
  blueprint       JSONB NOT NULL,
  label           TEXT,                  -- 'auto-save' | 'user-checkpoint'
  author          UUID REFERENCES app_user(id),
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- Async job tracking (mirrors Celery state for the FE).
CREATE TABLE generation_job (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deck_id         UUID REFERENCES deck(id) ON DELETE CASCADE,
  celery_task_id  TEXT,
  stage           TEXT,                  -- same enum as deck.status
  progress_pct    INT DEFAULT 0,
  error           TEXT,
  started_at      TIMESTAMPTZ,
  finished_at     TIMESTAMPTZ
);

-- Exports (PPTX, future PDF).
CREATE TABLE export_artifact (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deck_id         UUID REFERENCES deck(id) ON DELETE CASCADE,
  format          TEXT NOT NULL,         -- 'pptx' | 'pdf'
  storage_url     TEXT NOT NULL,         -- R2 key
  size_bytes      BIGINT,
  created_at      TIMESTAMPTZ DEFAULT now(),
  expires_at      TIMESTAMPTZ
);

CREATE INDEX idx_project_user ON project(user_id, updated_at DESC);
CREATE INDEX idx_deck_project ON deck(project_id, created_at DESC);
CREATE INDEX idx_template_user ON template(user_id, created_at DESC);
```

---

## 4. Background Job Pipeline

Celery queues, each task is idempotent and retried with exponential backoff (max 3):

```
generate_deck (orchestrator)
  ├─► research_topic       → queue: research    (Tavily + extract)
  ├─► extract_template     → queue: render      (if template_id set)
  ├─► author_blueprint     → queue: generate    (LLM call)
  ├─► fetch_images         → queue: generate    (parallel per slide)
  └─► persist_deck         → queue: render      (write to DB, mark ready)

export_pptx                → queue: export      (on user click "Download")
```

- Progress reported via Redis pub/sub channel `job:{deck_id}` → FastAPI SSE endpoint → client.
- Per-stage timeout: research 15s, LLM 25s, images 10s parallel, render 5s. Total budget ≤ 45s.

---

## 5. File Storage Strategy

| Asset | Bucket / Prefix | Lifecycle |
|---|---|---|
| Uploaded template PPTX | `r2://presentyourself/templates/{user}/{id}.pptx` | Permanent until user deletes |
| Extracted template thumbnails | `r2://presentyourself/templates/{user}/{id}_thumb.png` | Linked to template lifetime |
| Generated PPTX exports | `r2://presentyourself/exports/{deck}/{ts}.pptx` | 30-day TTL, signed URLs |
| Cached image search results | `r2://presentyourself/images/{hash}.jpg` | 7-day TTL, content-addressed |
| User-uploaded images | `r2://presentyourself/uploads/{user}/{id}.{ext}` | Permanent until user deletes |

All client uploads use **presigned PUT URLs** issued by the API; client posts directly to R2.

---

## 6. Adapter Pattern (Pluggable Providers)

```python
# api/adapters/llm.py
class LLMAdapter(Protocol):
    async def author_blueprint(
        self, *, research: ResearchBrief, settings: GenSettings, design: DesignTokens | None
    ) -> SlideBlueprint: ...

class OpenAIAdapter(LLMAdapter): ...
class AnthropicAdapter(LLMAdapter): ...
class GeminiAdapter(LLMAdapter): ...

# Registry resolves at runtime from user's selected provider + key.
LLM_REGISTRY: dict[str, type[LLMAdapter]] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "gemini": GeminiAdapter,
}
```

Same pattern for `ImageAdapter` (Unsplash/Pexels/Pixabay/Stability) and `ResearchAdapter` (Tavily/Brave). New providers = new file + registry entry, **no orchestrator changes**.

---

## 7. Why Not These Alternatives

| Considered | Rejected because |
|---|---|
| **Reveal.js / SlideKit** as the runtime | We need PPTX fidelity for corporate users; HTML-first decks don't round-trip to PowerPoint cleanly. |
| **PptxGenJS** (Node) for rendering | python-pptx has deeper master/layout support and clean theme XML manipulation. Keeping rendering in Python also keeps the heavy data path in one runtime. |
| **Pure WebSockets** for progress | One-way progress fits SSE; WebSockets add reconnect/heartbeat complexity we don't need. |
| **MongoDB** for blueprints | Postgres JSONB gives us JSON flexibility *and* relational integrity (users, projects, exports) in one store. |
| **Kubernetes** | Render is the target; we want simple managed services. |
| **LangChain** | Heavy abstraction tax for what is essentially three discrete LLM calls. We build the adapter ourselves. |

---

## 8. Local Development

- `docker-compose.yml` boots Postgres 16, Redis 7, MinIO (S3-compat) for offline R2 substitute.
- `.env.example` lists every key; secrets never committed.
- `make dev` runs FE + API + worker concurrently via Procfile (`hivemind` or `overmind`).
