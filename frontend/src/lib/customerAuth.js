const ACCESS_KEY = "kb_customer_token";
const REFRESH_KEY = "kb_customer_refresh";

export function saveCustomerTokens(access, refresh) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function getCustomerToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getCustomerRefreshToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function clearCustomerTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function isCustomerLoggedIn() {
  return !!getCustomerToken();
}

export async function customerFetch(url, options = {}) {
  const token = getCustomerToken();
  const headers = { ...(options.headers || {}) };
  
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body && !headers["Content-Type"] && typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, { ...options, headers });

  // Optional: handle 401 by clearing token and redirecting
  if (res.status === 401 && typeof window !== "undefined") {
    clearCustomerTokens();
    // Optional: window.location.href = "/account";
  }

  return res;
}