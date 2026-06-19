"use client";

import React from 'react';
import Link from 'next/link';
import { ArrowRight, BookOpen, Star, Shield, Cpu } from 'lucide-react';
import { AuthGuard, useAuth } from '../../lib/auth-context';
import { useState, useEffect } from 'react';
async function getAvailableOpenings() {
  try {
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "https://abhirva-backend.onrender.com";
    const res = await fetch(`${BACKEND_URL}/api/chess/openings`, {
      cache: 'no-store'
    });
    
    if (!res.ok) {
      return [];
    }
    
    const data = await res.json();
    return data.openings || [];
  } catch (error) {
    console.error("Failed to fetch openings:", error);
    return [];
  }
}

export default function ChessCoursesPageWrapper() {
  return (
    <AuthGuard requiredRole="STUDENT">
      <ChessCoursesPage />
    </AuthGuard>
  );
}

function ChessCoursesPage() {
  const [openings, setOpenings] = useState([]);
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const { profile } = useAuth();
  
  useEffect(() => {
    if (!profile?.id) return;
    
    // Check access
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "https://abhirva-backend.onrender.com";
    fetch(`${BACKEND_URL}/api/admin/student/${profile.id}/access`, { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success" && Array.isArray(data.subscriptions)) {
          const hasChess = data.subscriptions.some(s => s.name.toLowerCase().includes("chess"));
          setHasAccess(hasChess);
        }
      })
      .catch(console.error);

    // Fetch openings
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "https://abhirva-backend.onrender.com";
    fetch(`${BACKEND_URL}/api/chess/openings`, { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        if (data.openings) setOpenings(data.openings);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [profile?.id]);

  if (loading) {
    return <div style={{ color: 'white', padding: '2rem', textAlign: 'center' }}>Loading...</div>;
  }

  if (!hasAccess) {
    return (
      <main className="min-h-screen bg-[#0b0c10] text-white flex flex-col items-center justify-center">
        <div className="bg-white/10 p-10 rounded-2xl border border-white/20 text-center max-w-md">
          <div className="text-6xl mb-6">🔒</div>
          <h1 className="text-3xl font-bold mb-4">Access Denied</h1>
          <p className="text-gray-300 mb-8">You need the Chess Tutor subscription to access this feature. Please ask your parent to unlock it.</p>
          <Link href="/student/dashboard" className="px-6 py-3 bg-indigo-600 rounded-lg font-bold hover:bg-indigo-700 transition">
            Back to Dashboard
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0b0c10] text-white relative overflow-hidden font-sans">
      {/* Background Ornaments */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600 rounded-full mix-blend-multiply filter blur-[120px] opacity-40 animate-blob"></div>
      <div className="absolute top-[20%] right-[-10%] w-[40%] h-[40%] bg-purple-600 rounded-full mix-blend-multiply filter blur-[120px] opacity-40 animate-blob animation-delay-2000"></div>
      <div className="absolute bottom-[-20%] left-[20%] w-[50%] h-[50%] bg-pink-600 rounded-full mix-blend-multiply filter blur-[120px] opacity-40 animate-blob animation-delay-4000"></div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 z-10">
        
        {/* Header Section */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center justify-center p-3 mb-6 bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl">
            <Cpu className="w-8 h-8 text-indigo-400 mr-3" />
            <span className="text-2xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 uppercase">
              AI Powered
            </span>
          </div>
          <h1 className="text-6xl md:text-8xl font-black mb-6 tracking-tight text-white drop-shadow-lg">
            Master The <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">Board.</span>
          </h1>
          <p className="mt-6 text-xl md:text-3xl text-gray-400 max-w-3xl mx-auto font-medium">
            Select an opening to master its tactical variations with our interactive coach.
          </p>
        </div>

        <div className="glass-panel section" style={{ padding: "2rem", display: "flex", flexDirection: "column", justifyContent: "center" }}>
          <h2 style={{ marginBottom: "1rem" }}>📖 Study Concepts</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
            Learn foundational chess concepts extracted from Grandmaster books in English, Hindi, and Marathi!
          </p>
          <Link href="/chess/study" style={{ background: "linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%)", border: "none", textAlign: "center", display: "block", textDecoration: "none", padding: "12px", borderRadius: "8px", fontWeight: "bold" }}>
            Open Trilingual Study Guide →
          </Link>
        </div>

        {/* Courses Grid */}
        <div className="mb-12">
          <div className="flex items-center gap-4 mb-8 border-b border-white/10 pb-4">
            <BookOpen className="w-8 h-8 text-indigo-400" />
            <h2 className="text-3xl font-bold text-white">Available Masterclasses</h2>
          </div>
          
          {openings.length === 0 ? (
            <div className="p-12 text-center bg-white/5 backdrop-blur-lg rounded-3xl border border-white/10">
              <div className="text-5xl mb-4 opacity-50">♟️</div>
              <h3 className="text-2xl font-bold text-white mb-2">No Openings Found</h3>
              <p className="text-gray-400">The ingestion script is currently running or the backend is offline. Please check back soon.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {openings.map((opening) => (
                <Link href={`/chess/${opening}`} key={opening} className="group relative block h-full">
                  {/* Card Container */}
                  <div className="relative h-full bg-white/5 backdrop-blur-xl rounded-[2rem] border border-white/10 p-8 shadow-2xl transition-all duration-500 overflow-hidden group-hover:-translate-y-2 group-hover:shadow-[0_20px_40px_-15px_rgba(99,102,241,0.4)] group-hover:bg-white/10">
                    
                    {/* Hover Gradient Effect */}
                    <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                    
                    <div className="relative z-10 flex flex-col h-full">
                      {/* Top Bar */}
                      <div className="flex justify-between items-start mb-8">
                        <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg transform group-hover:scale-110 transition-transform duration-500">
                          <span className="text-3xl text-white">♟️</span>
                        </div>
                        <div className="flex items-center gap-1 bg-white/10 px-3 py-1 rounded-full border border-white/5 backdrop-blur-md">
                          <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                          <span className="text-sm font-bold text-yellow-400">Pro</span>
                        </div>
                      </div>

                      {/* Content */}
                      <h3 className="text-3xl font-black text-white mb-4 capitalize tracking-tight group-hover:text-indigo-300 transition-colors">
                        {opening} Opening
                      </h3>
                      <p className="text-gray-400 text-lg mb-8 font-medium leading-relaxed flex-grow">
                        Master the complex variations and deep positional ideas of the {opening} defense. Taught move-by-move by AI.
                      </p>

                      {/* Footer/Action */}
                      <div className="flex items-center justify-between mt-auto pt-6 border-t border-white/10">
                        <div className="flex -space-x-2">
                          <div className="w-8 h-8 rounded-full bg-indigo-500 border-2 border-[#15161d] flex items-center justify-center text-xs font-bold text-white shadow-sm">म</div>
                          <div className="w-8 h-8 rounded-full bg-purple-500 border-2 border-[#15161d] flex items-center justify-center text-xs font-bold text-white shadow-sm">हिं</div>
                          <div className="w-8 h-8 rounded-full bg-pink-500 border-2 border-[#15161d] flex items-center justify-center text-xs font-bold text-white shadow-sm">EN</div>
                        </div>
                        <div className="flex items-center text-indigo-400 font-bold group-hover:text-indigo-300 transition-colors">
                          <span className="mr-2 group-hover:mr-4 transition-all duration-300">Start Learning</span>
                          <ArrowRight className="w-5 h-5" />
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
        
        {/* Features Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
          <div className="bg-white/5 border border-white/10 p-6 rounded-3xl backdrop-blur-sm">
            <Shield className="w-10 h-10 text-emerald-400 mb-4" />
            <h4 className="text-xl font-bold text-white mb-2">Grandmaster Theory</h4>
            <p className="text-gray-400">Extracted directly from top-tier chess literature using AI.</p>
          </div>
          <div className="bg-white/5 border border-white/10 p-6 rounded-3xl backdrop-blur-sm">
            <Star className="w-10 h-10 text-yellow-400 mb-4" />
            <h4 className="text-xl font-bold text-white mb-2">Multilingual Tutor</h4>
            <p className="text-gray-400">Audio playback and visual coaching in Marathi, Hindi, and English.</p>
          </div>
          <div className="bg-white/5 border border-white/10 p-6 rounded-3xl backdrop-blur-sm">
            <Cpu className="w-10 h-10 text-blue-400 mb-4" />
            <h4 className="text-xl font-bold text-white mb-2">Interactive Board</h4>
            <p className="text-gray-400">Play through variations step-by-step with visual annotations.</p>
          </div>
        </div>

      </div>
    </main>
  );
}
