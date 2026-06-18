"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Session,
  SessionProfile,
  getSession,
  clearSession,
  logoutUser,
  loginWithCredentials,
  saveSession,
} from "./session";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface AuthContextValue {
  session: Session | null;
  profile: SessionProfile | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateSession: (updates: Partial<SessionProfile>) => void;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------
const AuthContext = createContext<AuthContextValue>({
  session: null,
  profile: null,
  isLoading: true,
  error: null,
  login: async () => {},
  logout: async () => {},
  updateSession: () => {},
});

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load session from sessionStorage on mount
  useEffect(() => {
    const stored = getSession();
    setSession(stored);
    setIsLoading(false);
  }, []);

  // ------------------------------------------------------------------
  // Login
  // ------------------------------------------------------------------
  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const sess = await loginWithCredentials(email, password);
      setSession(sess);
    } catch (err: any) {
      setError(err.message || "Login failed.");
      throw err; // re-throw so the form can catch it
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ------------------------------------------------------------------
  // Logout — clears ALL state and forces a hard redirect to /login
  // ------------------------------------------------------------------
  const logout = useCallback(async () => {
    try {
      await logoutUser();
    } catch {
      // even if network fails, clear local session
      clearSession();
    } finally {
      setSession(null);
      setError(null);
      // Hard redirect so back-button history cannot bypass auth
      window.location.href = "/login";
    }
  }, []);

  // ------------------------------------------------------------------
  // Update Profile Attributes in current session
  // ------------------------------------------------------------------
  const updateSession = useCallback((updates: Partial<SessionProfile>) => {
    setSession(prev => {
      if (!prev) return null;
      const updatedProfile = { ...prev.profile, ...updates };
      const newSession = { ...prev, profile: updatedProfile };
      saveSession(newSession);
      return newSession;
    });
  }, []);

  const profile = session?.profile ?? null;

  return (
    <AuthContext.Provider value={{ session, profile, isLoading, error, login, logout, updateSession }}>
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
export function useAuth() {
  return useContext(AuthContext);
}

// ---------------------------------------------------------------------------
// Auth Guard Component — use inside pages that require authentication
// ---------------------------------------------------------------------------
interface AuthGuardProps {
  children: React.ReactNode;
  requiredRole?: "STUDENT" | "PARENT" | "ADMIN";
}

export function AuthGuard({ children, requiredRole }: AuthGuardProps) {
  const { session, profile, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (!session) {
      router.replace("/login");
      return;
    }

    if (requiredRole && profile?.role !== requiredRole) {
      // Wrong role — redirect to their correct dashboard
      const roleRoutes: Record<string, string> = {
        STUDENT: "/student/dashboard",
        PARENT: "/parent/dashboard",
        ADMIN: "/admin",
      };
      const correctRoute = profile?.role ? roleRoutes[profile.role] : "/login";
      router.replace(correctRoute || "/login");
    }
  }, [session, profile, isLoading, requiredRole, router]);

  if (isLoading) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "60vh",
          flexDirection: "column",
          gap: "1.5rem",
        }}
      >
        <div
          style={{
            width: "52px",
            height: "52px",
            border: "4px solid rgba(99, 102, 241, 0.25)",
            borderTopColor: "#6366f1",
            borderRadius: "50%",
            animation: "spin 0.8s linear infinite",
          }}
        />
        <p style={{ color: "var(--text-secondary)", fontSize: "1rem", letterSpacing: "0.05em" }}>
          Verifying your session...
        </p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!session) return null;
  if (requiredRole && profile?.role !== requiredRole) return null;

  return <>{children}</>;
}
