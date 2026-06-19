"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import styles from "../signup/signup.module.css";
import { useAuth } from "../../lib/auth-context";

export default function Login() {
  const router = useRouter();
  const { login, session, isLoading: authLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // If already logged in, redirect to the correct dashboard
  useEffect(() => {
    if (!authLoading && session?.profile) {
      const roleRoutes: Record<string, string> = {
        STUDENT: "/student/dashboard",
        PARENT: "/parent/dashboard",
        ADMIN: "/admin",
      };
      const dest = roleRoutes[session.profile.role] || "/student/dashboard";
      router.replace(dest);
    }
  }, [session, authLoading, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError("Please enter both email and password.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await login(email.trim(), password);

      // login() saves session — now read the profile to route
      const { getSession } = await import("../../lib/session");
      const sess = getSession();
      if (!sess?.profile) throw new Error("Session not found after login.");

      const roleRoutes: Record<string, string> = {
        STUDENT: "/student/dashboard",
        PARENT: "/parent/dashboard",
        ADMIN: "/admin",
      };
      const dest = roleRoutes[sess.profile.role] || "/student/dashboard";
      router.push(dest);
    } catch (err: any) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <div style={{
          width: "48px", height: "48px",
          border: "4px solid rgba(99, 102, 241, 0.3)",
          borderTopColor: "#6366f1",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div className={styles.signupContainer}>
      <div className={`glass-panel ${styles.signupCard}`}>
        <div style={{ textAlign: "center", marginBottom: "0.5rem" }}>
          <span style={{ fontSize: "2.5rem" }}>🔐</span>
        </div>
        <h1 className={styles.title}>Welcome Back</h1>
        <p className={styles.subtitle}>Login to your Abhirva Learning account</p>

        {error && (
          <div style={{
            background: "rgba(244, 63, 94, 0.1)",
            border: "1px solid rgba(244, 63, 94, 0.4)",
            borderRadius: "8px",
            padding: "0.75rem 1rem",
            marginBottom: "1rem",
            color: "var(--accent-color)",
            fontSize: "0.9rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}>
            <span>⚠️</span> {error}
          </div>
        )}

        <form className={styles.form} onSubmit={handleLogin}>
          <div className={styles.inputGroup}>
            <label>Email or Username</label>
            <input
              type="text"
              className={styles.input}
              placeholder="Email or Username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="username"
              disabled={loading}
            />
          </div>

          <div className={styles.inputGroup}>
            <label>Password</label>
            <div style={{ position: "relative" }}>
              <input
                type={showPassword ? "text" : "password"}
                className={styles.input}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                disabled={loading}
                style={{ paddingRight: "3rem" }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(v => !v)}
                style={{
                  position: "absolute",
                  right: "0.75rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "1.1rem",
                  color: "var(--text-secondary)",
                  padding: "0.25rem",
                }}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "🙈" : "👁️"}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className={styles.submitBtn}
            disabled={loading || !email || !password}
            style={{ marginTop: "0.5rem" }}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}>
                <span style={{
                  width: "16px", height: "16px",
                  border: "2px solid rgba(255,255,255,0.4)",
                  borderTopColor: "white",
                  borderRadius: "50%",
                  display: "inline-block",
                  animation: "spin 0.7s linear infinite",
                }} />
                Signing in...
              </span>
            ) : "Login"}
          </button>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </form>

        <div style={{ marginTop: "1.5rem", textAlign: "center", fontSize: "0.9rem", color: "var(--text-secondary)" }}>
          <p>
            Don't have an account?{" "}
            <Link href="/signup" style={{ color: "var(--primary-color)", fontWeight: 600 }}>
              Sign up here
            </Link>
          </p>
          <p style={{ marginTop: "0.5rem" }}>
            <Link href="/" style={{ color: "var(--text-secondary)", textDecoration: "underline", fontSize: "0.85rem" }}>
              ← Back to Home
            </Link>
          </p>
        </div>

        <div style={{
          marginTop: "1.5rem",
          padding: "0.75rem",
          background: "rgba(99, 102, 241, 0.08)",
          borderRadius: "8px",
          border: "1px solid rgba(99, 102, 241, 0.15)",
          fontSize: "0.8rem",
          color: "var(--text-secondary)",
          textAlign: "center",
        }}>
          🔒 Secured by Abhirva Auth — your credentials are never stored locally
        </div>
      </div>
    </div>
  );
}
