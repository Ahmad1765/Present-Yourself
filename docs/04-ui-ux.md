# Document 4: UI/UX Specification

**Project:** Present Yourself
**Design intent:** Beautiful. Quick. Easy. Repeatable.
**Version:** 1.0

---

## 1. Design Principles

1. **One question per screen.** No overwhelming forms. The wizard asks one thing at a time so users move forward without friction.
2. **Defaults you'd actually pick.** 10 slides, images on, default model. The "Generate" button works after a single field.
3. **Forgiving.** Every destructive action has undo (or a 5-second toast with "Undo"). Auto-save runs constantly.
4. **Repeatable by surface area.** Duplicate, regenerate, restore — these verbs are visible everywhere they're applicable, not buried in menus.
5. **Honest motion.** Progress UI shows real stages; we don't fake a 30-second spinner for a 4-second job.
6. **No AI weirdness.** Editor feels like a real editor (Slides/Keynote vibe), not a chat box.

---

## 2. Visual Language

### 2.1 Color System (light theme)

| Token | Hex | Use |
|---|---|---|
| `--bg`         | `#FAFAF9` | App background |
| `--surface`    | `#FFFFFF` | Cards, panels |
| `--surface-2`  | `#F5F5F4` | Hover/active surfaces |
| `--border`     | `#E7E5E4` | Hairlines |
| `--fg`         | `#0C0A09` | Body text |
| `--fg-muted`   | `#57534E` | Secondary text |
| `--fg-subtle`  | `#A8A29E` | Tertiary text, placeholders |
| `--accent`     | `#4F46E5` | Primary actions, links |
| `--accent-fg`  | `#FFFFFF` | Text on accent |
| `--success`    | `#16A34A` | Saved states |
| `--warn`       | `#D97706` | Warnings |
| `--danger`     | `#DC2626` | Destructive |
| `--ring`       | `rgba(79,70,229,.35)` | Focus rings |

Dark theme mirrors with stone-950 base. Theme switch in user settings; system-default by default.

### 2.2 Typography

- **Primary font:** Inter (variable), self-hosted via Fontsource.
- **Display sizes:** 60 / 48 / 36 for landing + section headers in editor inspector.
- **UI sizes:** 14 base, 12 for metadata/labels, 16 for body content.
- **Mono:** JetBrains Mono for code/keys.
- Line-height 1.45 body, 1.15 display.

### 2.3 Spacing & Layout

- **4-pt scale.** Tokens: `space-1` (4px) → `space-12` (96px).
- **Max content width** in dashboard 1280px; editor uses full viewport.
- **Card radius** 12px (panels), 8px (controls), 4px (chips).
- **Shadow:** flat by default. Only the floating element toolbar and modals carry `shadow-lg` (subtle, tight).

### 2.4 Iconography

- **Lucide** icons throughout — 16px in inline UI, 20px in toolbar, 24px in empty states.
- Stroke width 1.75. Icons inherit text color.

### 2.5 Motion

- Standard ease: `cubic-bezier(0.2, 0.8, 0.2, 1)`.
- Standard duration: 150ms (UI), 250ms (panels), 400ms (page transitions).
- `prefers-reduced-motion` collapses to instant.

---

## 3. Information Architecture

```
/                          → Landing
/sign-in, /sign-up         → Clerk
/dashboard                 → Default after login
  /projects                → (default tab)
  /templates
  /exports
/p/{projectId}             → Project detail (deck list sidebar + active deck preview)
/p/{projectId}/new         → Wizard
/d/{deckId}                → Editor (full-screen)
/settings
  /settings/profile
  /settings/api-keys
  /settings/billing
  /settings/danger
```

---

## 4. Wireframes (text-based)

### 4.1 Landing

