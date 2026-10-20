const TOKEN_KEY = "kb_vendor_token";
const REFRESH_KEY = "kb_vendor_refresh";
const USER_KEY = "kb_vendor_user";
const ISSUED_KEY = "kb_vendor_issued_at";
const SESSION_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

export function saveVendorSession({ accessToken, refreshToken, user }) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(ISSUED_KEY, String(Date.now()));
}

export function getVendorToken() {
  if (typeof window === "undefined") return null;
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return null;
    const issuedAt = Number(localStorage.getItem(ISSUED_KEY) || 0);
    if (issuedAt && Date.now() - issuedAt > SESSION_MAX_AGE_MS) {
      clearVendorSession();
      return null;
    }
    return token;
  } catch {
    return null;
  }
}

export function getVendorRefreshToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function getVendorUser() {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearVendorSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(ISSUED_KEY);
}

export function isVendorLoggedIn() {
  return !!getVendorToken();
}