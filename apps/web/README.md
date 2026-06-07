# Present Yourself — Web

Next.js 16 (App Router) + React 19 + Tailwind v4.

## Local

```bash
cd apps/web
pnpm install        # or: corepack enable && pnpm install
pnpm dev
```

App at http://localhost:3000. Set `NEXT_PUBLIC_API_BASE_URL` if API is not on localhost:8000.

## Dev auth

The current scaffold uses a dev bypass: an `X-Dev-User-Id` header is sent from the
client (configurable from the top-right input in the app shell). Clerk wiring is
ready in the API; the web side will swap in `@clerk/nextjs` when we have keys.

## Layout

```
app/
  page.tsx                       landing
  dashboard/page.tsx             projects grid
  dashboard/new/page.tsx         wizard (4 steps)
  p/[projectId]/page.tsx         project detail
  d/[deckId]/page.tsx            editor + progress
  settings/api-keys/page.tsx     vault UI
components/AppShell.tsx          chrome
lib/api.ts                       typed API client + SSE
lib/schema.ts                    Zod mirror of SlideBlueprint
```
