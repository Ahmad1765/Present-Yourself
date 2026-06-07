# Document 2: Product Requirements Document (PRD)

**Product:** Present Yourself
**Owner:** Founding team
**Version:** 1.0
**Status:** Ready for build

---

## 1. Problem Statement

Knowledge workers spend 3–8 hours per week building slide decks. Most of that time is **research, writing, layout, and image hunting** — not the high-leverage thinking the deck is supposed to convey. Existing tools split into two failure modes:

1. **Manual editors** (PowerPoint, Google Slides, Keynote) — total control but slow, blank-canvas paralysis, no built-in research.
2. **AI generators** (Tome, Gamma, Beautiful.ai) — fast but produce generic-looking decks that don't match a company's existing template, and most lock users into proprietary export formats.

**Present Yourself** bridges the gap: an AI that does the research and first draft, clones the user's own corporate template, and outputs a clean **.pptx** that drops straight into existing workflows — with a real editor for the last-mile polish.

---

## 2. Target Audience

| Segment | % of focus | Why they pay |
|---|---|---|
| **Consultants & solo professionals** | 40% | Need many decks per week, value time saved, often work on client templates. |
| **Corporate IC's** (PM, marketing, sales) | 35% | Forced to use brand template; resent the manual labor. |
| **Educators & researchers** | 15% | Lecture decks, research summaries; appreciate citation-backed research. |
| **Founders & sales teams** | 10% | Pitch decks, weekly updates; need fast iteration. |

Primary persona: **Maya**, 34, strategy consultant. Lives in PowerPoint. Builds 5+ decks per week. Her firm has a strict brand template. She'll pay $20–40/mo if it saves her one evening per week.

---

## 3. Goals & Non-Goals

### 3.1 Product Goals (12-month)
1. **G1 — Time-to-first-draft < 2 min** for a 10-slide deck from a blank topic field.
2. **G2 — Template fidelity ≥ 90%** — uploaded brand templates produce output that visually matches (subjective expert review).
3. **G3 — Editor parity with Google Slides** for the 80% of editing actions users actually take (text, image swap, reorder, layout change).
4. **G4 — Repeatability** — users average ≥ 3 generations per project; ≥ 30% of new decks start from a saved template.

### 3.2 Non-Goals (v1)
- Real-time multi-user co-editing (Figma-style cursors). Single-user editing with versions only.
- Native mobile apps. Web-first; tablet-responsive.
- Video / audio embedding.
- Advanced chart authoring (we render chart **placeholders**, not interactive chart builder).
- Internal "wiki/knowledge base" integration (Notion, Confluence) — post-v1.

---

## 4. Feature List (Prioritized)

### P0 — Must-have for launch
| ID | Feature | Owner area |
|---|---|---|
| F-01 | Account + auth (Clerk) | FE/BE |
| F-02 | Project dashboard (list, search, duplicate, delete) | FE |
| F-03 | New-project wizard (topic, slide count, image toggle, optional template, optional API key) | FE |
| F-04 | Research pipeline (Tavily + extractor → research brief JSON) | BE |
| F-05 | LLM blueprint generator (OpenAI default; user-key override) | BE |
| F-06 | PPTX template upload + style extraction (`design_tokens`) | BE |
| F-07 | Image fetch (Unsplash default + Pexels fallback) | BE |
| F-08 | Slide editor — text edit, image swap, slide reorder, add/delete, undo/redo | FE |
| F-09 | Layout switcher per slide (8 base layouts) | FE/BE |
| F-10 | Per-slide regenerate; whole-deck regenerate | FE/BE |
| F-11 | Auto-save + version checkpoints | FE/BE |
| F-12 | PPTX export (matches template) | BE |
| F-13 | API key vault (encrypted; per-provider) | BE |
| F-14 | SSE generation progress UI | FE/BE |

### P1 — First fast-follow (weeks 4–8 post-launch)
| ID | Feature |
|---|---|
| F-15 | Template library (save / share within account) |
| F-16 | Speaker notes editor |
| F-17 | Color/font overrides per deck |
| F-18 | Source citations panel (from research brief) |
| F-19 | Anthropic + Gemini adapters |
| F-20 | User-uploaded images (drag-drop into editor) |
| F-21 | Duplicate-project flow (clone settings + blueprint) |

### P2 — Later (post product-market fit)
- PDF export, Google Slides direct push
- Plugin SDK (custom layouts, custom data sources)
- Team workspaces + shared templates
- Real-time collaboration
- AI image generation tab (Stability / OpenAI Images)
- Chart builder for `chart_placeholder` slide type
- pgvector-powered semantic search over user's past decks

---

## 5. Primary User Flows

### 5.1 First-time user → first export ("happy path")
```
Landing
  └─▶ Sign up (Clerk: email or OAuth)
        └─▶ Onboarding: "Add an API key now or use defaults?" (skippable)
              └─▶ Dashboard (empty state CTA: "Create your first deck")
                    └─▶ Wizard step 1: Topic + brief details
                    └─▶ Wizard step 2: Slide count (5–25 slider, default 10)
                    └─▶ Wizard step 3: Template (upload PPTX | use default | skip)
                    └─▶ Wizard step 4: Images (on/off, source preference)
                    └─▶ Click GENERATE
                          └─▶ Progress view: research → write → images → ready
                                └─▶ Editor opens with deck loaded
                                      └─▶ User edits → auto-save
                                      └─▶ Click EXPORT → .pptx downloads
```

