# Present Yourself — Design Documentation

Build a Render-deployed web app that turns a topic into a polished, brand-matched **.pptx** deck via AI research, template cloning, image discovery, and a real editor.

## Document Index

| # | Document | Purpose |
|---|---|---|
| 1 | [Tech Stack](./01-tech-stack.md) | Exact frameworks, libraries, services, schema, Render topology, adapter pattern. |
| 2 | [Product Requirements (PRD)](./02-prd.md) | Problem, audience, P0/P1/P2 features, user flows, mockup descriptions, success metrics, release criteria. |
| 3 | [Functional + Non-Functional Requirements](./03-requirements.md) | Testable spec, use cases, API surface, SlideBlueprint JSON schema, error handling, config, rate limits. |
| 4 | [UI/UX Specification](./04-ui-ux.md) | Visual language, wireframes, key interactions, component inventory, **system architecture diagram**. |

## Quick Build Order (suggested)

1. **Week 1** — Scaffold (Next.js + FastAPI + Postgres + Redis on Render), Clerk auth, dashboard skeleton, `/me` + `/api-keys` endpoints with AES-256-GCM vault.
2. **Week 2** — Research + LLM adapters, generate `SlideBlueprint`, persist `deck`, SSE progress.
3. **Week 3** — Template upload + parsing, design tokens extraction, image adapters, R2 wiring.
4. **Week 4** — Editor MVP: Konva canvas + Tiptap text + slide reorder + auto-save + version history.
5. **Week 5** — PPTX renderer (python-pptx) + export pipeline + round-trip QA across PowerPoint/Slides/LibreOffice.
6. **Week 6** — P1: speaker notes, citations panel, user-uploaded images, duplicate-project flow, polish, observability, load test, beta launch.
