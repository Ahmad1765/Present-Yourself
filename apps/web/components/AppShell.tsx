"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export function AppShell({ children, action }: { children: React.ReactNode; action?: React.ReactNode }) {
  const [devUserId, setDevUserId] = useState("");

  useEffect(() => {
    const id = window.localStorage.getItem("dev_user_id") ?? "dev-local";
    setDevUserId(id);
  }, []);

  function setUid(value: string) {
    setDevUserId(value);
    window.localStorage.setItem("dev_user_id", value || "dev-local");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="mx-auto max-w-7xl px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="font-semibold tracking-tight">Present Yourself</Link>
            <nav className="flex items-center gap-1 text-sm">
              <Link href="/dashboard" className="px-3 py-1.5 rounded-md hover:bg-[var(--color-surface-2)]">Projects</Link>
              <Link href="/dashboard/templates" className="px-3 py-1.5 rounded-md hover:bg-[var(--color-surface-2)]">Templates</Link>
              <Link href="/dashboard/exports" className="px-3 py-1.5 rounded-md hover:bg-[var(--color-surface-2)]">Exports</Link>
              <Link href="/settings/api-keys" className="px-3 py-1.5 rounded-md hover:bg-[var(--color-surface-2)]">Settings</Link>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <input
              aria-label="Dev user id"
              className="input max-w-[12rem] text-xs"
              placeholder="dev user id"
              value={devUserId}
              onChange={(e) => setUid(e.target.value)}
            />
            {action}
          </div>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
