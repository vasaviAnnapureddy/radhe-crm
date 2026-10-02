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

// 502, 503 and 504 mean the request never reached our app (the host's router could not pass it on,
// or the free server was still waking up). Trying again is safe, so we do it quietly, up to three times.
const GATEWAY_ERRORS = [502, 503, 504];
const RETRY_WAITS_MS = [500, 1500, 3000];
const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function api<T>(path: string, options: { method?: string; body?: unknown; params?: Params } = {}): Promise<T> {
  let reply: Response | null = null;
  for (let attempt = 0; attempt <= RETRY_WAITS_MS.length; attempt++) {
    try {
      reply = await fetch(`/api${withParams(path, options.params)}`, {
        method: options.method ?? "GET",
        credentials: "same-origin",
        headers: options.body ? { "Content-Type": "application/json" } : undefined,
        body: options.body ? JSON.stringify(options.body) : undefined,
      });
    } catch {
      reply = null;
    }
    const retry = (!reply || GATEWAY_ERRORS.includes(reply.status)) && attempt < RETRY_WAITS_MS.length;
    if (!retry) break;
    await wait(RETRY_WAITS_MS[attempt]);
  }
  if (!reply) throw new ApiError(0, "Cannot reach the server. Please try again in a moment.");
  if (GATEWAY_ERRORS.includes(reply.status)) {
    throw new ApiError(reply.status, "The server is waking up. Please try again in a few seconds.");
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
