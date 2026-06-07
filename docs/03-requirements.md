# Document 3: Requirements Specification (Functional + Non-Functional)

**Project:** Present Yourself
**Version:** 1.0
**Status:** Buildable

---

## 1. Functional Requirements

Each requirement is **testable** — has a clear acceptance check.

### FR-1: Authentication & Account
| ID | Requirement | Test |
|---|---|---|
| FR-1.1 | Users sign up via email or OAuth (Google, Microsoft) through Clerk. | Manual: create account each method. |
| FR-1.2 | Sessions expire after 30 days of inactivity. | Set clock fwd, verify re-auth. |
| FR-1.3 | Users can delete their account; all owned data purged within 24h. | Trigger delete, query DB after 24h. |

### FR-2: API Key Management
| ID | Requirement | Test |
|---|---|---|
| FR-2.1 | Users can add API keys for: `openai`, `anthropic`, `gemini`, `unsplash`, `pexels`, `pixabay`, `tavily`, `stability`. | UI accepts all 8 providers. |
| FR-2.2 | Keys are AES-256-GCM encrypted at rest using a master key from Render Secret File. | Decrypt requires master key; ciphertext ≠ plaintext in DB. |
| FR-2.3 | Keys are validated by a real test call to the provider before save. Invalid → user-facing error. | Submit bad key → rejected with provider-specific message. |
| FR-2.4 | Keys are returned to the client masked (`sk-...abc4`). Full plaintext never leaves the server after creation. | Inspect API responses for any full-key leak. |
| FR-2.5 | When generating a deck, user keys override system defaults; missing user key falls back to system default (if any). | Generate with and without user key; check logs. |

### FR-3: Project & Deck Lifecycle
| ID | Requirement | Test |
|---|---|---|
| FR-3.1 | Users can create, rename, duplicate, and delete projects. | CRUD round-trip per action. |
| FR-3.2 | Duplicating a project copies settings and the most recent deck blueprint; the new project is independent. | Modify duplicate; original unchanged. |
| FR-3.3 | Each project may have unlimited decks (regenerations) accessible via sidebar. | Generate 5x, all listed. |
| FR-3.4 | Deck status transitions: `queued → researching → writing → imaging → ready` or `failed`. | Each transition emitted on SSE channel. |

### FR-4: Research Pipeline
| ID | Requirement | Test |
|---|---|---|
| FR-4.1 | Given topic + brief, system fetches ≥ 5 sources within 15s. | Time + count assertion in test. |
| FR-4.2 | System extracts cleaned text via trafilatura. | Snapshot test on known URLs. |
| FR-4.3 | Output is a `ResearchBrief` (see §4) with citations (URL, title, snippet, fetched_at). | Schema validation. |
| FR-4.4 | If primary research provider fails, fallback provider is used; if both fail after 3 retries, deck status = `failed` with explicit error. | Mock failure, observe retry + fallback. |
| FR-4.5 | Robots.txt respected; per-domain rate limit 1 req/2s. | Crawl log inspection. |

### FR-5: AI Blueprint Generation
| ID | Requirement | Test |
|---|---|---|
| FR-5.1 | LLM is called with research brief + user settings + (optional) design tokens. Output validated against the **SlideBlueprint** schema (§4). Validation failure triggers one retry with a corrective prompt. | Mock invalid JSON → retry → success. |
| FR-5.2 | Generated decks must include narrative variety: ≥ 4 different slide types in any 10-slide deck. | Lint pass on output. |
| FR-5.3 | Each slide has speaker notes (≥ 40 words). | Length check. |
| FR-5.4 | Per-slide regenerate accepts an optional refinement hint; only that slide's JSON is replaced; deck_version row is created. | Regenerate slide 3, verify only slide 3 differs and v2 saved. |

### FR-6: Template Extraction
| ID | Requirement | Test |
|---|---|---|
| FR-6.1 | Accept `.pptx` ≤ 50 MB. | Reject > 50 MB. |
| FR-6.2 | Extract: slide dimensions, theme colors (accent1–6, dk1, lt1, dk2, lt2, hlink, folHlink), heading + body fonts, slide masters and their layouts, default bullet styles, any logo images from masters. | Compare against known reference template. |
| FR-6.3 | Store `design_tokens` JSON; store source PPTX in R2. | Verify both. |
| FR-6.4 | When rendering, the template's first matching layout is used per slide-type; if none match, fall back to system layout marked compatible. | Render w/ template; layouts respected. |
| FR-6.5 | Generate a 256x144 PNG thumbnail of the title master for the template card. | Visual check. |

