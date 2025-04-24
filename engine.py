from typing import List, Tuple, Dict, Optional
from enum import Enum
from board import Board
from move import Move
import math

class Color(Enum):
    WHITE = 1
    BLACK = 2

# Pré-computação das tabelas de deslocamento
# simple_shifts[player][is_king][idx] -> List[int]
# capture_shifts[player][is_king][idx] -> List[Tuple[int destino, int meio]]
def _build_shift_tables() -> Tuple[
    Dict[Color, Dict[bool, Dict[int, List[int]]]],
    Dict[Color, Dict[bool, Dict[int, List[Tuple[int,int]]]]]
]:
    simple_shifts = {
        Color.WHITE: {False: {}, True: {}},
        Color.BLACK: {False: {}, True: {}}
    }
    capture_shifts = {
        Color.WHITE: {False: {}, True: {}},
        Color.BLACK: {False: {}, True: {}}
    }

    for idx in range(32):
        row, col = Board.index_to_coords(idx)
        for player in (Color.WHITE, Color.BLACK):
            for is_king in (False, True):
                simple_shifts[player][is_king][idx]  = []
                capture_shifts[player][is_king][idx] = []

        # quatro direções diagonais
        for dr, dc in [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]:
            nr, nc = row + dr, col + dc
            ni = Board.dark_square_index(nr, nc)
            jr, jc = row + 2*dr, col + 2*dc
            ji = Board.dark_square_index(jr, jc)

            for player in (Color.WHITE, Color.BLACK):
                # branco avança dr = +1; preto avança dr = -1
                forward_ok = (player == Color.WHITE and dr == +1) or \
                             (player == Color.BLACK and dr == -1)

                # movimentos simples: só "para frente" para homens; damas em todas
                if ni != -1:
                    if forward_ok:
                        simple_shifts[player][False][idx].append(ni)
                    simple_shifts[player][True][idx].append(ni)

                # capturas: homens e damas em todas as direções
                if ji != -1 and ni != -1:
                    capture_shifts[player][False][idx].append((ji, ni))
                    capture_shifts[player][True][idx].append((ji, ni))

    return simple_shifts, capture_shifts

_SIMPLE_SHIFTS, _CAPTURE_SHIFTS = _build_shift_tables()

def generate_moves(board: Board, player: Color) -> List[Move]:
    """
    Gera todos os movimentos válidos para o jogador atual,
    respeitando captura obrigatória, múltiplos saltos e movimentos "flyer" de damas.
    """
    our_bb    = board.bitboard_white if player == Color.WHITE else board.bitboard_black
    opp_bb    = board.bitboard_black if player == Color.WHITE else board.bitboard_white
    our_kings = board.kings_white     if player == Color.WHITE else board.kings_black

    all_captures: List[Move] = []
    all_simples:  List[Move] = []

    # Para cada peça nossa
    for idx in range(32):
        if not ((our_bb >> idx) & 1):
            continue
        is_king = bool((our_kings >> idx) & 1)
        row0, col0 = Board.index_to_coords(idx)

        # Função recursiva para capturas de homens
        def _search_man_captures(pos, used_mid, used_pos, captured, path):
            found = False
            occupancy = (our_bb | opp_bb) & ~used_mid
            for dest, mid in _CAPTURE_SHIFTS[player][False][pos]:
                if ((opp_bb >> mid) & 1) and not ((occupancy >> dest) & 1) and not (used_pos & (1 << dest)):
                    # não promovido ainda; promoção final interrompe
                    r_dest, _ = Board.index_to_coords(dest)
                    promote = (player == Color.WHITE and r_dest == 7) or \
                              (player == Color.BLACK and r_dest == 0)
                    if promote:
                        all_captures.append(Move(path + [dest], captured + [mid]))
                        continue
                    found = True
                    _search_man_captures(
                        dest,
                        used_mid | (1 << mid),
                        used_pos | (1 << dest),
                        captured + [mid],
                        path + [dest]
                    )
            if not found and captured:
                all_captures.append(Move(path, captured))

        # Função recursiva para capturas de damas (flyer captures)
        def _search_king_captures(pos, used_mid, used_pos, captured, path):
            found = False
            r0, c0 = Board.index_to_coords(pos)
            for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                # primeiro encontre o adversário na diagonal
                r, c = r0+dr, c0+dc
                while True:
                    mid = Board.dark_square_index(r, c)
                    if mid < 0: break
                    if ((opp_bb >> mid) & 1) and not (used_mid & (1<<mid)):
                        # a seguir, possíveis landing points
                        lr, lc = r+dr, c+dc
                        while True:
                            dest = Board.dark_square_index(lr, lc)
                            if dest < 0: break
                            if ((our_bb|opp_bb) & (1<<dest)) or (used_pos & (1<<dest)):
                                break
                            found = True
                            _search_king_captures(
                                dest,
                                used_mid | (1<<mid),
                                used_pos | (1<<dest),
                                captured + [mid],
                                path + [dest]
                            )
                            lr += dr; lc += dc
                        break
                    if ((our_bb|opp_bb) & (1<<mid)):
                        break
                    r += dr; c += dc
            if not found and captured:
                all_captures.append(Move(path, captured))

        # chama a busca de capturas apropriada
        if is_king:
            _search_king_captures(idx, 0, 1<<idx, [], [idx])
        else:
            _search_man_captures(idx, 0, 1<<idx, [], [idx])

        # movimentos simples (só se não houver capturas em todo tabuleiro)
        if not all_captures:
            if is_king:
                # flyer moves
                for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    r, c = row0+dr, col0+dc
                    while True:
                        dest = Board.dark_square_index(r, c)
                        if dest < 0 or ((our_bb|opp_bb) & (1<<dest)):
                            break
                        all_simples.append(Move([idx, dest]))
                        r += dr; c += dc
            else:
                # movimentos simples de homem
                for dest in _SIMPLE_SHIFTS[player][False][idx]:
                    if not (((our_bb|opp_bb) >> dest) & 1):
                        all_simples.append(Move([idx, dest]))

    # se há capturas, filtra só as de maior comprimento (obrigatório)
    if all_captures:
        max_cap = max(len(m.captured) for m in all_captures)
        return [m for m in all_captures if len(m.captured) == max_cap]
    return all_simples

