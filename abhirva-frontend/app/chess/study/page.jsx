"use client";
import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "../../../lib/auth-context";
import CustomChessBoard from "../../../chess/src/components/CustomChessBoard";

const BACKEND_URL = process.env.NODE_ENV === "production" ? "https://abhirva-backend.onrender.com" : "http://127.0.0.1:8000";

export default function ChessStudyPage() {
  const { profile } = useAuth();
  const [concepts, setConcepts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lang, setLang] = useState("en"); // en, hi, mr
  
  const [selectedBook, setSelectedBook] = useState("All Books");
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/chess/study/concepts`)
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          setConcepts(data.concepts || []);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const handleLanguageChange = (l) => setLang(l);

  // Extract unique books for the dropdown filter
  const uniqueBooks = useMemo(() => {
    const books = new Set(concepts.map(c => c.book_source));
    return ["All Books", ...Array.from(books)];
  }, [concepts]);

  // Filter concepts by selected book
  const filteredConcepts = useMemo(() => {
    if (selectedBook === "All Books") return concepts;
    return concepts.filter(c => c.book_source === selectedBook);
  }, [concepts, selectedBook]);

  // Reset stepper when a new concept is selected
  useEffect(() => {
    setCurrentStepIndex(0);
  }, [selectedConcept]);

  const getLocalizedTitle = (c) => {
    if (lang === "en") return c.concept_name_en;
    if (lang === "hi") return c.concept_name_hi;
    if (lang === "mr") return c.concept_name_mr;
  };

  const getLocalizedExplanation = (step) => {
    if (!step) return "";
    if (lang === "en") return step.explanation_en;
    if (lang === "hi") return step.explanation_hi;
    if (lang === "mr") return step.explanation_mr;
  };

  const currentStep = selectedConcept?.steps?.[currentStepIndex];
  const totalSteps = selectedConcept?.steps?.length || 0;

  return (
    <div style={{ minHeight: '100vh', padding: '2rem', maxWidth: '1400px', margin: '0 auto', color: 'white' }}>
      <header style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', margin: 0 }}>
            Interactive <span className="gradient-text">Study Mode</span>
          </h1>
          <p style={{ color: "var(--text-secondary)", marginTop: "0.5rem" }}>
            Step-by-step masterclasses extracted from professional chess literature.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <select 
            value={lang} 
            onChange={(e) => handleLanguageChange(e.target.value)}
            style={{ padding: '0.5rem', borderRadius: '8px', background: 'rgba(0,0,0,0.5)', color: 'white', border: '1px solid var(--border-color)' }}
          >
            <option value="en">English</option>
            <option value="hi">हिंदी (Hindi)</option>
            <option value="mr">मराठी (Marathi)</option>
          </select>
          <Link href="/chess" style={{ padding: '0.5rem 1rem', border: '1px solid var(--primary-color)', color: 'var(--primary-color)', borderRadius: '8px', textDecoration: 'none' }}>
            ← Back to Chess Tutor
          </Link>
        </div>
      </header>

      {loading ? (
        <p>Loading deep concepts...</p>
      ) : concepts.length === 0 ? (
        <div className="glass-panel section" style={{ textAlign: "center" }}>
          <p style={{ color: "var(--text-secondary)" }}>No study concepts found! Wait for the V2 background ingestion script to finish processing.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "2rem" }}>
          {/* Sidebar list with Filter */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", height: "80vh" }}>
            
            {/* Filter Dropdown */}
            <div style={{ padding: "1rem", borderBottom: "1px solid var(--border-color)" }}>
              <label style={{ display: "block", fontSize: "0.9rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Filter by Book:</label>
              <select 
                value={selectedBook}
                onChange={(e) => setSelectedBook(e.target.value)}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "8px", background: "rgba(255,255,255,0.05)", color: "white", border: "1px solid var(--border-color)" }}
              >
                {uniqueBooks.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>

            {/* Concept List */}
            <div style={{ padding: "1rem", overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {filteredConcepts.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setSelectedConcept(c)}
                  style={{
                    padding: "1rem",
                    textAlign: "left",
                    background: selectedConcept?.id === c.id ? "var(--primary-color)" : "rgba(255,255,255,0.05)",
                    border: "none",
                    borderRadius: "8px",
                    color: selectedConcept?.id === c.id ? "#000" : "white",
                    cursor: "pointer",
                    transition: "all 0.2s"
                  }}
                >
                  <strong style={{ display: "block" }}>{getLocalizedTitle(c)}</strong>
                  {selectedBook === "All Books" && <span style={{ fontSize: "0.8rem", opacity: 0.7 }}>{c.book_source}</span>}
                </button>
              ))}
              {filteredConcepts.length === 0 && (
                <p style={{ color: "var(--text-secondary)", textAlign: "center", marginTop: "2rem" }}>No concepts extracted for this book yet.</p>
              )}
            </div>
          </div>

          {/* Main Visualizer */}
          <div className="glass-panel" style={{ padding: "2rem", display: "flex", flexDirection: "column", gap: "1rem", height: "80vh", overflowY: "auto" }}>
            {selectedConcept && currentStep ? (
              <>
                <h2 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>{getLocalizedTitle(selectedConcept)}</h2>
                <div style={{ color: "var(--text-secondary)", marginBottom: "1rem", fontSize: "0.9rem" }}>
                  Source: <i>{selectedConcept.book_source}</i>
                </div>

                <div style={{ display: "flex", gap: "2rem", flex: 1 }}>
                  
                  {/* Left: Interactive Board */}
                  <div style={{ width: "450px", display: "flex", flexDirection: "column", gap: "1rem" }}>
                    <CustomChessBoard fen={currentStep.fen} />

                    {/* STEPPER CONTROLS */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(0,0,0,0.3)", padding: "1rem", borderRadius: "12px" }}>
                      <button 
                        onClick={() => setCurrentStepIndex(i => Math.max(0, i - 1))}
                        disabled={currentStepIndex === 0}
                        style={{ padding: "0.5rem 1rem", borderRadius: "6px", background: currentStepIndex === 0 ? "rgba(255,255,255,0.1)" : "var(--primary-color)", color: currentStepIndex === 0 ? "gray" : "black", border: "none", cursor: currentStepIndex === 0 ? "not-allowed" : "pointer", fontWeight: "bold" }}
                      >
                        ← Previous Move
                      </button>
                      <span style={{ fontWeight: "bold", color: "var(--text-secondary)" }}>
                        Step {currentStepIndex + 1} of {totalSteps}
                      </span>
                      <button 
                        onClick={() => setCurrentStepIndex(i => Math.min(totalSteps - 1, i + 1))}
                        disabled={currentStepIndex === totalSteps - 1}
                        style={{ padding: "0.5rem 1rem", borderRadius: "6px", background: currentStepIndex === totalSteps - 1 ? "rgba(255,255,255,0.1)" : "var(--primary-color)", color: currentStepIndex === totalSteps - 1 ? "gray" : "black", border: "none", cursor: currentStepIndex === totalSteps - 1 ? "not-allowed" : "pointer", fontWeight: "bold" }}
                      >
                        Next Move →
                      </button>
                    </div>
                  </div>

                  {/* Right: Trilingual Explanation */}
                  <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                    <div style={{ background: "rgba(255,255,255,0.05)", padding: "1.5rem", borderRadius: "12px", borderLeft: "4px solid var(--primary-color)" }}>
                      <h4 style={{ color: "var(--primary-color)", marginBottom: "0.5rem", fontSize: "0.9rem", textTransform: "uppercase", letterSpacing: "1px" }}>
                        Move Played
                      </h4>
                      <div style={{ fontSize: "2rem", fontWeight: "black", letterSpacing: "2px" }}>
                        {currentStep.notation || "Starting Position"}
                      </div>
                    </div>

                    <div style={{ flex: 1, background: "rgba(255,255,255,0.05)", padding: "1.5rem", borderRadius: "12px", fontSize: "1.2rem", lineHeight: "1.8", color: "white" }}>
                      {getLocalizedExplanation(currentStep)}
                    </div>
                  </div>

                </div>
              </>
            ) : (
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-secondary)", fontSize: "1.2rem" }}>
                Select a concept from the library to start learning!
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
