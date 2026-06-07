"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus, MoreHorizontal, Sparkles } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { api, type Project } from "@/lib/api";
import { formatRelative } from "@/lib/utils";

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    api.listProjects(q).then(setProjects).catch((e) => setError(String(e)));
  }, [q]);

  return (
    <AppShell action={<NewDeckButton />}>
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-semibold tracking-tight">Projects</h1>
          <input
            className="input max-w-sm"
            placeholder="Search projects…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>

        {error && (
          <div className="card p-4 text-sm text-[var(--color-danger)] mb-6">{error}</div>
        )}

        {projects === null && <div className="text-sm text-[var(--color-fg-muted)]">Loading…</div>}

        {projects?.length === 0 && <EmptyState />}

        {projects && projects.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {projects.map((p) => (
              <ProjectCard key={p.id} project={p} onChange={() => api.listProjects(q).then(setProjects)} />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}

function NewDeckButton() {
  return (
    <Link href="/dashboard/new" className="btn-primary text-sm">
      <Plus className="size-4" /> New deck
    </Link>
  );
}

function EmptyState() {
  return (
    <div className="card p-12 text-center">
      <Sparkles className="mx-auto size-8 text-[var(--color-fg-subtle)]" />
      <h2 className="mt-4 text-lg font-medium">Create your first deck</h2>
      <p className="mt-2 text-sm text-[var(--color-fg-muted)]">
        Type a topic, pick a slide count, hit generate.
      </p>
      <Link href="/dashboard/new" className="btn-primary mt-6 inline-flex">
        <Plus className="size-4" /> New deck
      </Link>
    </div>
  );
}

function ProjectCard({ project, onChange }: { project: Project; onChange: () => void }) {
  async function duplicate() {
    await api.duplicateProject(project.id);
    onChange();
  }
  async function remove() {
    if (!confirm(`Delete "${project.title}"?`)) return;
    await api.deleteProject(project.id);
    onChange();
  }
  return (
    <div className="card overflow-hidden group">
      <Link href={`/p/${project.id}`} className="block">
        <div className="aspect-video bg-[var(--color-surface-2)] flex items-center justify-center text-xs text-[var(--color-fg-subtle)]">
          {project.title}
        </div>
      </Link>
      <div className="p-4 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-medium text-sm">{project.title}</div>
          <div className="text-xs text-[var(--color-fg-muted)] mt-1">
            {formatRelative(project.updated_at)}
          </div>
        </div>
        <details className="relative">
          <summary className="btn-ghost cursor-pointer list-none p-1 rounded-md">
            <MoreHorizontal className="size-4" />
          </summary>
          <div className="absolute right-0 mt-1 w-40 card shadow-lg p-1 text-sm z-10">
            <Link href={`/p/${project.id}`} className="block px-3 py-1.5 rounded hover:bg-[var(--color-surface-2)]">Open</Link>
            <button onClick={duplicate} className="block w-full text-left px-3 py-1.5 rounded hover:bg-[var(--color-surface-2)]">Duplicate</button>
            <button onClick={remove} className="block w-full text-left px-3 py-1.5 rounded text-[var(--color-danger)] hover:bg-[var(--color-surface-2)]">Delete</button>
          </div>
        </details>
      </div>
    </div>
  );
}
