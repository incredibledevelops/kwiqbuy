"use client";

import { API_URL } from "./api";

function authHeaders(extra = {}) {
  if (typeof window === "undefined") return extra;
  const token = localStorage.getItem("kb_rider_token");
  return token ? { Authorization: `Bearer ${token}`, ...extra } : { ...extra };
}

function clearRiderSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("kb_rider_token");
  localStorage.removeItem("kb_rider_user");
  localStorage.removeItem("kb_rider_issued_at");
}

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

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    ...options,
    headers: authHeaders(options.headers || {}),
  });

  if (res.status === 401) {
    clearRiderSession();
  }

  if (!res.ok) {
    const message = await parseError(res);
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }

  if (res.status === 204) return null;

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

export const riderApi = {
  get: (path) => request(path, { method: "GET" }),
  post: (path, body) =>
    request(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  patch: (path, body) =>
    request(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  del: (path) => request(path, { method: "DELETE" }),
};

export { API_URL };