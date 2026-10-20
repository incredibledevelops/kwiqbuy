"use client";

import { API_URL } from "./api";
import {
  getVendorToken,
  clearVendorSession,
  getVendorRefreshToken,
  saveVendorSession,
  getVendorUser,
} from "./vendorAuth";

function authHeaders(extra = {}) {
  const token = getVendorToken();
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

async function tryRefresh() {
  const refresh = getVendorRefreshToken();
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    if (!data.access_token) return false;
    saveVendorSession({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user: getVendorUser(),
    });
    return true;
  } catch {
    return false;
  }
}

async function request(path, options = {}, retried = false) {
  const res = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    ...options,
    headers: authHeaders(options.headers || {}),
  });

  if (res.status === 401 && !retried) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return request(path, options, true);
    }
    clearVendorSession();
  }

  if (!res.ok) {
    const message = await parseError(res);
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }

  if (res.status === 204) return null;

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return res.json();
  }
  return res.text();
}

export const vendorApi = {
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
  upload: async (path, formData) => {
    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const message = await parseError(res);
      const err = new Error(message);
      err.status = res.status;
      throw err;
    }
    return res.json();
  },
};

export { API_URL };