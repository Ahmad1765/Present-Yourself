import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <header className="border-b border-[var(--color-border)]">
        <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
          <Link href="/" className="font-semibold tracking-tight">Present Yourself</Link>
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/docs" className="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]">Docs</Link>
            <Link href="/dashboard" className="btn-secondary">Sign in</Link>
            <Link href="/dashboard" className="btn-primary">Start free</Link>
          </nav>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 py-24 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <h1 className="text-6xl font-bold tracking-tight leading-[1.05]">
            Decks. Done.
          </h1>
          <p className="mt-6 text-lg text-[var(--color-fg-muted)] max-w-prose">
            Type a topic. Get a draft. Match your brand. AI does the research and the
            first cut — you do the polish in a real editor, and export a clean .pptx.
          </p>
          <div className="mt-8 flex items-center gap-3">
            <Link href="/dashboard" className="btn-primary text-base px-5 py-3">Start free →</Link>
            <Link href="#how" className="btn-ghost text-base px-5 py-3">How it works</Link>
          </div>
          <ul className="mt-12 space-y-3 text-sm text-[var(--color-fg-muted)]">
            <li>✓ 10-slide draft in 90 seconds</li>
            <li>✓ Drop in your PPTX — output matches it</li>
            <li>✓ Export .pptx that opens anywhere</li>
          </ul>
        </div>
        <div aria-hidden className="card aspect-video p-6 flex items-center justify-center">
          <div className="text-[var(--color-fg-subtle)] text-sm">animated deck preview</div>
        </div>
      </section>

      <footer className="border-t border-[var(--color-border)] mt-24">
        <div className="mx-auto max-w-6xl px-6 py-8 text-xs text-[var(--color-fg-subtle)] flex justify-between">
          <span>© 2026 Present Yourself</span>
          <span>v0.1</span>
        </div>
      </footer>
    </main>
  );
}
