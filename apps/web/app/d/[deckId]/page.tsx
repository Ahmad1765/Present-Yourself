"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, Download, Sparkles, Trash2 } from "lucide-react";

import { api, type Deck } from "@/lib/api";
import { SlideBlueprint, type Slide } from "@/lib/schema";

type Stage = "queued" | "researching" | "writing" | "imaging" | "polishing" | "ready" | "failed";

export default function EditorPage() {
  const params = useParams<{ deckId: string }>();
  const deckId = params.deckId;
  const router = useRouter();

  const [deck, setDeck] = useState<Deck | null>(null);
  const [stage, setStage] = useState<Stage>("queued");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [saving, setSaving] = useState<"idle" | "saving" | "saved">("idle");
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const blueprint = useMemo(() => {
    if (!deck || !deck.blueprint || !("schema_version" in (deck.blueprint as object))) return null;
    const parsed = SlideBlueprint.safeParse(deck.blueprint);
    return parsed.success ? parsed.data : null;
  }, [deck]);

  const fetchDeck = useCallback(async () => {
    const d = await api.getDeck(deckId);
    setDeck(d);
    setStage(d.status as Stage);
    if (d.status === "ready") setProgress(100);
  }, [deckId]);

  useEffect(() => { fetchDeck().catch((e) => setError(String(e))); }, [fetchDeck]);

  useEffect(() => {
    if (stage === "ready" || stage === "failed") return;
    const close = api.streamProgress(deckId, (state) => {
      setStage(state.stage as Stage);
      setProgress((state.progress_pct as number) ?? 0);
      if (state.stage === "ready") fetchDeck();
      if (state.stage === "failed") setError(String(state.error ?? "Generation failed"));
    });
    return close;
  }, [deckId, fetchDeck, stage]);

  const handleEdit = useCallback((nextSlides: Slide[]) => {
    if (!blueprint) return;
    const next = { ...blueprint, deck: { ...blueprint.deck, slides: nextSlides } };
    setDeck((d) => (d ? { ...d, blueprint: next } : d));
    setSaving("saving");
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      try {
        await api.saveBlueprint(deckId, next);
        setSaving("saved");
      } catch (e) {
        setError(String(e));
        setSaving("idle");
      }
    }, 1200);
  }, [blueprint, deckId]);

  async function handleExport() {
    const job = await api.exportDeck(deckId);
    // poll briefly
    for (let i = 0; i < 30; i++) {
      const out = await api.getExport(job.id);
      if (out.storage_url) {
        window.open(out.storage_url, "_blank", "noopener");
        return;
      }
      await new Promise((r) => setTimeout(r, 1000));
    }
    alert("Export taking too long — check Exports tab.");
  }

  if (stage !== "ready" && (!deck || !blueprint)) {
    return <GenerationProgress stage={stage} progress={progress} error={error} />;
  }

  if (!blueprint) return <div className="p-8">No blueprint yet.</div>;

  const slides = blueprint.deck.slides;
  const current = slides[selectedIdx];

  return (
    <div className="h-screen grid grid-rows-[3.5rem_1fr]">
      <header className="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/dashboard")} className="btn-ghost p-2"><ChevronLeft className="size-4"/></button>
          <input
            className="font-medium bg-transparent border-0 focus:outline-none w-80"
            value={blueprint.deck.title}
            onChange={(e) => handleEdit(slides.map((s, i) => i === 0 ? s : s))}
            readOnly
          />
          <span className="text-xs text-[var(--color-fg-muted)]">
            {saving === "saving" ? "Saving…" : saving === "saved" ? "Saved" : ""}
          </span>
        </div>
        <button onClick={handleExport} className="btn-primary text-sm">
          <Download className="size-4" /> Export
        </button>
      </header>

      <div className="grid grid-cols-[14rem_1fr_18rem] min-h-0">
        <aside className="border-r border-[var(--color-border)] overflow-y-auto p-2 space-y-2">
          {slides.map((s, i) => (
            <button
              key={s.id}
              onClick={() => setSelectedIdx(i)}
              className={
                "w-full aspect-video card text-left p-3 transition-colors text-xs " +
                (i === selectedIdx ? "ring-2 ring-[var(--color-accent)]" : "hover:bg-[var(--color-surface-2)]")
              }
            >
              <div className="text-[10px] text-[var(--color-fg-subtle)]">{i + 1} · {s.type}</div>
              <div className="mt-1 font-medium line-clamp-3">
                {s.elements.find((e) => e.role === "title")?.content ?? "Untitled"}
              </div>
            </button>
          ))}
        </aside>

        <section className="bg-[var(--color-surface-2)] overflow-y-auto p-8 flex items-start justify-center">
          <div
            className="card shadow-lg w-full max-w-4xl aspect-video p-12 flex flex-col"
            style={{ backgroundColor: blueprint.deck.design_tokens.palette.background, color: blueprint.deck.design_tokens.palette.foreground }}
          >
            <SlideRenderer slide={current} palette={blueprint.deck.design_tokens.palette} />
          </div>
        </section>

        <aside className="border-l border-[var(--color-border)] overflow-y-auto p-4 space-y-4">
          <div>
            <div className="label">Slide {selectedIdx + 1}</div>
            <div className="text-sm font-medium mt-1">{current.type}</div>
          </div>

          <div>
            <div className="label">Speaker notes</div>
            <textarea
              className="input mt-2 min-h-[8rem] text-xs"
              value={current.notes ?? ""}
              onChange={(e) => {
                const next = slides.map((s, i) => i === selectedIdx ? { ...s, notes: e.target.value } : s);
                handleEdit(next);
              }}
            />
          </div>

          <button
            onClick={async () => {
              const hint = window.prompt("Refinement hint (optional)") ?? undefined;
              await api.regenerateSlide(deckId, selectedIdx, hint);
              setTimeout(fetchDeck, 4000);
            }}
            className="btn-secondary w-full text-sm"
          >
            <Sparkles className="size-4" /> Regenerate slide
          </button>

          <button
            onClick={() => {
              if (slides.length <= 1) return;
              const next = slides.filter((_, i) => i !== selectedIdx);
              handleEdit(next);
              setSelectedIdx(Math.max(0, selectedIdx - 1));
            }}
            className="btn-ghost w-full text-sm text-[var(--color-danger)]"
          >
            <Trash2 className="size-4" /> Delete slide
          </button>
        </aside>
      </div>
    </div>
  );
}

