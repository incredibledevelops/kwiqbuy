"use client";

import { API_URL } from "./api";
import { getAdminToken, clearAdminSession } from "./adminAuth";

function authHeaders(extra = {}) {
  const token = getAdminToken();
  return token ? { Authorization: `Bearer ${token}`, ...extra } : { ...extra };
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
    clearAdminSession();
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

export const adminApi = {
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
  download: async (path, suggestedFilename) => {
    const res = await fetch(`${API_URL}${path}`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      const message = await parseError(res);
      const err = new Error(message);
      err.status = res.status;
      throw err;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = suggestedFilename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

export { API_URL };