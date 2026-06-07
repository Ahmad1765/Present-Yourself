// Lightweight typed API client. Server-side reads NEXT_PUBLIC_API_BASE_URL.
import type { SlideBlueprint } from "./schema";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Provider =
  | "openai"
  | "anthropic"
  | "gemini"
  | "tavily"
  | "unsplash"
  | "pexels"
  | "pixabay"
  | "stability";

export interface Project {
  id: string;
  title: string;
  topic: string;
  brief: string | null;
  language: string;
  template_id: string | null;
  default_settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Deck {
  id: string;
  project_id: string;
  status: "queued" | "researching" | "writing" | "imaging" | "polishing" | "ready" | "failed";
  slide_count: number;
  blueprint: SlideBlueprint | Record<string, never>;
  generation_meta: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ApiKey {
  provider: Provider;
  fingerprint: string;
  last_used_at: string | null;
  created_at: string;
}

export interface Template {
  id: string;
  name: string;
  design_tokens: Record<string, unknown>;
  thumbnail_url: string | null;
  created_at: string;
}

export interface GenerationSettings {
  slide_count: number;
  with_images: boolean;
  model_provider: "openai" | "anthropic" | "gemini";
  image_providers?: Array<"unsplash" | "pexels" | "pixabay">;
  template_id?: string | null;
  hints?: string | null;
  tone?: string | null;
  audience?: string | null;
}

function devHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const uid = window.localStorage.getItem("dev_user_id") ?? "dev-local";
  return { "X-Dev-User-Id": uid };
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const r = await fetch(`${BASE}/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...devHeader(),
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!r.ok) {
    let body: unknown = null;
    try { body = await r.json(); } catch { /* ignore */ }
    throw new ApiError(r.status, r.statusText, body);
  }
  if (r.status === 204) return undefined as T;
  return (await r.json()) as T;
}

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, statusText: string, body: unknown) {
    super(`${status} ${statusText}`);
    this.status = status;
    this.body = body;
  }
}

export const api = {
  me: () => request<{ id: string; email: string }>(`/me`),

  listKeys: () => request<ApiKey[]>(`/api-keys`),
  upsertKey: (provider: Provider, key: string) =>
    request<ApiKey>(`/api-keys`, { method: "POST", body: JSON.stringify({ provider, key }) }),
  deleteKey: (provider: Provider) => request<void>(`/api-keys/${provider}`, { method: "DELETE" }),

  listProjects: (q?: string) =>
    request<Project[]>(`/projects${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  createProject: (data: Partial<Project>) =>
    request<Project>(`/projects`, { method: "POST", body: JSON.stringify(data) }),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  duplicateProject: (id: string) =>
    request<Project>(`/projects/${id}/duplicate`, { method: "POST" }),
  deleteProject: (id: string) =>
    request<void>(`/projects/${id}`, { method: "DELETE" }),

  generateDeck: (projectId: string, settings: GenerationSettings) =>
    request<Deck>(`/projects/${projectId}/decks`, {
      method: "POST",
      body: JSON.stringify(settings),
    }),
  getDeck: (id: string) => request<Deck>(`/decks/${id}`),
  saveBlueprint: (id: string, blueprint: SlideBlueprint, label?: string) =>
    request<Deck>(`/decks/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ blueprint, label }),
    }),
  regenerateSlide: (deckId: string, idx: number, hint?: string) =>
    request<{ task_id: string }>(`/decks/${deckId}/slides/${idx}/regenerate`, {
      method: "POST",
      body: JSON.stringify({ hint }),
    }),
  exportDeck: (deckId: string) =>
    request<{ id: string; storage_url: string | null }>(`/decks/${deckId}/export`, {
      method: "POST",
      body: JSON.stringify({ format: "pptx" }),
    }),
  getExport: (id: string) =>
    request<{ id: string; storage_url: string | null }>(`/exports/${id}`),

  listTemplates: () => request<Template[]>(`/templates`),
  registerTemplate: (name: string, storageKey: string) =>
    request<Template>(`/templates`, {
      method: "POST",
      body: JSON.stringify({ name, storage_key: storageKey }),
    }),

  signUpload: (purpose: "template" | "image", contentType: string, size: number) =>
    request<{ upload_url: string; storage_key: string; expires_in: number }>(`/uploads/sign`, {
      method: "POST",
      body: JSON.stringify({ purpose, content_type: contentType, size }),
    }),

  searchImages: (q: string, providers = "unsplash,pexels", page = 1) =>
    request<{ results: Array<{ provider: string; url: string; thumb_url: string; credit: string }>; next_page: number | null }>(
      `/images/search?q=${encodeURIComponent(q)}&providers=${providers}&page=${page}`,
    ),

  streamProgress(deckId: string, onState: (state: { stage: string; progress_pct: number; [k: string]: unknown }) => void): () => void {
    const uid = typeof window !== "undefined" ? window.localStorage.getItem("dev_user_id") ?? "dev-local" : "dev-local";
    const url = new URL(`${BASE}/v1/decks/${deckId}/stream`);
    url.searchParams.set("dev_user_id", uid); // EventSource cannot set headers
    const es = new EventSource(url.toString());
    es.addEventListener("state", (ev) => {
      try { onState(JSON.parse((ev as MessageEvent).data)); } catch { /* ignore */ }
    });
    es.addEventListener("error", () => es.close());
    return () => es.close();
  },
};