```
┌──────────────────────────────────────────────────────────────────────┐
│  Present Yourself                  Pricing  Docs   [ Sign in ]  [ +Start ]│
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Decks. Done.                              ┌────────────────────┐  │
│   Type a topic. Get a draft.                │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │  │
│   Match your brand.                         │  (animated deck   │  │
│                                              │   preview, 3      │  │
│   [ Start free →                         ]   │   rotating)       │  │
│                                              └────────────────────┘  │
│   ✓ 10-slide draft in 90s                                            │
│   ✓ Drop in your PPTX — output matches it                            │
│   ✓ Export .pptx that opens anywhere                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Dashboard — Projects tab

```
┌─────────────────────────────────────────────────────────────────────┐
│ ▓ Workspace ▾   [ search projects…           ]      [ + New deck ] │
├─────────────────────────────────────────────────────────────────────┤
│  Projects  Templates  Exports                                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ [thumb]  │  │ [thumb]  │  │ [thumb]  │  │ [thumb]  │             │
│  │ Q1 review│  │ EV avia. │  │ Pitch v3 │  │ AI report│             │
│  │ 12 slides│  │ 10 slides│  │ 14 slides│  │ 8 slides │             │
│  │ 2h ago ⋯ │  │ Yest.  ⋯ │  │ Mon    ⋯ │  │ Last wk⋯ │             │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

Card `⋯` menu: Open · Duplicate · Rename · Delete.

### 4.3 New-Project Wizard (4 steps, one-at-a-time)

```
Step 1 / 4
┌─────────────────────────────────────────────────────────────┐
│  ● ─ ○ ─ ○ ─ ○                                              │
│                                                             │
│  What's your deck about?                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Future of electric aviation                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Add details (optional)                                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Audience: aerospace execs. Tone: optimistic.        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│                                       [ Cancel ] [ Next → ] │
└─────────────────────────────────────────────────────────────┘

Step 2: Slide count (slider 5–25, default 10, live preview "≈ 90s")
Step 3: Template (3 cards: [None] [Library ▾] [Upload .pptx ↑])
Step 4: Images (toggle, source dropdown, language, model selector)

           ↓ Generate
```

