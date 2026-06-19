// stockfish_worker.ts
// Wrapper for the stockfish web worker to evaluate positions

export class StockfishEngine {
  private worker: Worker | null = null;
  private isReady: boolean = false;
  private currentResolve: ((result: any) => void) | null = null;
  private currentReject: ((err: Error) => void) | null = null;
  private resolveMode: 'eval' | 'move' = 'eval';
  private lastScore: number = 0;
  private bestMove: string = '';

  constructor() {
    if (typeof window !== 'undefined') {
      try {
        this.worker = new Worker('/engine/stockfish.js');
        
        this.worker.onmessage = (event) => {
          const line = event.data;
          
          if (line === 'uciok') {
            this.isReady = true;
          }
          
          // Parse evaluation score
          // Stockfish output example: "info depth 15 seldepth 22 multipv 1 score cp 45 nodes 12345 nps 123456 ..."
          // "score mate 3" -> forced mate in 3
          if (line.startsWith('info depth') && line.includes('score cp')) {
            const match = line.match(/score cp (-?\d+)/);
            if (match && this.currentResolve) {
              const score = parseInt(match[1], 10) / 100.0; // convert centipawns to pawns
              // We don't resolve immediately here, we wait for 'bestmove' 
              // but we store the latest score.
              this.lastScore = score;
            }
          } else if (line.startsWith('info depth') && line.includes('score mate')) {
            const match = line.match(/score mate (-?\d+)/);
            if (match && this.currentResolve) {
              const mateIn = parseInt(match[1], 10);
              // Arbitrary large value for mate
              this.lastScore = mateIn > 0 ? 100 - mateIn : -100 - mateIn;
            }
          }
          
          if (line.startsWith('bestmove')) {
            const match = line.match(/bestmove\s+(\S+)/);
            if (match) {
              this.bestMove = match[1];
            }
            if (this.currentResolve) {
              if (this.resolveMode === 'eval') {
                this.currentResolve(this.lastScore);
              } else {
                this.currentResolve(this.bestMove);
              }
              this.currentResolve = null;
              this.currentReject = null;
            }
          }
        };

        this.worker.postMessage('uci');
      } catch (err) {
        console.error("Failed to initialize Stockfish worker:", err);
      }
    }
  }

  /**
   * Evaluate a FEN string.
   * Returns a promise with the evaluation in pawns (e.g. +1.5, -0.8).
   * Positive means White is better, Negative means Black is better.
   */
  public evaluatePosition(fen: string, depth: number = 12): Promise<number> {
    return new Promise((resolve, reject) => {
      if (!this.worker) {
        return reject(new Error("Stockfish not initialized"));
      }
      
      this.currentResolve = resolve;
      this.currentReject = reject;
      this.resolveMode = 'eval';
      this.lastScore = 0;
      
      this.worker.postMessage('position fen ' + fen);
      this.worker.postMessage('go depth ' + depth);
      
      // Safety timeout in case it hangs
      setTimeout(() => {
        if (this.currentResolve) {
          this.worker?.postMessage('stop');
          // Wait a tiny bit for bestmove to trigger after stop
          setTimeout(() => {
             if (this.currentResolve && this.resolveMode === 'eval') {
                this.currentResolve(this.lastScore);
                this.currentResolve = null;
                this.currentReject = null;
             }
          }, 100);
        }
      }, 5000); // 5 sec max wait
    });
  }

  /**
   * Get the best move for a FEN string.
   * Returns a promise with the best move string (e.g. "e2e4").
   */
  public getBestMove(fen: string, depth: number = 10): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!this.worker) {
        return reject(new Error("Stockfish not initialized"));
      }
      
      this.currentResolve = resolve;
      this.currentReject = reject;
      this.resolveMode = 'move';
      this.bestMove = '';
      
      this.worker.postMessage('position fen ' + fen);
      this.worker.postMessage('go depth ' + depth);
      
      setTimeout(() => {
        if (this.currentResolve) {
          this.worker?.postMessage('stop');
          setTimeout(() => {
             if (this.currentResolve && this.resolveMode === 'move') {
                this.currentResolve(this.bestMove);
                this.currentResolve = null;
                this.currentReject = null;
             }
          }, 100);
        }
      }, 5000); // 5 sec max wait
    });
  }

  public stop() {
    if (this.worker) {
      this.worker.postMessage('stop');
      this.worker.terminate();
    }
  }
}

// Singleton instance
export const engine = new StockfishEngine();