def apply_move(board: Board, move: Move) -> Board:
    """
    Aplica um movimento (simples ou com captura) e retorna novo Board.
    Promoções de homens a damas são tratadas automaticamente.
    """
    w_bb, b_bb = board.bitboard_white, board.bitboard_black
    w_k, b_k   = board.kings_white, board.kings_black

    origin = move.path[0]
    is_white = ((w_bb >> origin) & 1) == 1

    # remove origem
    if is_white:
        w_bb &= ~(1 << origin)
        w_k  &= ~(1 << origin)
    else:
        b_bb &= ~(1 << origin)
        b_k  &= ~(1 << origin)

    # remove capturadas
    for mid in move.captured:
        if is_white:
            b_bb &= ~(1 << mid)
            b_k  &= ~(1 << mid)
        else:
            w_bb &= ~(1 << mid)
            w_k  &= ~(1 << mid)

    # coloca na casa destino
    dest = move.path[-1]
    if is_white:
        w_bb |= (1 << dest)
        # promoção: homens viram damas ao chegar na última linha (linha 7);
        # damas mantêm o status
        if dest // 4 == 7 or ((w_k >> origin) & 1):
            w_k |= (1 << dest)
    else:
        b_bb |= (1 << dest)
        # promoção: homens viram damas ao chegar na primeira linha (linha 0);
        # damas mantêm o status
        if dest // 4 == 0 or ((b_k >> origin) & 1):
            b_k |= (1 << dest)

    return Board(w_bb, b_bb, w_k, b_k)

def evaluate(board: Board) -> float:
    """
    Heurística simples: diferença de material
    (1 ponto por homem, 1.5 por dama).
    """
    white_men   = bin(board.bitboard_white & ~board.kings_white).count("1")
    white_kings = bin(board.kings_white).count("1")
    black_men   = bin(board.bitboard_black & ~board.kings_black).count("1")
    black_kings = bin(board.kings_black).count("1")

    return (white_men + 1.5*white_kings) - (black_men + 1.5*black_kings)

# ————————————————
# Transposition Table
# ————————————————
# Chave simples: tupla dos quatro bitboards
def _board_key(board: Board) -> Tuple[int,int,int,int]:
    return (
        board.bitboard_white,
        board.bitboard_black,
        board.kings_white,
        board.kings_black
    )

# ————————————————
# Alpha-Beta Poda
# ————————————————
def alpha_beta(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    player: Color,
    tt: dict
) -> Tuple[float, Optional[Move]]:
    """
    Retorna (valor, melhor_move) usando poda Alpha-Beta.
    Armazena resultados em 'tt' para reaproveitar posições.
    """
    # nó terminal
    if depth == 0:
        return evaluate(board), None

    key = (*_board_key(board), player)
    # veja se já temos essa posição em profundidade >= depth
    if key in tt:
        stored_depth, stored_val, stored_move = tt[key]
        if stored_depth >= depth:
            return stored_val, stored_move

    moves = generate_moves(board, player)
    if not moves:
        # Se não há movimentos, é posição terminal: vitória do adversário
        return (math.inf, None) if player == Color.BLACK else (-math.inf, None)

    best_move: Optional[Move] = None

    if player == Color.WHITE:
        value = -math.inf
        for mv in moves:
            vb, _ = alpha_beta(
                apply_move(board, mv),
                depth - 1,
                alpha,
                beta,
                Color.BLACK,
                tt
            )
            if vb > value:
                value, best_move = vb, mv
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:  # vez das pretas
        value = math.inf
        for mv in moves:
            vb, _ = alpha_beta(
                apply_move(board, mv),
                depth - 1,
                alpha,
                beta,
                Color.WHITE,
                tt
            )
            if vb < value:
                value, best_move = vb, mv
            beta = min(beta, value)
            if beta <= alpha:
                break

    # armazena na tabela de transposição
    tt[key] = (depth, value, best_move)
    return value, best_move

# ————————————————
# Iterative Deepening
# ————————————————
def suggest_move(
    board: Board,
    max_depth: int = 6,
    player: Color = Color.WHITE
) -> Optional[Move]:
    """
    Executa profundidades de 1 até max_depth e retorna o melhor Move encontrado
    para o jogador especificado (padrão: brancas).
    """
    tt = {}
    best: Optional[Move] = None
    for d in range(1, max_depth + 1):
        _, mv = alpha_beta(board, d, -math.inf, math.inf, player, tt)
        if mv is not None:
            best = mv
    return best