### 4.4 Generation Progress

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│             Building your deck                           │
│                                                          │
│   🔍 Research        ████████░░  Found 12 sources        │
│   ✍️ Write           ██░░░░░░░░  Drafting slide 3 of 10  │
│   🖼️ Images          ░░░░░░░░░░  Queued                  │
│   ✨ Polish          ░░░░░░░░░░  Queued                  │
│                                                          │
│   "Decarbonizing short-haul aviation by 2030..."         │
│                                                          │
│                                          [ Cancel ]      │
└──────────────────────────────────────────────────────────┘
```

Live text snippets appear as the LLM streams — gives the wait a sense of progress.

### 4.5 Editor (the centerpiece)

```
┌────────────────────────────────────────────────────────────────────────┐
│  ‹ Back   Future of Electric Aviation  v3 ▾   [ Saved 2s ago ]  [Export]│
├──┬──────────────────────────────────────────────────────────┬──────────┤
│  │                                                          │ Layout   │
│  │   ┌─ floating toolbar above selected element ─┐          │ Style    │
│  │   │ B I U  A▾  • ☰  ↔ size  ☼ color  ⌫       │          │ Notes    │
│  │  ┌┴───────────────────────────────────────────┴┐         │ AI       │
│ T│  │                                              │         │──────────│
│ h│  │        Future of Electric Aviation           │         │ Layouts  │
│ u│  │                                              │         │ [grid of │
│ m│  │  • Battery density doubled 2018→2025         │         │  8 thumb]│
│ b│  │  • FAA Part 23 amendments cleared cert path  │         │          │
│ s│  │  • 30+ eVTOL programs in flight test         │         │ Image:   │
│  │  │                              [   image   ]   │         │ [Replace]│
│ ::│  │                                              │         │ [Search] │
│ ::│  └──────────────────────────────────────────────┘         │          │
│ ::│                                                          │ Citations│
│ ::│  Slide 3 of 10           ← →     [ + add slide ]         │ — FAA…   │
│  │                                                          │ — Joby…  │
└──┴──────────────────────────────────────────────────────────┴──────────┘
```

Key behaviors:
- **Left rail (slides):** drag to reorder, click thumbnail to focus, right-click for context menu (Duplicate / Delete / Regenerate / Move…).
- **Center canvas (Konva):** click element → floating toolbar; double-click text → Tiptap inline editor; click image → right rail switches to "Image" tab.
- **Right rail:** four tabs.
  - **Layout** — 8 thumbnails of layout variants; click to switch; preview updates instantly.
  - **Style** — color (palette swatches from design_tokens), font size, alignment. If template is locked, controls are disabled with tooltip "Locked by template — duplicate to customize."
  - **Notes** — speaker notes textarea.
  - **AI** — "Regenerate slide" with optional hint textarea; "Improve writing" quick action; "Make shorter / longer / more visual" chips.
- **Top bar:** deck title (click to rename), **version dropdown** (every auto-save listed; restore opens preview), **Export** primary button.
- **Bottom-center:** slide counter + arrows + "+ add slide".

### 4.6 Image Search Drawer

```
┌────────────────────────── Replace image ──────────────────┐
│  Search  Upload  URL                                       │
│  [ team collaboration                  ] [ Search ]        │
│  Source: ◉ Any  ○ Unsplash  ○ Pexels  ○ Pixabay            │
│                                                            │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐                              │
│  │ 🖼️ │ │ 🖼️ │ │ 🖼️ │ │ 🖼️ │                              │
│  └────┘ └────┘ └────┘ └────┘                              │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐                              │
│  │ 🖼️ │ │ 🖼️ │ │ 🖼️ │ │ 🖼️ │                              │
│  └────┘ └────┘ └────┘ └────┘                              │
│                                       [ Load more ]        │
└────────────────────────────────────────────────────────────┘
```

Hover shows credit + provider; click sets immediately and closes drawer.

### 4.7 Template Upload / Management

```
Templates tab
┌─────────────────────────────────────────────────────────────┐
│  Your templates                          [ + Upload .pptx ] │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐                        │
│  │ [thumbnail]  │   │ [thumbnail]  │                        │
│  │ Acme Brand   │   │ Pitch 2026   │                        │
│  │ 16:9 · Inter │   │ 16:9 · Helv. │                        │
│  │ ▣▣▣▣ ⋯       │   │ ▣▣▣▣ ⋯       │                        │
│  └──────────────┘   └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

Upload modal: drag-drop zone, then a preview pane that shows extracted palette swatches, fonts, and the title master image. Confirm to save.

### 4.8 Settings → API Keys

```
┌─────────────────────────────────────────────────────────────┐
│  API Keys                                                   │
│  Your keys are encrypted with AES-256 and never logged.     │
├─────────────────────────────────────────────────────────────┤
│  Provider     Key            Last used      Action          │
│  OpenAI       sk-…•••abc4    2h ago        [Replace][🗑]    │
│  Anthropic    sk-ant-•••42   never         [Replace][🗑]    │
│  Unsplash     —              —              [+ Add]         │
│  Pexels       —              —              [+ Add]         │
└─────────────────────────────────────────────────────────────┘
```

Add key form: provider dropdown · paste field (masked) · [ Validate & Save ] (a real API call confirms before persisting).

---

## 5. Key Interactions

### 5.1 Drag-and-Drop (dnd-kit)
- **Slide reorder:** grab handle on thumbnail, ghost preview, drop indicator line. Keyboard: focus thumbnail, `Space` to lift, arrows to move, `Space` to drop. `Esc` cancels.
- **Asset drop:** drag image file from desktop onto an image element → upload begins, progress overlay, replaces on done.

### 5.2 Inline editing (Tiptap)
- Double-click text → caret appears, toolbar floats above.
- `Cmd/Ctrl+B/I/U`, `Cmd+K` to link, `/` opens a slash menu (heading, bullet, callout, divider).
- Click outside or `Esc` commits.

