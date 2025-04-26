from typing import List, Tuple, Dict, Optional
from enum import Enum
from board import Board
from move import Move
import math
import logging

# --- PARÂMETROS DE TUNING ---
PST_WEIGHT           = 0.02
BORDER_PST_FACTOR    = 0.5
MOBILITY_WEIGHT      = 0.1
FUTILITY_DEPTH       = 0
FUTILITY_MARGIN      = 0.01
ENDGAME_PIECE_LIMIT  = 8
ENDGAME_MULTIPLIER   = 1.0
HISTORY_CUTOFF_BONUS = lambda d: d*d
# ----------------------------

# profundidade máxima de busca padrão
MAX_SEARCH_DEPTH = 10

# contador de nós de busca
nodes = 0

# flag para ligar/desligar quiescence
USE_QUIESCENCE = True

# valores para MVV-LVA
PIECE_VALUES = {
    'man': 100,
    'king': 150
}

# valores em "centavos" (ou unidades) para cada casa 0–31
PSQT_MAN = [
    0,  0,  0,  0,   0,  5,  5,  0,
    0, 10, 15, 10,  10, 15, 10,  0,
    0, 15, 20, 15,  15, 20, 15,  0,
    0, 10, 15, 10,  10, 15, 10,  0
]

PSQT_KING = [
    0,  0,  0,  0,   0,  2,  2,  0,
    0,  5, 10,  5,   5, 10,  5,  0,
    0, 10, 15, 10,  10, 15, 10,  0,
    0,  5, 10,  5,   5, 10,  5,  0
]

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
    Promoções de homens a damas são tratadas automaticamente, preservando damas.
    """
    w_bb, b_bb = board.bitboard_white, board.bitboard_black
    w_k,  b_k  = board.kings_white, board.kings_black

    origin = move.path[0]
    is_white = ((w_bb >> origin) & 1) == 1

    # grava se era dama antes de limpar
    if is_white:
        was_king = ((w_k >> origin) & 1) == 1
    else:
        was_king = ((b_k >> origin) & 1) == 1

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
        # preserva dama se já era, ou promove ao chegar na última linha
        if was_king or dest // 4 == 7:
            w_k |= (1 << dest)
    else:
        b_bb |= (1 << dest)
        # preserva dama se já era, ou promove ao chegar na primeira linha
        if was_king or dest // 4 == 0:
            b_k |= (1 << dest)

    return Board(w_bb, b_bb, w_k, b_k)

def evaluate_material_only(board: Board) -> float:
    # material: 1.0 por man, 1.5 por king
    wm = bin(board.bitboard_white & ~board.kings_white).count("1")
    wk = bin(board.kings_white).count("1")
    bm = bin(board.bitboard_black & ~board.kings_black).count("1")
    bk = bin(board.kings_black).count("1")
    return (wm + 1.5*wk) - (bm + 1.5*bk)

def evaluate(board: Board) -> float:
    """
    Heurística simples: diferença de material
    (1 ponto por homem, 1.5 por dama).
    """
    white_men   = bin(board.bitboard_white & ~board.kings_white).count("1")
    white_kings = bin(board.kings_white).count("1")
    black_men   = bin(board.bitboard_black & ~board.kings_black).count("1")
    black_kings = bin(board.kings_black).count("1")

    # base de material
    score = (white_men + 1.5*white_kings) - (black_men + 1.5*black_kings)
    # PST com peso maior e penalidade em bordas
    for idx in range(32):
        row, col = Board.index_to_coords(idx)
        border = row in (0, 7) or col in (0, 7)
        bit = 1 << idx
        if board.bitboard_white & bit:
            pst_val = PSQT_KING[idx] if (board.kings_white & bit) else PSQT_MAN[idx]
            weight = PST_WEIGHT * (BORDER_PST_FACTOR if border else 1.0)
            bonus = pst_val * weight
            score += bonus
        if board.bitboard_black & bit:
            pst_val = PSQT_KING[idx] if (board.kings_black & bit) else PSQT_MAN[idx]
            weight = PST_WEIGHT * (BORDER_PST_FACTOR if border else 1.0)
            bonus = pst_val * weight
            score -= bonus
    # bonificação de mobilidade com peso moderado
    white_moves = len(generate_moves(board, Color.WHITE))
    black_moves = len(generate_moves(board, Color.BLACK))
    score += (white_moves - black_moves) * MOBILITY_WEIGHT
    # Endgame material bonus: amplifica diferença de material se poucas peças restarem
    total_pieces = white_men + white_kings + black_men + black_kings
    if total_pieces < ENDGAME_PIECE_LIMIT:
        score *= ENDGAME_MULTIPLIER
    return score

def mvv_lva_score(move: Move, board: Board, player: Color) -> int:
    """
    Retorna um escore para ordenar capturas:
    valor_da_vitima menos valor_do_atacante.
    """
    if not move.is_capture():
        return 0
    # a vítima mais valiosa
    victim_idxs = move.captured
    opp_kings = board.kings_black if player == Color.WHITE else board.kings_white
    max_victim_value = max(
        PIECE_VALUES['king'] if (opp_kings >> mid) & 1 else PIECE_VALUES['man']
        for mid in victim_idxs
    )
    # atacante
    origin = move.path[0]
    our_kings = board.kings_white if player == Color.WHITE else board.kings_black
    attacker_value = PIECE_VALUES['king'] if (our_kings >> origin) & 1 else PIECE_VALUES['man']
    return max_victim_value - attacker_value

# avalia do ponto de vista do jogador atual
def eval_side(board: Board, player: Color) -> float:
    base = evaluate(board)
    return base if player == Color.WHITE else -base

# Adiciona busca quiescente no estilo Negamax
def quiesce_negamax(board: Board, alpha: float, beta: float, player: Color) -> float:
    """
    Quiescence search: estende a busca em posições com capturas pendentes usando Negamax.
    """
    global nodes, QT
    nodes += 1
    # Caching exato de posições sem capturas (leaf quiescence)
    key_q = (*_board_key(board), player, 'q')
    if key_q in QT:
        d_stored, val_stored, bound_stored, _ = QT[key_q]
        if bound_stored == BoundType.EXACT:
            return val_stored
    # 1) Avaliação estática da posição "quieta" para o jogador
    stand_pat = eval_side(board, player)

    # 2) Corte de stand-pat
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    # 3) Gerar apenas movimentos de captura
    captures = [m for m in generate_moves(board, player) if m.is_capture()]
    # leaf quiescence: sem capturas -> armazena e retorna exact
    if not captures:
        QT[key_q] = (0, stand_pat, BoundType.EXACT, None)
        return stand_pat

    # 4) Explorar cada captura em modo negamax
    for m in captures:
        next_board = apply_move(board, m)
        opponent = Color.WHITE if player == Color.BLACK else Color.BLACK
        score = -quiesce_negamax(next_board, -beta, -alpha, opponent)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha

# Transposition Table e tipos de bound para Negamax
class BoundType(Enum):
    EXACT = 1
    LOWER = 2
    UPPER = 3

# tabela global de transposição: key->(depth, value, bound, best_move)
TT: Dict[Tuple[int,int,int,int,Color], Tuple[int, float, BoundType, Optional[Move]]] = {}
QT: Dict[Tuple[int,int,int,int,Color,str], Tuple[int, float, BoundType, Optional[Move]]] = {}  # Quiescence Transposition Table
# history heuristic: map (origem, destino) to score
HISTORY: Dict[Tuple[int,int], int] = {}

def _board_key(board: Board) -> Tuple[int,int,int,int]:
    return (
        board.bitboard_white,
        board.bitboard_black,
        board.kings_white,
        board.kings_black
    )

def negamax(board: Board, depth: int, alpha: float, beta: float, player: Color) -> Tuple[float, Optional[Move]]:
    """Retorna (valor, melhor_move) usando Negamax + Poda Alpha-Beta."""
    global nodes, TT
    nodes += 1
    # guardo α e β originais antes de qualquer modificação em α
    alpha_orig, beta_orig = alpha, beta
    # Transposition Table lookup
    key = (*_board_key(board), player)
    if key in TT:
        d_stored, val_stored, bound_stored, mv_stored = TT[key]
        if d_stored >= depth:
            if bound_stored == BoundType.EXACT:
                return val_stored, mv_stored
            elif bound_stored == BoundType.LOWER:
                alpha = max(alpha, val_stored)
            else:
                beta = min(beta, val_stored)
            if alpha >= beta:
                return val_stored, mv_stored

    # nó terminal com quiescence apenas se houver capturas
    if depth == 0:
        if USE_QUIESCENCE and any(m.is_capture() for m in generate_moves(board, player)):
            val = quiesce_negamax(board, alpha, beta, player)
        else:
            val = eval_side(board, player)
        return val, None

    # gera e ordena movimentos (MVV-LVA)
    moves = generate_moves(board, player)
    # SEE DEBUG (temporariamente desativado): imprimindo quando haveria forced capture
    filtered_moves: List[Move] = []
    opponent = Color.BLACK if player == Color.WHITE else Color.WHITE
    for mv in moves:
        if mv.is_capture():
            filtered_moves.append(mv)
        else:
            b2 = apply_move(board, mv)
            # verifica se haveria captura forçada em mv.path[-1]
            forced = any(
                opp_mv.is_capture() and mv.path[-1] in opp_mv.captured
                for opp_mv in generate_moves(b2, opponent)
            )
            if forced:
                logging.debug("move %s static_child=%.2f, forced_capture=%s", mv, evaluate(b2), forced)
            # mantém todos os movimentos (não descarto mais)
            filtered_moves.append(mv)
    moves = filtered_moves
    # ordena movimentos: captures primeiro (padrão MVV-LVA), depois history heuristic, depois PSQT
    moves.sort(
        key=lambda mv: (
            1 if mv.is_capture() else 0,
            mvv_lva_score(mv, board, player),
            HISTORY.get((mv.path[0], mv.path[-1]), 0),
            0 if mv.is_capture() else PSQT_MAN[mv.path[-1]]
        ),
        reverse=True
    )

    best_val = -math.inf
    best_move: Optional[Move] = None
    # futility pruning: descarta moves simples em profundidade rasa usando alpha original para evitar não-determinismo
    for mv in moves:
        next_board = apply_move(board, mv)
        if depth <= FUTILITY_DEPTH and not mv.is_capture():
            static_val = evaluate(next_board)
            if static_val <= alpha_orig - FUTILITY_MARGIN:
                continue
        val, _ = negamax(next_board, depth - 1, -beta, -alpha, opponent)
        val = -val
        if val > best_val:
            best_val, best_move = val, mv
        alpha = max(alpha, val)
        if alpha >= beta:
            # history heuristic: penaliza movimentos não-capture que causam cutoff (ranking positivo)
            if not mv.is_capture():
                key_move = (mv.path[0], mv.path[-1])
                HISTORY[key_move] = HISTORY.get(key_move, 0) + depth * depth
            break

    # Armazena resultado na Transposition Table
    if best_val <= alpha_orig:
        bound_type = BoundType.UPPER
    elif best_val >= beta_orig:
        bound_type = BoundType.LOWER
    else:
        bound_type = BoundType.EXACT
    TT[key] = (depth, best_val, bound_type, best_move)
    # history heuristic: reforça movimento que foi efetivamente escolhido
    if best_move is not None and not best_move.is_capture():
        key_best = (best_move.path[0], best_move.path[-1])
        HISTORY[key_best] = HISTORY.get(key_best, 0) + depth * depth
    return best_val, best_move

def suggest_move(board: Board, max_depth: int = MAX_SEARCH_DEPTH, player: Color = Color.WHITE, debug: bool = False) -> Optional[Move]:
    """Se debug=True, imprime para cada profundidade quantos nós foram buscados e o melhor movimento."""
    best_move: Optional[Move] = None
    for d in range(1, max_depth + 1):
        if debug:
            start_nodes = nodes
        value, mv = negamax(board, d, -math.inf, math.inf, player)
        if debug:
            nodes_searched = nodes - start_nodes
            print(f"[DEBUG] Depth={d}: nodes={nodes_searched}, best_move={mv}, value={value:.2f}")
        if mv is not None:
            best_move = mv
    return best_move

# configuração de logging para debug de movimentos
logging.basicConfig(
    level=logging.INFO,  # DEBUG para logs mais verbosos
    format="%(asctime)s [%(levelname)s] %(message)s",
)
