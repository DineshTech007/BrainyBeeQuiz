"use client";

import React, { useState, useEffect } from 'react';
import ChessTutor from '@/chess/src/components/ChessTutor';

const BACKEND_URL = 'http://localhost:8000';

interface Variation {
  id: string;
  name_en: string;
  name_mr: string;
  name_hi: string;
  description_en?: string;
  description_mr?: string;
  description_hi?: string;
  moves: any[];
}

interface SyllabusData {
  variations: Variation[];
}

export default function ChessTutorPage() {
  const [openings, setOpenings] = useState<string[]>([]);
  const [selectedOpening, setSelectedOpening] = useState<string>('');
  const [syllabusData, setSyllabusData] = useState<SyllabusData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all available openings
  useEffect(() => {
    async function fetchOpenings() {
      try {
        const res = await fetch(`${BACKEND_URL}/api/chess/openings`, { cache: 'no-store' });
        if (!res.ok) throw new Error('Failed to load openings');
        const data = await res.json();
        const openingList: string[] = data.openings || [];
        // Sort for consistent display
        openingList.sort();
        setOpenings(openingList);
        if (openingList.length > 0) {
          setSelectedOpening(openingList[0]);
        }
      } catch (e: any) {
        setError('Backend offline — cannot load openings. Make sure the FastAPI server is running.');
      }
    }
    fetchOpenings();
  }, []);

  // Fetch syllabus data whenever the selected opening changes
  useEffect(() => {
    if (!selectedOpening) return;

    async function fetchSyllabus() {
      setLoading(true);
      setError(null);
      setSyllabusData(null);
      try {
        const res = await fetch(`${BACKEND_URL}/api/chess/openings/${encodeURIComponent(selectedOpening)}`, {
          cache: 'no-store',
        });
        if (!res.ok) throw new Error(`No data for opening: ${selectedOpening}`);
        const data = await res.json();
        setSyllabusData(data.syllabusData);
      } catch (e: any) {
        setError(e.message || 'Failed to load opening data');
      } finally {
        setLoading(false);
      }
    }

    fetchSyllabus();
  }, [selectedOpening]);

  // Label map for nice display names
  const openingLabel = (name: string) =>
    name.charAt(0).toUpperCase() + name.slice(1);

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold text-indigo-900 tracking-tight sm:text-5xl">
            AI Chess Tutor
          </h1>
          <p className="mt-4 max-w-2xl text-xl text-gray-500 mx-auto">
            Learn and master chess openings with our interactive &quot;Marathish&quot; AI coach.
          </p>
        </div>

        {/* Opening Selector */}
        {openings.length > 0 && (
          <div className="flex justify-center mb-8">
            <div className="bg-white rounded-2xl shadow-md border border-gray-200 p-4 flex flex-wrap gap-3 items-center">
              <span className="text-sm font-bold text-gray-600 mr-2">Select Opening:</span>
              {openings.map((op) => (
                <button
                  key={op}
                  onClick={() => setSelectedOpening(op)}
                  className={`px-5 py-2 rounded-xl font-bold text-sm transition-all duration-200 border-2 ${
                    selectedOpening === op
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-md scale-105'
                      : 'bg-white text-indigo-700 border-indigo-200 hover:border-indigo-400 hover:bg-indigo-50'
                  }`}
                >
                  ♟ {openingLabel(op)}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-center font-semibold">
            ⚠️ {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <div className="flex flex-col items-center gap-4">
              <div className="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
              <p className="text-indigo-600 font-bold text-lg">Loading {openingLabel(selectedOpening)} variations...</p>
            </div>
          </div>
        )}

        {/* Chess Tutor */}
        {syllabusData && !loading && (
          <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-3">
              <h2 className="text-white font-bold text-lg">
                ♟ {openingLabel(selectedOpening)} Opening — {syllabusData.variations.length} Variation{syllabusData.variations.length !== 1 ? 's' : ''}
              </h2>
            </div>
            <div className="p-6 sm:p-10">
              <ChessTutor key={selectedOpening} syllabusData={syllabusData} />
            </div>
          </div>
        )}

        {/* No openings */}
        {!loading && !error && openings.length === 0 && (
          <div className="text-center py-20 text-gray-500 font-semibold">
            <p className="text-5xl mb-4">♟️</p>
            <p>No openings found. Make sure the backend is running and has chess data.</p>
          </div>
        )}
      </div>
    </div>
  );
}
