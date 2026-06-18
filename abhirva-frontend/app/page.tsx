"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import styles from "./page.module.css";
import { useAuth } from "../lib/auth-context";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Home() {
  const { profile, isLoading: authLoading } = useAuth();
  const [quizLeaderboard, setQuizLeaderboard] = useState<any[]>([]);
  const [bookLeaderboard, setBookLeaderboard] = useState<any[]>([]);

  useEffect(() => {
    // Fetch quiz leaderboard
    fetch(`${BACKEND_URL}/api/student/gamification/leaderboard`, { cache: 'no-store' })
      .then(res => res.json())
      .then(data => { if (data.status === "success") setQuizLeaderboard(data.leaderboard.slice(0, 5)); })
      .catch(err => console.error("Leaderboard fetch error:", err));

    // Fetch book leaderboard
    fetch(`${BACKEND_URL}/api/library/leaderboard`, { cache: 'no-store' })
      .then(res => res.json())
      .then(data => { if (data.status === "success") setBookLeaderboard(data.leaderboard.slice(0, 5)); })
      .catch(err => console.error("Book Leaderboard fetch error:", err));
  }, []);

  return (
    <main className={`${styles.main} font-sans`}>
      <div className={styles.hero}>
        <h1 className={styles.title}>
          Master Your Exams with <br />
          <span className="gradient-text">Abhirva Learning</span>
        </h1>
        <p className={styles.subtitle}>
          The ultimate AI-powered preparation platform for 10th Board Exams and Olympiads. 
          Dynamic quizzes, intelligent grading, and a rewarding gamified experience.
        </p>
        
        <div className={styles.ctaContainer}>
          {!authLoading && (
            profile ? (
              <Link href={profile.role === "PARENT" ? "/parent/dashboard" : "/student/dashboard"} className={styles.primaryBtn}>
                Go to My Dashboard →
              </Link>
            ) : (
              <>
                <Link href="/signup" className={styles.primaryBtn}>
                  Sign Up
                </Link>
                <Link href="/login" className={styles.secondaryBtn} style={{display: 'inline-block', textDecoration: 'none'}}>
                  Student Login
                </Link>
                <Link href="/parent/login" className={styles.secondaryBtn} style={{display: 'inline-block', textDecoration: 'none'}}>
                  Parent Login
                </Link>
              </>
            )
          )}
        </div>
      </div>

      {/* Leaderboards Section */}
      <div className="w-full max-w-5xl mt-24 grid grid-cols-1 md:grid-cols-2 gap-8 text-left">
        {/* Quiz Leaderboard */}
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl">
          <h2 className="text-2xl font-bold mb-6 text-white flex items-center gap-3">
            <span className="text-3xl">🏆</span> Top Quiz Scorers
          </h2>
          <div className="flex flex-col gap-3">
            {quizLeaderboard.length === 0 ? (
              <p className="text-gray-400">No scores yet. Be the first!</p>
            ) : (
              quizLeaderboard.map((student: any, idx: number) => {
                const rank = idx + 1;
                let rankColor = "text-gray-400";
                if (rank === 1) rankColor = "text-yellow-400 drop-shadow-[0_0_10px_rgba(250,204,21,0.5)]";
                if (rank === 2) rankColor = "text-gray-300";
                if (rank === 3) rankColor = "text-amber-600";

                return (
                  <div key={student.id} className="flex items-center p-4 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 transition">
                    <span className={`text-2xl font-black w-12 ${rankColor}`}>
                      #{rank}
                    </span>
                    <span className="flex-1 font-semibold text-gray-200">{student.full_name}</span>
                    <span className="font-bold text-green-400">{student.total_points} pts</span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Library Leaderboard */}
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl">
          <h2 className="text-2xl font-bold mb-6 text-white flex items-center gap-3">
            <span className="text-3xl">📚</span> Top Readers
          </h2>
          <div className="flex flex-col gap-3">
            {bookLeaderboard.length === 0 ? (
              <p className="text-gray-400">No readers yet. Start reading!</p>
            ) : (
              bookLeaderboard.map((student: any, idx: number) => {
                const rank = idx + 1;
                let rankColor = "text-gray-400";
                if (rank === 1) rankColor = "text-yellow-400 drop-shadow-[0_0_10px_rgba(250,204,21,0.5)]";
                if (rank === 2) rankColor = "text-gray-300";
                if (rank === 3) rankColor = "text-amber-600";

                return (
                  <div key={student.id} className="flex items-center p-4 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 transition">
                    <span className={`text-2xl font-black w-12 ${rankColor}`}>
                      #{rank}
                    </span>
                    <span className="flex-1 font-semibold text-gray-200">{student.full_name}</span>
                    <span className="font-bold text-blue-400">{student.book_points} pts</span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
