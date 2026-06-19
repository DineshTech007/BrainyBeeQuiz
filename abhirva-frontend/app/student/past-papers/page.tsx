"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../lib/auth-context";
import styles from "../dashboard/dashboard.module.css";

const BACKEND_URL = process.env.NODE_ENV === "production" ? "https://abhirva-backend.onrender.com" : "http://127.0.0.1:8000";

export default function PastPapersList() {
  const { profile } = useAuth();
  const router = useRouter();
  const [papers, setPapers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSubject, setSelectedSubject] = useState<string>("All");
  const [selectedYear, setSelectedYear] = useState<string>("All");

  useEffect(() => {
    if (!profile) return;
    fetch(`${BACKEND_URL}/api/student/past_papers`)
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          setPapers(data.past_papers || []);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [profile]);

  return (
    <div className={styles.dashboardContainer} style={{ minHeight: '100vh' }}>
      <header className={styles.header}>
        <div className={styles.welcomeText}>
          <h1>
            Simulate <span className="gradient-text">Past Papers</span>
          </h1>
          <p>Take actual past year board exams to test your knowledge.</p>
        </div>
        <Link href="/student/dashboard" className={styles.startBtn} style={{ background: 'transparent', border: '1px solid var(--primary-color)', color: 'var(--primary-color)' }}>
          ← Back to Dashboard
        </Link>
      </header>

      <div className="glass-panel section">
        <h2 className={styles.sectionTitle}>Available Past Papers</h2>
        
        {loading ? (
          <p>Loading past papers...</p>
        ) : papers.length === 0 ? (
          <p style={{ color: "var(--text-secondary)" }}>No past papers available yet. Ask your admin to generate some!</p>
        ) : (
          <>
            <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem" }}>
              <select 
                value={selectedSubject} 
                onChange={(e) => setSelectedSubject(e.target.value)} 
                style={{ padding: "0.5rem 1rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.5)", color: "white" }}
              >
                <option value="All">All Subjects</option>
                {Array.from(new Set(papers.map(p => p.subject))).sort().map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>

              <select 
                value={selectedYear} 
                onChange={(e) => setSelectedYear(e.target.value)} 
                style={{ padding: "0.5rem 1rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.5)", color: "white" }}
              >
                <option value="All">All Years</option>
                {Array.from(new Set(papers.map(p => p.year))).sort((a,b) => Number(b) - Number(a)).map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>

            <div className={styles.subjectsGrid}>
              {papers
                .filter(p => selectedSubject === "All" || p.subject === selectedSubject)
                .filter(p => selectedYear === "All" || p.year === selectedYear)
                .map((paper, idx) => (
              <div key={idx} className={styles.subjectCard}>
                <div>
                  <div className={styles.subjectEmoji}>📜</div>
                  <h3>{paper.year} {paper.subject}</h3>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "4px" }}>
                    {paper.board} • {paper.grade}
                  </p>
                </div>
                <button
                  className={styles.startBtn}
                  onClick={() => router.push(`/student/past-papers/exam?id=${paper.id}`)}
                  style={{ width: "100%", marginTop: "1rem" }}
                >
                  Start Exam →
                </button>
              </div>
              ))}
            </div>
            {papers.filter(p => selectedSubject === "All" || p.subject === selectedSubject).filter(p => selectedYear === "All" || p.year === selectedYear).length === 0 && (
              <p style={{ color: "var(--text-secondary)", textAlign: "center", width: "100%", marginTop: "2rem" }}>No past papers match your selection.</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
