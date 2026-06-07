"use client";

import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { api, type ApiKey, type Provider } from "@/lib/api";
import { formatRelative } from "@/lib/utils";

const ALL_PROVIDERS: Provider[] = [
  "openai", "anthropic", "gemini", "tavily", "unsplash", "pexels", "pixabay", "stability",
];

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [provider, setProvider] = useState<Provider>("openai");
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() { setKeys(await api.listKeys()); }
  useEffect(() => { refresh().catch((e) => setError(String(e))); }, []);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      await api.upsertKey(provider, value);
      setValue("");
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function remove(p: Provider) {
    if (!confirm(`Remove ${p} key?`)) return;
    try {
      await api.deleteKey(p);
      await refresh();
    } catch (e) {
      console.error("Delete key failed:", e);
      setError(String(e));
    }
  }

  const byProvider = Object.fromEntries(keys.map((k) => [k.provider, k]));

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="text-2xl font-semibold">API Keys</h1>
        <p className="text-sm text-[var(--color-fg-muted)] mt-2">
          Your keys are encrypted with AES-256-GCM and never logged.
        </p>

        <div className="card mt-8 divide-y divide-[var(--color-border)]">
          {ALL_PROVIDERS.map((p) => {
            const k = byProvider[p];
            return (
              <div key={p} className="px-5 py-3 flex items-center justify-between text-sm">
                <div className="flex-1">
                  <div className="font-medium capitalize">{p}</div>
                  <div className="text-xs text-[var(--color-fg-muted)] mt-0.5">
                    {k ? <>fingerprint <code className="font-mono">{k.fingerprint}</code> · {k.last_used_at ? `used ${formatRelative(k.last_used_at)}` : "never used"}</> : "Not configured"}
                  </div>
                </div>
                {k && (
                  <button onClick={() => remove(p)} className="btn-ghost text-[var(--color-danger)] p-2">
                    <Trash2 className="size-4" />
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <h2 className="text-lg font-semibold mt-10">Add or replace key</h2>
        <div className="card mt-4 p-5 flex flex-col sm:flex-row gap-3">
          <select className="input sm:max-w-[10rem]" value={provider} onChange={(e) => setProvider(e.target.value as Provider)}>
            {ALL_PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <input className="input flex-1 font-mono" type="password" placeholder="Paste API key" value={value} onChange={(e) => setValue(e.target.value)} />
          <button className="btn-primary" disabled={!value || busy} onClick={save}>{busy ? "Saving…" : "Save"}</button>
        </div>

        {error && <div className="mt-4 text-sm text-[var(--color-danger)]">{error}</div>}
      </div>
    </AppShell>
  );
}