function SlideRenderer({ slide, palette }: { slide: Slide; palette: { accent1: string; muted: string } }) {
  const title = slide.elements.find((e) => e.role === "title")?.content ?? "";
  const subtitle = slide.elements.find((e) => e.role === "subtitle")?.content;
  const bullets = slide.elements.find((e) => e.kind === "bullets")?.items ?? [];
  const image = slide.elements.find((e) => e.kind === "image");

  return (
    <div className="h-full flex flex-col">
      <h1 className="text-4xl font-bold" style={{ color: palette.accent1 }}>{title}</h1>
      {subtitle && <p className="mt-2 text-base" style={{ color: palette.muted }}>{subtitle}</p>}
      <div className="mt-6 grid grid-cols-2 gap-6 flex-1 min-h-0">
        <ul className="space-y-2 text-sm">
          {bullets.map((b, i) => <li key={i}>• {b}</li>)}
        </ul>
        {image?.source?.url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={image.source.url as string} alt={image.alt ?? ""} className="object-cover rounded-md w-full h-full" />
        ) : null}
      </div>
    </div>
  );
}

function GenerationProgress({ stage, progress, error }: { stage: Stage; progress: number; error: string | null }) {
  const stages: Array<[Stage, string]> = [
    ["researching", "🔍 Research"],
    ["writing", "✍️ Write"],
    ["imaging", "🖼️ Images"],
    ["polishing", "✨ Polish"],
  ];
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-surface-2)]">
      <div className="card p-10 max-w-md w-full">
        <h2 className="text-lg font-semibold">Building your deck</h2>
        <div className="mt-6 space-y-3">
          {stages.map(([s, label]) => {
            const active = stage === s;
            const done = stages.findIndex(([x]) => x === stage) > stages.findIndex(([x]) => x === s);
            return (
              <div key={s} className="flex items-center gap-3 text-sm">
                <div className={"size-2 rounded-full " + (done || stage === "ready" ? "bg-[var(--color-success)]" : active ? "bg-[var(--color-accent)] animate-pulse" : "bg-[var(--color-border)]")} />
                <div className="flex-1">{label}</div>
                {active && <div className="text-xs text-[var(--color-fg-muted)]">{progress}%</div>}
              </div>
            );
          })}
        </div>
        {error && <div className="mt-4 text-sm text-[var(--color-danger)]">{error}</div>}
        <Link href="/dashboard" className="btn-ghost text-sm mt-6 inline-flex">Cancel</Link>
      </div>
    </div>
  );
}
