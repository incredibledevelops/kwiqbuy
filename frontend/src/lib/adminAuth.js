const TOKEN_KEY = "kb_admin_token";
const ISSUED_KEY = "kb_admin_token_issued_at";
const USER_KEY = "kb_admin_user";
const SESSION_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

export function saveAdminSession(token, user) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ISSUED_KEY, String(Date.now()));
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getAdminToken() {
  if (typeof window === "undefined") return null;
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return null;
    const issuedAt = Number(localStorage.getItem(ISSUED_KEY) || 0);
    if (issuedAt && Date.now() - issuedAt > SESSION_MAX_AGE_MS) {
      clearAdminSession();
      return null;
    }
    return token;
  } catch {
    return null;
  }
}

export function getAdminUser() {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearAdminSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ISSUED_KEY);
  localStorage.removeItem(USER_KEY);
}