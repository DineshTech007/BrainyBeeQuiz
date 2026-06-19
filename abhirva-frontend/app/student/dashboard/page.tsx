"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import styles from "./dashboard.module.css";
import { AuthGuard, useAuth } from "../../../lib/auth-context";

const SUBJECTS = [
  { name: "Mathematics", emoji: "📐" },
  { name: "English", emoji: "📖" },
  { name: "Science", emoji: "🔬" },
  { name: "SST", emoji: "🌍" },
  { name: "Hindi", emoji: "🇮🇳" },
  { name: "Marathi", emoji: "📜" },
  { name: "Computers", emoji: "💻" },
  { name: "IMO Test", emoji: "🏆" },
];

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "https://abhirva-backend.onrender.com";

// ---------------------------------------------------------------------------
// Locked Feature Overlay Card
// ---------------------------------------------------------------------------
function LockedFeatureCard({ title, emoji, description }: { title: string; emoji: string; description: string }) {
  return (
    <div className={styles.lockedCard}>
      <div className={styles.lockedEmoji}>{emoji}</div>
      <h3 className={styles.lockedTitle}>{title}</h3>
      <p className={styles.lockedDesc}>{description}</p>
      <div className={styles.lockedBadge}>
        🔒 Ask your parent to unlock
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Dashboard Content
// ---------------------------------------------------------------------------
function StudentDashboardContent() {
  const { profile } = useAuth();
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [bookLeaderboard, setBookLeaderboard] = useState<any[]>([]);
  const [subscriptions, setSubscriptions] = useState<string[]>([]); // list of package names
  const [subLoading, setSubLoading] = useState(true);

  const studentId = profile?.id;
  const studentName = profile?.full_name || "Student";

  // Helper to check if student has a specific package access
  const hasAccess = (keyword: string): boolean => {
    return subscriptions.some(name =>
      name.toLowerCase().includes(keyword.toLowerCase())
    );
  };

  useEffect(() => {
    if (!studentId) return;

    // Fetch student's active subscriptions
    fetch(`${BACKEND_URL}/api/admin/student/${studentId}/access`, { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success" && Array.isArray(data.subscriptions)) {
          setSubscriptions(data.subscriptions.map((s: any) => s.name || ""));
        }
        setSubLoading(false);
      })
      .catch(err => {
        console.error("Subscription fetch error:", err);
        setSubLoading(false);
      });
  }, [studentId]);

  const hasLibraryAccess = hasAccess("book library") || hasAccess("library");
  const hasChessAccess = hasAccess("chess");

  return (
    <div className={styles.dashboardContainer}>
      {/* ---------------------------------------------------------------- */}
      {/* Header */}
      {/* ---------------------------------------------------------------- */}
      <header className={styles.header}>
        <div className={styles.welcomeText}>
          <h1>
            Welcome back,{" "}
            <span className="gradient-text">{studentName}</span>!
          </h1>
          <p>10th Board Prep — Ready to ace your next exam? 🎯</p>
        </div>

        <div className={styles.pointsBadge} style={{display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', background: 'transparent', boxShadow: 'none'}}>
          <div style={{background: 'rgba(255,255,255,0.1)', padding: '0.5rem 1rem', borderRadius: '50px', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.2)'}}>
            <span>🏆 Points:</span>
            <span className={styles.pointsValue} style={{marginLeft: '0.5rem', fontWeight: 'bold', color: '#fbbf24'}}>
              {(profile?.total_points || 0) + (profile?.book_points || 0)}
            </span>
          </div>
          <Link href="/student/report" style={{
            background: 'linear-gradient(90deg, #6366f1, #a855f7)',
            padding: '0.5rem 1.5rem',
            borderRadius: '50px',
            fontWeight: 'bold',
            color: 'white',
            textDecoration: 'none',
            boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)',
            transition: 'transform 0.2s',
            display: 'inline-block'
          }}>
            📊 My Progress Report
          </Link>
        </div>
      </header>

      <div className={styles.grid}>
        {/* ============================================================ */}
        {/* ZONE 1: Assigned Quizzes (Always Visible — free tier) */}
        {/* ============================================================ */}
        <div className="glass-panel section" style={{ gridColumn: "1 / -1" }}>
          <h2 className={styles.sectionTitle}>📚 My Assigned Quizzes & Subjects</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem", fontSize: "0.9rem" }}>
            Select a subject to take a quiz. Free tier includes 2 trial quizzes per subject.
          </p>

          <div className={styles.subjectsGrid}>
            {SUBJECTS.map((sub, idx) => (
              <div key={idx} className={styles.subjectCard}>
                <div>
                  <div className={styles.subjectEmoji}>{sub.emoji}</div>
                  <h3>{sub.name}</h3>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "4px" }}>
                    Board Prep {hasAccess(sub.name) ? "🌟 Premium" : "Free Tier"}
                  </p>
                </div>
                <Link
                  href={`/student/quiz/setup?subject=${sub.name}`}
                  className={styles.startBtn}
                >
                  Take Quiz →
                </Link>
              </div>
            ))}
          </div>
        </div>

        {/* ============================================================ */}
        {/* ZONE 2: Book Library */}
        {/* ============================================================ */}
        <div className="glass-panel section">
          <h2 className={styles.sectionTitle}>📚 Reading Library</h2>
          {hasLibraryAccess ? (
            <div style={{ padding: "1rem", background: "rgba(255,255,255,0.05)", borderRadius: "12px", borderLeft: "4px solid var(--primary-color)" }}>
              <h3>Explore the Library</h3>
              <p style={{ color: "var(--text-secondary)", marginBottom: "1rem" }}>Read books and earn points!</p>
              <Link href="/student/library" className={styles.startBtn} style={{display: 'inline-block'}}>Open Library →</Link>
            </div>
          ) : (
            <LockedFeatureCard 
              title="Book Library" 
              emoji="📚" 
              description="Unlock the full library to read thousands of books and earn reading points."
            />
          )}
        </div>

        {/* ============================================================ */}
        {/* ZONE 3: Chess Tutor */}
        {/* ============================================================ */}
        <div className="glass-panel section">
          <h2 className={styles.sectionTitle}>♟️ Chess Tutor</h2>
          {hasChessAccess ? (
            <div style={{ padding: "1rem", background: "rgba(255,255,255,0.05)", borderRadius: "12px", borderLeft: "4px solid var(--primary-color)" }}>
              <h3>Play & Learn Chess</h3>
              <p style={{ color: "var(--text-secondary)", marginBottom: "1rem" }}>Master your moves with AI assistance.</p>
              <Link href="/chess" className={styles.startBtn} style={{display: 'inline-block'}}>Play Chess →</Link>
            </div>
          ) : (
            <LockedFeatureCard 
              title="Chess Tutor" 
              emoji="♟️" 
              description="Unlock the interactive chess tutor to learn strategies and play against AI."
            />
          )}
        </div>

        {/* ============================================================ */}
        {/* ZONE 4: Past Papers */}
        {/* ============================================================ */}
        <div className="glass-panel section">
          <h2 className={styles.sectionTitle}>📜 Past Board Exams</h2>
          <div style={{ padding: "1rem", background: "rgba(255,255,255,0.05)", borderRadius: "12px", borderLeft: "4px solid var(--primary-color)" }}>
            <h3>Simulate Real Board Exams</h3>
            <p style={{ color: "var(--text-secondary)", marginBottom: "1rem" }}>Take actual past year papers to prepare for the real thing.</p>
            <Link href="/student/past-papers" className={styles.startBtn} style={{display: 'inline-block'}}>Browse Past Papers →</Link>
          </div>
        </div>

      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Exported page — wrapped in AuthGuard
// ---------------------------------------------------------------------------
export default function StudentDashboard() {
  return (
    <AuthGuard requiredRole="STUDENT">
      <StudentDashboardContent />
    </AuthGuard>
  );
}
