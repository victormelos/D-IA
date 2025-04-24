import unittest
from board import Board

class TestBoard(unittest.TestCase):
    def test_initial_board(self):
        board = Board.initial()
        # 12 peças brancas e 12 pretas
        self.assertEqual(bin(board.bitboard_white).count('1'), 12)
        self.assertEqual(bin(board.bitboard_black).count('1'), 12)
        self.assertEqual(board.kings_white, 0)
        self.assertEqual(board.kings_black, 0)
        print(board)

if __name__ == '__main__':
    unittest.main() 