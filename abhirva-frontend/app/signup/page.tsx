"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import styles from "./signup.module.css";
import { signupUser, loginWithCredentials, saveSession } from "../../lib/session";

export default function Signup() {
  const router = useRouter();
  const [role, setRole] = useState("Student");
  const [grade, setGrade] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const validatePassword = (pw: string): string | null => {
    if (pw.length < 8) return "Password must be at least 8 characters.";
    if (!/[A-Z]/.test(pw)) return "Password must contain at least one uppercase letter.";
    if (!/[0-9]/.test(pw)) return "Password must contain at least one number.";
    return null;
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    // Client-side validation
    const pwError = validatePassword(password);
    if (pwError) { setError(pwError); return; }
    if (password !== confirmPassword) { setError("Passwords do not match."); return; }
    if (role === "Student" && !grade) { setError("Please select a grade."); return; }

    setLoading(true);

    try {
      // 1. Create account via backend
      await signupUser({
        email: email.trim(),
        password,
        full_name: name.trim(),
        role: role.toUpperCase(),
        ...(role === "Student" ? { grade } : {}),
      });

      setSuccess("Account created! Logging you in...");

      // 2. Auto-login after signup
      const session = await loginWithCredentials(email.trim(), password);
      saveSession(session);

      // 3. Route to correct dashboard
      const roleRoutes: Record<string, string> = {
        STUDENT: "/student/dashboard",
        PARENT: "/parent/dashboard",
        ADMIN: "/admin",
      };
      router.push(roleRoutes[session.profile.role] || "/student/dashboard");

    } catch (err: any) {
      setError(err.message || "Signup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const passwordStrength = (): { label: string; color: string; width: string } => {
    if (!password) return { label: "", color: "transparent", width: "0%" };
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    const levels = [
      { label: "Weak", color: "#f43f5e", width: "25%" },
      { label: "Fair", color: "#f97316", width: "50%" },
      { label: "Good", color: "#eab308", width: "75%" },
      { label: "Strong", color: "#10b981", width: "100%" },
    ];
    return levels[score - 1] || levels[0];
  };

  const strength = passwordStrength();

  return (
    <div className={styles.signupContainer}>
      <div className={`glass-panel ${styles.signupCard}`}>
        <div style={{ textAlign: "center", marginBottom: "0.5rem" }}>
          <span style={{ fontSize: "2.5rem" }}>🎓</span>
        </div>
        <h1 className={styles.title}>Create Account</h1>
        <p className={styles.subtitle}>Join Abhirva Learning today</p>

        {error && (
          <div style={{
            background: "rgba(244, 63, 94, 0.1)",
            border: "1px solid rgba(244, 63, 94, 0.4)",
            borderRadius: "8px",
            padding: "0.75rem 1rem",
            marginBottom: "1rem",
            color: "var(--accent-color)",
            fontSize: "0.9rem",
          }}>
            ⚠️ {error}
          </div>
        )}

        {success && (
          <div style={{
            background: "rgba(16, 185, 129, 0.1)",
            border: "1px solid rgba(16, 185, 129, 0.4)",
            borderRadius: "8px",
            padding: "0.75rem 1rem",
            marginBottom: "1rem",
            color: "var(--success-color)",
            fontSize: "0.9rem",
          }}>
            ✅ {success}
          </div>
        )}

        <form className={styles.form} onSubmit={handleSignup}>
          <div className={styles.inputGroup}>
            <label>I am a</label>
            <select
              className={styles.input}
              value={role}
              onChange={(e) => {
                setRole(e.target.value);
                if (e.target.value !== "Student") setGrade("");
              }}
              style={{ color: "black" }}
              disabled={loading}
            >
              <option value="Student">Student</option>
              <option value="Parent">Parent</option>
            </select>
          </div>

          {role === "Student" && (
            <div className={styles.inputGroup}>
              <label>Grade / Class</label>
              <select
                className={styles.input}
                value={grade}
                onChange={(e) => setGrade(e.target.value)}
                style={{ color: "black" }}
                disabled={loading}
                required
              >
                <option value="">-- Select Grade --</option>
                <option value="Kindergarten">Kindergarten</option>
                <option value="Grade 1">Grade 1</option>
                <option value="Grade 2">Grade 2</option>
                <option value="Grade 3">Grade 3</option>
                <option value="Grade 4">Grade 4</option>
                <option value="Grade 5">Grade 5</option>
                <option value="Grade 6">Grade 6</option>
                <option value="Grade 7">Grade 7</option>
                <option value="Grade 8">Grade 8</option>
                <option value="Grade 9">Grade 9</option>
                <option value="Grade 10">Grade 10</option>
              </select>
            </div>
          )}

          <div className={styles.inputGroup}>
            <label>Full Name</label>
            <input
              type="text"
              className={styles.input}
              placeholder="e.g. Aarav Sharma"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className={styles.inputGroup}>
            <label>Email Address</label>
            <input
              type="email"
              className={styles.input}
              placeholder="example@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              disabled={loading}
            />
          </div>

          <div className={styles.inputGroup}>
            <label>Password</label>
            <div style={{ position: "relative" }}>
              <input
                type={showPassword ? "text" : "password"}
                className={styles.input}
                placeholder="Min 8 chars, 1 uppercase, 1 number"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
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
                }}
              >
                {showPassword ? "🙈" : "👁️"}
              </button>
            </div>
            {password && (
              <div style={{ marginTop: "0.4rem" }}>
                <div style={{
                  height: "4px",
                  borderRadius: "2px",
                  background: "rgba(255,255,255,0.1)",
                  overflow: "hidden",
                }}>
                  <div style={{
                    height: "100%",
                    width: strength.width,
                    background: strength.color,
                    transition: "all 0.3s ease",
                    borderRadius: "2px",
                  }} />
                </div>
                <span style={{ fontSize: "0.75rem", color: strength.color }}>
                  {strength.label}
                </span>
              </div>
            )}
          </div>

          <div className={styles.inputGroup}>
            <label>Confirm Password</label>
            <input
              type="password"
              className={styles.input}
              placeholder="Re-enter your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
              disabled={loading}
            />
            {confirmPassword && password !== confirmPassword && (
              <span style={{ fontSize: "0.75rem", color: "var(--accent-color)", marginTop: "0.25rem", display: "block" }}>
                ⚠️ Passwords do not match
              </span>
            )}
          </div>

          <button
            type="submit"
            className={styles.submitBtn}
            disabled={loading || !name || !email || !password || !confirmPassword || (role === "Student" && !grade)}
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
                Creating Account...
              </span>
            ) : "Create Account"}
          </button>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </form>

        <p style={{ marginTop: "2rem", fontSize: "0.9rem", color: "var(--text-secondary)", textAlign: "center" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--primary-color)", fontWeight: 600 }}>
            Login here
          </Link>
        </p>
      </div>
    </div>
  );
}