### FR-7: Image Discovery
| ID | Requirement | Test |
|---|---|---|
| FR-7.1 | Per image-slot slide, system queries the image adapter with `f"{title} | {top 5 body keywords}"`. | Log query strings. |
| FR-7.2 | Returns top 3 candidates; first inserted, others stashed for one-click swap. | Inspect deck JSON `image_candidates`. |
| FR-7.3 | Images cached by `sha256(url)` in R2 to avoid re-download. | Second request hits cache. |
| FR-7.4 | If all image providers fail, slide renders with a neutral placeholder; deck does NOT fail. | Mock failure, deck still ready. |
| FR-7.5 | User can override with own upload (any of: jpg, png, webp ≤ 10 MB). | Upload + display. |

### FR-8: Editor
| ID | Requirement | Test |
|---|---|---|
| FR-8.1 | Text editing is inline WYSIWYG (Tiptap). Bold/italic/underline, color, list, link, font-size. | UI integration test. |
| FR-8.2 | Image swap modes: search, URL paste, upload, AI-generate (P1). | Per-mode test. |
| FR-8.3 | Drag-reorder slides via thumbnails rail. | Cypress drag test. |
| FR-8.4 | Add slide: dropdown of layouts; new slide inserts after current. | UI test. |
| FR-8.5 | Delete slide: confirm dialog. | UI test. |
| FR-8.6 | Undo/redo: 50-step history per session; persists on reload via deck_version snapshots every 30s. | Force reload, redo still works. |
| FR-8.7 | Auto-save debounce: 1.5s after last edit; visible "Saved" indicator. | Edit + observe. |
| FR-8.8 | Version history side panel; click any version → preview → "Restore" creates new version equal to that one. | E2E. |

### FR-9: Export
| ID | Requirement | Test |
|---|---|---|
| FR-9.1 | "Export" button generates PPTX via python-pptx, uploads to R2, returns signed URL valid 60 min. | Click → file downloads. |
| FR-9.2 | Exported PPTX opens cleanly in PowerPoint 2019+, Google Slides, LibreOffice Impress 7+. | Round-trip suite. |
| FR-9.3 | Export uses the project's `design_tokens` when set; system default theme otherwise. | Compare colors/fonts in output. |
| FR-9.4 | Export history accessible from dashboard "Exports" tab. | Tab shows past exports. |

### FR-10: Repeatability & Library
| ID | Requirement | Test |
|---|---|---|
| FR-10.1 | Saved templates appear in wizard step 3 + Templates tab. | Lifecycle test. |
| FR-10.2 | Search projects by title (FTS). | Index hit. |
| FR-10.3 | Each project shows generation history with timestamps; reverting opens that deck. | E2E. |

---

## 2. Non-Functional Requirements

| ID | Requirement | Acceptance |
|---|---|---|
| NFR-1 | End-to-end generation for 10-slide deck ≤ 45s p95. | Load test report. |
| NFR-2 | Editor interactions respond ≤ 200ms (text input → render). | Lighthouse + RUM. |
| NFR-3 | Support 100 concurrent generation jobs across worker pool (auto-scale 1–4 workers). | k6 load test. |
| NFR-4 | API availability ≥ 99.5% monthly. | Uptime monitoring. |
| NFR-5 | All client/server traffic over TLS 1.3. Render handles cert. | SSL Labs A+. |
| NFR-6 | User-provided API keys encrypted at rest (AES-256-GCM); decryption only in worker memory; never logged. | Code review + log scan. |
| NFR-7 | User data isolated per `user_id`; every read query parameterized by authenticated user. | Static analysis + pytest fixtures simulating cross-user access. |
| NFR-8 | OWASP Top-10 covered: input sanitization for all FE-supplied text, CSRF tokens on state-changing endpoints, rate-limits per-user + per-IP (Redis token bucket). | Pen test report. |
| NFR-9 | Logs structured (JSON) with `request_id`, `user_id`, `deck_id`. Sensitive fields redacted. | Sample log review. |
| NFR-10 | All external API calls have 3-attempt retry with exponential backoff + jitter; circuit breaker opens after 5 consecutive failures over 60s. | Chaos test. |
| NFR-11 | GDPR: account delete purges within 24h; data export endpoint produces ZIP of user's projects + decks within 1h. | Functional check. |
| NFR-12 | A11y: editor meets WCAG 2.1 AA — keyboard nav for all editor actions; visible focus rings; screen-reader labels. | axe audit. |
| NFR-13 | Internationalization-ready: all UI strings in i18n catalog (English only at v1). | Inspect source. |

