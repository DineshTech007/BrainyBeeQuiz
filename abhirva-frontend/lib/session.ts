/**
 * Session Manager — stores the JWT access token returned by the backend /api/auth/login.
 * Uses sessionStorage so it's automatically cleared when the browser tab is closed.
 * Provides helpers to get, set, and clear the session.
 */

const BACKEND_URL = process.env.NODE_ENV === "production" ? "https://abhirva-backend.onrender.com" : "http://127.0.0.1:8000";

export interface SessionProfile {
  id: string;
  full_name: string;
  email: string;
  role: "STUDENT" | "PARENT" | "ADMIN";
  total_points?: number;
  book_points?: number;
  free_tests_taken?: number;
  grade?: string;
}

export interface Session {
  access_token: string;
  refresh_token?: string;
  profile: SessionProfile;
}

const SESSION_KEY = "abhirva_session";

// ---------------------------------------------------------------------------
// Storage helpers
// ---------------------------------------------------------------------------
export function saveSession(session: Session): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(SESSION_KEY);
  // Also clear any legacy localStorage keys
  const legacyKeys = [
    "isLoggedIn", "student_name", "student_id",
    "user_id", "user_name", "user_role", "parent_name",
  ];
  legacyKeys.forEach(k => localStorage.removeItem(k));
}

export function isAuthenticated(): boolean {
  return getSession() !== null;
}

export function getProfile(): SessionProfile | null {
  return getSession()?.profile ?? null;
}

// ---------------------------------------------------------------------------
// API Calls
// ---------------------------------------------------------------------------
export async function loginWithCredentials(
  email: string,
  password: string
): Promise<Session> {
  const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Login failed. Please check your credentials.");
  }

  if (data.status !== "success") {
    throw new Error(data.detail || "Authentication failed.");
  }

  const session: Session = {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    profile: data.profile,
  };

  saveSession(session);
  return session;
}

export async function signupUser(params: {
  email: string;
  password: string;
  full_name: string;
  role: string;
  grade?: string;
}): Promise<{ profile_id: string; email: string; full_name: string; role: string; grade?: string }> {
  const res = await fetch(`${BACKEND_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Signup failed.");
  }

  return data;
}

export async function logoutUser(): Promise<void> {
  try {
    await fetch(`${BACKEND_URL}/api/auth/logout`, { method: "POST" });
  } catch {
    // ignore network errors on logout
  } finally {
    clearSession();
  }
}
