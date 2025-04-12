import React, { useState, useEffect } from "react";
import { Square, CheckIcon, X, ArrowRightIcon } from "lucide-react";

interface CheckersBoardProps {
  boardState?: number[][];
  selectedPiece?: { row: number; col: number } | null;
  validMoves?: Array<{ row: number; col: number }>;
  suggestedMove?: {
    from: { row: number; col: number };
    to: { row: number; col: number };
  };
  onPieceSelect?: (row: number, col: number) => void;
  onPieceMove?: (
    fromRow: number,
    fromCol: number,
    toRow: number,
    toCol: number,
  ) => void;
  isConfigureMode?: boolean;
  onConfigurePiece?: (row: number, col: number, pieceType: number) => void;
  showDebugInfo?: boolean;
}

const CheckersBoard: React.FC<CheckersBoardProps> = ({
  boardState = Array(8)
    .fill(0)
    .map(() => Array(8).fill(0)),
  selectedPiece = null,
  validMoves = [],
  suggestedMove = undefined,
  onPieceSelect = () => {},
  onPieceMove = () => {},
  isConfigureMode = false,
  onConfigurePiece = () => {},
  showDebugInfo = false,
}) => {
  // State to track hover state for showing valid moves more clearly
  const [hoveredSquare, setHoveredSquare] = useState<{
    row: number;
    col: number;
  } | null>(null);

  // Determine if a square is a valid move destination
  const isValidMove = (row: number, col: number) => {
    return validMoves.some((move) => move.row === row && move.col === col);
  };

  // Determine if a square is part of the suggested move
  const isSuggestedMove = (row: number, col: number) => {
    if (!suggestedMove) return false;

    return (
      (suggestedMove.from.row === row && suggestedMove.from.col === col) ||
      (suggestedMove.to.row === row && suggestedMove.to.col === col)
    );
  };

  // Handle click on a board square
  const handleSquareClick = (row: number, col: number) => {
    // If in configure mode, cycle through piece types
    if (isConfigureMode) {
      const currentPiece = boardState[row][col];
      let nextPiece;

      // Cycle through: empty -> red man -> red king -> black man -> black king -> empty
      switch (currentPiece) {
        case 0:
          nextPiece = 1;
          break; // empty -> red man
        case 1:
          nextPiece = 2;
          break; // red man -> red king
        case 2:
          nextPiece = -1;
          break; // red king -> black man
        case -1:
          nextPiece = -2;
          break; // black man -> black king
        case -2:
          nextPiece = 0;
          break; // black king -> empty
        default:
          nextPiece = 0;
      }

      onConfigurePiece(row, col, nextPiece);
      return;
    }

    // Normal game mode
    // If there's a piece at this position and no piece is currently selected
    if (boardState[row][col] !== 0 && !selectedPiece) {
      onPieceSelect(row, col);
    }
    // If a piece is selected and this is a valid move destination
    else if (selectedPiece && isValidMove(row, col)) {
      onPieceMove(selectedPiece.row, selectedPiece.col, row, col);
    }
    // If a piece is selected but this is not a valid move, deselect
    else if (selectedPiece) {
      onPieceSelect(-1, -1); // Deselect
    }
  };

  // Render a piece based on its value
  const renderPiece = (value: number) => {
    if (value === 0) return null;

    const isRed = value > 0;
    const isKing = Math.abs(value) === 2;

    return (
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center
          ${isRed ? "bg-red-600" : "bg-gray-800"}
          ${isKing ? "border-2 border-yellow-400" : ""}
        `}
      >
        {isKing && <CheckIcon className="h-5 w-5 text-yellow-400" />}
      </div>
    );
  };

  // Convert board to bitboard for debug info
  const getBitboardDebugInfo = () => {
    if (!showDebugInfo) return null;

    // Import functions from bitboard.ts
    const { arrayToBitboard, bitboardToString } = require("../ai/bitboard");
    const bitboard = arrayToBitboard(boardState);

    return (
      <div className="mt-4 p-3 bg-gray-100 rounded text-xs font-mono overflow-x-auto">
        <pre>{bitboardToString(bitboard)}</pre>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 w-[600px] h-[600px]">
      {isConfigureMode && (
        <div className="mb-4 p-2 bg-yellow-100 rounded text-sm">
          <p className="font-bold">Configure Mode</p>
          <p>Click on squares to cycle through piece types</p>
        </div>
      )}
      <div className="grid grid-cols-8 grid-rows-8 w-full h-full gap-0 border border-gray-300">
        {Array(8)
          .fill(0)
          .map((_, rowIndex) =>
            Array(8)
              .fill(0)
              .map((_, colIndex) => {
                const isBlackSquare = (rowIndex + colIndex) % 2 === 1;
                const isSelected =
                  selectedPiece?.row === rowIndex &&
                  selectedPiece?.col === colIndex;
                const isValidMoveSquare = isValidMove(rowIndex, colIndex);
                const isSuggested = isSuggestedMove(rowIndex, colIndex);
                const isHovered =
                  hoveredSquare?.row === rowIndex &&
                  hoveredSquare?.col === colIndex;

                return (
                  <div
                    key={`${rowIndex}-${colIndex}`}
                    className={`
                  relative flex items-center justify-center
                  ${isBlackSquare ? "bg-gray-600" : "bg-gray-200"}
                  ${isSelected ? "ring-4 ring-blue-500 z-10" : ""}
                  ${isValidMoveSquare && isHovered ? "bg-green-200" : ""}
                  ${isSuggested ? "ring-2 ring-yellow-400 z-10" : ""}
                  cursor-pointer
                `}
                    onClick={() => handleSquareClick(rowIndex, colIndex)}
                    onMouseEnter={() =>
                      setHoveredSquare({ row: rowIndex, col: colIndex })
                    }
                    onMouseLeave={() => setHoveredSquare(null)}
                  >
                    {renderPiece(boardState[rowIndex][colIndex])}

                    {/* Valid move indicator */}
                    {isValidMoveSquare && (
                      <div className="absolute w-4 h-4 rounded-full bg-green-500 opacity-50"></div>
                    )}

                    {/* Suggested move arrow/indicator */}
                    {suggestedMove &&
                      suggestedMove.to.row === rowIndex &&
                      suggestedMove.to.col === colIndex && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="w-6 h-6 rounded-full bg-yellow-400 opacity-70 animate-pulse"></div>
                        </div>
                      )}

                    {/* Suggested move arrow */}
                    {suggestedMove &&
                      suggestedMove.from.row === rowIndex &&
                      suggestedMove.from.col === colIndex && (
                        <div className="absolute top-0 right-0 w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center animate-pulse">
                          <ArrowRightIcon className="h-4 w-4 text-black" />
                        </div>
                      )}
                  </div>
                );
              }),
          )
          .flat()}
      </div>

      {/* Board coordinates */}
      <div className="flex justify-between mt-2 px-6">
        {["A", "B", "C", "D", "E", "F", "G", "H"].map((letter) => (
          <div key={letter} className="text-sm text-gray-600">
            {letter}
          </div>
        ))}
      </div>
      <div className="absolute left-0 top-0 h-full flex flex-col justify-between py-6 px-1">
        {[8, 7, 6, 5, 4, 3, 2, 1].map((number) => (
          <div key={number} className="text-sm text-gray-600">
            {number}
          </div>
        ))}
      </div>

      {showDebugInfo && getBitboardDebugInfo()}
    </div>
  );
};

export default CheckersBoard;
