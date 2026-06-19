"use client";
import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import styles from "../quiz.module.css";

function QuizSetupContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const subject = searchParams.get("subject") || "Mathematics";

  const [examType, setExamType] = useState("Chapter-wise");
  const [sstSubSubject, setSstSubSubject] = useState("");
  const [chapter, setChapter] = useState("");
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [options, setOptions] = useState<string[]>([]);
  const [grade, setGrade] = useState("Grade 1");

  useEffect(() => {
    const fetchTopics = async () => {
      // If SST and no sub-subject is selected yet, don't fetch topics
      if (subject === "SST" && !sstSubSubject) {
        setOptions([]);
        setLoadingOptions(false);
        return;
      }
      
      setLoadingOptions(true);
      try {
        const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "https://abhirva-backend.onrender.com";
        let url = `${BACKEND_URL}/api/admin/topics?subject=${encodeURIComponent(subject)}`;
        if (subject === "SST" && sstSubSubject) {
          url += `&sst_sub_subject=${encodeURIComponent(sstSubSubject)}`;
        }
        const res = await fetch(url);
        const data = await res.json();
        if (data.status === "success") {
          setOptions(data.topics || []);
        }
      } catch(e) {
        console.error("Failed to fetch topics", e);
      } finally {
        setLoadingOptions(false);
      }
    };
    fetchTopics();
  }, [subject, sstSubSubject]);

  const filteredOptions = options.filter(opt => {
    if (subject === "Marathi" || subject === "English" || subject === "Hindi") {
      if (examType === "Grammar") {
        return opt.startsWith("Grammar:");
      } else {
        return !opt.startsWith("Grammar:");
      }
    }
    return true;
  });

  const handleStartQuiz = () => {
    if (!chapter) {
      alert("Please select a specific topic or chapter to continue.");
      return;
    }
    // Navigate to actual quiz page with the selected hierarchy
    // We must pass subject=SST to the backend, not the sub-subject, because quizzes are saved under 'SST'
    let url = `/student/quiz?subject=${subject}&type=${examType}&chapter=${encodeURIComponent(chapter)}`;
    if (subject === "SST") {
      url += `&sub_subject=${encodeURIComponent(sstSubSubject)}`;
    }
    if (subject === "IMO Test") {
      url += `&grade=${encodeURIComponent(grade)}`;
    }
    router.push(url);
  };

  return (
    <div className={styles.quizContainer}>
      <header className={styles.header}>
        <h2>{subject} - Take Quiz</h2>
        <Link href="/student/dashboard" style={{color: 'var(--text-secondary)'}}>Back</Link>
      </header>

      <div className={`glass-panel ${styles.questionCard}`}>
        <h3 className={styles.questionText}>Select your {subject} Exam</h3>
        
        {/* Exam Type Toggle - mainly for language subjects */}
        {(subject === "Marathi" || subject === "English" || subject === "Hindi") && (
          <div style={{marginBottom: '2rem'}}>
            <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Exam Type</label>
            <div style={{display: 'flex', gap: '1rem'}}>
              <button 
                className={styles.optionBtn} 
                style={{flex: 1, borderColor: examType === "Chapter-wise" ? 'var(--primary-color)' : ''}}
                onClick={() => setExamType("Chapter-wise")}
              >
                Chapter-wise
              </button>
              <button 
                className={styles.optionBtn} 
                style={{flex: 1, borderColor: examType === "Grammar" ? 'var(--primary-color)' : ''}}
                onClick={() => setExamType("Grammar")}
              >
                Grammar & Skills
              </button>
            </div>
          </div>
        )}

        {/* SST Sub-Subject Selection */}
        {subject === "SST" && (
          <div style={{marginBottom: '2rem'}}>
            <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Select Sub-Subject</label>
            <select 
              value={sstSubSubject} 
              onChange={(e) => {
                setSstSubSubject(e.target.value);
                setChapter(""); // Reset chapter when changing sub-subject
              }}
              style={{padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", width: "100%", color: "black", marginBottom: "1rem"}}
            >
              <option value="">-- Select Sub-Subject --</option>
              <option value="Geography">Geography</option>
              <option value="Economics">Economics</option>
              <option value="History">History</option>
              <option value="Political Science">Political Science</option>
            </select>
          </div>
        )}

        {/* Chapter/Topic Selection */}
        {subject === "IMO Test" && (
          <div style={{marginBottom: '2rem'}}>
            <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Select Grade</label>
            <select 
              value={grade} 
              onChange={(e) => setGrade(e.target.value)}
              style={{padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", width: "100%", color: "black", marginBottom: "1rem"}}
            >
              {[...Array(10)].map((_, i) => (
                <option key={i} value={`Grade ${i + 1}`}>Grade {i + 1}</option>
              ))}
            </select>
          </div>
        )}

        <div style={{marginBottom: '2rem'}}>
          <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Select Topic</label>
          {loadingOptions ? (
            <div style={{ color: "var(--text-secondary)", padding: "1rem" }}>Loading topics...</div>
          ) : filteredOptions.length === 0 ? (
            <div style={{ color: "var(--text-secondary)", padding: "1rem" }}>No topics found for this selection.</div>
          ) : (
            <select
              value={chapter}
              onChange={(e) => setChapter(e.target.value)}
              style={{padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", width: "100%", color: "black"}}
            >
              <option value="">-- Select a Topic --</option>
              {filteredOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt.replace("Grammar: ", "")}
                </option>
              ))}
            </select>
          )}
        </div>

      </div>

      <footer className={styles.footer}>
        <button 
          className={styles.nextBtn} 
          disabled={!chapter}
          onClick={handleStartQuiz}
        >
          Take Quiz
        </button>
      </footer>
    </div>
  );
}

export default function QuizSetup() {
  return (
    <Suspense fallback={<div style={{padding: '2rem', color: 'white', textAlign: 'center'}}>Loading setup...</div>}>
      <QuizSetupContent />
    </Suspense>
  );
}
