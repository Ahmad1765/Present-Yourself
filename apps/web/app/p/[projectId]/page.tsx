"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { api, type Project } from "@/lib/api";

export default function ProjectPage() {
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);

  useEffect(() => {
    api.getProject(params.projectId).then(setProject);
  }, [params.projectId]);

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-6 py-10">
        <Link href="/dashboard" className="text-sm text-[var(--color-fg-muted)] hover:underline">← Back to projects</Link>
        {project && (
          <>
            <h1 className="text-2xl font-semibold mt-4">{project.title}</h1>
            <p className="text-sm text-[var(--color-fg-muted)] mt-2">{project.topic}</p>
            <div className="mt-8 card p-8 text-sm text-[var(--color-fg-muted)]">
              Deck list per project — to be wired to <code>GET /v1/decks?project_id=…</code> in the next iteration.
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
