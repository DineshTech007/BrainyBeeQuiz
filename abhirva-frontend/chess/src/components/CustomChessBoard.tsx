import React from 'react';

const PIECE_IMAGES: Record<string, string> = {
  'P': '/chess-pieces/piece_wP.svg',
  'R': '/chess-pieces/piece_wR.svg',
  'N': '/chess-pieces/piece_wN.svg',
  'B': '/chess-pieces/piece_wB.svg',
  'Q': '/chess-pieces/piece_wQ.svg',
  'K': '/chess-pieces/piece_wK.svg',
  'p': '/chess-pieces/piece_bP.svg',
  'r': '/chess-pieces/piece_bR.svg',
  'n': '/chess-pieces/piece_bN.svg',
  'b': '/chess-pieces/piece_bB.svg',
  'q': '/chess-pieces/piece_bQ.svg',
  'k': '/chess-pieces/piece_bK.svg',
};

interface CustomChessBoardProps {
  fen: string;
}

export default function CustomChessBoard({ fen }: CustomChessBoardProps) {
  // Parse FEN into 8x8 array
  const boardFen = fen.split(' ')[0];
  const rows = boardFen.split('/');
  const board: string[][] = [];

  for (let r = 0; r < 8; r++) {
    const rowFen = rows[r] || '8';
    const row: string[] = [];
    for (let i = 0; i < rowFen.length; i++) {
      const char = rowFen[i];
      if (/[1-8]/.test(char)) {
        for (let j = 0; j < parseInt(char, 10); j++) row.push('');
      } else {
        row.push(char);
      }
    }
    board.push(row);
  }

  return (
    <div className="w-full max-w-[550px] aspect-square shadow-[0_20px_50px_rgba(0,_0,_0,_0.2)] rounded-xl overflow-hidden border-4 border-gray-800">
      <div className="grid grid-rows-8 grid-cols-8 w-full h-full">
        {board.map((row, rIdx) => 
          row.map((piece, cIdx) => {
            const isDark = (rIdx + cIdx) % 2 !== 0;
            // Classic premium chess colors
            const bgColor = isDark ? '#739552' : '#ebecd0';
            
            return (
              <div 
                key={`${rIdx}-${cIdx}`}
                className="flex items-center justify-center w-full h-full select-none"
                style={{ backgroundColor: bgColor }}
              >
                {piece && PIECE_IMAGES[piece] && (
                  <img 
                    src={PIECE_IMAGES[piece]} 
                    alt={piece} 
                    className="w-[80%] h-[80%] object-contain drop-shadow-sm transition-transform duration-100 ease-in-out hover:scale-105"
                    draggable={false}
                  />
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
