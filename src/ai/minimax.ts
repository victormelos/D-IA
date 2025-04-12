/**
 * Minimax Algorithm with Alpha-Beta Pruning for Checkers
 *
 * This module provides functions for evaluating possible moves and suggesting
 * the best move for the AI player using the minimax algorithm with alpha-beta pruning.
 */

import {
  BitboardState,
  Player,
  bitboardToArray,
  arrayToBitboard,
} from "./bitboard";
import { queryEndgameDatabase, DatabaseOutcome } from "./endgameDatabase";

// Interface for representing a move
export interface Move {
  from: { row: number; col: number };
  to: { row: number; col: number };
  captures?: Array<{ row: number; col: number }>; // Optional list of captured pieces
}

// Interface for the result of the minimax algorithm
export interface MinimaxResult {
  move: Move;
  score: number;
  depth: number;
  positionsEvaluated: number;
}

/**
 * Suggests the best move for the current player using minimax with alpha-beta pruning
 *
 * @param boardArray The current board state as a 2D array
 * @param currentPlayer The player to move (1 for red, -1 for black)
 * @param maxDepth The maximum search depth
 * @returns The best move and its evaluation
 */
export function suggestMove(
  boardArray: number[][],
  currentPlayer: Player,
  maxDepth: number = 6,
): MinimaxResult {
  // Convert the board array to bitboard representation
  const bitboard = arrayToBitboard(boardArray);
  bitboard.currentPlayer = currentPlayer;

  // Generate all valid moves
  const validMoves = generateMoves(bitboard);

  if (validMoves.length === 0) {
    throw new Error("No valid moves available");
  }

  let bestScore = -Infinity;
  let bestMove = validMoves[0];
  let positionsEvaluated = 0;

  // Apply alpha-beta pruning to each move
  for (const move of validMoves) {
    // Make the move on a copy of the bitboard
    const newBitboard = applyMove(bitboard, move);

    // Switch player
    newBitboard.currentPlayer =
      currentPlayer === Player.RED ? Player.BLACK : Player.RED;

    // Evaluate the move using minimax with alpha-beta pruning
    const score = -alphaBeta(
      newBitboard,
      maxDepth - 1,
      -Infinity,
      -bestScore,
      positionsEvaluated,
    );

    // Update best score and move if this move is better
    if (score > bestScore) {
      bestScore = score;
      bestMove = move;
    }
  }

  return {
    move: bestMove,
    score: bestScore,
    depth: maxDepth,
    positionsEvaluated: positionsEvaluated,
  };
}

/**
 * Minimax algorithm with alpha-beta pruning
 *
 * @param bitboard The current bitboard state
 * @param depth The remaining search depth
 * @param alpha The alpha value for pruning
 * @param beta The beta value for pruning
 * @param positionsEvaluated Counter for positions evaluated
 * @returns The evaluation score for the position
 */
function alphaBeta(
  bitboard: BitboardState,
  depth: number,
  alpha: number,
  beta: number,
  positionsEvaluated: number,
): number {
  // Increment positions evaluated counter
  positionsEvaluated++;

  // Check endgame database
  const dbOutcome = queryEndgameDatabase(bitboard);
  if (dbOutcome !== DatabaseOutcome.UNKNOWN) {
    if (dbOutcome === DatabaseOutcome.WIN) {
      return 10000 + depth; // Prefer quicker wins
    } else if (dbOutcome === DatabaseOutcome.LOSS) {
      return -10000 - depth; // Avoid quicker losses
    } else {
      return 0; // DRAW
    }
  }

  // If we've reached the maximum depth, evaluate the position
  if (depth === 0) {
    return evaluatePosition(bitboard);
  }

  // Generate all valid moves
  const validMoves = generateMoves(bitboard);

  // If there are no valid moves, this is a terminal position
  if (validMoves.length === 0) {
    // No moves means loss for the current player
    return -10000 - depth;
  }

  let bestScore = -Infinity;

  // Evaluate each move
  for (const move of validMoves) {
    // Make the move on a copy of the bitboard
    const newBitboard = applyMove(bitboard, move);

    // Switch player
    newBitboard.currentPlayer =
      bitboard.currentPlayer === Player.RED ? Player.BLACK : Player.RED;

    // Recursively evaluate the position
    const score = -alphaBeta(
      newBitboard,
      depth - 1,
      -beta,
      -alpha,
      positionsEvaluated,
    );

    // Update best score
    bestScore = Math.max(bestScore, score);

    // Update alpha
    alpha = Math.max(alpha, score);

    // Alpha-beta pruning
    if (alpha >= beta) {
      break;
    }
  }

  return bestScore;
}

/**
 * Applies a move to a bitboard and returns the new bitboard state
 *
 * @param bitboard The current bitboard state
 * @param move The move to apply
 * @returns The new bitboard state after the move
 */
function applyMove(bitboard: BitboardState, move: Move): BitboardState {
  // Create a copy of the bitboard
  const newBitboard: BitboardState = {
    redPieces: bitboard.redPieces,
    redKings: bitboard.redKings,
    blackPieces: bitboard.blackPieces,
    blackKings: bitboard.blackKings,
    currentPlayer: bitboard.currentPlayer,
  };

  // Convert to array for easier manipulation (for now)
  const boardArray = bitboardToArray(newBitboard);

  // Get the piece at the from position
  const piece = boardArray[move.from.row][move.from.col];

  // Move the piece
  boardArray[move.to.row][move.to.col] = piece;
  boardArray[move.from.row][move.from.col] = 0;

  // Handle captures
  if (move.captures) {
    for (const capture of move.captures) {
      boardArray[capture.row][capture.col] = 0;
    }
  }

  // Handle promotion to king
  if (piece === 1 && move.to.row === 0) {
    boardArray[move.to.row][move.to.col] = 2; // Promote to red king
  } else if (piece === -1 && move.to.row === 7) {
    boardArray[move.to.row][move.to.col] = -2; // Promote to black king
  }

  // Convert back to bitboard
  return arrayToBitboard(boardArray);
}

