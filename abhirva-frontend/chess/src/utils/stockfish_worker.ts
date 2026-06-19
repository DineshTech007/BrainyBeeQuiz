// stockfish_worker.ts
// Robust wrapper for the stockfish web worker with MultiPV support

export interface EngineAnalysis {
  eval: number;       // evaluation in pawns (+white, -black)
  bestMove: string;   // best move in UCI format (e.g. "e2e4")
  topMoves: { move: string; eval: number; mate: number | null }[];
}

export class StockfishEngine {
  private worker: Worker | null = null;
  private isReady: boolean = false;
  private initPromise: Promise<void> | null = null;

  private ensureWorker(): Promise<void> {
    if (this.isReady && this.worker) return Promise.resolve();
    if (this.initPromise) return this.initPromise;

    this.initPromise = new Promise<void>((resolve) => {
      if (typeof window === 'undefined') {
        resolve();
        return;
      }

      try {
        this.worker = new Worker('/engine/stockfish.js');

        const onReady = (event: MessageEvent) => {
          if (event.data === 'uciok') {
            this.isReady = true;
            // Enable MultiPV (top 3 lines)
            this.worker!.postMessage('setoption name MultiPV value 3');
            this.worker!.postMessage('isready');
          }
          if (event.data === 'readyok') {
            resolve();
          }
        };

        this.worker.addEventListener('message', onReady);
        this.worker.postMessage('uci');

        // Safety: resolve after 3s even if no uciok
        setTimeout(() => {
          resolve();
        }, 3000);
      } catch (err) {
        console.error("Failed to initialize Stockfish worker:", err);
        resolve();
      }
    });

    return this.initPromise;
  }

  /**
   * Full analysis: evaluation + best move + top 3 lines.
   */
  public async analyzePosition(fen: string, depth: number = 12): Promise<EngineAnalysis> {
    await this.ensureWorker();

    if (!this.worker) {
      return { eval: 0, bestMove: '', topMoves: [] };
    }

    return new Promise<EngineAnalysis>((resolve) => {
      const topMoves: { move: string; eval: number; mate: number | null }[] = [];
      let bestMove = '';

      const handler = (event: MessageEvent) => {
        const line: string = event.data;

        // Parse MultiPV info lines
        if (line.startsWith('info depth') && line.includes('multipv')) {
          const pvMatch = line.match(/multipv\s+(\d+)/);
          const moveMatch = line.match(/\spv\s+(\S+)/);
          const cpMatch = line.match(/score cp\s+(-?\d+)/);
          const mateMatch = line.match(/score mate\s+(-?\d+)/);
          const depthMatch = line.match(/^info depth\s+(\d+)/);

          if (pvMatch && moveMatch && depthMatch) {
            const currentDepth = parseInt(depthMatch[1], 10);
            // Only use results from the final depths
            if (currentDepth >= depth - 2) {
              const pvIdx = parseInt(pvMatch[1], 10) - 1;
              const moveUci = moveMatch[1];
              const evalScore = cpMatch ? parseInt(cpMatch[1], 10) / 100.0 : 0;
              const mateIn = mateMatch ? parseInt(mateMatch[1], 10) : null;

              topMoves[pvIdx] = {
                move: moveUci,
                eval: mateIn !== null ? (mateIn > 0 ? 100 : -100) : evalScore,
                mate: mateIn
              };
            }
          }
        }

        // Parse bestmove
        if (line.startsWith('bestmove')) {
          const bmMatch = line.match(/bestmove\s+(\S+)/);
          if (bmMatch) bestMove = bmMatch[1];

          this.worker!.removeEventListener('message', handler);

          const mainEval = topMoves.length > 0 ? topMoves[0].eval : 0;
          resolve({
            eval: mainEval,
            bestMove,
            topMoves: topMoves.filter(Boolean) // remove any gaps
          });
        }
      };

      this.worker!.addEventListener('message', handler);
      this.worker!.postMessage('position fen ' + fen);
      this.worker!.postMessage('go depth ' + depth);

      // Safety timeout
      setTimeout(() => {
        this.worker?.postMessage('stop');
      }, 6000);
    });
  }

  /**
   * Quick evaluation only (backward compatible).
   */
  public async evaluatePosition(fen: string, depth: number = 12): Promise<number> {
    const result = await this.analyzePosition(fen, depth);
    return result.eval;
  }

  /**
   * Get best move only (backward compatible).
   */
  public async getBestMove(fen: string, depth: number = 10): Promise<string> {
    const result = await this.analyzePosition(fen, depth);
    return result.bestMove;
  }

  public stop() {
    if (this.worker) {
      this.worker.postMessage('stop');
    }
  }

  public terminate() {
    if (this.worker) {
      this.worker.postMessage('stop');
      this.worker.terminate();
      this.worker = null;
      this.isReady = false;
      this.initPromise = null;
    }
  }
}

// Singleton instance
export const engine = new StockfishEngine();
