"use client";

// @ts-nocheck
import React, { useState, useEffect, useRef } from 'react';
import CustomChessBoard from './CustomChessBoard';
import audioEngine from '../utils/audio_engine';

import { Chess } from 'chess.js';

// ---------------------------------------------------------------------------
// FEN Resolution Utilities
// ---------------------------------------------------------------------------

/**
 * Parses the full move list into an array of guaranteed valid FEN strings.
 * It prioritizes the backend's FEN if present. If missing, it computes it via chess.js.
 */
function computeVariationFens(moves: any[]): string[] {
  if (!moves || moves.length === 0) return [];
  
  const fens: string[] = [];
  const chess = new Chess();
  
  for (let i = 0; i < moves.length; i++) {
    const moveData = moves[i];
    
    // If backend explicitly provided a valid FEN, use it and sync the chess.js state to it!
    if (moveData.fen && moveData.fen.split(' ').length >= 4) {
      fens.push(moveData.fen);
      try { chess.load(moveData.fen); } catch(e) {} // Sync our fallback engine
      continue;
    }
    
    // Otherwise, try to compute it from the notation
    let fen = fens.length > 0 ? fens[i-1] : 'start';
    if (moveData && moveData.notation) {
      let cleanNotation = String(moveData.notation)
        .replace(/[!?]/g, '')
        .trim()
        .replace(/^\d+\.?\s*\.?\s*\.?\s*/, '')
        .split(/\s+/)[0];
        
      if (cleanNotation) {
        try {
          chess.move(cleanNotation);
          fen = chess.fen();
        } catch (e) {
          // If chess.js rejects it (e.g. placeholder text), keep the previous FEN
        }
      }
    }
    fens.push(fen);
  }
  return fens;
}

/**
 * Parse a move notation (SAN like "e4", "Nf3", "O-O") into from/to squares.
 * Returns highlight squares for the last move.
 * This is a best-effort parser; react-chessboard also auto-highlights.
 */
