import tkinter as tk
from tkinter import messagebox
from board import Board
from engine import generate_moves, apply_move, suggest_move, Color

SQUARE_SIZE = 80
BOARD_SIZE = 8
PIECE_RADIUS = SQUARE_SIZE // 2 - 8

class DamasGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Damas Brasileiras - Jogue contra a IA")
        self.canvas = tk.Canvas(master,
                                width=SQUARE_SIZE*BOARD_SIZE,
                                height=SQUARE_SIZE*BOARD_SIZE)
        self.canvas.pack()

        # Estado do jogo
        self.board = Board.initial()
        self.turn = Color.BLACK   # humano (pretas) joga primeiro
        self.selected = None      # casa selecionada para mover

        self.canvas.bind("<Button-1>", self.on_click)
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        # desenha as casas
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x1, y1 = col*SQUARE_SIZE, row*SQUARE_SIZE
                x2, y2 = x1+SQUARE_SIZE, y1+SQUARE_SIZE
                color = "#EEE" if (row+col)%2==0 else "#555"
                self.canvas.create_rectangle(x1, y1, x2, y2,
                                             fill=color, outline="black")

        # desenha as peças
        for idx in range(32):
            r, c = Board.index_to_coords(idx)
            x = c*SQUARE_SIZE + SQUARE_SIZE//2
            y = r*SQUARE_SIZE + SQUARE_SIZE//2
            if (self.board.bitboard_white >> idx) & 1:
                self.draw_piece(x, y, "white",
                                bool((self.board.kings_white >> idx) & 1))
            elif (self.board.bitboard_black >> idx) & 1:
                self.draw_piece(x, y, "black",
                                bool((self.board.kings_black >> idx) & 1))

        # destaque da seleção
        if self.selected is not None:
            r, c = Board.index_to_coords(self.selected)
            x1, y1 = c*SQUARE_SIZE, r*SQUARE_SIZE
            x2, y2 = x1+SQUARE_SIZE, y1+SQUARE_SIZE
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                         outline="yellow", width=3)

    def draw_piece(self, x, y, color, is_king):
        r = PIECE_RADIUS
        self.canvas.create_oval(x-r, y-r, x+r, y+r,
                                fill=color, outline="black")
        if is_king:
            self.canvas.create_text(x, y, text="♛",
                                    fill="gold", font=(None,24))

    def on_click(self, event):
        # somente casas escuras
        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE
        idx = Board.dark_square_index(row, col)
        if idx < 0:
            return

        # turno do humano?
        if self.turn != Color.BLACK:
            return

        human_moves = generate_moves(self.board, Color.BLACK)
        if not human_moves:
            messagebox.showinfo("Fim de Jogo",
                                "Você não tem movimentos. A IA venceu!")
            return

        # selecionar ou mover
        if self.selected is None:
            # só permite selecionar peça preta
            if (self.board.bitboard_black >> idx) & 1:
                self.selected = idx
                self.draw_board()
        else:
            # tenta achar movimento correspondente
            chosen = None
            for m in human_moves:
                if m.path[0] == self.selected and m.path[-1] == idx:
                    chosen = m
                    break
            if chosen:
                # aplica o movimento do humano
                self.board = apply_move(self.board, chosen)
                self.selected = None
                self.draw_board()
                # passa a vez para a IA
                self.turn = Color.WHITE
                self.master.after(200, self.ai_move)
            else:
                # movimento inválido: cancela seleção
                self.selected = None
                self.draw_board()

    def ai_move(self):
        # turno da IA
        ai_moves = generate_moves(self.board, Color.WHITE)
        if not ai_moves:
            messagebox.showinfo("Fim de Jogo",
                                "IA não possui movimentos. Você venceu!")
            self.turn = Color.BLACK
            return

        suggestion = suggest_move(self.board, max_depth=6)
        if suggestion:
            start, end = suggestion.path[0], suggestion.path[-1]
            msg = f"IA sugere mover de {start} para {end}."
            if messagebox.askyesno("Movimento da IA", msg+"\nExecutar?"):
                self.board = apply_move(self.board, suggestion)
                self.draw_board()
        else:
            messagebox.showinfo("Fim de Jogo",
                                "IA não encontrou movimentos. Você venceu!")

        # volta a vez para o humano
        self.turn = Color.BLACK

if __name__ == '__main__':
    root = tk.Tk()
    gui = DamasGUI(root)
    root.mainloop()
