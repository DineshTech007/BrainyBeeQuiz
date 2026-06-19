"use client";
import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import styles from "../quiz.module.css";
import { useAuth } from "../../../../lib/auth-context";

function QuizSetupContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const subject = searchParams.get("subject") || "Mathematics";
  const isOlympiadTest = subject === "IMO Test" || subject === "SOF Test" || subject === "IEO Test";

  const [examType, setExamType] = useState("Chapter-wise");
  const [sstSubSubject, setSstSubSubject] = useState("");
  const [chapter, setChapter] = useState("");
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [options, setOptions] = useState<string[]>([]);
  const [imoMode, setImoMode] = useState("Topic-wise");
  const [numQuestions, setNumQuestions] = useState(10);
  const { profile } = useAuth();

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
        const BACKEND_URL = process.env.NODE_ENV === "production" ? "https://abhirva-backend.onrender.com" : "http://127.0.0.1:8000";
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
    if (isOlympiadTest) {
      url += `&grade=${encodeURIComponent(profile?.grade || "Grade 3")}&num_questions=${numQuestions}`;
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
        {isOlympiadTest && (
          <div style={{marginBottom: '2rem'}}>
            <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Syllabus Mode</label>
            <div style={{display: 'flex', gap: '1rem', marginBottom: '1.5rem'}}>
              <button 
                type="button"
                className={styles.optionBtn} 
                style={{flex: 1, borderColor: imoMode === "Topic-wise" ? 'var(--primary-color)' : 'rgba(255,255,255,0.1)'}}
                onClick={() => {
                  setImoMode("Topic-wise");
                  setChapter("");
                }}
              >
                Topic-wise
              </button>
              <button 
                type="button"
                className={styles.optionBtn} 
                style={{flex: 1, borderColor: imoMode === "Mix" ? 'var(--primary-color)' : 'rgba(255,255,255,0.1)'}}
                onClick={() => {
                  setImoMode("Mix");
                  setChapter("Mix of all topics");
                }}
              >
                Mix of all topics
              </button>
            </div>

            <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Number of Questions</label>
            <select 
              value={numQuestions} 
              onChange={(e) => setNumQuestions(Number(e.target.value))}
              style={{padding: "0.5rem", borderRadius: "4px", border: "1px solid #ccc", width: "100%", color: "black", marginBottom: "1.5rem"}}
            >
              <option value={5}>5 Questions</option>
              <option value={10}>10 Questions</option>
              <option value={15}>15 Questions</option>
              <option value={20}>20 Questions</option>
              <option value={25}>25 Questions</option>
              <option value={30}>30 Questions</option>
            </select>
          </div>
        )}

        {!(isOlympiadTest && imoMode === "Mix") && (
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
        )}

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
