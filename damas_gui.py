from board import Board
from engine import generate_moves, apply_move, suggest_move, Color
from move import Move

import tkinter as tk
from tkinter import messagebox

BOARD_SIZE = 8
SQUARE_SIZE = 60

# cores estilo "madeira" (claro / escuro)
LIGHT_SQUARE = "#f0d9b5"
DARK_SQUARE  = "#b58863"

# estilo das peças
WHITE_FILL    = "#fff"      # branco clássico
WHITE_OUTLINE = "#bbb"      # cinza claro
BLACK_FILL    = "#000"      # preto clássico
BLACK_OUTLINE = "#444"      # cinza escuro

class DamasGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Damas Brasileiras")
        self.canvas = tk.Canvas(master, width=BOARD_SIZE*SQUARE_SIZE, height=BOARD_SIZE*SQUARE_SIZE)
        self.canvas.pack()
        self.board = Board.initial()
        self.selected = None
        self.turn = Color.WHITE
        self.canvas.bind("<Button-1>", self.on_click)
        self.draw_board()
        self.status = tk.Label(master, text="Turno: Pretas")
        self.status.pack()
        self.ai_button = tk.Button(master, text="Sugestão IA", command=self.ai_move)
        self.ai_button.pack()

    def draw_board(self):
        self.canvas.delete("all")
        # desenha as casas (flip vertical + estilo madeira)
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x1, y1 = col*SQUARE_SIZE, row*SQUARE_SIZE
                x2, y2 = x1+SQUARE_SIZE, y1+SQUARE_SIZE
                # casa escura quando (row+col)%2==1, garantindo canto duplo à direita
                color = "#555" if (row+col)%2==1 else "#EEE"
                self.canvas.create_rectangle(x1, y1, x2, y2,
                                             fill=color, outline=color)
        # desenha as peças (flip vertical + cores madeira/vermelho)
        radius = SQUARE_SIZE//2 - 8
        for idx in range(32):
            r, c = Board.index_to_coords(idx)
            x = c*SQUARE_SIZE + SQUARE_SIZE//2
            y = r*SQUARE_SIZE + SQUARE_SIZE//2
            if (self.board.bitboard_white >> idx) & 1:
                # peça "branca" → desenhada em vermelho
                fill, outline = WHITE_FILL, WHITE_OUTLINE
                self.canvas.create_oval( x-radius, y-radius, x+radius, y+radius,
                                        fill=fill, outline=outline, width=4)
                if (self.board.kings_white >> idx) & 1:
                    # coroa simples
                    self.canvas.create_text(x, y, text="♛", font=("Arial", 24), fill=outline)
            elif (self.board.bitboard_black >> idx) & 1:
                # peça "preta" → desenhada em marrom escuro
                fill, outline = BLACK_FILL, BLACK_OUTLINE
                self.canvas.create_oval( x-radius, y-radius, x+radius, y+radius,
                                        fill=fill, outline=outline, width=4)
                if (self.board.kings_black >> idx) & 1:
                    self.canvas.create_text(x, y, text="♛", font=("Arial", 24), fill=outline)

        # destaque da seleção (flip vertical)
        if self.selected is not None:
            r, c = Board.index_to_coords(self.selected)
            x1, y1 = c*SQUARE_SIZE, r*SQUARE_SIZE
            x2, y2 = x1+SQUARE_SIZE, y1+SQUARE_SIZE
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                         outline="yellow", width=3)

    def highlight_move(self, move: Move):
        """Destaca graficamente origem e destino de uma sugestão."""
        # redesenha sem seleção
        self.selected = None
        self.draw_board()
        start, end = move.path[0], move.path[-1]
        for idx in (start, end):
            r, c = Board.index_to_coords(idx)
            x1, y1 = c*SQUARE_SIZE, r*SQUARE_SIZE
            x2, y2 = x1+SQUARE_SIZE, y1+SQUARE_SIZE
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                         outline="red", width=3)

    def on_click(self, event):
        # mapeia clique diretamente
        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE
        idx = Board.dark_square_index(row, col)
        if idx < 0:
            return
        if self.selected is None:
            # seleciona peça do jogador atual (brancas)
            bb = self.board.bitboard_white
            if (bb >> idx) & 1:
                self.selected = idx
                self.draw_board()
        else:
            # tenta mover
            moves = generate_moves(self.board, self.turn)
            for m in moves:
                if m.path[0] == self.selected and m.path[-1] == idx:
                    # executa movimentação do humano
                    self.board = apply_move(self.board, m)
                    self.selected = None
                    # passa a vez para a IA (pretas)
                    self.turn = Color.BLACK
                    self.draw_board()
                    self.status.config(text="Turno: Pretas")
                    # IA recalcula e sugere movimento automaticamente
                    self.ai_move()
                    return
            # clique inválido, desmarca
            self.selected = None
            self.draw_board()

    def ai_move(self):
        # Sugere jogada para as pretas (Color.BLACK)
        suggestion = suggest_move(self.board, max_depth=6, player=Color.BLACK)
        if suggestion:
            self.highlight_move(suggestion)
            start, end = suggestion.path[0], suggestion.path[-1]
            msg = f"IA sugere mover de {start} para {end}."
            if messagebox.askyesno("Movimento da IA", msg+"\nExecutar?"):
                self.board = apply_move(self.board, suggestion)
                self.draw_board()
        # volta a vez para o jogador (brancas)
        self.turn = Color.WHITE
        self.status.config(text="Turno: Brancas")

if __name__ == "__main__":
    root = tk.Tk()
    gui = DamasGUI(root)
    root.mainloop()
