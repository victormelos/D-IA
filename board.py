class Board:
    """
    Representa o estado do tabuleiro usando bitboards de 32 bits (casas escuras).
    - bitboard_white: peças brancas (homens e damas)
    - bitboard_black: peças pretas (homens e damas)
    - kings_white: damas brancas
    - kings_black: damas pretas
    """
    def __init__(self, bitboard_white: int, bitboard_black: int, kings_white: int = 0, kings_black: int = 0):
        self.bitboard_white = bitboard_white
        self.bitboard_black = bitboard_black
        self.kings_white = kings_white
        self.kings_black = kings_black

    @staticmethod
    def initial():
        """Retorna o tabuleiro inicial padrão das Damas Brasileiras."""
        # 12 peças brancas nas casas escuras das 3 primeiras linhas
        white = 0b00000000000000000000111111111111
        # 12 peças pretas nas casas escuras das 3 últimas linhas
        black = 0b11111111111100000000000000000000
        return Board(white, black)

    @staticmethod
    def dark_square_index(row: int, col: int) -> int:
        """
        Converte (linha, coluna) para índice de casa escura (0-31).
        Retorna -1 se fora do tabuleiro ou não for casa escura.
        """
        # limites de 0 a 7
        if row < 0 or row >= 8 or col < 0 or col >= 8:
            return -1
        # só casas escuras
        if (row + col) % 2 == 0:
            return -1
        return (row * 4) + (col // 2)

    @staticmethod
    def index_to_coords(index: int) -> (int, int):
        """Converte índice de casa escura (0-31) para (linha, coluna) no tabuleiro 8x8."""
        row = index // 4
        col = (index % 4) * 2 + (1 if row % 2 == 0 else 0)
        return row, col

    def __str__(self):
        """Retorna uma string visual do tabuleiro para debug (apenas casas escuras)."""
        board = [['. ' for _ in range(8)] for _ in range(8)]
        for idx in range(32):
            row, col = self.index_to_coords(idx)
            if (self.bitboard_white >> idx) & 1:
                if (self.kings_white >> idx) & 1:
                    board[row][col] = 'W '
                else:
                    board[row][col] = 'w '
            elif (self.bitboard_black >> idx) & 1:
                if (self.kings_black >> idx) & 1:
                    board[row][col] = 'B '
                else:
                    board[row][col] = 'b '
        return '\n'.join(''.join(row) for row in board) 