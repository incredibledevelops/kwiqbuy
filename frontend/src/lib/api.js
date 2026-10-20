import { randomKey } from "./utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function parseError(res) {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
    }
    return `${res.status} ${res.statusText}`;
  } catch {
    return `${res.status} ${res.statusText}`;
  }
}

export async function apiGet(path, options = {}) {
  const { token, headers: extraHeaders = {}, ...rest } = options;
  const headers = { ...extraHeaders };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    headers,
    ...rest,
  });
  if (!res.ok) throw new Error(await parseError(res));
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

export async function apiSend(path, method, body, options = {}) {
  const { token, idempotencyKey, headers: extraHeaders = {} } = options;
  const headers = { "Content-Type": "application/json", ...extraHeaders };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (method === "POST" && !headers["X-Idempotency-Key"]) {
    headers["X-Idempotency-Key"] = idempotencyKey || randomKey();
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body:
      body !== undefined && body !== null ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) throw new Error(await parseError(res));
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

export async function apiUpload(path, formData, { token } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) throw new Error(await parseError(res));
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

export { API_URL, randomKey };