/**
 * Generates all valid moves for the current player
 *
 * @param bitboard The current bitboard state
 * @returns Array of valid moves
 */
export function generateMoves(bitboard: BitboardState): Move[] {
  // This is a stub implementation
  // In a real implementation, this would generate all valid moves using bit manipulation

  // Convert to array representation for now
  const boardArray = bitboardToArray(bitboard);

  // Find all pieces of the current player
  const moves: Move[] = [];
  const playerPieces = bitboard.currentPlayer === Player.RED ? 1 : -1;

  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const piece = boardArray[row][col];

      // Check if this is a piece of the current player
      if (Math.sign(piece) === playerPieces) {
        // Check for possible moves
        // This is a very simplified implementation
        const isKing = Math.abs(piece) === 2;
        const directions = [];

        // Regular pieces can only move forward
        if (playerPieces === 1) {
          // Red moves up
          directions.push([-1, -1], [-1, 1]);
        } else {
          // Black moves down
          directions.push([1, -1], [1, 1]);
        }

        // Kings can move in all directions
        if (isKing) {
          if (playerPieces === 1) {
            directions.push([1, -1], [1, 1]);
          } else {
            directions.push([-1, -1], [-1, 1]);
          }
        }

        // Check each direction for a valid move
        for (const [dRow, dCol] of directions) {
          const newRow = row + dRow;
          const newCol = col + dCol;

          // Check if the new position is on the board
          if (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {
            // Check if the new position is empty
            if (boardArray[newRow][newCol] === 0) {
              moves.push({
                from: { row, col },
                to: { row: newRow, col: newCol },
              });
            }
            // Check for captures
            else if (Math.sign(boardArray[newRow][newCol]) === -playerPieces) {
              const jumpRow = newRow + dRow;
              const jumpCol = newCol + dCol;

              // Check if the jump position is on the board and empty
              if (
                jumpRow >= 0 &&
                jumpRow < 8 &&
                jumpCol >= 0 &&
                jumpCol < 8 &&
                boardArray[jumpRow][jumpCol] === 0
              ) {
                moves.push({
                  from: { row, col },
                  to: { row: jumpRow, col: jumpCol },
                  captures: [{ row: newRow, col: newCol }],
                });
              }
            }
          }
        }
      }
    }
  }

  return moves;
}

/**
 * Evaluates a board position
 *
 * @param bitboard The bitboard state to evaluate
 * @returns A score for the position (positive is good for red, negative for black)
 */
export function evaluatePosition(bitboard: BitboardState): number {
  // Check the endgame database first
  const dbOutcome = queryEndgameDatabase(bitboard);

  if (dbOutcome !== DatabaseOutcome.UNKNOWN) {
    // Return a large value for a win/loss position
    if (dbOutcome === DatabaseOutcome.WIN) {
      return bitboard.currentPlayer === Player.RED ? 10000 : -10000;
    } else if (dbOutcome === DatabaseOutcome.LOSS) {
      return bitboard.currentPlayer === Player.RED ? -10000 : 10000;
    } else {
      // DRAW
      return 0;
    }
  }

  // Material evaluation
  const redMen = countBits(bitboard.redPieces & ~bitboard.redKings);
  const redKings = countBits(bitboard.redKings);
  const blackMen = countBits(bitboard.blackPieces & ~bitboard.blackKings);
  const blackKings = countBits(bitboard.blackKings);

  // Kings are worth more than men (2.5 instead of just 2)
  const materialScore = redMen + redKings * 2.5 - (blackMen + blackKings * 2.5);

  // Position evaluation - favor center control and advancement
  let positionScore = 0;
  const boardArray = bitboardToArray(bitboard);

  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const piece = boardArray[row][col];
      if (piece === 0) continue;

      const isRed = piece > 0;
      const isKing = Math.abs(piece) === 2;

      // Center control bonus (higher for center squares)
      const centerValue = getCenterValue(row, col);
      positionScore += isRed ? centerValue : -centerValue;

      // Advancement bonus for non-kings (encourage pawns to advance toward promotion)
      if (!isKing) {
        const advancementValue = isRed ? (7 - row) * 0.1 : row * 0.1;
        positionScore += isRed ? advancementValue : -advancementValue;
      }

      // Edge penalty (pieces on the edge are less mobile)
      if (col === 0 || col === 7) {
        positionScore += isRed ? -0.2 : 0.2;
      }
    }
  }

  // Combine material and position scores
  return materialScore * 3 + positionScore;
}

/**
 * Returns a value indicating how valuable a square is based on its position
 * Center squares are more valuable
 *
 * @param row The row of the square
 * @param col The column of the square
 * @returns A value between 0 and 1 indicating the square's value
 */
function getCenterValue(row: number, col: number): number {
  // Distance from center (3.5, 3.5)
  const rowDistance = Math.abs(row - 3.5);
  const colDistance = Math.abs(col - 3.5);
  const distance = Math.sqrt(
    rowDistance * rowDistance + colDistance * colDistance,
  );

  // Normalize to 0-1 range (max distance is ~5)
  return Math.max(0, 1 - distance / 5);
}

/**
 * Counts the number of set bits in a number
 *
 * @param n The number to count bits in
 * @returns The number of set bits
 */
function countBits(n: number): number {
  let count = 0;
  while (n) {
    count += n & 1;
    n >>>= 1;
  }
  return count;
}
