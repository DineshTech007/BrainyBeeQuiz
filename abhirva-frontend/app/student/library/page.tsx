"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import styles from "./library.module.css";
import { AuthGuard, useAuth } from "../../../lib/auth-context";

const BACKEND_URL = process.env.NODE_ENV === "production" ? "https://abhirva-backend.onrender.com" : "http://127.0.0.1:8000";

const GRADES = ["Kindergarten", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"];
const LANGUAGES = ["English", "Marathi", "Hindi"];

export default function BookLibraryWrapper() {
  return (
    <AuthGuard requiredRole="STUDENT">
      <BookLibrary />
    </AuthGuard>
  );
}

function BookLibrary() {
  const [selectedGrade, setSelectedGrade] = useState("Grade 1");
  const [selectedLanguage, setSelectedLanguage] = useState("English");
  const [books, setBooks] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasAccess, setHasAccess] = useState(false);
  const { profile } = useAuth();

  useEffect(() => {
    if (!profile?.id) return;
    
    fetch(`${BACKEND_URL}/api/admin/student/${profile.id}/access`, { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          const hasLibrary = data.subscriptions.some((s: any) => s.name.toLowerCase().includes("library"));
          setHasAccess(hasLibrary);
        }
      })
      .catch(err => console.error(err));

    setLoading(true);
    fetch(`${BACKEND_URL}/api/library/books?grade=${encodeURIComponent(selectedGrade)}&language=${encodeURIComponent(selectedLanguage)}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          setBooks(data.books);
        }
      })
      .catch(err => console.error("Error fetching books:", err))
      .finally(() => setLoading(false));
  }, [selectedGrade, selectedLanguage, profile?.id]);

  if (!hasAccess && !loading) {
    return (
      <div className={styles.libraryContainer} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', textAlign: 'center'}}>
        <div style={{fontSize: '5rem', marginBottom: '1rem'}}>🔒</div>
        <h1 style={{fontSize: '2.5rem', marginBottom: '1rem', color: 'white'}}>Access Denied</h1>
        <p style={{fontSize: '1.2rem', marginBottom: '2rem', color: 'var(--text-secondary)'}}>You need the Book Library subscription to access this feature. Please ask your parent to unlock it.</p>
        <Link href="/student/dashboard" style={{padding: '0.8rem 1.5rem', background: 'var(--primary-color)', color: 'white', borderRadius: '8px', textDecoration: 'none', fontWeight: 'bold'}}>
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className={styles.libraryContainer}>
      <header className={styles.header}>
        <h1>📚 Book <span className="gradient-text">Library</span></h1>
        <p>Read books, expand your mind, and earn points!</p>
      </header>

      <div className={styles.controls}>
        <select 
          className={styles.gradeSelect}
          value={selectedGrade} 
          onChange={(e) => setSelectedGrade(e.target.value)}
        >
          {GRADES.map(g => (
            <option key={g} value={g}>{g}</option>
          ))}
        </select>
        <select 
          className={styles.gradeSelect}
          value={selectedLanguage} 
          onChange={(e) => setSelectedLanguage(e.target.value)}
        >
          {LANGUAGES.map(l => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>

      <div className={styles.bookGrid}>
        {loading ? (
          <div className={styles.emptyState}>Loading books...</div>
        ) : books.length === 0 ? (
          <div className={styles.emptyState}>
            No books found for {selectedGrade}. Check back later!
          </div>
        ) : (
          books.map((book, idx) => (
            <Link 
              key={idx} 
              href={`/student/library/read?grade=${encodeURIComponent(selectedGrade)}&language=${encodeURIComponent(selectedLanguage)}&book=${encodeURIComponent(book)}`}
              className={styles.bookCard}
            >
              <div className={styles.bookIcon}>📖</div>
              <div className={styles.bookTitle}>{book.replace(".pdf", "")}</div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