### 5.3 Slide navigation
- Arrow keys (when not in text edit) move between slides.
- `J/K` also navigate (power users).
- `Cmd/Ctrl+/` opens command palette: jump to slide, regenerate, export, swap layout, etc.

### 5.4 Undo/redo
- `Cmd/Ctrl+Z` / `Cmd+Shift+Z`. 50-step in-memory; every 30s a `deck_version` row snapshot — refresh-safe.

### 5.5 Auto-save indicator
- Tiny text near deck title: "Saved 2s ago" → "Saving…" → "Saved". On offline: "Reconnecting…" with retry queue.

---

## 6. How the UI Reinforces Repeatability

| Surface | Repeatability lever |
|---|---|
| Dashboard card menu | Duplicate is the **second** option, not buried. |
| Project page sidebar | Lists every generation (deck) under the project; users see history at a glance. |
| Editor top bar | Version dropdown — every auto-save is a one-click restore. |
| Wizard step 3 | "From a saved template" is a first-class option, not an upsell. |
| Templates tab | Front-and-center in dashboard tabs — promotes brand-locked reuse. |
| Editor right rail "AI" tab | Regenerate slide / regenerate deck are normalized, low-friction. |
| Command palette | `Cmd+/` → "Duplicate this project" is one keystroke away. |
| Exports tab | Past PPTX downloads always retrievable — users return rather than regenerate. |

---

## 7. Accessibility

- All interactive elements reachable via keyboard.
- Focus rings visible (`outline-offset: 2px`, `--ring`).
- ARIA labels on all icon-only buttons.
- Color contrast ≥ 4.5:1 for body text, ≥ 3:1 for large text and UI controls.
- `prefers-reduced-motion` respected.
- Editor canvas elements expose an accessible tree (alt text on images, role=textbox for editable text).
- Screen-reader landmarks: `<main>`, `<nav aria-label="Slides">`, `<aside aria-label="Inspector">`.

---

## 8. Empty / Error / Edge States

| State | Treatment |
|---|---|
| **No projects** | Big illustration, single CTA "Create your first deck". |
| **Generation failed** | Inline banner with cause, action: "Retry" + "Switch provider". |
| **No image results** | "No results — try fewer words or different source." Link to upload. |
| **No API key + no system default** | Settings nudge: "Add an OpenAI key to generate." Direct deep-link. |
| **PPTX parse failure** | Modal: "We couldn't read this template. Try saving as `.pptx` from PowerPoint and re-uploading." |
| **Rate-limited** | Toast with `Retry-After`; link to upgrade. |
| **Offline** | Top banner; auto-save queues; restore on reconnect. |

---

## 9. Component Inventory (build with shadcn/ui)

Buttons (primary, secondary, ghost, destructive) · Input · Textarea · Select · Slider · Switch · Tabs · Dialog · Sheet (drawer) · DropdownMenu · ContextMenu · Tooltip · Toast · Card · Badge · Avatar · Progress · Skeleton · CommandPalette · Resizable panels · DataTable (Exports) · FileDropzone (custom over react-dropzone).

Custom-built:
- **SlideThumbnail** (rendered via offscreen Konva → image data)
- **SlideCanvas** (Konva stage; integrates Tiptap overlays for text)
- **InspectorPanel** (4 tabs)
- **VersionDropdown**
- **LayoutPicker** (grid of 8 layouts)
- **ColorSwatchPicker** (reads from design_tokens)
- **ImageSearchDrawer**
- **GenerationProgress**

---

## 10. High-Level System Architecture (ASCII)

