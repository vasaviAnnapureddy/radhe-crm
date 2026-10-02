// The one place that talks to the backend. Always the same address as the page (/api/...), so the
// login cookie is sent automatically and there are no cross-site problems.

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export const SIGNED_OUT_EVENT = "radhe:signed-out";

export type Params = Record<string, string | number | boolean | null | undefined>;

export function withParams(path: string, params?: Params): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== null && value !== undefined && value !== "") query.set(key, String(value));
  }
  const text = query.toString();
  return text ? `${path}${path.includes("?") ? "&" : "?"}${text}` : path;
}

export async function api<T>(path: string, options: { method?: string; body?: unknown; params?: Params } = {}): Promise<T> {
  let reply: Response;
  try {
    reply = await fetch(`/api${withParams(path, options.params)}`, {
      method: options.method ?? "GET",
      credentials: "same-origin",
      headers: options.body ? { "Content-Type": "application/json" } : undefined,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check that the backend is running.");
  }
  if (reply.status === 204) return undefined as T;
  if (!reply.ok) {
    let message = `Request failed (${reply.status}).`;
    try {
      const detail = (await reply.json()).detail;
      if (typeof detail === "string") message = detail;
    } catch { /* the reply had no JSON body */ }
    if (reply.status === 401 && !path.startsWith("/auth/")) window.dispatchEvent(new Event(SIGNED_OUT_EVENT));
    throw new ApiError(reply.status, message);
  }
  return reply.json() as Promise<T>;
}