function parseNotationToSquares(notation: string | undefined): string[] {
  if (!notation) return [];
  // If we have a move like "e4" — the destination square is in the notation
  // Extract any lowercase letter + number combos as potential squares
  const matches = notation.match(/[a-h][1-8]/g);
  return matches ? [...new Set(matches)] : [];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface ChessTutorProps {
  syllabusData: any;
}

export default function ChessTutor({ syllabusData }: ChessTutorProps) {
  const [selectedVariationIdx, setSelectedVariationIdx] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [stars, setStars] = useState(0);
  const [audioSpeed, setAudioSpeed] = useState(0.9);
  const [language, setLanguage] = useState<'mr' | 'hi' | 'en'>('mr');
  const [isMounted, setIsMounted] = useState(false);
  const [showDebug, setShowDebug] = useState(false);
  const prevStepRef = useRef(-1);

  const variations = syllabusData?.variations || [];
  const currentVariation = variations[selectedVariationIdx];
  const moves = currentVariation?.moves || [];
  const currentMoveData = moves[currentStep];

  // Pre-calculate all FENs for this variation once using the robust parser
  const variationFens = React.useMemo(() => computeVariationFens(moves), [moves]);
  const currentFen = variationFens[currentStep] || 'start';

  // Highlight squares from the current move notation
  const highlightSquares = parseNotationToSquares(currentMoveData?.notation);
  const customSquareStyles = React.useMemo(() => {
    const styles: Record<string, object> = {};
    if (Array.isArray(currentMoveData?.highlight_squares)) {
      currentMoveData.highlight_squares.forEach((sq: string) => {
        styles[sq] = {
          background: 'radial-gradient(circle, rgba(16,185,129,0.65) 25%, transparent 75%)',
          borderRadius: '50%',
        };
      });
    }
    highlightSquares.forEach(sq => {
      if (!styles[sq]) {
        styles[sq] = {
          background: 'rgba(255, 213, 0, 0.3)',
          borderRadius: '4px',
        };
      }
    });
    return styles;
  }, [currentMoveData?.highlight_squares, highlightSquares.join(',')]);

  useEffect(() => {
    setIsMounted(true);
    return () => audioEngine.stop();
  }, []);

  // Reset to step 0 when variation changes
  useEffect(() => {
    setCurrentStep(0);
    prevStepRef.current = -1;
  }, [selectedVariationIdx]);

  // Speak when step changes (but not on initial render for same step)
  useEffect(() => {
    if (!currentMoveData) return;
    if (currentStep === prevStepRef.current) return;
    prevStepRef.current = currentStep;

    const textToSpeak = currentMoveData[`coach_text_${language}`];
    if (textToSpeak) {
      audioEngine.speak(textToSpeak, audioSpeed);
    }
  }, [currentStep, language, audioSpeed, selectedVariationIdx, currentMoveData]);

  const handleNext = () => {
    if (currentStep < moves.length - 1) {
      setCurrentStep(prev => prev + 1);
      if (stars < 50) setStars(prev => prev + 2);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const toggleAudioSpeed = () => {
    setAudioSpeed(prev => prev === 0.9 ? 0.7 : (prev === 0.7 ? 1.1 : 0.9));
  };

  if (!currentMoveData) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#ef4444' }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚠️</div>
        <p>No lesson data available. Please check the backend has parsed the opening data.</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-10 items-start justify-center font-sans">

      {/* ---- Left Column: Board & Controls ---- */}
      <div className="w-full lg:w-[55%] flex flex-col items-center">

        {/* Variation Selector */}
        <div className="mb-6 w-full">
          <label htmlFor="variation-select" className="block text-sm font-bold text-gray-700 mb-2">
            Select Chess Variation (व्हेरिएशन निवडा):
          </label>
          <select
            id="variation-select"
            value={selectedVariationIdx}
            onChange={(e) => setSelectedVariationIdx(Number(e.target.value))}
            className="w-full p-4 border-2 border-indigo-300 rounded-xl bg-white text-lg font-semibold text-indigo-900 shadow-sm focus:outline-none focus:ring-4 focus:ring-indigo-200 transition-all cursor-pointer"
          >
            {variations.map((v: any, idx: number) => (
              <option key={v.id || idx} value={idx}>
                {v[`name_${language}`] || v.name_en || `Variation ${idx + 1}`}
              </option>
            ))}
          </select>
        </div>

        <h2 className="text-3xl font-extrabold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-indigo-800 to-purple-800 drop-shadow-sm">
          {currentVariation?.[`name_${language}`] || currentVariation?.name_en}
        </h2>

        {/* Description */}
        {currentVariation?.[`description_${language}`] && (
          <div className="mb-6 w-full max-w-[550px] bg-gradient-to-r from-indigo-50 to-purple-50 border-l-4 border-indigo-600 p-4 rounded-r-2xl shadow-sm">
            <p className="text-gray-700 italic text-base leading-relaxed">
              &ldquo;{currentVariation[`description_${language}`]}&rdquo;
            </p>
          </div>
        )}

        {/* Chess Board — Premium Glassmorphism UI */}
        <div className="w-full max-w-[550px] shadow-[0_20px_50px_rgba(79,_70,_229,_0.3)] rounded-2xl overflow-hidden border-8 border-indigo-900/30 backdrop-blur-xl bg-white/10 relative">
          <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent pointer-events-none z-10" />
          {isMounted && (
            <CustomChessBoard fen={currentFen} />
          )}
        </div>

        {/* Step indicator */}
        <div className="text-xs text-gray-400 mt-2 flex items-center gap-3">
          <span>Move {currentStep + 1}/{moves.length}</span>
          <span>|</span>
          <span style={{ fontFamily: 'monospace' }}>{currentMoveData.notation || '—'}</span>
          <span>|</span>
          <span style={{ fontFamily: 'monospace', fontSize: '0.65rem', color: '#9ca3af', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            FEN: {currentFen === 'start' ? 'start (no position data)' : currentFen.substring(0, 30) + '...'}
          </span>
        </div>



        {/* Controls */}
        <div className="w-full max-w-[550px] mt-6 flex flex-col gap-4">
          <div className="flex justify-between items-center bg-white/80 backdrop-blur-md p-4 rounded-2xl shadow-xl border border-gray-100">
            <button
              onClick={handlePrev}
              disabled={currentStep === 0}
              className="px-6 py-3 bg-white border border-gray-200 text-indigo-700 rounded-xl disabled:opacity-50 font-bold shadow-sm hover:shadow hover:bg-gray-50 transition-all flex items-center gap-2"
            >
              <span>←</span> मागे (Prev)
            </button>
            <div className="text-center">
              <div className="font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600 text-2xl drop-shadow-sm">
                {currentMoveData.notation || `Step ${currentStep + 1}`}
              </div>
              <div className="text-sm font-semibold text-gray-400 uppercase tracking-widest mt-1">
                चाल {currentStep + 1} / {moves.length}
              </div>
            </div>
            <button
              onClick={handleNext}
              disabled={currentStep === moves.length - 1}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl disabled:opacity-50 font-bold shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all flex items-center gap-2"
            >
              पुढे (Next) <span>→</span>
            </button>
          </div>
        </div>
      </div>

      {/* ---- Right Column: AI Coach & Info ---- */}
      <div className="w-full lg:w-[45%] flex flex-col gap-6">

        {/* Stars, Audio, Language */}
        <div className="flex justify-between items-center bg-gradient-to-r from-yellow-50 to-amber-50 p-5 rounded-2xl border border-yellow-200 shadow-sm flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <span className="text-3xl filter drop-shadow-md animate-bounce">⭐</span>
            <span className="font-black text-2xl text-yellow-700">{stars} XP</span>
          </div>

          <div className="flex gap-2 bg-white p-1 rounded-xl shadow-inner border border-gray-100">
            {(['mr', 'hi', 'en'] as const).map(lang => (
              <button
                key={lang}
                onClick={() => setLanguage(lang)}
                className={`px-3 py-1 rounded-lg font-bold text-sm transition-all ${language === lang ? 'bg-indigo-100 text-indigo-700 shadow-sm' : 'text-gray-500 hover:bg-gray-50'}`}
              >
                {lang === 'mr' ? 'मराठी' : lang === 'hi' ? 'हिंदी' : 'English'}
              </button>
            ))}
          </div>

          <button
            onClick={toggleAudioSpeed}
            className="flex items-center gap-2 px-4 py-2 bg-white rounded-full font-bold text-indigo-700 shadow hover:shadow-md transition-all transform hover:scale-105"
          >
            🔊 {audioSpeed}x
          </button>
        </div>

        {/* Coach Card */}
        <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-[2px] rounded-3xl shadow-2xl">
          <div className="bg-white/95 backdrop-blur-xl p-8 rounded-3xl h-full relative overflow-hidden">
            <div className="absolute -top-6 -right-6 text-8xl opacity-10 filter blur-sm">🤖</div>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-2xl shadow-inner">
                🤖
              </div>
              <h3 className="font-black text-2xl text-transparent bg-clip-text bg-gradient-to-r from-indigo-800 to-purple-800">
                AI गुरूजी (Coach)
              </h3>
            </div>
            <p className="text-xl text-gray-800 leading-relaxed font-semibold">
              {currentMoveData[`coach_text_${language}`] || currentMoveData.coach_text_en || 'No coach text for this step.'}
            </p>
          </div>
        </div>

        {/* Pro Tip */}
        {(currentMoveData.tips_mr || currentMoveData.tips_en) && (
          <div className="bg-emerald-50 p-6 rounded-3xl border-2 border-emerald-200 shadow-md transform transition-all hover:-translate-y-1">
            <h4 className="font-black text-emerald-800 text-lg mb-3 flex items-center gap-2">
              <span className="text-2xl">💡</span> महत्त्वाची टीप (Pro Tip)
            </h4>
            <p className="text-emerald-900 text-lg font-medium">
              {language === 'mr' ? (currentMoveData.tips_mr || currentMoveData.tips_en)
               : language === 'hi' ? (currentMoveData.tips_hi || currentMoveData.tips_en)
               : currentMoveData.tips_en}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
