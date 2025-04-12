/**
 * Game State Evaluation for Checkers
 *
 * This module provides functions for evaluating the current state of the game
 * and determining if the game is over (win, loss, or draw).
 */

import {
  BitboardState,
  Player,
  bitboardToArray,
  arrayToBitboard,
} from "./bitboard";
import { generateMoves } from "./minimax";

// Possible game outcomes
export enum GameOutcome {
  IN_PROGRESS = 0,
  RED_WINS = 1,
  BLACK_WINS = -1,
  DRAW = 2,
}

/**
 * Evaluates the current game state and determines if the game is over
 *
 * @param boardArray The current board state as a 2D array
 * @returns The game outcome (in progress, red wins, black wins, or draw)
 */
export function evaluateGameState(boardArray: number[][]): GameOutcome {
  // Convert the board array to bitboard representation
  const bitboard = arrayToBitboard(boardArray);

  // Check if red has any pieces left
  const redPiecesCount = countBits(bitboard.redPieces);
  if (redPiecesCount === 0) {
    return GameOutcome.BLACK_WINS;
  }

  // Check if black has any pieces left
  const blackPiecesCount = countBits(bitboard.blackPieces);
  if (blackPiecesCount === 0) {
    return GameOutcome.RED_WINS;
  }

  // Check if red has any valid moves
  bitboard.currentPlayer = Player.RED;
  const redMoves = generateMoves(bitboard);
  if (redMoves.length === 0) {
    return GameOutcome.BLACK_WINS;
  }

  // Check if black has any valid moves
  bitboard.currentPlayer = Player.BLACK;
  const blackMoves = generateMoves(bitboard);
  if (blackMoves.length === 0) {
    return GameOutcome.RED_WINS;
  }

  // Check for draw conditions (e.g., 40 moves without a capture)
  // This would require tracking move history, which we don't have yet
  // For now, we'll just check for a simple material draw condition
  if (isLikelyDraw(bitboard)) {
    return GameOutcome.DRAW;
  }

  return GameOutcome.IN_PROGRESS;
}

/**
 * Determines if the current position is likely a draw
 * This is a simplified implementation that checks for common draw patterns
 *
 * @param bitboard The current bitboard state
 * @returns True if the position is likely a draw, false otherwise
 */
function isLikelyDraw(bitboard: BitboardState): boolean {
  const redPiecesCount = countBits(bitboard.redPieces);
  const blackPiecesCount = countBits(bitboard.blackPieces);
  const redKingsCount = countBits(bitboard.redKings);
  const blackKingsCount = countBits(bitboard.blackKings);

  // If both sides have only kings and the material is balanced, it's likely a draw
  if (
    redPiecesCount === redKingsCount &&
    blackPiecesCount === blackKingsCount
  ) {
    // Single king vs single king is always a draw
    if (redKingsCount === 1 && blackKingsCount === 1) {
      return true;
    }

    // Two kings vs one king is usually a draw (unless there's a forced win)
    if (
      (redKingsCount === 2 && blackKingsCount === 1) ||
      (redKingsCount === 1 && blackKingsCount === 2)
    ) {
      return true;
    }
  }

  return false;
}

/**
 * Counts the number of set bits in a number (population count)
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

/**
 * Returns a string representation of the game outcome
 *
 * @param outcome The game outcome
 * @returns String representation of the outcome
 */
export function outcomeToString(outcome: GameOutcome): string {
  switch (outcome) {
    case GameOutcome.IN_PROGRESS:
      return "Game in progress";
    case GameOutcome.RED_WINS:
      return "Red wins!";
    case GameOutcome.BLACK_WINS:
      return "Black wins!";
    case GameOutcome.DRAW:
      return "Game drawn";
    default:
      return "Unknown outcome";
  }
}
