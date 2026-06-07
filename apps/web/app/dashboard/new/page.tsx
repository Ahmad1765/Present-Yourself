"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function NewProjectWizard() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [brief, setBrief] = useState("");
  const [slideCount, setSlideCount] = useState(10);
  const [withImages, setWithImages] = useState(true);
  const [modelProvider, setModelProvider] = useState<"openai" | "anthropic" | "gemini">("openai");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const project = await api.createProject({ title: title || topic, topic, brief, language: "en" });
      const deck = await api.generateDeck(project.id, {
        slide_count: slideCount,
        with_images: withImages,
        model_provider: modelProvider,
      });
      router.push(`/d/${deck.id}?status=generating`);
    } catch (e) {
      setError(String(e));
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-2xl px-6 py-12">
        <Stepper step={step} />

        {step === 0 && (
          <section className="card p-8 mt-8">
            <h2 className="text-xl font-semibold">What&apos;s your deck about?</h2>
            <label className="label mt-6 block">Topic</label>
            <input
              autoFocus
              className="input mt-2"
              placeholder="Future of electric aviation"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
            <label className="label mt-6 block">Title (optional)</label>
            <input
              className="input mt-2"
              placeholder="Defaults to topic"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <label className="label mt-6 block">Audience &amp; tone (optional)</label>
            <textarea
              className="input mt-2 min-h-[6rem]"
              placeholder="e.g. aerospace execs, optimistic but data-driven"
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
            />
            <NavButtons disabled={!topic.trim()} onNext={() => setStep(1)} />
          </section>
        )}

        {step === 1 && (
          <section className="card p-8 mt-8">
            <h2 className="text-xl font-semibold">How many slides?</h2>
            <p className="mt-2 text-sm text-[var(--color-fg-muted)]">≈ {Math.max(45, slideCount * 9)}s to generate</p>
            <div className="mt-6 flex items-center gap-4">
              <input
                type="range" min={5} max={25}
                className="flex-1"
                value={slideCount}
                onChange={(e) => setSlideCount(Number(e.target.value))}
              />
              <div className="text-3xl font-semibold tabular-nums w-12 text-right">{slideCount}</div>
            </div>
            <NavButtons onBack={() => setStep(0)} onNext={() => setStep(2)} />
          </section>
        )}

        {step === 2 && (
          <section className="card p-8 mt-8">
            <h2 className="text-xl font-semibold">Template &amp; images</h2>

            <label className="mt-6 flex items-center gap-3 text-sm">
              <input type="checkbox" checked={withImages} onChange={(e) => setWithImages(e.target.checked)} />
              Add relevant images automatically
            </label>

            <label className="label mt-6 block">AI model</label>
            <select className="input mt-2" value={modelProvider} onChange={(e) => setModelProvider(e.target.value as never)}>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic Claude</option>
              <option value="gemini">Google Gemini</option>
            </select>

            <p className="mt-6 text-xs text-[var(--color-fg-muted)]">
              Templates: upload yours from the Templates tab — coming next in the wizard.
            </p>

            <NavButtons onBack={() => setStep(1)} onNext={() => setStep(3)} />
          </section>
        )}

        {step === 3 && (
          <section className="card p-8 mt-8">
            <h2 className="text-xl font-semibold">Ready to generate</h2>
            <dl className="mt-6 grid grid-cols-2 gap-y-3 text-sm">
              <dt className="text-[var(--color-fg-muted)]">Topic</dt><dd>{topic}</dd>
              <dt className="text-[var(--color-fg-muted)]">Slides</dt><dd>{slideCount}</dd>
              <dt className="text-[var(--color-fg-muted)]">Images</dt><dd>{withImages ? "On" : "Off"}</dd>
              <dt className="text-[var(--color-fg-muted)]">Model</dt><dd>{modelProvider}</dd>
            </dl>
            {error && <div className="mt-4 text-sm text-[var(--color-danger)]">{error}</div>}
            <div className="mt-8 flex justify-end gap-3">
              <button className="btn-secondary" onClick={() => setStep(2)} disabled={submitting}>Back</button>
              <button className="btn-primary" onClick={submit} disabled={submitting}>
                {submitting ? "Generating…" : "Generate →"}
              </button>
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}

function Stepper({ step }: { step: number }) {
  return (
    <ol className="flex items-center gap-2 text-xs text-[var(--color-fg-muted)]">
      {["Topic", "Slides", "Style", "Generate"].map((label, i) => (
        <li key={label} className="flex items-center gap-2">
          <span
            className={
              "size-6 rounded-full inline-flex items-center justify-center text-[10px] font-medium " +
              (i < step ? "bg-[var(--color-accent)] text-white" :
                i === step ? "border border-[var(--color-accent)] text-[var(--color-accent)]" :
                "border border-[var(--color-border)]")
            }
          >{i + 1}</span>
          {label}
          {i < 3 && <span className="text-[var(--color-fg-subtle)]">·</span>}
        </li>
      ))}
    </ol>
  );
}

function NavButtons({ onBack, onNext, disabled }: { onBack?: () => void; onNext: () => void; disabled?: boolean }) {
  return (
    <div className="mt-8 flex justify-end gap-3">
      {onBack && <button className="btn-secondary" onClick={onBack}>Back</button>}
      <button className="btn-primary" onClick={onNext} disabled={disabled}>Next →</button>
    </div>
  );
}
