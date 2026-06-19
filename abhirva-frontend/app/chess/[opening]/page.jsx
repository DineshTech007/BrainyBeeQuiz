import React from 'react';
import ChessTutor from '../../../chess/src/components/ChessTutor';

async function getOpeningData(opening) {
  // Try to fetch from backend
  try {
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "https://abhirva-backend.onrender.com";
    const res = await fetch(`${BACKEND_URL}/api/chess/openings/${opening}`, {
      cache: 'no-store'
    });
    
    if (!res.ok) {
      return null;
    }
    
    const data = await res.json();
    return data.syllabusData;
  } catch (error) {
    console.error("Failed to fetch chess data:", error);
    return null;
  }
}

export default async function ChessOpeningPage({ params }) {
  // Await the params in Next.js 15+ if needed, or destructure directly.
  const { opening } = await params;
  
  const syllabusData = await getOpeningData(opening);

  if (!syllabusData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
        <div className="bg-white shadow-xl rounded-2xl p-10 max-w-lg w-full text-center">
          <h1 className="text-3xl font-black text-red-600 mb-4">Opening Not Found</h1>
          <p className="text-gray-600 text-lg">
            Could not load variations for "{opening}". Have you run the backend parser script yet?
          </p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#f8f9fa] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto mb-8 text-center">
        <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-700 to-purple-700 drop-shadow-md inline-block capitalize">
          {opening} Opening Masterclass
        </h1>
        <p className="mt-4 text-xl text-gray-600 font-medium">Learn the theory behind the {opening} opening, move by move.</p>
      </div>
      
      <ChessTutor syllabusData={syllabusData} />
    </main>
  );
}