### 5.2 Repeat user — clone-and-tweak
```
Dashboard → Project card → "⋯" → Duplicate
  └─▶ New project pre-filled with original settings
  └─▶ User changes slide count: 10 → 15
  └─▶ Click GENERATE → new deck under same project
  └─▶ Both decks visible in project sidebar (v1, v2)
```

### 5.3 Per-slide regenerate
```
Editor → Slide 5 not great
  └─▶ Right-click slide → "Regenerate this slide"
  └─▶ Modal: free-text refinement hint (optional)
  └─▶ LLM called with full deck context + hint → new slide JSON
  └─▶ Old version saved to deck_version (one-click revert)
```

### 5.4 Image swap from search
```
Editor → click image on slide
  └─▶ Side drawer opens: search input, "team collaboration"
  └─▶ Results grid (Unsplash + Pexels merged, dedup'd)
  └─▶ Click image → replaces slot, auto-saves
  └─▶ "Upload" tab → user can drag own image
```

---

## 6. Mock-up Descriptions

### 6.1 Landing Page
- Single hero: H1 "Decks. Done." Sub: "Type a topic. Get a draft. Match your brand."
- Animated deck preview (3 slides rotating) on right.
- One CTA: **Start free**. Secondary: "See a demo".
- Footer with pricing teaser + social proof (logos after launch).

### 6.2 Dashboard
- Top bar: workspace name, search, "+ New deck" button (primary).
- Three tabs: **Projects** (default) · **Templates** · **Exports**.
- Project cards (grid 3-col on desktop) with: thumbnail of first slide, title, slide count, last edited, ⋯ menu (open / duplicate / rename / delete).
- Empty state: large illustration + "Create your first deck" CTA.

### 6.3 New-Project Wizard
- 4 horizontal steps with progress dots.
- Each step is one focused question. Keyboard shortcuts: `Enter` advances, `Esc` cancels.
- "Generate" is the only button on step 4; everything else is back/next.

### 6.4 Generation Progress View
- Center card on dimmed background.
- 4 stages with animated icons: 🔍 Researching → ✍️ Writing → 🖼️ Imaging → ✨ Polishing.
- Status text under each: "Found 12 sources", "Drafted 10 slides", "Selected 7 images".
- Cancel button bottom-right.

### 6.5 Slide Editor
- Left rail: slide thumbnails (drag to reorder, click to focus).
- Center: canvas with the active slide (Konva).
- Right rail: contextual inspector — tabs **Layout · Style · Notes · AI**.
- Top bar: deck title, version dropdown, **Export** primary button.
- Floating toolbar above selected element (text formatting, image actions).

### 6.6 Template Upload Modal
- Drag-and-drop zone for `.pptx`.
- After parse: preview pane shows extracted master, palette swatches, fonts.
- "Save as template" → goes into Templates tab.

### 6.7 Settings → API Keys
- Table: Provider · Key fingerprint · Last used · Replace · Delete.
- Add-key form: provider dropdown, paste field (masked), validate button (test request).
- Banner: "Your keys are encrypted with AES-256 and never leave our servers."

---

## 7. Success Metrics

| Metric | Target (90 days post-launch) | Instrumentation |
|---|---|---|
| Activation: signup → first export | ≥ 45% | Mixpanel funnel |
| Time-to-first-draft (median) | ≤ 90s | API timing logs |
| Generation success rate | ≥ 95% | `deck.status='ready'` / total |
| Decks per active user per week | ≥ 2.5 | Aggregated query |
| Template upload rate (paid users) | ≥ 60% | Product telemetry |
| Editor session length (median) | 4–12 min (engaged but not stuck) | FE analytics |
| W4 retention | ≥ 25% | Cohort analysis |
| NPS (in-app survey, after 3rd export) | ≥ 40 | Survicate |

---

## 8. Release Criteria

A build ships to production when:
- All **P0** features functional end-to-end on staging for 7 consecutive days.
- 0 critical bugs, ≤ 5 high bugs in tracker.
- Generation success rate ≥ 95% across 500 synthetic deck runs (smoke test suite).
- Median end-to-end generation time ≤ 45s on Render `standard` tier.
- PPTX output passes round-trip test: open in PowerPoint 2021, Google Slides, LibreOffice — no broken layouts.
- Security review: API key vault verified, RLS-equivalent checks on every BE query, OWASP top-10 scan clean.
- Privacy: data export + delete-my-account both work.
- Pricing page + billing (Stripe) wired (even if launching with single tier).

---

## 9. Out of Scope (Explicit)

- Co-editing / shared cursors
- Native iOS / Android
- Voice generation, video export
- AI chart authoring (placeholders only)
- Enterprise SSO (SAML/SCIM) — post-Series A
- On-prem deployment
- Custom-domain white-label
- Slide animations / transitions
