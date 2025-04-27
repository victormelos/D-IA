from board import Board
from engine import generate_moves, apply_move, evaluate, suggest_move, Color

def main():
    # Posicao inicial (pode mudar para qualquer board de teste)
    board = Board.initial()
    player = Color.WHITE
    opponent = Color.BLACK

    print('>>> Minimax puro (profundidade=2) – avaliando cada par de lances:\n')
    # Gera e avalia cada par de lances
    for mv1 in generate_moves(board, player):
        b1 = apply_move(board, mv1)
        for mv2 in generate_moves(b1, opponent):
            b2 = apply_move(b1, mv2)
            val = evaluate(b2)
            print(f"{mv1} -> {mv2}: evaluate = {val:.2f}")

    # Obtém melhor lance via suggest_move (usando negamax sem poda)
    best_move = suggest_move(board, max_depth=2, player=player)
    print(f"\nLance sugerido pelo minimax puro (profundidade=2): {best_move}")

if __name__ == '__main__':
    main() 