```
                              ┌─────────────────────────────┐
                              │            USER             │
                              │       (browser, desktop)    │
                              └──────────────┬──────────────┘
                                             │ HTTPS
                                             ▼
                       ┌──────────────────────────────────────────┐
                       │     RENDER WEB SERVICE: frontend         │
                       │     Next.js 16 · Node 24                 │
                       │     Server Components + Konva editor     │
                       └────────────┬─────────────────────────────┘
                                    │ JSON over HTTPS / SSE
                                    ▼
   ┌────────────────────────────────────────────────────────────────┐
   │              RENDER WEB SERVICE: api                            │
   │              FastAPI (Python 3.13) · Uvicorn/Gunicorn           │
   │                                                                 │
   │   ┌─────────────────────────────────────────────────────────┐  │
   │   │ Routes: /projects /decks /templates /exports /me        │  │
   │   │ Middleware: auth (Clerk JWT) · rate-limit · request-id  │  │
   │   │ Adapters (interfaces only on web): not invoked here      │  │
   │   └─────────────────────────────────────────────────────────┘  │
   │                                                                 │
   │   reads/writes ▶ Postgres (project, deck, user_api_key, …)     │
   │   enqueues ▶ Redis  (Celery broker)                            │
   │   signs URLs ▶ R2                                              │
   │   streams progress ▶ SSE (subscribes to Redis pub/sub)         │
   └────────────────────────────────────────────────────────────────┘
                  │                              │
                  │ enqueue task                 │ pub/sub progress
                  ▼                              ▼
   ┌────────────────────────────────┐    ┌──────────────────────┐
   │  REDIS  (Render managed)       │◀──▶│  POSTGRES (Render)   │
   │  - Celery broker queues        │    │  Source of truth     │
   │  - rate-limit counters         │    │  (rows + JSONB)      │
   │  - SSE pub/sub channels        │    └──────────────────────┘
   └────────────────────────────────┘
                  │ Celery worker pulls
                  ▼
   ┌────────────────────────────────────────────────────────────────┐
   │            RENDER BACKGROUND WORKER: worker                     │
   │            Celery (Python 3.13) · auto-scale 1–4                │
   │                                                                 │
   │   Pipeline: generate_deck                                       │
   │     ├─ ResearchAdapter ─────────▶  Tavily / Brave + trafilatura │
   │     ├─ TemplateExtractor ───────▶  python-pptx + lxml           │
   │     ├─ LLMAdapter ──────────────▶  OpenAI / Anthropic / Gemini  │
   │     ├─ ImageAdapter (parallel) ─▶  Unsplash / Pexels / Pixabay  │
   │     └─ RendererAdapter ─────────▶  python-pptx → R2             │
   │                                                                 │
   │   Other tasks: export_pptx, extract_template, cleanup_expired   │
   └────────────────────────────────────────────────────────────────┘
                  │
                  ▼
   ┌────────────────────────────────────────────────────────────────┐
   │            OBJECT STORAGE: Cloudflare R2 (S3-compatible)        │
   │            templates/  exports/  images/  uploads/              │
   └────────────────────────────────────────────────────────────────┘

   ┌─────── Observability ────────────────────────────────────────────┐
   │  Sentry (FE + BE errors)   OpenTelemetry → Grafana Cloud         │
   │  Render logs (stdout JSON)                                       │
   └──────────────────────────────────────────────────────────────────┘

   ┌─────── External Auth ────────────────────────────────────────────┐
   │  Clerk → frontend (SDK) + api (JWT verify via JWKS)              │
   └──────────────────────────────────────────────────────────────────┘
```

**Data flow for a generation (happy path):**

1. Browser `POST /projects/{id}/decks` → api.
2. api writes `deck (status=queued)` + `generation_job`; enqueues Celery task → Redis.
3. Browser opens SSE `GET /decks/{id}/stream`; api subscribes to `redis:job:{deck_id}`.
4. worker pulls task → ResearchAdapter → publishes `stage=researching` to Redis.
5. worker → LLMAdapter (with user's key decrypted in-memory) → publishes `stage=writing`.
6. worker → ImageAdapter in parallel per slide → caches images in R2 → publishes `stage=imaging`.
7. worker writes final blueprint to Postgres, sets `status=ready`, publishes `done` event.
8. Browser SSE receives `done` → fetches `GET /decks/{id}` → renders editor.

**Failure isolation:** each adapter is independently retried and circuit-broken; one bad provider key doesn't cascade.