---

## 3. API Surface (REST, JSON, JWT auth)

Base URL: `https://api.presentyourself.app/v1`

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/session` | Exchange Clerk JWT for app session (server-side). |
| GET | `/me` | Current user profile + feature flags. |
| GET | `/api-keys` | List user's API keys (masked). |
| POST | `/api-keys` | Add or replace key. Body `{provider, key}`. Validates with provider. |
| DELETE | `/api-keys/{provider}` | Remove. |
| GET | `/projects` | Paginated list. `?q=&page=&limit=`. |
| POST | `/projects` | Create project. |
| GET | `/projects/{id}` | Project + decks list. |
| PATCH | `/projects/{id}` | Rename / update settings. |
| DELETE | `/projects/{id}` | Soft-delete (30-day purge). |
| POST | `/projects/{id}/duplicate` | Clone. |
| POST | `/projects/{id}/decks` | **Kick off generation**. Body `{slide_count, with_images, template_id?, model_provider, hints?}`. Returns `{deck_id, job_id}`. |
| GET | `/decks/{id}` | Deck + blueprint + status. |
| PATCH | `/decks/{id}` | Save blueprint (auto-save). Body `{blueprint, label?}`. Creates deck_version. |
| POST | `/decks/{id}/slides/{idx}/regenerate` | Regenerate one slide. Body `{hint?}`. |
| POST | `/decks/{id}/regenerate` | Regenerate full deck (new deck row). |
| GET | `/decks/{id}/stream` | **SSE** of generation progress events. |
| GET | `/decks/{id}/versions` | Version list. |
| POST | `/decks/{id}/versions/{vid}/restore` | Restore. |
| POST | `/decks/{id}/export` | Build PPTX. Body `{format: 'pptx'}`. Returns `{artifact_id, status}`. |
| GET | `/exports/{id}` | Status + signed URL when ready. |
| POST | `/templates` | Multipart upload `.pptx`. Returns `{template_id, design_tokens, thumbnail_url}`. |
| GET | `/templates` | List user's templates. |
| DELETE | `/templates/{id}` | Remove. |
| POST | `/uploads/sign` | Get presigned R2 PUT URL. Body `{purpose, content_type, size}`. |
| GET | `/images/search` | `?q=&providers=unsplash,pexels&page=`. Proxies through user's keys. |

**Error envelope (all 4xx/5xx):**
```json
{
  "error": {
    "code": "INVALID_API_KEY",
    "message": "OpenAI rejected this key.",
    "request_id": "req_01HZA...",
    "details": { "provider": "openai" }
  }
}
```

**Standard codes:** `400 INVALID_INPUT`, `401 UNAUTHENTICATED`, `403 FORBIDDEN`, `404 NOT_FOUND`, `409 CONFLICT`, `422 SCHEMA_ERROR`, `429 RATE_LIMITED`, `502 UPSTREAM_FAILED`, `504 UPSTREAM_TIMEOUT`, `500 INTERNAL`.

---

## 4. SlideBlueprint JSON Schema

This is the **canonical contract** between BE (generator) and FE (editor/renderer). Versioned with `schema_version`.

```jsonc
{
  "schema_version": "1.0",
  "deck": {
    "id": "uuid",
    "title": "Future of Electric Aviation",
    "language": "en",
    "design_tokens": {
      "dimensions": { "width_emu": 12192000, "height_emu": 6858000, "aspect": "16:9" },
      "palette": {
        "background": "#FFFFFF",
        "foreground": "#0F172A",
        "accent1": "#2563EB",
        "accent2": "#0EA5E9",
        "accent3": "#F59E0B",
        "muted": "#64748B"
      },
      "fonts": {
        "heading": { "family": "Inter", "weight": 700 },
        "body":    { "family": "Inter", "weight": 400 }
      },
      "logo": { "url": "r2://.../logo.png", "position": "top-right" } // nullable
    },
    "slides": [
      {
        "id": "slide_01",
        "type": "title",                    // see slide types below
        "layout_hint": "centered",
        "elements": [
          { "id": "el_1", "kind": "text",  "role": "title",    "content": "Future of Electric Aviation", "style": { "size": 60, "color": "accent1", "align": "center" } },
          { "id": "el_2", "kind": "text",  "role": "subtitle", "content": "From eVTOL to commercial flight", "style": { "size": 24, "color": "muted" } }
        ],
        "notes": "Open with the stat that...",
        "citations": ["src_1", "src_3"]
      },
      {
        "id": "slide_02",
        "type": "bullet_list",
        "layout_hint": "left_text_only",
        "elements": [
          { "id": "el_t", "kind": "text", "role": "title", "content": "Why now?" },
          { "id": "el_b", "kind": "bullets", "items": [
              "Battery energy density doubled 2018→2025",
              "FAA Part 23 amendments cleared certification path",
              "30+ eVTOL programs in flight test"
          ]}
        ],
        "notes": "...",
        "citations": ["src_2"]
      },
      {
        "id": "slide_03",
        "type": "image_caption",
        "layout_hint": "right_image",
        "elements": [
          { "id": "el_t", "kind": "text", "role": "title", "content": "Joby S4 in flight test" },
          { "id": "el_i", "kind": "image",
            "source": { "provider": "unsplash", "url": "https://...", "credit": "Photo by X on Unsplash" },
            "candidates": [ { "url": "..." }, { "url": "..." } ],
            "alt": "eVTOL prototype at sunset"
          },
          { "id": "el_c", "kind": "text", "role": "caption", "content": "Joby S4, 2025." }
        ],
        "notes": "...",
        "citations": ["src_5"]
      }
    ],
    "citations": [
      { "id": "src_1", "url": "https://...", "title": "...", "publisher": "FAA",   "fetched_at": "2026-06-07T12:00:00Z" },
      { "id": "src_2", "url": "https://...", "title": "...", "publisher": "Joby",  "fetched_at": "2026-06-07T12:00:01Z" },
      { "id": "src_3", "url": "https://...", "title": "...", "publisher": "MIT",   "fetched_at": "2026-06-07T12:00:02Z" }
    ]
  }
}
```

**Allowed slide types (v1):**
`title`, `section_header`, `bullet_list`, `two_column`, `image_caption`, `quote`, `stat_callout`, `comparison_table`, `chart_placeholder`, `closing`.

**Allowed element kinds:** `text`, `bullets`, `image`, `shape`, `table`, `chart_placeholder`.

**Validation:** Pydantic v2 model in BE; Zod schema generated from it for FE. CI step asserts the two schemas are equivalent.

---

## 5. Detailed Use Cases

### UC-1 — Generate Deck From Topic
- **Actor:** Authenticated user
- **Preconditions:** Valid session; quota not exhausted.
- **Trigger:** `POST /projects/{id}/decks`
- **Main success scenario:**
  1. API validates payload (Zod/Pydantic).
  2. Creates `deck` row (status=`queued`) + `generation_job`.
  3. Enqueues Celery `generate_deck` task; returns `{deck_id, job_id}` (HTTP 202).
  4. Worker runs research → write → image fetch (parallel) → persist.
  5. SSE emits stage events; FE updates progress UI.
  6. On `ready`, FE redirects to editor with deck loaded.
- **Exceptions:**
  - Research timeout (15s): retry once with relaxed query → if still failing, surface partial brief if any source returned.
  - LLM rejects JSON: one corrective retry with prior output + error → if fails, `deck.status='failed'`, FE shows "Generation failed, try again or change provider".
  - Image fetch failure: slide proceeds with placeholder; non-fatal.
  - User cancels (DELETE during job): Celery task receives revoke; deck marked `cancelled`.

### UC-2 — Upload & Apply Template
- **Actor:** User
- **Trigger:** Template upload in wizard or Templates tab.
- **Main:**
  1. FE requests presigned URL (`POST /uploads/sign`), PUTs directly to R2.
  2. FE posts metadata to `POST /templates` with R2 key.
  3. Worker parses PPTX (python-pptx + lxml), extracts `design_tokens`, generates thumbnail, persists.
  4. Template appears in wizard / library.
- **Exceptions:**
  - Corrupt PPTX: `422 INVALID_TEMPLATE` with parser hint.
  - File too large: `413 PAYLOAD_TOO_LARGE`.
  - No master found: warn + fall back to first slide's layout as the master.

### UC-3 — Manual Image Swap
- **Actor:** User in editor
- **Trigger:** Click image element → "Replace" → search.
- **Main:**
  1. FE calls `GET /images/search?q=&providers=unsplash,pexels`.
  2. API uses user's keys (or defaults), merges + dedups, returns paginated grid.
  3. User clicks an image → FE patches deck blueprint, calls `PATCH /decks/{id}`.
  4. Auto-save fires; new `deck_version` row.
- **Exceptions:** No keys + no defaults → friendly empty state "Add an Unsplash key in Settings."

### UC-4 — Export PPTX
- **Trigger:** `POST /decks/{id}/export`
- **Main:**
  1. API enqueues `export_pptx` worker job.
  2. Worker hydrates blueprint, applies design tokens, calls python-pptx renderer.
  3. Uploads to R2, creates `export_artifact`, returns signed URL.
  4. FE polls `/exports/{id}` until `status='ready'`, triggers browser download.
- **Exceptions:** Renderer failure → fall back to "safe" theme rendering; if still fails, `502` with task ID for support.

---

## 6. Logging & Telemetry

- **Structured JSON** via `structlog` (Python) and `pino` (Node).
- Every request: `request_id`, `user_id`, `route`, `latency_ms`, `status`.
- Every Celery task: `task_name`, `deck_id`, `stage`, `duration_ms`, `provider`, `tokens` (LLM), `cache_hit` (images).
- **Sensitive field redaction list:** `key`, `key_ciphertext`, `Authorization`, `cookie`, full `prompt` (we keep prompt **hash** + length).
- **Sentry** captures FE + BE exceptions; release tagging on every deploy.
- **OpenTelemetry traces:** root span = HTTP request; child spans for each adapter call (LLM, research, image).

---

## 7. Configuration

All env vars documented in `.env.example`. Required at boot:

| Var | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection (Render provides). |
| `REDIS_URL` | Celery broker + cache (Render provides). |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY`, `R2_SECRET`, `R2_BUCKET` | Object storage. |
| `MASTER_ENCRYPTION_KEY` | 32-byte base64. **Render Secret File**, mounted to `/etc/secrets/master.key`. |
| `CLERK_SECRET_KEY`, `CLERK_PUBLISHABLE_KEY` | Auth. |
| `SYSTEM_OPENAI_KEY` | Default LLM (may be empty → users must supply own). |
| `SYSTEM_TAVILY_KEY` | Default research. |
| `SYSTEM_UNSPLASH_KEY`, `SYSTEM_PEXELS_KEY` | Default images. |
| `SENTRY_DSN` | Error tracking. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Traces. |
| `RATE_LIMIT_GENERATIONS_PER_DAY` | Free-tier guard (default 10). |
| `MAX_PPTX_UPLOAD_MB` | Default 50. |
| `MAX_IMAGE_UPLOAD_MB` | Default 10. |

Boot fails fast if any required var is missing (Pydantic `Settings`).

---

## 8. Rate Limits & Quotas

| Resource | Free | Paid (v1) |
|---|---|---|
| Generations per day | 10 | 100 |
| Exports per day | 20 | 500 |
| Templates stored | 3 | unlimited |
| Concurrent generations | 1 | 5 |
| Image searches per hour | 60 | 600 |

Enforced via Redis sliding window per `user_id`; over-limit returns `429` with `Retry-After`.
