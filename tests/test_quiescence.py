# test_quiescence.py
import engine
from board import Board
from engine import suggest_move, Color


def make_test_board() -> Board:
    """
    Posição de exemplo para captura múltipla de dama:
    Dama branca em 14; peças pretas em 18 e 22.
    """
    queen_idx = 14
    w_bb = 1 << queen_idx
    w_k  = 1 << queen_idx   # marca como king
    b_bb = (1 << 18) | (1 << 22)
    b_k  = 0
    return Board(w_bb, b_bb, w_k, b_k)


def make_quiet_board() -> Board:
    """
    Posição sem capturas possíveis.
    """
    w_bb = 1 << 10
    w_k  = 0
    b_bb = 0            # sem peças do adversário => não há capturas
    b_k  = 0
    return Board(w_bb, b_bb, w_k, b_k)


def run_test(use_quiescence: bool, board: Board, label: str = ""):
    """
    Executa suggest_move em board com/sem quiescence e imprime move e nodes.
    """
    # reinicia contador e configura quiescence
    engine.nodes = 0
    engine.USE_QUIESCENCE = use_quiescence
    move = suggest_move(board, max_depth=2, player=Color.WHITE)
    print(f"{label} USE_QUIESCENCE={use_quiescence!s:5}  move={move!s:25}  nodes={engine.nodes}")


if __name__ == "__main__":
    # Teste de captura múltipla
    test_board = make_test_board()
    print("=== TESTE CAPTURA MÚLTIPLA ===")
    run_test(False, test_board, "SEM QUIESCENCE:")
    run_test(True,  test_board, "COM QUIESCENCE:")

    # Teste de regressão (sem capturas)
    quiet_board = make_quiet_board()
    print("\n=== TESTE REGRESSÃO (sem capturas) ===")
    run_test(True, quiet_board, "REGRESSÃO:") 