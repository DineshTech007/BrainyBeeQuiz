"use client";
import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import styles from "../../quiz/quiz.module.css";
import { useAuth, AuthGuard } from "../../../../lib/auth-context";

function QuizContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { profile, updateSession } = useAuth();
  const board = searchParams.get("board") || "CBSE";
  const grade = searchParams.get("grade") || "10";
  const language = searchParams.get("language") || "English";
  const subject = searchParams.get("subject") || "Mathematics";
  const chapter = searchParams.get("chapter") || "Random Topic";
  const examType = searchParams.get("type") || "Chapter-wise";
  
  const [loading, setLoading] = useState(true);
  const [paywallHit, setPaywallHit] = useState(false);
  const [paywallMessage, setPaywallMessage] = useState("");
  const [notFound, setNotFound] = useState(false);
  const [notFoundMessage, setNotFoundMessage] = useState("");
  const [quizData, setQuizData] = useState<any>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [textAnswer, setTextAnswer] = useState("");
  const [score, setScore] = useState(0);
  const [showReward, setShowReward] = useState(false);
  const [pointsEarned, setPointsEarned] = useState(0);

  useEffect(() => {
    // If auth context isn't fully loaded or no profile, wait (AuthGuard handles redirects)
    if (!profile) return;
    
    const studentId = profile.id;

    // Fetch Quiz from Backend
    fetch("http://localhost:8000/api/student/past_papers/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: studentId, past_paper_id: searchParams.get('id') })
    })
    .then(async (res) => {
      const data = await res.json();
      if (res.status === 403) {
        setPaywallHit(true);
        setPaywallMessage(data.detail.message || "Free trial exhausted.");
        setLoading(false);
      } else if (res.status === 404) {
        setNotFound(true);
        setNotFoundMessage(data.detail || "This quiz hasn't been published yet. Please ask your administrator.");
        setLoading(false);
      } else if (res.ok) {
        setQuizData(data.data);
        setLoading(false);
      } else {
        throw new Error(data.detail || "Error loading quiz");
      }
    })
    .catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [searchParams, router]);

  const [isAnswerChecked, setIsAnswerChecked] = useState(false);

  const handleNext = async () => {
    if (!quizData) return;
    
    if (!isAnswerChecked) {
      // First click: check the answer
      setIsAnswerChecked(true);
      return;
    }

    const question = quizData.questions[currentIdx];
    let newScore = score;
    
    const options = Array.isArray(question.options) ? question.options : 
                  (question.options_list || ["Option A", "Option B", "Option C", "Option D"]);
                  
    if (question.question_type === "INTEGER") {
      if (textAnswer.trim() === question.correct_option?.trim()) {
        newScore += 1;
      }
    } else {
      if (selectedOption !== null && options[selectedOption] === question.correct_option) {
        newScore += 1;
      }
    }
    setScore(newScore);

    if (currentIdx + 1 < quizData.questions.length) {
      setCurrentIdx(currentIdx + 1);
      setSelectedOption(null);
      setTextAnswer("");
      setIsAnswerChecked(false);
    } else {
      // Submit score to Gamification Backend
      const studentId = profile?.id;
      try {
        const endpoint = board === "Library" 
          ? "http://localhost:8000/api/library/quiz/submit"
          : "http://localhost:8000/api/student/gamification/quiz/submit";
          
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            student_id: studentId,
            quiz_id: quizData.quiz_id,
            score: newScore,
            total_questions: quizData.questions.length
          })
        });
        const d = await res.json();
        if (d.status === "success") {
          setPointsEarned(d.data.points_earned);
          if (d.data.new_total !== undefined) {
            updateSession({ total_points: d.data.new_total });
          }
        }
      } catch (err) {
        console.error("Failed to submit gamification data", err);
      }
      setShowReward(true);
    }
  };

  if (loading) {
    return <div className={styles.quizContainer}><h2 className="gradient-text">Loading Quiz...</h2></div>;
  }

  if (paywallHit) {
    return (
      <div className={styles.rewardOverlay}>
        <div className={styles.rewardCard}>
          <h1 style={{color: 'var(--accent-color)', fontSize: '2.5rem', marginBottom: '1rem'}}>Paywall Blocked</h1>
          <p style={{fontSize: '1.2rem', marginBottom: '2rem'}}>{paywallMessage}</p>
          <Link href="/student/dashboard" className={styles.nextBtn} style={{display: 'inline-block', textDecoration: 'none'}}>
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  if (notFound) {
    return (
      <div className={styles.rewardOverlay}>
        <div className={styles.rewardCard}>
          <h1 style={{color: 'var(--accent-color)', fontSize: '2.5rem', marginBottom: '1rem'}}>Quiz Not Available</h1>
          <p style={{fontSize: '1.2rem', marginBottom: '2rem'}}>{notFoundMessage}</p>
          <Link href="/student/dashboard" className={styles.nextBtn} style={{display: 'inline-block', textDecoration: 'none'}}>
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  if (showReward) {
    return (
      <div className={styles.rewardOverlay}>
        <div className={styles.rewardCard}>
          <h1 className="gradient-text" style={{fontSize: '3rem', marginBottom: '1rem'}}>Quiz Complete!</h1>
          <p>You scored</p>
          <div className={styles.rewardScore}>{score} / {quizData.questions.length}</div>
          <p>Points Earned</p>
          <div className={styles.rewardPoints}>+{pointsEarned} pts! 🏆</div>
          <Link href="/student/dashboard" className={styles.nextBtn} style={{display: 'inline-block', textDecoration: 'none'}}>
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const question = quizData.questions[currentIdx];
  const progress = ((currentIdx) / quizData.questions.length) * 100;
  
  // Safety check if options isn't array
  const options = Array.isArray(question.options) ? question.options : 
                  (question.options_list || ["Option A", "Option B", "Option C", "Option D"]);

  const isCorrect = question.question_type === "INTEGER"
    ? textAnswer.trim() === question.correct_option?.trim()
    : selectedOption !== null && options[selectedOption] === question.correct_option;

  return (
    <div className={styles.quizContainer}>
      <header className={styles.header}>
        <h2>Past Paper Exam</h2>
        <div>Question {currentIdx + 1} of {quizData.questions.length}</div>
      </header>

      <div className={styles.progressBar}>
        <div className={styles.progressFill} style={{ width: `${progress}%` }}></div>
      </div>

      {quizData.passage && (
        <div className={`glass-panel`} style={{ marginBottom: "2rem", padding: "1.5rem", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)", background: "rgba(0,0,0,0.2)" }}>
          <h3 style={{ marginBottom: "1rem", color: "var(--accent-color)" }}>📖 Reading Comprehension Passage</h3>
          <p style={{ lineHeight: "1.8", fontSize: "1.1rem", whiteSpace: "pre-wrap" }}>
            {quizData.passage}
          </p>
        </div>
      )}

      <div className={`glass-panel ${styles.questionCard}`}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
          <h3 className={styles.questionText} style={{ flex: 1 }}>{question.question_text || question.text}</h3>
          {question.difficulty_level && (
            <span style={{ 
              padding: "4px 10px", 
              borderRadius: "20px", 
              fontSize: "0.85rem", 
              fontWeight: "bold", 
              backgroundColor: question.difficulty_level === 'Easy' ? 'rgba(34, 197, 94, 0.2)' : question.difficulty_level === 'Hard' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(234, 179, 8, 0.2)',
              color: question.difficulty_level === 'Easy' ? '#4ade80' : question.difficulty_level === 'Hard' ? '#f87171' : '#facc15',
              marginLeft: "1rem",
              whiteSpace: "nowrap"
            }}>
              {question.difficulty_level === 'Easy' ? '🟢 Easy' : question.difficulty_level === 'Hard' ? '🔴 Hard' : '🟡 Medium'}
            </span>
          )}
        </div>
        
        {question.question_type === "INTEGER" ? (
          <div style={{ margin: "2rem 0" }}>
            <input 
              type="text" 
              value={textAnswer}
              onChange={(e) => !isAnswerChecked && setTextAnswer(e.target.value)}
              placeholder="Type your integer answer here..."
              disabled={isAnswerChecked}
              style={{
                width: "100%",
                padding: "1rem",
                fontSize: "1.2rem",
                borderRadius: "8px",
                border: isAnswerChecked ? (isCorrect ? "2px solid #22c55e" : "2px solid #ef4444") : "2px solid rgba(255,255,255,0.2)",
                background: "rgba(0,0,0,0.5)",
                color: "#fff",
                outline: "none"
              }}
            />
            {isAnswerChecked && !isCorrect && (
              <div style={{ marginTop: "0.5rem", color: "#4ade80", fontWeight: "bold" }}>
                Correct Answer: {question.correct_option}
              </div>
            )}
          </div>
        ) : (
          <div className={styles.optionsGrid}>
            {options.map((opt: string, idx: number) => {
              let btnClass = `${styles.optionBtn} ${selectedOption === idx ? styles.selectedOption : ''}`;
              if (isAnswerChecked) {
                if (opt === question.correct_option) {
                  btnClass += ` ${styles.correctOption || ''}`;
                } else if (selectedOption === idx && opt !== question.correct_option) {
                  btnClass += ` ${styles.incorrectOption || ''}`;
                }
              }
              return (
                <button
                  key={idx}
                  className={btnClass}
                  onClick={() => !isAnswerChecked && setSelectedOption(idx)}
                  style={isAnswerChecked ? {
                    backgroundColor: opt === question.correct_option ? '#22c55e' : (selectedOption === idx ? '#ef4444' : ''),
                    color: opt === question.correct_option || selectedOption === idx ? '#fff' : '',
                    cursor: 'default'
                  } : {}}
                >
                  <span style={{marginRight: '15px', fontWeight: 'bold'}}>{String.fromCharCode(65 + idx)}.</span>
                  {opt}
                </button>
              );
            })}
          </div>
        )}
        
        {isAnswerChecked && (
          <div style={{ marginTop: '2rem', padding: '1.5rem', borderRadius: '12px', backgroundColor: isCorrect ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', border: `1px solid ${isCorrect ? '#22c55e' : '#ef4444'}` }}>
            <h4 style={{ color: isCorrect ? '#16a34a' : '#dc2626', marginBottom: '0.5rem', fontSize: '1.2rem' }}>
              {isCorrect ? '✅ Correct!' : '❌ Incorrect'}
            </h4>
            <p style={{ color: 'var(--text-primary)', lineHeight: '1.6' }}>
              {question.explanation_description || question.solution_steps || 'No explanation provided.'}
            </p>
          </div>
        )}
      </div>

      <footer className={styles.footer}>
        <button 
          className={styles.nextBtn} 
          disabled={question.question_type === "INTEGER" ? textAnswer.trim() === "" : selectedOption === null}
          onClick={handleNext}
        >
          {!isAnswerChecked ? 'Check Answer' : (currentIdx === quizData.questions.length - 1 ? 'Submit Quiz' : 'Next Question')}
        </button>
      </footer>
    </div>
  );
}

export default function QuizInterface() {
  return (
    <AuthGuard requiredRole="STUDENT">
      <QuizContent />
    </AuthGuard>
  );
}
