"use client";
import { useState } from "react";
import { Chessboard } from "react-chessboard";
import { Chess } from "chess.js";

export default function TestPage() {
  const [chess] = useState(new Chess());
  const [fen, setFen] = useState(chess.fen());

  const makeRandomMove = () => {
    const moves = chess.moves();
    if (moves.length === 0) return;
    const move = moves[Math.floor(Math.random() * moves.length)];
    chess.move(move);
    setFen(chess.fen());
  };

  return (
    <div style={{ padding: 50, maxWidth: 600 }}>
      <button onClick={makeRandomMove} style={{ marginBottom: 20, padding: 10, background: 'blue', color: 'white' }}>
        Make Random Move
      </button>
      <Chessboard position={fen} />
      <div style={{ marginTop: 20 }}>Current FEN: {fen}</div>
    </div>
  );
}
