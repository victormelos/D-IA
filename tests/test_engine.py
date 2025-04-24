import unittest
from board import Board
from engine import generate_moves, Color, apply_move

class TestGenerateMoves(unittest.TestCase):
    def test_initial_position_white(self):
        board = Board.initial()
        moves = generate_moves(board, Color.WHITE)
        # Na posição inicial, cada peão branco da terceira linha pode avançar para frente
        # São 7 movimentos possíveis (casas 12 a 15)
        self.assertTrue(all(len(m.path) == 2 for m in moves))
        self.assertTrue(all(not m.is_capture() for m in moves))
        print('Movimentos brancos na posição inicial:')
        for m in moves:
            print(m)

    def test_initial_position_black(self):
        board = Board.initial()
        moves = generate_moves(board, Color.BLACK)
        # Na posição inicial, cada peão preto da sexta linha pode avançar para frente
        self.assertTrue(all(len(m.path) == 2 for m in moves))
        self.assertTrue(all(not m.is_capture() for m in moves))
        print('Movimentos pretos na posição inicial:')
        for m in moves:
            print(m)

    def test_intermediate_capture_white(self):
        # Tabuleiro com captura obrigatória para branco
        # Branco em 17, preto em 22, casa 26 livre
        # Índices: 17 (linha 4, col 2), 22 (linha 5, col 5), 26 (linha 6, col 4)
        w = 1 << 17
        b = 1 << 22
        board = Board(w, b)
        moves = generate_moves(board, Color.WHITE)
        # Deve haver uma captura
        self.assertTrue(any(m.is_capture() for m in moves))
        print('Movimentos brancos com captura obrigatória:')
        for m in moves:
            print(m)

    def test_intermediate_capture_black(self):
        # Tabuleiro com captura obrigatória para preto
        # Preto em 14, branco em 9, casa 5 livre
        b = 1 << 14
        w = 1 << 9
        board = Board(w, b)
        moves = generate_moves(board, Color.BLACK)
        self.assertTrue(any(m.is_capture() for m in moves))
        print('Movimentos pretos com captura obrigatória:')
        for m in moves:
            print(m)

if __name__ == '__main__':
    unittest.main() 