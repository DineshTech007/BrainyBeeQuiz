"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AuthGuard, useAuth } from "../../../lib/auth-context";

const BACKEND_URL = process.env.NODE_ENV === "production" ? "https://abhirva-backend.onrender.com" : "http://127.0.0.1:8000";

function StudentReportContent() {
  const { profile } = useAuth();
  const [progress, setProgress] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!profile?.id) return;

    fetch(`${BACKEND_URL}/api/parent/student_progress/${profile.id}`, { cache: "no-store" })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          setProgress(data.progress);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch progress", err);
        setLoading(false);
      });
  }, [profile?.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0c10] text-white flex items-center justify-center font-sans">
        <div className="animate-pulse text-xl text-indigo-400 font-bold">Loading Your Progress...</div>
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="min-h-screen bg-[#0b0c10] text-white flex flex-col items-center justify-center font-sans">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="text-2xl font-bold mb-4">Could not load progress</h2>
        <Link href="/student/dashboard" className="text-indigo-400 underline">Back to Dashboard</Link>
      </div>
    );
  }

  const { total_points, book_points, recent_attempts } = progress;
  const overallPoints = total_points + book_points;

  return (
    <main className="min-h-screen bg-[#0b0c10] text-white relative overflow-hidden font-sans">
      {/* Background Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600 rounded-full mix-blend-multiply filter blur-[120px] opacity-30 animate-blob"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-600 rounded-full mix-blend-multiply filter blur-[120px] opacity-30 animate-blob animation-delay-2000"></div>

      <div className="relative max-w-5xl mx-auto px-6 py-16 z-10">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12">
          <div>
            <Link href="/student/dashboard" className="text-indigo-400 hover:text-indigo-300 transition flex items-center gap-2 mb-4 font-bold text-sm uppercase tracking-wider">
              ← Back to Dashboard
            </Link>
            <h1 className="text-5xl md:text-6xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
              My Progress Report
            </h1>
            <p className="text-gray-400 mt-2 text-lg">Detailed breakdown of your learning journey.</p>
          </div>
        </div>

        {/* Gamification Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl relative overflow-hidden group hover:border-indigo-500/50 transition-colors">
            <div className="absolute top-0 right-0 p-4 text-4xl opacity-20 group-hover:opacity-100 transition-opacity">🏆</div>
            <h3 className="text-gray-400 font-bold mb-2 uppercase tracking-widest text-sm">Overall XP</h3>
            <div className="text-5xl font-black text-white">{overallPoints}</div>
            <p className="text-indigo-300 mt-2 text-sm font-medium">Total learning points earned</p>
          </div>

          <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl relative overflow-hidden group hover:border-green-500/50 transition-colors">
            <div className="absolute top-0 right-0 p-4 text-4xl opacity-20 group-hover:opacity-100 transition-opacity">📝</div>
            <h3 className="text-gray-400 font-bold mb-2 uppercase tracking-widest text-sm">Quiz Points</h3>
            <div className="text-5xl font-black text-white">{total_points}</div>
            <p className="text-green-300 mt-2 text-sm font-medium">Earned from taking tests</p>
          </div>

          <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl relative overflow-hidden group hover:border-purple-500/50 transition-colors">
            <div className="absolute top-0 right-0 p-4 text-4xl opacity-20 group-hover:opacity-100 transition-opacity">📚</div>
            <h3 className="text-gray-400 font-bold mb-2 uppercase tracking-widest text-sm">Library Points</h3>
            <div className="text-5xl font-black text-white">{book_points}</div>
            <p className="text-purple-300 mt-2 text-sm font-medium">Earned from reading books</p>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <span>⚡</span> Recent Quiz Attempts
          </h2>
          
          {recent_attempts && recent_attempts.length > 0 ? (
            <div className="space-y-4">
              {recent_attempts.map((attempt: any) => {
                const percentage = Math.round((attempt.score / attempt.max_score) * 100) || 0;
                let colorClass = "text-green-400";
                let bgClass = "bg-green-400/10";
                if (percentage < 50) {
                  colorClass = "text-red-400";
                  bgClass = "bg-red-400/10";
                } else if (percentage < 80) {
                  colorClass = "text-yellow-400";
                  bgClass = "bg-yellow-400/10";
                }

                return (
                  <div key={attempt.id} className="flex flex-col md:flex-row md:items-center justify-between p-6 bg-white/5 border border-white/5 rounded-2xl hover:bg-white/10 transition-colors">
                    <div className="mb-4 md:mb-0">
                      <div className="font-bold text-lg text-white mb-1">
                        {attempt.topics?.join(", ") || "General Quiz"}
                      </div>
                      <div className="text-gray-400 text-sm">
                        {new Date(attempt.created_at).toLocaleDateString("en-US", {
                          year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
                        })}
                      </div>
                    </div>
                    
                    <div className={`px-6 py-3 rounded-xl flex flex-col items-center min-w-[120px] ${bgClass}`}>
                      <div className={`text-2xl font-black ${colorClass}`}>
                        {attempt.score} / {attempt.max_score}
                      </div>
                      <div className={`text-xs font-bold uppercase tracking-widest mt-1 ${colorClass}`}>
                        {percentage}% Score
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12 bg-white/5 rounded-2xl border border-dashed border-white/20">
              <div className="text-4xl mb-3 opacity-50">📭</div>
              <p className="text-gray-400 font-medium">No recent quiz attempts found.</p>
              <Link href="/student/quiz/setup" className="inline-block mt-4 px-6 py-2 bg-indigo-600/20 text-indigo-400 rounded-lg font-bold hover:bg-indigo-600/40 transition">
                Take a Quiz Now
              </Link>
            </div>
          )}
        </div>

      </div>
    </main>
  );
}

export default function StudentReportPage() {
  return (
    <AuthGuard requiredRole="STUDENT">
      <StudentReportContent />
    </AuthGuard>
  );
}
