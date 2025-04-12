/**
 * Bitboard representation for checkers
 *
 * This module provides functions for representing and manipulating a checkers board
 * using bit manipulation techniques for efficiency.
 *
 * The board is represented using two 32-bit integers:
 * - One for tracking the positions of all pieces of a player
 * - One for tracking which of those pieces are kings
 */

// Board representation constants
export const BOARD_SIZE = 8;
export const TOTAL_SQUARES = 32; // Only dark squares are used in checkers

// Player constants
export enum Player {
  RED = 1,
  BLACK = -1,
}

// Piece type constants (matches the current board representation)
export enum PieceType {
  EMPTY = 0,
  RED_MAN = 1,
  RED_KING = 2,
  BLACK_MAN = -1,
  BLACK_KING = -2,
}

/**
 * Represents the state of a checkers game using bitboards
 */
export interface BitboardState {
  redPieces: number; // Bitboard for all red pieces
  redKings: number; // Bitboard for red kings
  blackPieces: number; // Bitboard for all black pieces
  blackKings: number; // Bitboard for black kings
  currentPlayer: Player; // Whose turn it is
}

/**
 * Creates an initial bitboard state with pieces in starting positions
 */
export function createInitialBitboardState(): BitboardState {
  // Initial positions for red pieces (bottom 3 rows)
  const redPieces = 0x00000fff; // 12 pieces in the first 3 rows

  // Initial positions for black pieces (top 3 rows)
  const blackPieces = 0xfff00000; // 12 pieces in the last 3 rows

  // No kings at the start
  const redKings = 0;
  const blackKings = 0;

  return {
    redPieces,
    redKings,
    blackPieces,
    blackKings,
    currentPlayer: Player.RED, // Red (bottom) moves first
  };
}

/**
 * Converts from the 2D array board representation to bitboard representation
 *
 * @param boardArray The 8x8 2D array representing the board
 * @returns BitboardState representing the same position
 */
export function arrayToBitboard(boardArray: number[][]): BitboardState {
  let redPieces = 0;
  let redKings = 0;
  let blackPieces = 0;
  let blackKings = 0;

  // Determine whose turn it is based on piece count (simple heuristic)
  // In a real implementation, this would be tracked separately
  let redCount = 0;
  let blackCount = 0;

  // Convert the 8x8 array to bitboard representation
  for (let row = 0; row < BOARD_SIZE; row++) {
    for (let col = 0; col < BOARD_SIZE; col++) {
      // Only process dark squares (where row+col is odd)
      if ((row + col) % 2 === 1) {
        const piece = boardArray[row][col];

        // Calculate the bit position (0-31) for this square
        const bitPosition = getBitPosition(row, col);
        const bitMask = 1 << bitPosition;

        if (piece === PieceType.RED_MAN || piece === PieceType.RED_KING) {
          redPieces |= bitMask;
          redCount++;
          if (piece === PieceType.RED_KING) {
            redKings |= bitMask;
          }
        } else if (
          piece === PieceType.BLACK_MAN ||
          piece === PieceType.BLACK_KING
        ) {
          blackPieces |= bitMask;
          blackCount++;
          if (piece === PieceType.BLACK_KING) {
            blackKings |= bitMask;
          }
        }
      }
    }
  }

  // Simple heuristic: if red has more pieces, it's black's turn and vice versa
  // In a real implementation, turn would be tracked separately
  const currentPlayer = redCount > blackCount ? Player.BLACK : Player.RED;

  return {
    redPieces,
    redKings,
    blackPieces,
    blackKings,
    currentPlayer,
  };
}

/**
 * Converts from bitboard representation to the 2D array board representation
 *
 * @param bitboard The bitboard state
 * @returns 8x8 2D array representing the board
 */
export function bitboardToArray(bitboard: BitboardState): number[][] {
  // Create an empty 8x8 board
  const boardArray = Array(BOARD_SIZE)
    .fill(0)
    .map(() => Array(BOARD_SIZE).fill(0));

  // Fill in the board with pieces from the bitboard
  for (let row = 0; row < BOARD_SIZE; row++) {
    for (let col = 0; col < BOARD_SIZE; col++) {
      // Only process dark squares (where row+col is odd)
      if ((row + col) % 2 === 1) {
        const bitPosition = getBitPosition(row, col);
        const bitMask = 1 << bitPosition;

        if (bitboard.redPieces & bitMask) {
          if (bitboard.redKings & bitMask) {
            boardArray[row][col] = PieceType.RED_KING;
          } else {
            boardArray[row][col] = PieceType.RED_MAN;
          }
        } else if (bitboard.blackPieces & bitMask) {
          if (bitboard.blackKings & bitMask) {
            boardArray[row][col] = PieceType.BLACK_KING;
          } else {
            boardArray[row][col] = PieceType.BLACK_MAN;
          }
        }
      }
    }
  }

  return boardArray;
}

/**
 * Converts row and column coordinates to a bit position (0-31)
 *
 * @param row Row index (0-7)
 * @param col Column index (0-7)
 * @returns Bit position (0-31)
 */
export function getBitPosition(row: number, col: number): number {
  // Only dark squares are used in checkers (where row+col is odd)
  if ((row + col) % 2 === 0) {
    throw new Error("Invalid square: only dark squares are used in checkers");
  }

  // Calculate the bit position (0-31) for this square
  // The mapping goes from bottom-right to top-left in a zigzag pattern
  return row * 4 + (col >> 1);
}

/**
 * Converts a bit position (0-31) to row and column coordinates
 *
 * @param bitPosition Bit position (0-31)
 * @returns [row, col] coordinates
 */
export function getSquareCoordinates(bitPosition: number): [number, number] {
  if (bitPosition < 0 || bitPosition >= TOTAL_SQUARES) {
    throw new Error(`Invalid bit position: ${bitPosition}`);
  }

  const row = Math.floor(bitPosition / 4);
  const col = (bitPosition % 4) * 2 + (row % 2 === 0 ? 1 : 0);

  return [row, col];
}

/**
 * Returns a string representation of the bitboard for debugging
 *
 * @param bitboard The bitboard state
 * @returns String representation of the bitboard
 */
export function bitboardToString(bitboard: BitboardState): string {
  let result = "Bitboard State:\n";
  result += `Red Pieces: 0x${bitboard.redPieces.toString(16).padStart(8, "0")}\n`;
  result += `Red Kings: 0x${bitboard.redKings.toString(16).padStart(8, "0")}\n`;
  result += `Black Pieces: 0x${bitboard.blackPieces.toString(16).padStart(8, "0")}\n`;
  result += `Black Kings: 0x${bitboard.blackKings.toString(16).padStart(8, "0")}\n`;
  result += `Current Player: ${bitboard.currentPlayer === Player.RED ? "RED" : "BLACK"}\n`;

  return result;
}
