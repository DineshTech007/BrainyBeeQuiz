"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "../../student/dashboard/dashboard.module.css";
import { AuthGuard, useAuth } from "../../../lib/auth-context";

function ParentDashboardContent() {
  const { profile } = useAuth();
  const router = useRouter();
  const [students, setStudents] = useState<any[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<string>("");
  const [studentProgress, setStudentProgress] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showReportCard, setShowReportCard] = useState(false);


  useEffect(() => {
    if (!profile?.id) return;
    let url = `${process.env.NEXT_PUBLIC_BACKEND_URL || "https://abhirva-backend.onrender.com"}/api/parent/students`;
    if (profile.email) {
      url += `?parent_email=${encodeURIComponent(profile.email)}`;
    }

    fetch(url, { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          setStudents(data.students || []);
          if (data.students?.length > 0) {
            setSelectedStudentId(data.students[0].id);
          }
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch students", err);
        setLoading(false);
      });
  }, [profile]);

  useEffect(() => {
    if (selectedStudentId) {
      setLoading(true);
      setShowReportCard(false);
      fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "https://abhirva-backend.onrender.com"}/api/parent/student_progress/${selectedStudentId}`, { cache: 'no-store' })
        .then(res => res.json())
        .then(data => {
          if (data.status === "success") {
            setStudentProgress(data.progress);
          } else {
            setStudentProgress(null);
          }
          setLoading(false);
        })
        .catch(err => {
          console.error("Failed to fetch progress", err);
          setLoading(false);
        });
    } else {
      setStudentProgress(null);
      setShowReportCard(false);
    }
  }, [selectedStudentId]);

  return (
    <div className={styles.dashboardContainer}>
      <header className={styles.header}>
        <div className={styles.welcomeText}>
          <h1>Parent <span className="gradient-text">Dashboard</span></h1>
          <p>Track your child's progress and performance</p>
        </div>
      </header>

      <div className={styles.grid}>
        <div className="glass-panel section" style={{ gridColumn: '1 / -1' }}>
          <h2 className={styles.sectionTitle}>👨‍👩‍👧 Linked Students</h2>
          
          <div style={{ marginBottom: "2rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", color: "var(--text-secondary)" }}>Select a Student to Track:</label>
            {students.length === 0 ? (
              <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-gray-300">
                You have no linked students. Please contact the administrator to link your child's account.
              </div>
            ) : (
              <select
                value={selectedStudentId}
                onChange={(e) => setSelectedStudentId(e.target.value)}
                style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.2)", width: "100%", maxWidth: "400px", color: "black", fontSize: "1rem" }}
              >
                <option value="">-- Select a Student --</option>
                {students.map(student => (
                  <option key={student.id} value={student.id}>
                    {student.full_name || student.name || student.email || student.id.substring(0, 8)}{student.grade ? ` (${student.grade})` : ""}
                  </option>
                ))}
              </select>
            )}
          </div>

          {loading && (
            <div className="animate-pulse text-indigo-400 font-bold py-4">Loading student progress...</div>
          )}
          
          {!loading && studentProgress && (
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 shadow-xl transition-all">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <div>
                  <h3 className="text-2xl font-bold text-white mb-1">
                    {students.find(s => s.id === selectedStudentId)?.full_name || students.find(s => s.id === selectedStudentId)?.name || students.find(s => s.id === selectedStudentId)?.email || 'Student'}
                  </h3>
                  <p className="text-gray-400 text-sm uppercase tracking-widest">Recent Activity & Points</p>
                </div>
                
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-xl font-black text-green-400 mb-1">
                      {studentProgress.total_points} <span className="text-sm font-normal text-gray-400">Quiz pts</span>
                    </p>
                    <p className="text-xl font-black text-blue-400">
                      {studentProgress.book_points} <span className="text-sm font-normal text-gray-400">Book pts</span>
                    </p>
                  </div>
                  
                  <button 
                    onClick={() => setShowReportCard(!showReportCard)}
                    className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white font-bold py-3 px-6 rounded-xl shadow-[0_0_15px_rgba(99,102,241,0.5)] hover:shadow-[0_0_25px_rgba(99,102,241,0.7)] transition-all transform hover:-translate-y-1"
                  >
                    {showReportCard ? 'Hide Report Card' : '📄 Generate Report Card'}
                  </button>
                </div>
              </div>

              {showReportCard && (
                <div className="mt-8 pt-8 border-t border-white/10">
                  <div className="bg-white text-black p-8 md:p-12 rounded-xl shadow-2xl printable-report">
                    <div className="text-center mb-8 border-b-2 border-gray-200 pb-6">
                      <h2 className="text-4xl font-black text-indigo-900 mb-2">PROGRESS REPORT</h2>
                      <p className="text-gray-500 font-medium">Abhirva Learning Official Transcript</p>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-8 mb-10">
                      <div className="bg-gray-50 p-6 rounded-xl border border-gray-100">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Student Name</h4>
                        <p className="text-xl font-bold text-gray-800">
                          {students.find(s => s.id === selectedStudentId)?.full_name || 'N/A'}
                        </p>
                      </div>
                      <div className="bg-gray-50 p-6 rounded-xl border border-gray-100 flex justify-around">
                        <div className="text-center">
                          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Quiz Score</h4>
                          <p className="text-3xl font-black text-green-600">{studentProgress.total_points}</p>
                        </div>
                        <div className="text-center">
                          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Library Score</h4>
                          <p className="text-3xl font-black text-blue-600">{studentProgress.book_points}</p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-lg font-bold text-gray-800 mb-4 border-b pb-2">Recent Quiz Performances</h4>
                      {(!studentProgress.recent_attempts || studentProgress.recent_attempts.length === 0) ? (
                        <p className="text-gray-500 italic py-4">No recent quiz attempts found on record.</p>
                      ) : (
                        <div className="space-y-3">
                          {studentProgress.recent_attempts.map((attempt: any) => {
                            const percentage = Math.round((attempt.score / attempt.max_score) * 100) || 0;
                            let gradeColor = "text-green-600";
                            if (percentage < 50) gradeColor = "text-red-600";
                            else if (percentage < 80) gradeColor = "text-yellow-600";

                            return (
                              <div key={attempt.id} className="flex justify-between items-center p-4 bg-gray-50 rounded-lg border border-gray-100">
                                <div>
                                  <strong className="text-gray-800 text-lg">{attempt.topics || "General Quiz"}</strong>
                                  <p className="text-sm text-gray-500 mt-1">
                                    {new Date(attempt.created_at).toLocaleDateString("en-US", { year: 'numeric', month: 'long', day: 'numeric' })}
                                  </p>
                                </div>
                                <div className="text-right">
                                  <div className={`text-2xl font-black ${gradeColor}`}>
                                    {attempt.score} <span className="text-sm text-gray-400">/ {attempt.max_score}</span>
                                  </div>
                                  <div className={`text-xs font-bold uppercase ${gradeColor}`}>{percentage}%</div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                    
                    <div className="mt-10 pt-6 border-t border-gray-200 text-center">
                      <button 
                        onClick={() => window.print()}
                        className="bg-gray-800 hover:bg-black text-white font-bold py-2 px-8 rounded-full transition-colors print:hidden"
                      >
                        🖨️ Print Document
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ParentDashboard() {
  return (
    <AuthGuard requiredRole="PARENT">
      <ParentDashboardContent />
    </AuthGuard>
  );
}
