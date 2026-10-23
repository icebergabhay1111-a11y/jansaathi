// Browser-side API client. All calls go to same-origin /api (proxied to FastAPI by next.config.ts).

export class ApiError extends Error {
  status: number;
  fieldErrors: { field: string; message: string }[];
  constructor(status: number, message: string, fieldErrors: { field: string; message: string }[] = []) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

function messageFrom(data: unknown, status: number): string {
  const d = (data as { detail?: unknown })?.detail;
  if (typeof d === "string") return d;
  if (d && typeof d === "object" && Array.isArray((d as { errors?: unknown }).errors)) return ((d as { errors: string[] }).errors).join("; ");
  if (status === 0) return "You appear to be offline. Check your connection and try again.";
  if (status >= 500) return "Something went wrong on our side. Please try again.";
  return "Request failed.";
}

export async function api<T = unknown>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const { json, headers, ...rest } = init;
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      ...rest,
      credentials: "same-origin",
      headers: {
        "x-requested-with": "jansaathi",
        ...(json !== undefined ? { "content-type": "application/json" } : {}),
        ...headers,
      },
      body: json !== undefined ? JSON.stringify(json) : rest.body,
    });
  } catch {
    throw new ApiError(0, messageFrom(null, 0));
  }
  const text = await res.text();
  let data: unknown = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = null; }
  if (!res.ok) {
    const errs = (data as { errors?: { field: string; message: string }[] })?.errors || [];
    throw new ApiError(res.status, messageFrom(data, res.status), errs);
  }
  return data as T;
}
