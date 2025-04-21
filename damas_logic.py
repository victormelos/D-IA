# -*- coding: utf-8 -*-
# damas_logic.py (v12.3: Iterative Deepening + Time Management)

import time
import random
from typing import List, Tuple, Optional, Dict, Set, NamedTuple
from collections import defaultdict
from collections import OrderedDict
import statistics
import math
import logging
import cProfile, pstats
from functools import lru_cache

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.WARNING
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)    # Configurando para INFO por padrão (era DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
if not logger.hasHandlers():
    logger.addHandler(ch)

# --- Constantes ---
BRANCO = 1; PRETO = -1; VAZIO = 0; PEDRA = 1; DAMA = 2; PB = 1; PP = -1; DB = 2; DP = -2
DIRECOES_PEDRA = {BRANCO: [(-1, -1), (-1, 1)], PRETO: [(1, -1), (1, 1)]}
DIRECOES_CAPTURA_PEDRA = [(-1,-1),(-1,1),(1,-1),(1,1)] # Mantido para referência
DIRECOES_DAMA = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
TAMANHO_TABULEIRO = 8
PROFUNDIDADE_IA = 7 # Profundidade máxima (aumentada para facilitar TT hits)
TEMPO_PADRAO_IA = 60.0 # Tempo padrão em segundos (ajustado para dar folga no teste)

# Definição de exceção para tempo excedido
class TempoExcedidoError(Exception):
    """Exceção levantada quando o tempo de busca é excedido."""
    pass

# Parâmetros básicos (Constantes Globais)
VALOR_PEDRA = 12.0              # suaviza swing do PSQT
VALOR_DAMA  = 36.0              # mantém proporção de 1:3
BONUS_AVANCO_PEDRA = 0.08       # menos peso no avanço
PENALIDADE_PEDRA_ATRASADA = -0.2
BONUS_CONTROLE_CENTRO_PEDRA = 0.2
BONUS_CONTROLE_CENTRO_DAMA = 0.5
BONUS_SEGURANCA_ULTIMA_LINHA = 0.1
BONUS_MOBILIDADE_DAMA = 0.2
BONUS_PRESTES_PROMOVER = 0.5
BONUS_PECA_NA_BORDA = -0.1
BONUS_PECA_PROTEGIDA = 0.5
PENALIDADE_PECA_VULNERAVEL = -0.25  # vulnerabilidade não deve punir tanto
PENALIDADE_PECA_AMEACADA_2L = -0.5
BONUS_PAR_PEDRAS_CONECTADAS = 0.2
BONUS_MOBILIDADE_FUTURA = 0.15  # metade do que era
BONUS_BLOQUEIO_AVANCO = 0.2
BONUS_FORMACAO_PONTE = 0.3
BONUS_FORMACAO_LANCA = 0.2
BONUS_FORMACAO_PAREDE = 0.5
PENALIDADE_CAPTURA_IMEDIATA = -15.0  # <-- aqui, junto das outras

# Tabelas Piece-Square (PSQT)
PSQT_PEDRA = [
    [ 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00],
    [ 0.00,  0.05,  0.05,  0.05,  0.05,  0.05,  0.05,  0.00],
    [ 0.00,  0.05,  0.10,  0.10,  0.10,  0.10,  0.05,  0.00],
    [ 0.00,  0.05,  0.10,  0.15,  0.15,  0.10,  0.05,  0.00],
    [ 0.00,  0.05,  0.10,  0.15,  0.15,  0.10,  0.05,  0.00],
    [ 0.00,  0.05,  0.10,  0.10,  0.10,  0.10,  0.05,  0.00],
    [ 0.00,  0.05,  0.05,  0.05,  0.05,  0.05,  0.05,  0.00],
    [ 0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00],
]

PSQT_DAMA = [
    [ 0.00,  0.05,  0.05,  0.05,  0.05,  0.05,  0.05,  0.00],
    [ 0.05,  0.10,  0.10,  0.10,  0.10,  0.10,  0.10,  0.05],
    [ 0.05,  0.10,  0.15,  0.15,  0.15,  0.15,  0.10,  0.05],
    [ 0.05,  0.10,  0.15,  0.20,  0.20,  0.15,  0.10,  0.05],
    [ 0.05,  0.10,  0.15,  0.20,  0.20,  0.15,  0.10,  0.05],
    [ 0.05,  0.10,  0.15,  0.15,  0.15,  0.15,  0.10,  0.05],
    [ 0.05,  0.10,  0.10,  0.10,  0.10,  0.10,  0.10,  0.05],
    [ 0.00,  0.05,  0.05,  0.05,  0.05,  0.05,  0.05,  0.00],
]

# Regra: Uma dama recém-promovida não pode se mover imediatamente, deve esperar o próximo turno do jogador
# (após o adversário jogar). Esta regra é implementada utilizando o conjunto damas_recem_promovidas no tabuleiro.

# Parâmetros de Otimização
MAX_QUIESCENCE_DEPTH = 5 # Reduzido para enxugar a busca de quiescência
TT_TAMANHO_MB = 128; TT_ENTRIES = (TT_TAMANHO_MB * 1024 * 1024) // 32
TT_FLAG_EXACT = 0; TT_FLAG_LOWERBOUND = 1; TT_FLAG_UPPERBOUND = 2

# Adicione no início do arquivo, junto das outras constantes globais:
MAX_PROFUNDIDADE_TOTAL = 64  # Limite absoluto para evitar RecursionError

# --- Tipos e Estruturas Auxiliares ---
Posicao = Tuple[int, int]; Movimento = List[Posicao]
class EstadoLanceDesfazer(NamedTuple):
    movimento: Movimento
    peca_movida_original: int
    pecas_capturadas: Dict[Posicao, int]
    foi_promovido: bool
    hash_anterior: int
    damas_recem_promovidas_adicionadas: Set[Posicao] = set()  # Damas adicionadas neste movimento
    troca_turno: bool = True  # NOVO: indica se houve troca de turno
class TTEntry(NamedTuple):
    profundidade: int; score: float; flag: int; melhor_movimento: Optional[Movimento] = None

# --- Zobrist Hashing ---
ZOBRIST_TABELA = [[[random.randint(1, 2**64 - 1) for _ in range(5)] for _ in range(TAMANHO_TABULEIRO)] for _ in range(TAMANHO_TABULEIRO)]
ZOBRIST_VEZ_PRETA = random.randint(1, 2**64 - 1)
Z_PROM = [[random.randint(1, 2**64 - 1) for _ in range(TAMANHO_TABULEIRO)] for _ in range(TAMANHO_TABULEIRO)]

# --- Constantes para Bitboards ---
# Shifts para as 4 direções diagonais (NE, NO, SE, SO)
BB_SHIFT_NE = -7  # Nordeste (para cima e direita)
BB_SHIFT_NW = -9  # Noroeste (para cima e esquerda)
BB_SHIFT_SE = 9   # Sudeste (para baixo e direita)
BB_SHIFT_SW = 7   # Sudoeste (para baixo e esquerda)

# Máscara para as casas escuras onde ocorre o jogo (r+c)%2==1
DARK_SQUARES = 0x55AA55AA55AA55AA

# Shifts para as direções de cada cor
BB_SHIFTS_WHITE = [BB_SHIFT_NE, BB_SHIFT_NW]       # para cima/norte (brancas)
BB_SHIFTS_BLACK = [BB_SHIFT_SE, BB_SHIFT_SW]       # para baixo/sul (pretas)
BB_SHIFTS_ALL = [BB_SHIFT_NE, BB_SHIFT_NW, BB_SHIFT_SE, BB_SHIFT_SW]

# Constantes para movimentos especiais em debug e testes
BIT_K = 0x01  # Constante para representar um movimento de Rei (King)
BIT_R = 0x02  # Constante para representar um movimento de Torre (Rook)
BIT_G = 0x04  # Constante para representar um movimento genérico/especial (Generic)

# Máscaras para evitar wrap-around nas bordas
BB_NOT_A_FILE = ~0x0101010101010101  # Não está na coluna A (0)
BB_NOT_H_FILE = ~0x8080808080808080  # Não está na coluna H (7)

# Máscaras para as colunas (positivas)
MASK_FILE_A = 0x0101010101010101  # Coluna A (0)
MASK_FILE_H = 0x8080808080808080  # Coluna H (7)

# Fileiras de promoção
BB_RANK_1 = 0x00000000000000FF  # Primeira fileira (para brancas)
BB_RANK_8 = 0xFF00000000000000  # Última fileira (para pretas)

# --- Classe Peca ---
class Peca:
    def __init__(self, c: int, t: int=PEDRA): self.cor=c; self.tipo=t
    def __repr__(self)->str: cs="B" if self.cor==BRANCO else "P"; ts="P" if self.tipo==PEDRA else "D"; return f"{cs}{ts}"
    @staticmethod
    def get_cor(v: int)->int: return VAZIO if v==VAZIO else (BRANCO if v>0 else PRETO)
    @staticmethod
    def get_tipo(v: int)->int: return VAZIO if v==VAZIO else (DAMA if abs(v)==DAMA else PEDRA)
    @staticmethod
    def get_char(v: int)->str: return {PB:'b',PP:'p',DB:'B',DP:'P'}.get(v,'.')
    @staticmethod
    def get_zobrist_indice(v: int)->int: return {PB:1,PP:2,DB:3,DP:4}.get(v,0)

# --- Classe Tabuleiro ---
class Tabuleiro:
    def __init__(self, estado_inicial: bool = True) -> None:
        # Inicializa os bitboards (representações de 64 bits do tabuleiro)
        self.bitboard_brancas = 0
        self.bitboard_pretas = 0
        self.bitboard_damas_brancas = 0
        self.bitboard_damas_pretas = 0
        
        # Inicializa o grid tradicional (para compatibilidade)
        self.grid = [[0]*8 for _ in range(8)]
        
        # Constantes para máscaras de colunas (usadas para prevenir wraparound)
        self.BB_COL_A = 0x0101010101010101
        self.BB_COL_H = 0x8080808080808080
        self.BB_NOT_COL_A = 0xFEFEFEFEFEFEFEFE
        self.BB_NOT_COL_H = 0x7F7F7F7F7F7F7F7F
        
        # Aliases para compatibilidade com nomenclatura padrão de chess engines
        self.BB_A_FILE = self.BB_COL_A  # Máscara para coluna A (0x0101010101010101)
        self.BB_H_FILE = self.BB_COL_H  # Máscara para coluna H (0x8080808080808080)
        self.BB_NOT_A_FILE = self.BB_NOT_COL_A  # Máscara para todas as colunas exceto A
        self.BB_NOT_H_FILE = self.BB_NOT_COL_H  # Máscara para todas as colunas exceto H
        
        # Inicializa atributos de controle
        self.damas_recem_promovidas = set()
        self.max_depth_reached = 0
        
        # Inicializa caches
        self._cache_capturas = {}
        self._moves_cache = {}
        self._eval_cache = {}
        
        # Preenche o tabuleiro com a configuração inicial, se solicitado
        if estado_inicial:
            self._inicializar_tabuleiro()
            self.hash_atual = self.calcular_hash_zobrist_inicial()
        else:
            self.hash_atual = 0
        
        # Outras inicializações
        self.movimentos_cache = {}
        self.capturas_cache = {}
        
    def print_bitboards_hex(self) -> None:
        """Imprime todos os bitboards no formato hexadecimal."""
        logger.info(f"White Men:   0x{self.bitboard_brancas:016X}")
        logger.info(f"White Kings: 0x{self.bitboard_damas_brancas:016X}")
        logger.info(f"Black Men:   0x{self.bitboard_pretas:016X}")
        logger.info(f"Black Kings: 0x{self.bitboard_damas_pretas:016X}")
        logger.info(f"All Pieces:  0x{self.get_all_pieces():016X}")
        logger.info(f"Empty Sqrs:  0x{self.get_empty_squares():016X}")

    def print_all_bitboards(self) -> None:
        """Imprime todos os bitboards em formato visual de tabuleiro."""
        def print_bitboard(bb, nome):
            logger.info(f"\n{nome}:")
            for linha in range(8):
                linha_str = ""
                for coluna in range(8):
                    bit_pos = 1 << (linha * 8 + coluna)
                    if bb & bit_pos:
                        linha_str += "X "
                    else:
                        linha_str += ". "
                logger.info(f"{7-linha} {linha_str}")
            logger.info("  0 1 2 3 4 5 6 7")
        print_bitboard(self.bitboard_brancas, "Peças Brancas")
        print_bitboard(self.bitboard_damas_brancas, "Damas Brancas")
        print_bitboard(self.bitboard_pretas, "Peças Pretas")
        print_bitboard(self.bitboard_damas_pretas, "Damas Pretas")
        print_bitboard(self.bitboard_brancas | self.bitboard_damas_brancas | self.bitboard_pretas | self.bitboard_damas_pretas, "Todas as Peças")
    
    def pos_to_bit(self, pos: Posicao) -> int:
        """Converte uma posição (linha, coluna) para sua representação em bit."""
        linha, coluna = pos
        return 1 << (linha * 8 + coluna)
        
    def bit_to_pos(self, bit: int) -> Optional[Posicao]:
        """Converte um bit para sua posição (linha, coluna)."""
        if bit == 0:
            return None
        # Encontra a posição do bit 1 (começando do LSB)
        bit_pos = 0
        while bit > 1:
            bit >>= 1
            bit_pos += 1
        return (bit_pos // 8, bit_pos % 8)
    
    def _bit_scan_forward(self, bb: int) -> int:
        """
        Retorna o índice do bit menos significativo setado em 1.
        Esta é uma versão otimizada para ser usada em operações com bitboards.
        
        Args:
            bb: O bitboard a ser analisado
            
        Returns:
            O índice (0-63) do bit menos significativo que está ligado,
            ou -1 se o bitboard for zero.
        """
        if bb == 0:
            return -1
        idx = 0
        while bb & 1 == 0:
            bb >>= 1
            idx += 1
        return idx
    
    def validar_movimentos_simples(self, cor: int) -> bool:
        """Compara os resultados de gera_movimentos_simples com o método legado."""
        movs_bit = self.gera_movimentos_simples(cor)
        movs_legados = []
        for mov in self.encontrar_movimentos_possiveis(cor, apenas_capturas=False):
            if len(mov) == 2 and not self.identificar_pecas_capturadas(mov):
                movs_legados.append((mov[0], mov[1]))
        set_bit = set(movs_bit)
        set_legados = set(movs_legados)
        diffs_a = set_bit - set_legados
        diffs_b = set_legados - set_bit
        if diffs_a or diffs_b:
            logger.info(f"Validação falhou para a cor {cor}.")
            if diffs_a:
                logger.info(f"Movimentos extras nos bitboards: {diffs_a}")
            if diffs_b:
                logger.info(f"Movimentos extras no legado: {diffs_b}")
        return set_bit == set_legados

    def imprimir_bitboard(self, bb: int, nome: str = "Bitboard") -> None:
        """Imprime um bitboard no formato visual de tabuleiro (usa logger)."""
        logger.info(f"{nome} (hex: {bb:016x}):")
        logger.info("  0 1 2 3 4 5 6 7")
        for r in range(8):
            linha = f"{r} "
            for c in range(8):
                idx = r * 8 + c
                bit = (bb >> idx) & 1
                linha += "# " if bit else ". "
            logger.info(linha)
        logger.info("")

    def _inicializar_tabuleiro(self) -> None:
        """Inicializa o tabuleiro com a configuração inicial de jogo."""
        # Inicializa o grid tradicional
        for i in range(8):
            for j in range(8):
                if (i + j) % 2 == 1:  # Casas pretas (jogáveis)
                    if i < 3:
                        self.grid[i][j] = PP  # Peças pretas nas linhas superiores
                    elif i > 4:
                        self.grid[i][j] = PB  # Peças brancas nas linhas inferiores
                    else:
                        self.grid[i][j] = 0   # Casas vazias
                else:
                    self.grid[i][j] = 0   # Casas brancas (não jogáveis)
        
        # Atualiza os bitboards baseado no grid
        for linha in range(8):
            for coluna in range(8):
                bit_pos = 1 << (linha * 8 + coluna)
                if self.grid[linha][coluna] == PB:
                    self.bitboard_brancas |= bit_pos
                elif self.grid[linha][coluna] == PP:
                    self.bitboard_pretas |= bit_pos
                elif self.grid[linha][coluna] == DB:
                    self.bitboard_brancas |= bit_pos
                    self.bitboard_damas_brancas |= bit_pos
                elif self.grid[linha][coluna] == DP:
                    self.bitboard_pretas |= bit_pos
                    self.bitboard_damas_pretas |= bit_pos
                   
    def get_pieces_by_color(self, cor: int) -> int:
        """Retorna um bitboard com todas as peças de uma determinada cor."""
        if cor == BRANCO:
            return self.bitboard_brancas | self.bitboard_damas_brancas
        else:
            return self.bitboard_pretas | self.bitboard_damas_pretas
            
    def get_all_pieces(self) -> int:
        """Retorna um bitboard com todas as peças no tabuleiro."""
        return self.bitboard_brancas | self.bitboard_damas_brancas | self.bitboard_pretas | self.bitboard_damas_pretas
        
    def get_empty_squares(self) -> int:
        """Retorna um bitboard com todas as casas vazias do tabuleiro."""
        all_pieces = self.get_all_pieces()
        # No tabuleiro de damas, só usamos as casas escuras (1 bit sim, 1 bit não)
        return ~all_pieces & DARK_SQUARES
        
    @staticmethod
    def lsb(bb: int) -> int:
        """Retorna o bit menos significativo ligado."""
        if bb == 0:
            return 0
        return bb & -bb

    @staticmethod
    def idx_lsb(bb: int) -> int:
        """Retorna o índice do bit menos significativo ligado (0-63), ou -1 se bb==0."""
        if bb == 0:
            return -1
        return (bb & -bb).bit_length() - 1

    def bits_to_positions(self, bb: int) -> List[Posicao]:
        """Converte um bitboard em uma lista de posições (r,c)."""
        positions = []
        while bb:
            lsb = self.lsb(bb)
            positions.append(self.bit_to_pos(lsb))
            bb = self.clear_lsb(bb)
        return positions

    def _clear_move_and_capture_cache(self) -> None:
        """Limpa apenas os caches relacionados a movimentos e capturas."""
        self.movimentos_cache.clear()
        self.capturas_cache.clear()
        
    def limpar_cache_capturas(self) -> None:
        """Método legado para compatibilidade, agora só limpa os caches de movimentos."""
        self._clear_move_and_capture_cache()

    def configuracao_inicial(self) -> None:
        # **Reinicia** os bitboards
        self.bitboard_brancas = 0
        self.bitboard_pretas = 0
        self.bitboard_damas_brancas = 0
        self.bitboard_damas_pretas = 0

        # Preenche só os men (pedras) nas posições iniciais
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 == 1:  # casas escuras
                    b = self.pos_to_bit((r, c))
                    if r < 3:
                        self.bitboard_pretas |= b  # Peças pretas nas linhas superiores
                    elif r > 4:
                        self.bitboard_brancas |= b  # Peças brancas nas linhas inferiores

        # Atualiza self.grid para manter o __repr__ funcionando
        for r in range(TAMANHO_TABULEIRO):
            for c in range(TAMANHO_TABULEIRO):
                bit = self.pos_to_bit((r, c))
                if self.bitboard_brancas & bit: 
                    self.grid[r][c] = PB
                elif self.bitboard_damas_brancas & bit: 
                    self.grid[r][c] = DB
                elif self.bitboard_pretas & bit: 
                    self.grid[r][c] = PP
                elif self.bitboard_damas_pretas & bit: 
                    self.grid[r][c] = DP
                else:
                    self.grid[r][c] = VAZIO

        # limpa caches ligados a movimentos/avaliação
        self._clear_move_and_capture_cache()
        self._eval_cache.clear()  # Aqui limpamos também o eval_cache porque é uma nova configuração inicial

    def calcular_hash_zobrist_inicial(self) -> int:
        h = 0
        
        # Processar peças brancas
        white_man = self.bitboard_brancas
        while white_man:
            lsb = self.lsb(white_man)
            r, c = self.bit_to_pos(lsb)
            h ^= ZOBRIST_TABELA[r][c][Peca.get_zobrist_indice(PB)]
            white_man = self.clear_lsb(white_man)
            
        # Processar damas brancas
        white_king = self.bitboard_damas_brancas
        while white_king:
            lsb = self.lsb(white_king)
            r, c = self.bit_to_pos(lsb)
            h ^= ZOBRIST_TABELA[r][c][Peca.get_zobrist_indice(DB)]
            white_king = self.clear_lsb(white_king)
            
        # Processar peças pretas
        black_man = self.bitboard_pretas
        while black_man:
            lsb = self.lsb(black_man)
            r, c = self.bit_to_pos(lsb)
            h ^= ZOBRIST_TABELA[r][c][Peca.get_zobrist_indice(PP)]
            black_man = self.clear_lsb(black_man)
            
        # Processar damas pretas
        black_king = self.bitboard_damas_pretas
        while black_king:
            lsb = self.lsb(black_king)
            r, c = self.bit_to_pos(lsb)
            h ^= ZOBRIST_TABELA[r][c][Peca.get_zobrist_indice(DP)]
            black_king = self.clear_lsb(black_king)
            
        return h

    def _atualizar_hash_zobrist(self, r: int, c: int, v: int) -> None:
        if self.is_valido(r,c): self.hash_atual ^= ZOBRIST_TABELA[r][c][Peca.get_zobrist_indice(v)]

    def _atualizar_hash_turno(self): self.hash_atual ^= ZOBRIST_VEZ_PRETA

    def __repr__(self) -> str:
        h="  "+" ".join(chr(ord('a')+i) for i in range(TAMANHO_TABULEIRO))+" "; l=[h];
        for r in range(TAMANHO_TABULEIRO): l.append(f"{TAMANHO_TABULEIRO-r:<2}"+"".join(Peca.get_char(self.grid[r][c])+" " for c in range(TAMANHO_TABULEIRO))+f"{TAMANHO_TABULEIRO-r:<2}");
        l.append(h); return "\n".join(l)
    def get_peca(self, p: Posicao)->int: 
        r, c = p
        if not self.is_valido(r, c):
            return VAZIO

        bit = self.pos_to_bit(p)
        if self.bitboard_brancas & bit:
            return PB
        elif self.bitboard_damas_brancas & bit:
            return DB
        elif self.bitboard_pretas & bit:
            return PP
        elif self.bitboard_damas_pretas & bit:
            return DP
        else:
            return VAZIO

    def set_peca(self, p: Posicao, v: int) -> None:
        r, c = p
        if not self.is_valido(r, c):
            return
        
        # Atualizar hash do Zobrist ao remover a peça antiga
        peca_antiga = self.get_peca(p)
        if peca_antiga != VAZIO:
            self._atualizar_hash_zobrist(r, c, peca_antiga)
        
        # Remover qualquer peça existente na posição
        bit = self.pos_to_bit(p)
        self.bitboard_brancas &= ~bit
        self.bitboard_damas_brancas &= ~bit
        self.bitboard_pretas &= ~bit
        self.bitboard_damas_pretas &= ~bit
        
        # Adicionar a nova peça
        if v == PB:
            self.bitboard_brancas |= bit
        elif v == DB:
            self.bitboard_damas_brancas |= bit
        elif v == PP:
            self.bitboard_pretas |= bit
        elif v == DP:
            self.bitboard_damas_pretas |= bit
        
        # Atualizar hash do Zobrist para a nova peça
        if v != VAZIO:
            self._atualizar_hash_zobrist(r, c, v)
        
        # Atualizar a grid para compatibilidade
        self.grid[r][c] = v
        
        # Limpar caches
        self._clear_move_and_capture_cache()

    def mover_peca(self, o: Posicao, d: Posicao):
        peca = self.get_peca(o)
        self.set_peca(o, VAZIO)
        self.set_peca(d, peca)
        self._clear_move_and_capture_cache()

    def remover_peca(self, p: Posicao):
        self.set_peca(p, VAZIO)
        self._clear_move_and_capture_cache()

    @staticmethod
    def is_valido(r: int, c: int) -> bool: return 0<=r<TAMANHO_TABULEIRO and 0<=c<TAMANHO_TABULEIRO
    @staticmethod
    def get_oponente(cor: int) -> int: return PRETO if cor==BRANCO else BRANCO
    
    def get_posicoes_pecas(self, cor: int) -> List[Posicao]:
        """Retorna todas as posições das peças de uma determinada cor."""
        bb = self.get_pieces_by_color(cor)
        return self.bits_to_positions(bb)

    @staticmethod
    @lru_cache(maxsize=50000)
    def _encontrar_capturas_recursivo_cached(
        hash_atual: int, pos_a: tuple, cor: int, tipo: int, cam_a: tuple, caps_cam: tuple, visited: frozenset, damas_recem_promovidas: frozenset, depth: int
    ) -> list:
        # Esta função é uma versão cacheada e pura da recursão de capturas
        # O corpo da função será adaptado da versão original, mas sem acessar self
        # O acesso ao tabuleiro e métodos auxiliares deve ser feito via argumentos adicionais se necessário
        # (Aqui, só esboço a assinatura e a estrutura para você adaptar o corpo conforme necessário)
        pass

    # O método original _encontrar_capturas_recursivo deve ser adaptado para chamar a versão cacheada,
    # convertendo os argumentos mutáveis em tipos hashable e repassando o contexto necessário.
    # Remover toda a lógica de self._cache_capturas.

    def _encontrar_capturas_recursivo(self, pos_a: Posicao, cor: int, tipo: int, cam_a: Movimento, caps_cam: list, visited=None, depth=0) -> List[Movimento]:
        # Monitoramento de profundidade global
        if depth > self.max_depth_reached:
            self.max_depth_reached = depth
            if depth > 900 and not getattr(self, '_depth_warning_emitted', False):
                logging.warning(f"Alerta de profundidade (Tabuleiro): {depth}")
                self._depth_warning_emitted = True
        # dama recém‐promovida não captura **ao iniciar** o salto
        if depth == 0 and pos_a in self.damas_recem_promovidas:
            return []
        # --- se chegou à última linha como pedra, para na promoção: não captura mais ---
        if tipo == PEDRA and self.chegou_para_promover(pos_a, cor):
            return []
        # Prevenção de ciclos: não voltar para a mesma casa
        if visited is None:
            visited = set()
        if pos_a in visited:
            return []
        visited = visited | {pos_a}
        use_cache = len(visited) <= 1
        if not hasattr(self, '_cache_capturas'):
            self._cache_capturas = {}
        key = (self.hash_atual, pos_a, cor, tipo, tuple(sorted(caps_cam)), frozenset(visited), frozenset(self.damas_recem_promovidas))
        if use_cache and key in self._cache_capturas:
            return self._cache_capturas[key]
        seqs = []
        op = self.get_oponente(cor)
        dirs = DIRECOES_CAPTURA_PEDRA if tipo == PEDRA else DIRECOES_DAMA
        for dr, dc in dirs:
            if tipo == PEDRA:
                pc = (pos_a[0] + dr, pos_a[1] + dc)
                pd = (pos_a[0] + 2 * dr, pos_a[1] + 2 * dc)
                l_promo = 0 if cor == BRANCO else TAMANHO_TABULEIRO - 1
                if self.is_valido(*pd) and Peca.get_cor(self.get_peca(pc)) == op and self.get_peca(pd) == VAZIO and pc not in caps_cam:
                    novo_cam = cam_a + [pd]
                    novo_caps = caps_cam + [pc]
                    cont = self._encontrar_capturas_recursivo(pd, cor, tipo, novo_cam, novo_caps, visited, depth=depth+1)
                    if cont:
                        seqs.extend(cont)
                    else:
                        seqs.append(novo_cam)
            else:  # DAMA
                for i in range(1, TAMANHO_TABULEIRO):
                    pi = (pos_a[0] + i * dr, pos_a[1] + i * dc)
                    if not self.is_valido(*pi):
                        break
                    peca_i = self.get_peca(pi)
                    if Peca.get_cor(peca_i) == op and pi not in caps_cam:
                        for j in range(i + 1, TAMANHO_TABULEIRO):
                            pd = (pos_a[0] + j * dr, pos_a[1] + j * dc)
                            if not self.is_valido(*pd):
                                break
                            caminho_livre = True
                            for k in range(i+1, j):
                                interm = (pos_a[0] + k*dr, pos_a[1] + k*dc)
                                if self.get_peca(interm) != VAZIO:
                                    caminho_livre = False
                                    break
                            if caminho_livre and self.get_peca(pd) == VAZIO:
                                novo_cam = cam_a + [pd]
                                novo_caps = caps_cam + [pi]
                                cont = []
                                for dr2, dc2 in DIRECOES_DAMA:
                                    if (dr2, dc2) == (-dr, -dc):
                                        continue
                                    cont.extend(self._encontrar_capturas_recursivo(pd, cor, tipo, novo_cam, novo_caps, visited, depth=depth+1))
                                if cont:
                                    seqs.extend(cont)
                                else:
                                    seqs.append(novo_cam)
                        break
                    elif peca_i != VAZIO:
                        break
        if use_cache:
            self._cache_capturas[key] = seqs
        return seqs

    def encontrar_movimentos_possiveis(self, cor: int, apenas_capturas: bool = False) -> List[Movimento]:
        if not hasattr(self, '_moves_cache'):
            self._moves_cache = {}
        key = (self.hash_atual, cor, apenas_capturas)
        if key in self._moves_cache:
            return self._moves_cache[key]
            
        all_capturas = []
        simples = []
        capturas_por_pos = {}
        for pos_i in self.get_posicoes_pecas(cor):
            if not hasattr(self, 'damas_recem_promovidas'):
                self.damas_recem_promovidas = set()
            if pos_i in self.damas_recem_promovidas:
                continue
            pv = self.get_peca(pos_i)
            tipo = Peca.get_tipo(pv)
            if pos_i not in capturas_por_pos:
                capturas_por_pos[pos_i] = self._encontrar_capturas_recursivo(pos_i, cor, tipo, [pos_i], [])
            caps_peca = capturas_por_pos[pos_i]
            if caps_peca:
                all_capturas.extend(caps_peca)
        if all_capturas:
            max_caps = max(len(seq)-1 for seq in all_capturas)
            result = [seq for seq in all_capturas if len(seq)-1 == max_caps]
            self._moves_cache[key] = result
            return result
        if apenas_capturas:
            result = []
            self._moves_cache[key] = result
            return result
        for pos_i in self.get_posicoes_pecas(cor):
            if pos_i in self.damas_recem_promovidas:
                continue
            pv = self.get_peca(pos_i)
            tp = Peca.get_tipo(pv)
            cp = Peca.get_cor(pv)
            dirs = DIRECOES_PEDRA[cp] if tp == PEDRA else DIRECOES_DAMA
            if tp == PEDRA:
                for dr, dc in dirs:
                    pd = (pos_i[0]+dr, pos_i[1]+dc)
                    if self.is_valido(*pd) and self.get_peca(pd) == VAZIO:
                        simples.append([pos_i, pd])
            else:
                for dr, dc in dirs:
                    for i in range(1, TAMANHO_TABULEIRO):
                        pd = (pos_i[0]+i*dr, pos_i[1]+i*dc)
                        if not self.is_valido(*pd):
                            break
                        if self.get_peca(pd) == VAZIO:
                            simples.append([pos_i, pd])
                        else:
                            break
        self._moves_cache[key] = simples
        return simples

    def identificar_pecas_capturadas(self, mov: Movimento) -> Dict[Posicao, int]:
        caps={};
        if len(mov)<=1: return caps;
        try: pv=self.get_peca(mov[0]); c=Peca.get_cor(pv); op=self.get_oponente(c)
        except IndexError: return caps
        if pv==VAZIO: return caps
        for i in range(len(mov)-1):
            try:
                p1,p2=mov[i],mov[i+1]; dr,dc=p2[0]-p1[0],p2[1]-p1[1]; d=max(abs(dr),abs(dc));
                if d==0: continue
                sr,sc=dr//d,dc//d
                for j in range(1,d):
                    pi=(p1[0]+j*sr,p1[1]+j*sc); pv_i=self.get_peca(pi);
                    if Peca.get_cor(pv_i) == op: caps[pi] = pv_i; break
            except IndexError: print(f"Erro idx id_caps: {mov}"); continue
        return caps

    def _fazer_lance(self, mov: Movimento, troca_turno: bool = True) -> EstadoLanceDesfazer:
        self._clear_move_and_capture_cache()
        if hasattr(self, '_cache_ameaca_2l'):
            self._cache_ameaca_2l.clear()
        o=mov[0]; d=mov[-1]; h_a=self.hash_atual; p_o=self.get_peca(o); c=Peca.get_cor(p_o); t_o=Peca.get_tipo(p_o)
        pc=self.identificar_pecas_capturadas(mov); self.mover_peca(o,d);
        for pos_c in pc: self.remover_peca(pos_c)
        pr=False; l_p=0 if c==BRANCO else TAMANHO_TABULEIRO-1;
        damas_adicionadas = set()
        if t_o==PEDRA and d[0]==l_p:
            nv=DB if c==BRANCO else DP;
            self.set_peca(d,nv);
            pr=True
            self.hash_atual ^= Z_PROM[d[0]][d[1]]
            self.damas_recem_promovidas.add(d)
            damas_adicionadas.add(d)
        if troca_turno:
            self._atualizar_hash_turno()
        return EstadoLanceDesfazer(mov,p_o,pc,pr,h_a,damas_adicionadas, troca_turno)

    def _desfazer_lance(self, e: EstadoLanceDesfazer):
        self._clear_move_and_capture_cache()
        self.hash_atual=e.hash_anterior; mov=e.movimento; o=mov[0]; d=mov[-1]; p_r=e.peca_movida_original
        self.grid[d[0]][d[1]]=VAZIO; self.grid[o[0]][o[1]]=p_r;
        for pos_c,val_c in e.pecas_capturadas.items(): self.grid[pos_c[0]][pos_c[1]] = val_c
        for pos in e.damas_recem_promovidas_adicionadas:
            if pos in self.damas_recem_promovidas:
                self.hash_atual ^= Z_PROM[pos[0]][pos[1]]
                self.damas_recem_promovidas.remove(pos)
        if e.troca_turno:
            self._atualizar_hash_turno()

    def calcular_mobilidade_futura(self, r: int, c: int, cor: int, tipo: int) -> int:
        """
        Calcula a mobilidade futura de uma peça: quantos movimentos válidos ela terá
        nos próximos 1-2 lances, incluindo possíveis capturas.
        """
        mobilidade = 0
        pos = (r, c)
        
        # Para pedras, verificar movimentos simples possíveis (diagonais da cor)
        if tipo == PEDRA:
            for dr, dc in DIRECOES_PEDRA[cor]:
                # Movimento simples a 1 casa
                nr, nc = r + dr, c + dc
                if self.is_valido(nr, nc) and self.grid[nr][nc] == VAZIO:
                    mobilidade += 1
                    
                    # Verificar movimentos adicionais a 2 casas (mobilidade futura)
                    for dr2, dc2 in DIRECOES_PEDRA[cor]:
                        nr2, nc2 = nr + dr2, nc + dc2
                        if self.is_valido(nr2, nc2) and self.grid[nr2][nc2] == VAZIO:
                            mobilidade += 0.5  # Meio ponto por movimentos futuros
        
        # Para damas, verificar até 2 casas em cada direção
        elif tipo == DAMA:
            for dr, dc in DIRECOES_DAMA:
                for dist in range(1, 3):  # Verificar até 2 casas
                    nr, nc = r + dist*dr, c + dist*dc
                    if self.is_valido(nr, nc):
                        if self.grid[nr][nc] == VAZIO:
                            mobilidade += (1 if dist == 1 else 0.5)  # Peso menor para casas mais distantes
                        else:
                            break  # Parar quando encontrar uma peça
        
        return mobilidade
    
    def detectar_bloqueio_avanco(self, r: int, c: int, cor: int) -> bool:
        """
        Detecta se a peça em (r,c) está bloqueando o avanço de alguma pedra adversária.
        Ex: Se cor=BRANCO, ver se há pedra PRETA atrás tentando avançar.
        """
        oponente = self.get_oponente(cor)
        
        # Para peças brancas, olhar para baixo; para peças pretas, olhar para cima
        dr_blq = 1 if cor == BRANCO else -1
        
        # Verificar nas diagonais traseiras se há uma peça adversária
        for dc in [-1, 1]:
            r_adv, c_adv = r + dr_blq, c + dc
            if self.is_valido(r_adv, c_adv):
                peca_adv = self.grid[r_adv][c_adv]
                if Peca.get_cor(peca_adv) == oponente and Peca.get_tipo(peca_adv) == PEDRA:
                    # Verificar se a casa à frente da peça adversária está ocupada pela nossa peça
                    if self.grid[r][c] != VAZIO and Peca.get_cor(self.grid[r][c]) == cor:
                        return True
        
        return False
        
    def detectar_formacao_parede(self, r: int, c: int, cor: int) -> bool:
        """
        Detecta se a peça em (r,c) faz parte de uma formação de parede 
        (3+ peças alinhadas horizontalmente que bloqueiam avanço adversário)
        """
        conta_conectadas = 1
        
        # Verificar à esquerda
        for delta in range(1, 3):
            col = c - delta
            if not self.is_valido(r, col):
                break
            if self.grid[r][col] != VAZIO and Peca.get_cor(self.grid[r][col]) == cor:
                conta_conectadas += 1
            else:
                break
        
        # Verificar à direita
        for delta in range(1, 3):
            col = c + delta
            if not self.is_valido(r, col):
                break
            if self.grid[r][col] != VAZIO and Peca.get_cor(self.grid[r][col]) == cor:
                conta_conectadas += 1
            else:
                break
        
        # Consideramos uma parede quando há pelo menos 3 peças conectadas
        return conta_conectadas >= 3

    def _heuristica_para_cor(self, cor_ref: int, debug: bool = False) -> float:
        mp, md = 0, 0
        bonus = 0.0
        debug_info = []
        bordas = [(0, 1), (0, 3), (0, 5), (0, 7), (1, 0), (2, 7), (3, 0), (4, 7), (5, 0), (6, 7), (7, 0), (7, 2), (7, 4), (7, 6)]
        cache_vulneravel = {}
        for r in range(TAMANHO_TABULEIRO):
            for c in range(TAMANHO_TABULEIRO):
                p = self.grid[r][c]
                if p == VAZIO:
                    continue
                cor_p = Peca.get_cor(p)
                tp = Peca.get_tipo(p)
                pos = (r, c)
                if cor_p != cor_ref:
                    continue
                if tp == PEDRA:
                    mp += 1
                else:
                    md += 1
                debug_piece = {'pos': pos, 'tipo': 'PEDRA' if tp == PEDRA else 'DAMA', 'bônus': {}}
                val = 0.0
                tabela = PSQT_PEDRA if tp == PEDRA else PSQT_DAMA
                if cor_ref == BRANCO:
                    linha = r
                else:
                    linha = (TAMANHO_TABULEIRO - 1 - r)
                mult = VALOR_PEDRA if tp == PEDRA else VALOR_DAMA
                bonus_psqt = tabela[linha][c] * mult * 0.7  # reduz impacto do PSQT em 30%
                bonus += bonus_psqt
                debug_piece['bônus']['PSQT'] = bonus_psqt
                val += bonus_psqt
                vulneravel = self.eh_peca_vulneravel(r, c, cache_vulneravel)
                protegida = self.eh_peca_protegida(r, c)
                if vulneravel and not (tp == PEDRA and ((cor_p == BRANCO and r in [0, 1]) or (cor_p == PRETO and r in [TAMANHO_TABULEIRO-1, TAMANHO_TABULEIRO-2]))):
                    bonus += PENALIDADE_PECA_VULNERAVEL
                    debug_piece['bônus']['PENALIDADE_PECA_VULNERAVEL'] = PENALIDADE_PECA_VULNERAVEL
                    val += PENALIDADE_PECA_VULNERAVEL
                if protegida:
                    bonus += BONUS_PECA_PROTEGIDA
                    debug_piece['bônus']['BONUS_PECA_PROTEGIDA'] = BONUS_PECA_PROTEGIDA
                    val += BONUS_PECA_PROTEGIDA
                mov_fut = self.calcular_mobilidade_futura(r, c, cor_p, tp)
                if mov_fut > 0:
                    bonus += mov_fut * BONUS_MOBILIDADE_FUTURA
                    debug_piece['bônus']['BONUS_MOBILIDADE_FUTURA'] = mov_fut * BONUS_MOBILIDADE_FUTURA
                    val += mov_fut * BONUS_MOBILIDADE_FUTURA
                if self.detectar_bloqueio_avanco(r, c, cor_p):
                    bonus += BONUS_BLOQUEIO_AVANCO
                    debug_piece['bônus']['BONUS_BLOQUEIO_AVANCO'] = BONUS_BLOQUEIO_AVANCO
                    val += BONUS_BLOQUEIO_AVANCO
                if self.detectar_formacao_parede(r, c, cor_p) and self.detectar_bloqueio_avanco(r, c, cor_p):
                    bonus += BONUS_FORMACAO_PAREDE
                    debug_piece['bônus']['BONUS_FORMACAO_PAREDE'] = BONUS_FORMACAO_PAREDE
                    val += BONUS_FORMACAO_PAREDE
                if self.tem_pedras_conectadas(r, c) and self.detectar_bloqueio_avanco(r, c, cor_p):
                    bonus += BONUS_PAR_PEDRAS_CONECTADAS
                    debug_piece['bônus']['BONUS_PAR_PEDRAS_CONECTADAS'] = BONUS_PAR_PEDRAS_CONECTADAS
                    val += BONUS_PAR_PEDRAS_CONECTADAS
                ponte_bloqueio = self.tem_formacao_ponte(r, c) and self.detectar_bloqueio_avanco(r, c, cor_p)
                if ponte_bloqueio:
                    bonus += BONUS_FORMACAO_PONTE
                    debug_piece['bônus']['BONUS_FORMACAO_PONTE'] = BONUS_FORMACAO_PONTE
                    val += BONUS_FORMACAO_PONTE
                l_av = r if cor_p == PRETO else (TAMANHO_TABULEIRO-1 - r)
                avanco = l_av * BONUS_AVANCO_PEDRA if tp == PEDRA else 0
                bonus += avanco
                debug_piece['bônus']['BONUS_AVANCO_PEDRA'] = avanco
                val += avanco
                centro = (BONUS_CONTROLE_CENTRO_DAMA if tp == DAMA else BONUS_CONTROLE_CENTRO_PEDRA) if pos in self.casas_centro_expandido else 0
                bonus += centro
                debug_piece['bônus']['BONUS_CONTROLE_CENTRO'] = centro
                val += centro
                l_seg_propria = 0 if cor_p == BRANCO else TAMANHO_TABULEIRO - 1
                l_base_propria = {0, 1} if cor_p == BRANCO else {TAMANHO_TABULEIRO - 1, TAMANHO_TABULEIRO - 2}
                l_promo_iminente = 1 if cor_p == BRANCO else TAMANHO_TABULEIRO - 2
                seg = BONUS_SEGURANCA_ULTIMA_LINHA if r == l_seg_propria else 0
                bonus += seg
                debug_piece['bônus']['BONUS_SEGURANCA_ULTIMA_LINHA'] = seg
                val += seg
                pen_atrasada = PENALIDADE_PEDRA_ATRASADA if tp == PEDRA and r in l_base_propria else 0
                bonus += pen_atrasada
                debug_piece['bônus']['PENALIDADE_PEDRA_ATRASADA'] = pen_atrasada
                val += pen_atrasada
                prestes = BONUS_PRESTES_PROMOVER if tp == PEDRA and r == l_promo_iminente and not vulneravel else 0
                bonus += prestes
                debug_piece['bônus']['BONUS_PRESTES_PROMOVER'] = prestes
                val += prestes
                borda = BONUS_PECA_NA_BORDA if tp == DAMA and pos in bordas else 0.0
                bonus += borda
                debug_piece['bônus']['BONUS_PECA_NA_BORDA'] = borda
                val += borda
                if tp == DAMA:
                    mobilidade = sum(1 for dr, dc in DIRECOES_DAMA if self.is_valido(r + dr, c + dc) and self.get_peca((r + dr, c + dc)) == VAZIO)
                    mob_dama = mobilidade * BONUS_MOBILIDADE_DAMA if mobilidade > 0 else 0
                    bonus += mob_dama
                    debug_piece['bônus']['BONUS_MOBILIDADE_DAMA'] = mob_dama
                    val += mob_dama
                
                if self.tem_formacao_ponte(r, c):
                    bonus += BONUS_FORMACAO_PONTE
                    debug_piece['bônus']['BONUS_FORMACAO_PONTE'] = BONUS_FORMACAO_PONTE
                    val += BONUS_FORMACAO_PONTE
                
                # Removido verificação de peça ameaçada em 2 lances para melhorar performance
                # ameacada_2l = self.eh_peca_ameacada_em_2_lances(r, c)
                # if ameacada_2l:
                #     bonus += PENALIDADE_PECA_AMEACADA_2L
                #     debug_piece['bônus']['PENALIDADE_PECA_AMEACADA_2L'] = PENALIDADE_PECA_AMEACADA_2L
                #     val += PENALIDADE_PECA_AMEACADA_2L
                
                if self.eh_peca_ameacada(r, c):
                    bonus += PENALIDADE_PECA_AMEACADA_2L
                    debug_piece['bônus']['PENALIDADE_PECA_AMEACADA_2L'] = PENALIDADE_PECA_AMEACADA_2L
                    val += PENALIDADE_PECA_AMEACADA_2L
                debug_piece['score_parcial'] = val
                if debug:
                    debug_info.append(debug_piece)
        # ---- penaliza movimentos que deixam captura imediata ----
        tab_temp = self.criar_copia()
        cor_op = Tabuleiro.get_oponente(cor_ref)
        caps = tab_temp.encontrar_movimentos_possiveis(cor_op, apenas_capturas=True)
        # soma valor das vítimas (última casa de cada movimento)
        valor_caps = 0.0
        for m in caps:
            v = tab_temp.get_peca(m[-1])
            valor_caps += (VALOR_DAMA if abs(v)==DAMA else VALOR_PEDRA)
        bonus += -valor_caps
        if valor_caps > 0:
            if debug:
                debug_info.append({
                    'pos': None, 'tipo':'PÊNALTI TÁTICO',
                    'bônus':{'PENALIDADE_CAPTURA_IMEDIATA': -valor_caps},
                    'score_parcial': -valor_caps
                })
        # só depois é que fecha o score
        score = mp * VALOR_PEDRA + md * VALOR_DAMA + bonus
        if debug:
            self._last_debug_info = debug_info
        return score

    def avaliar_heuristica(self, cor_ref: int, debug_aval: bool = False) -> float:
        # só cachear quando não for em modo debug
        if not hasattr(self, '_eval_cache'):
            self._eval_cache = {}
        key = (self.hash_atual, cor_ref)
        if not debug_aval and key in self._eval_cache:
            return self._eval_cache[key]

        allied = self._heuristica_para_cor(cor_ref, debug_aval)
        opponent = self._heuristica_para_cor(self.get_oponente(cor_ref), False)
        score = allied - opponent

        if not debug_aval:
            self._eval_cache[key] = score
        return score

    @staticmethod
    def pos_para_alg(p: Posicao)->str: r,c=p; return chr(ord('a')+c)+str(TAMANHO_TABULEIRO-r) if Tabuleiro.is_valido(r,c) else "Inv"
    @staticmethod
    def alg_para_pos(alg: str)->Optional[Posicao]: alg=alg.lower().strip(); return (lambda c,l: (l,c) if Tabuleiro.is_valido(l,c) else None)(ord(alg[0])-ord('a'), TAMANHO_TABULEIRO-int(alg[1])) if len(alg)==2 and 'a'<=alg[0]<='h' and '1'<=alg[1]<='8' else None

    def criar_copia(self) -> 'Tabuleiro':
        """Cria uma cópia profunda do tabuleiro atual."""
        nova_copia = Tabuleiro(estado_inicial=False)  # Cria um tabuleiro vazio
        
        # Copia os bitboards
        nova_copia.bitboard_brancas = self.bitboard_brancas
        nova_copia.bitboard_damas_brancas = self.bitboard_damas_brancas
        nova_copia.bitboard_pretas = self.bitboard_pretas
        nova_copia.bitboard_damas_pretas = self.bitboard_damas_pretas
        
        # Copia os dados convencionais
        nova_copia.grid = [linha[:] for linha in self.grid]  # Copia profunda da grade
        nova_copia.hash_atual = self.hash_atual
        nova_copia.damas_recem_promovidas = set(self.damas_recem_promovidas)  # Propaga flags de promoção
        nova_copia._eval_cache = dict(self._eval_cache)  # Copia o cache de avaliação
        nova_copia._moves_cache = dict(self._moves_cache)  # Copia o cache de movimentos
        
        return nova_copia

    def limpar_damas_recem_promovidas_por_cor(self, cor: int):
        """
        Remove as damas recém-promovidas de uma cor específica da lista de controle.
        Chamado quando termina o turno do jogador oponente.
        """
        # Para cada posição no conjunto de damas recém-promovidas
        damas_para_remover = []
        for pos in self.damas_recem_promovidas:
            peca = self.get_peca(pos)
            # Verificar se a peça pertence à cor especificada
            if Peca.get_cor(peca) == cor:
                damas_para_remover.append(pos)
        
        # Remover as damas da cor especificada
        for pos in damas_para_remover:
            self.hash_atual ^= Z_PROM[pos[0]][pos[1]]
            self.damas_recem_promovidas.remove(pos)

    def eh_peca_vulneravel(self, r: int, c: int, cache_vulneravel: dict = None) -> bool:
        """
        Retorna True se a peça em (r, c) pode ser capturada imediatamente por uma peça adversária adjacente (profundidade 1).
        Não faz busca recursiva nem combos.
        """
        cor_peca = Peca.get_cor(self.grid[r][c])
        if cor_peca == VAZIO:
            if cache_vulneravel is not None:
                cache_vulneravel[(r, c)] = False
            return False
        cor_oponente = self.get_oponente(cor_peca)
        tipo_peca = Peca.get_tipo(self.grid[r][c])
        dirs = DIRECOES_CAPTURA_PEDRA if tipo_peca == PEDRA else DIRECOES_DAMA
        for dr, dc in dirs:
            r_op, c_op = r + dr, c + dc
            r_dest, c_dest = r - dr, c - dc
            if self.is_valido(r_op, c_op) and self.is_valido(r_dest, c_dest):
                peca_op = self.grid[r_op][c_op]
                if Peca.get_cor(peca_op) == cor_oponente:
                    tipo_op = Peca.get_tipo(peca_op)
                    # Só permite captura se destino está vazio e tipo permite
                    if self.grid[r_dest][c_dest] == VAZIO:
                        if tipo_op == DAMA or (tipo_op == PEDRA and ((cor_oponente == BRANCO and dr == -1) or (cor_oponente == PRETO and dr == 1))):
                            if cache_vulneravel is not None:
                                cache_vulneravel[(r, c)] = True
                            return True
        if cache_vulneravel is not None:
            cache_vulneravel[(r, c)] = False
        return False

    def eh_peca_protegida(self, r: int, c: int) -> bool:
        """
        Retorna True se a peça em (r, c) está "protegida" contra capturas adjacentes (profundidade 1):
        após uma captura adjacente, existe uma peça aliada adjacente ao destino que poderia recapturar imediatamente.
        Não faz busca recursiva nem combos.
        """
        cor_peca = Peca.get_cor(self.grid[r][c])
        if cor_peca == VAZIO:
            return False
        cor_oponente = self.get_oponente(cor_peca)
        tipo_peca = Peca.get_tipo(self.grid[r][c])
        dirs = DIRECOES_CAPTURA_PEDRA if tipo_peca == PEDRA else DIRECOES_DAMA
        for dr, dc in dirs:
            r_op, c_op = r + dr, c + dc
            r_dest, c_dest = r - dr, c - dc
            if self.is_valido(r_op, c_op) and self.is_valido(r_dest, c_dest):
                peca_op = self.grid[r_op][c_op]
                if Peca.get_cor(peca_op) == cor_oponente:
                    tipo_op = Peca.get_tipo(peca_op)
                    if self.grid[r_dest][c_dest] == VAZIO:
                        if tipo_op == DAMA or (tipo_op == PEDRA and ((cor_oponente == BRANCO and dr == -1) or (cor_oponente == PRETO and dr == 1))):
                            # Agora, verifica se há uma peça aliada adjacente ao destino que pode recapturar
                            for dr2, dc2 in DIRECOES_CAPTURA_PEDRA if tipo_peca == PEDRA else DIRECOES_DAMA:
                                r_ali, c_ali = r_dest + dr2, c_dest + dc2
                                r_recapt, c_recapt = r_dest - dr2, c_dest - dc2
                                if self.is_valido(r_ali, c_ali) and self.is_valido(r_recapt, c_recapt):
                                    peca_ali = self.grid[r_ali][c_ali]
                                    if Peca.get_cor(peca_ali) == cor_peca:
                                        tipo_ali = Peca.get_tipo(peca_ali)
                                        if self.grid[r_recapt][c_recapt] == VAZIO:
                                            if tipo_ali == DAMA or (tipo_ali == PEDRA and ((cor_peca == BRANCO and dr2 == -1) or (cor_peca == PRETO and dr2 == 1))):
                                                return True
        return False

    def tem_pedras_conectadas(self, r: int, c: int) -> bool:
        """
        Retorna True se a peça em (r, c) tem pelo menos uma pedra aliada conectada diagonalmente (adjacente).
        Considera apenas conexões diagonais imediatas.
        """
        cor_peca = Peca.get_cor(self.grid[r][c])
        if cor_peca == VAZIO:
            return False
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if self.is_valido(nr, nc) and Peca.get_cor(self.grid[nr][nc]) == cor_peca:
                return True
        return False

    def tem_formacao_ponte(self, r: int, c: int) -> bool:
        """
        Detecta se (r,c) faz parte de uma 'ponte' clássica:
        Duas peças da mesma cor separadas por uma casa vazia na linha,
        e atrás da casa vazia (na diagonal) uma peça da mesma cor.
        """
        cor_peca = Peca.get_cor(self.grid[r][c])
        if cor_peca == VAZIO:
            return False
        # Ponte para a direita
        if self.is_valido(r, c+2):
            if (self.grid[r][c+2] != VAZIO and
                Peca.get_cor(self.grid[r][c+2]) == cor_peca and
                self.grid[r][c+1] == VAZIO):
                # Para BRANCO, atrás é (r+1, c+1); para PRETO, atrás é (r-1, c+1)
                r_tras = r+1 if cor_peca == BRANCO else r-1
                if self.is_valido(r_tras, c+1) and Peca.get_cor(self.grid[r_tras][c+1]) == cor_peca:
                    return True
        # Ponte para a esquerda
        if self.is_valido(r, c-2):
            if (self.grid[r][c-2] != VAZIO and
                Peca.get_cor(self.grid[r][c-2]) == cor_peca and
                self.grid[r][c-1] == VAZIO):
                r_tras = r+1 if cor_peca == BRANCO else r-1
                if self.is_valido(r_tras, c-1) and Peca.get_cor(self.grid[r_tras][c-1]) == cor_peca:
                    return True
        return False

    def tem_formacao_lanca(self, r: int, c: int) -> bool:
        """
        Detecta se (r,c) faz parte de uma 'lança' clássica:
        Duas peças da mesma cor formando um Y com uma casa vazia à frente.
        Exemplo (para BRANCO):
        . x .
        x o x
        . . .
        Onde 'o' é a peça avaliada, 'x' são aliadas, '.' são casas vazias.
        """
        cor_peca = Peca.get_cor(self.grid[r][c])
        if cor_peca == VAZIO:
            return False
        # Para BRANCO, lança aponta para cima; para PRETO, para baixo
        direcao = -1 if cor_peca == BRANCO else 1
        # Checar as duas diagonais à frente
        for dc in [-1, 1]:
            r1, c1 = r + direcao, c + dc
            r2, c2 = r + 2*direcao, c
            if self.is_valido(r1, c1) and self.is_valido(r2, c2):
                if (self.grid[r1][c1] != VAZIO and Peca.get_cor(self.grid[r1][c1]) == cor_peca and
                    self.grid[r2][c2] == VAZIO):
                    return True
        return False

    def eh_peca_ameacada_em_2_lances(self, r: int, c: int) -> bool:
        """
        Retorna True se a peça em (r, c) pode ser capturada em até 2 lances do adversário,
        considerando que o próprio jogador pode responder entre os lances do oponente.
        Utiliza análise simplificada baseada em vulnerabilidade imediata, proteção e presença de atacantes/defensores próximos.
        Resultados são cacheados para eficiência.
        """
        # Se já temos o resultado no cache, retornamos ele direto
        if not hasattr(self, '_cache_ameaca_2l'):
            self._cache_ameaca_2l = {}
        key = (self.hash_atual, r, c)
        if key in self._cache_ameaca_2l:
            return self._cache_ameaca_2l[key]
        
        # Verifica se é uma peça válida
        cor_peca = Peca.get_cor(self.grid[r][c])
        if cor_peca == VAZIO:
            return False
            
        cor_oponente = self.get_oponente(cor_peca)
        
        # Primeira otimização: verificar ameaça direta (em 1 lance)
        if self.eh_peca_vulneravel(r, c):
            self._cache_ameaca_2l[key] = True
            return True
            
        # Segunda otimização: verificamos se a peça está protegida
        if self.eh_peca_protegida(r, c):
            self._cache_ameaca_2l[key] = False
            return False
        
        # Terceira otimização: verificar se existem atacantes potenciais próximos
        atacantes_proximos = 0
        defensores_proximos = 0
        diagonais_proximas = [
            (-1, -1), (-1, 1), (1, -1), (1, 1),  # 1 casa de distância
            (-2, -2), (-2, 2), (2, -2), (2, 2)   # 2 casas de distância
        ]
        
        for dr, dc in diagonais_proximas:
            nr, nc = r + dr, c + dc
            if self.is_valido(nr, nc):
                peca = self.grid[nr][nc]
                if peca != VAZIO:
                    peca_cor = Peca.get_cor(peca)
                    if peca_cor == cor_oponente:
                        if Peca.get_tipo(peca) == DAMA:
                            atacantes_proximos += 1
                        elif Peca.get_tipo(peca) == PEDRA:
                            if (cor_oponente == PRETO and dr > 0) or (cor_oponente == BRANCO and dr < 0):
                                atacantes_proximos += 1
                    elif peca_cor == cor_peca:
                        defensores_proximos += 1
        
        result = atacantes_proximos > defensores_proximos
        self._cache_ameaca_2l[key] = result
        return result

    def material_balance(self, cor_ref: int) -> float:
        """Calcula o balanço material: diferença entre peças do jogador e do oponente."""
        # Contar peças usando bitboards
        white_men_count = bin(self.bitboard_brancas).count("1")
        white_kings_count = bin(self.bitboard_damas_brancas).count("1")
        black_men_count = bin(self.bitboard_pretas).count("1")
        black_kings_count = bin(self.bitboard_damas_pretas).count("1")
        
        # Calcular valores totais
        white_value = white_men_count * VALOR_PEDRA + white_kings_count * VALOR_DAMA
        black_value = black_men_count * VALOR_PEDRA + black_kings_count * VALOR_DAMA
        
        # Retornar o balanço com base na cor de referência
        if cor_ref == BRANCO:
            return white_value - black_value
        else:
            return black_value - white_value

    def chegou_para_promover(self, pos: Posicao, cor: int) -> bool:
        """Verifica se uma peça chegou à fileira de promoção (usando bitboards)."""
        bit = self.pos_to_bit(pos)
        
        if cor == BRANCO:
            # Peças brancas promovem na primeira fileira (rank 1)
            return bit & BB_RANK_1 != 0
        else:
            # Peças pretas promovem na última fileira (rank 8)
            return bit & BB_RANK_8 != 0

    def eh_peca_ameacada(self, r: int, c: int) -> bool:
        """
        Retorna True se a peça em (r, c) está ameaçada por uma peça adversária adjacente.
        """
        for dr, dc in DIRECOES_CAPTURA_PEDRA:
            r_dest, c_dest = r + dr, c + dc
            if self.is_valido(r_dest, c_dest) and self.grid[r_dest][c_dest] != VAZIO:
                return True
        return False

    def get_all_king_moves_bitboard(self, pos: Posicao, cor: int) -> int:
        """Retorna um bitboard com todas as posições que uma dama na posição pos pode se mover."""
        bit_pos = self.pos_to_bit(pos)
        all_pieces = self.get_all_pieces()
        empty = self.get_empty_squares()
        moves = 0
        
        # Verificar as 4 direções
        for shift in BB_SHIFTS_ALL:
            # Começar da posição inicial
            current_bit = bit_pos
            
            # Continuar na direção até encontrar uma barreira
            while True:
                # Aplicar o shift correspondente à direção com mascaramento para evitar wrap-around
                if shift == BB_SHIFT_NE:
                    current_bit = (current_bit >> 7) & BB_NOT_A_FILE
                elif shift == BB_SHIFT_NW:
                    current_bit = (current_bit >> 9) & BB_NOT_H_FILE
                elif shift == BB_SHIFT_SE:
                    current_bit = (current_bit << 9) & BB_NOT_H_FILE
                elif shift == BB_SHIFT_SW:
                    current_bit = (current_bit << 7) & BB_NOT_A_FILE
                
                # Se saiu do tabuleiro ou encontrou uma peça, para
                if current_bit == 0 or (current_bit & all_pieces) != 0:
                    break
                    
                # Adiciona esta posição como um movimento possível
                moves |= current_bit
        
        return moves
        
    def get_man_moves_bitboard(self, pos: Posicao, cor: int) -> int:
        """Retorna um bitboard com todas as posições que uma pedra na posição pos pode se mover."""
        bit_pos = self.pos_to_bit(pos)
        empty = self.get_empty_squares()
        moves = 0
        
        # Verificar as 2 direções permitidas para a cor
        shifts = BB_SHIFTS_WHITE if cor == BRANCO else BB_SHIFTS_BLACK
        
        for shift in shifts:
            # Aplicar o shift correspondente à direção com mascaramento para evitar wrap-around
            if shift == BB_SHIFT_NE:
                move_bit = (bit_pos >> 7) & BB_NOT_A_FILE
            elif shift == BB_SHIFT_NW:
                move_bit = (bit_pos >> 9) & BB_NOT_H_FILE
            elif shift == BB_SHIFT_SE:
                move_bit = (bit_pos << 9) & BB_NOT_H_FILE
            elif shift == BB_SHIFT_SW:
                move_bit = (bit_pos << 7) & BB_NOT_A_FILE
            
            # Se é uma casa válida e está vazia, adiciona como movimento possível
            if move_bit != 0 and (move_bit & empty) != 0:
                moves |= move_bit
        
        return moves
        
    def get_man_capture_moves_bitboard(self, pos: Posicao, cor: int) -> Tuple[int, Dict[int, int]]:
        """
        Retorna um bitboard com todas as posições que uma pedra na posição pos pode capturar
        e um dicionário mapeando os bits de destino para os bits das peças capturadas.
        """
        bit_pos = self.pos_to_bit(pos)
        empty = self.get_empty_squares()
        oponente = self.get_pieces_by_color(self.get_oponente(cor))
        moves = 0
        captured_pieces = {}
        
        # Verificar as 4 direções
        for shift in BB_SHIFTS_ALL:
            # Aplicar o shift para encontrar a posição adjacente
            if shift == BB_SHIFT_NE:
                adjacent_bit = (bit_pos >> 7) & BB_NOT_A_FILE
                capture_bit = (adjacent_bit >> 7) & BB_NOT_A_FILE
            elif shift == BB_SHIFT_NW:
                adjacent_bit = (bit_pos >> 9) & BB_NOT_H_FILE
                capture_bit = (adjacent_bit >> 9) & BB_NOT_H_FILE
            elif shift == BB_SHIFT_SE:
                adjacent_bit = (bit_pos << 9) & BB_NOT_H_FILE
                capture_bit = (adjacent_bit << 9) & BB_NOT_H_FILE
            elif shift == BB_SHIFT_SW:
                adjacent_bit = (bit_pos << 7) & BB_NOT_A_FILE
                capture_bit = (adjacent_bit << 7) & BB_NOT_A_FILE
            
            # Se a posição adjacente contém uma peça do oponente e a posição após está vazia
            if adjacent_bit != 0 and (adjacent_bit & oponente) != 0 and capture_bit != 0 and (capture_bit & empty) != 0:
                moves |= capture_bit
                captured_pieces[capture_bit] = adjacent_bit
        
        return moves, captured_pieces
        
    def gera_movimentos_simples(self, cor: int) -> List[Tuple[Posicao, Posicao]]:
        """
        Gera todos os movimentos simples (não-captura) para uma cor usando operações puras de bitboards.
        Retorna uma lista de tuplas (origem, destino).
        
        Args:
            cor: BRANCO ou PRETO, a cor das peças para gerar movimentos
        
        Returns:
            Lista de movimentos no formato [(origem, destino), ...]
        """
        movimentos = []
        
        # Casas vazias no tabuleiro (apenas casas escuras válidas para jogo)
        bb_vazias = self.get_empty_squares()
        
        # Processar movimentos das pedras (men)
        if cor == BRANCO:
            # Pedras brancas (excluindo as que são damas)
            bb_pedras = self.bitboard_brancas & ~self.bitboard_damas_brancas
            
            # Nordeste: cima+direita => >>7, exclui H-file
            moves_ne = ((bb_pedras & BB_NOT_H_FILE) >> 7) & bb_vazias
            orig_ne = (moves_ne << 7) & bb_pedras
            while orig_ne:
                b_orig = self.lsb(orig_ne)
                pos_o = self.bit_to_pos(b_orig)
                b_dest = b_orig >> 7
                pos_d = self.bit_to_pos(b_dest)
                movimentos.append((pos_o, pos_d))
                orig_ne = self.clear_lsb(orig_ne)
            
            # Noroeste: cima+esquerda => >>9, exclui A-file
            moves_nw = ((bb_pedras & BB_NOT_A_FILE) >> 9) & bb_vazias
            orig_nw = (moves_nw << 9) & bb_pedras
            while orig_nw:
                b_orig = self.lsb(orig_nw)
                pos_o = self.bit_to_pos(b_orig)
                b_dest = b_orig >> 9
                pos_d = self.bit_to_pos(b_dest)
                movimentos.append((pos_o, pos_d))
                orig_nw = self.clear_lsb(orig_nw)
            
        else:  # PRETO
            # Pedras pretas (excluindo as que são damas)
            bb_pedras = self.bitboard_pretas & ~self.bitboard_damas_pretas
            
            # Sudeste: baixo+direita => <<9, exclui H-file
            moves_se = ((bb_pedras & BB_NOT_H_FILE) << 9) & bb_vazias
            orig_se = (moves_se >> 9) & bb_pedras
            while orig_se:
                b_orig = self.lsb(orig_se)
                pos_o = self.bit_to_pos(b_orig)
                b_dest = b_orig << 9
                pos_d = self.bit_to_pos(b_dest)
                movimentos.append((pos_o, pos_d))
                orig_se = self.clear_lsb(orig_se)
            
            # Sudoeste: baixo+esquerda => <<7, exclui A-file
            moves_sw = ((bb_pedras & BB_NOT_A_FILE) << 7) & bb_vazias
            orig_sw = (moves_sw >> 7) & bb_pedras
            while orig_sw:
                b_orig = self.lsb(orig_sw)
                pos_o = self.bit_to_pos(b_orig)
                b_dest = b_orig << 7
                pos_d = self.bit_to_pos(b_dest)
                movimentos.append((pos_o, pos_d))
                orig_sw = self.clear_lsb(orig_sw)
        
        # Processar movimentos das damas (kings)
        if cor == BRANCO:
            bb_damas = self.bitboard_damas_brancas
        else:
            bb_damas = self.bitboard_damas_pretas
        
        # Para cada dama, obtém todos os movimentos possíveis
        temp_damas = bb_damas
        while temp_damas:
            bit_dama = self.lsb(temp_damas)
            pos_dama = self.bit_to_pos(bit_dama)
            
            # Obtém todas as posições para onde a dama pode se mover
            # Usando uma função auxiliar que retorna um bitboard com todos os destinos possíveis
            destinos = self.get_all_king_moves_bitboard(pos_dama, cor)
            
            # Converte o bitboard de destinos em pares de movimento
            temp_dest = destinos
            while temp_dest:
                bit_dest = self.lsb(temp_dest)
                pos_dest = self.bit_to_pos(bit_dest)
                
                movimentos.append((pos_dama, pos_dest))
                
                temp_dest = self.clear_lsb(temp_dest)
            
            temp_damas = self.clear_lsb(temp_damas)
        
        return movimentos
        
    @staticmethod
    def print_bitboard(bb: int):
        """Imprime uma representação visual de um bitboard."""
        print("  abcdefgh")
        for r in range(TAMANHO_TABULEIRO):
            linha = f"{TAMANHO_TABULEIRO-r} "
            for c in range(TAMANHO_TABULEIRO):
                bit = 1 << (r * 8 + c)
                if bb & bit:
                    linha += "X"
                else:
                    linha += "." if (r + c) % 2 == 1 else " "
            linha += f" {TAMANHO_TABULEIRO-r}"
            print(linha)
        print("  abcdefgh")
        
    
    def obter_estatisticas_aspiration(self):
        """
        Dummy para compatibilidade com a interface. Retorna estatísticas vazias ou padrão.
        """
        return {
            'sucessos': 0,
            'falhas': 0,
            'taxa_sucesso': 0.0,
            'movimentos_reusados': 0,
            'busca_otimizada': 0,
            'janelas_usadas': []
        }

    def _search_root(self, tab, prof, alpha, beta, movs_ord_raiz, cor_ia, cache_capturas_oponente):
        resultados = {}
        best_score = -float('inf')
        best_move = None
        for mov in movs_ord_raiz:
            if self.verificar_tempo(): raise TempoExcedidoError("Tempo excedido durante avaliação de movimentos")
            cp = bool(tab.identificar_pecas_capturadas(mov))
            pos_final = mov[-1]
            peca_final = tab.get_peca(pos_final)
            tipo_final = Peca.get_tipo(peca_final)
            capturas_combo = tab._encontrar_capturas_recursivo(pos_final, cor_ia, tipo_final, [pos_final], []) if cp else []
            troca_turno = not (cp and capturas_combo)
            estado_d = tab._fazer_lance(mov, troca_turno=troca_turno)
            try:
                cor_op = Tabuleiro.get_oponente(cor_ia) if troca_turno else cor_ia
                hash_apos = tab.hash_atual
                if hash_apos in cache_capturas_oponente:
                    capturas_oponente = cache_capturas_oponente[hash_apos]
                else:
                    capturas_oponente = tab.encontrar_movimentos_possiveis(cor_op, apenas_capturas=True)
                    cache_capturas_oponente[hash_apos] = capturas_oponente
                # força root a ignorar lances ruins
                # if capturas_oponente:
                #     continue
                jog_apos = Tabuleiro.get_oponente(cor_ia) if troca_turno else cor_ia
                pd = (Peca.get_tipo(estado_d.peca_movida_original)==PEDRA)
                ct_p = 0
                score = -self.minimax(tab, ct_p, prof - 1, -beta, -alpha, jog_apos, cor_ia, depth=1)
                fmt = self._formatar_movimento(mov)
                resultados[fmt] = score
                if score > best_score:
                    best_score = score
                    best_move = mov
                alpha = max(alpha, best_score)
                if self.verificar_tempo(): raise TempoExcedidoError("Tempo excedido após avaliação de um movimento")
            finally:
                tab._desfazer_lance(estado_d)
        return best_score, best_move, resultados

    ENDGAME_PIECES = 5
    FEW_PIECES_TOTAL = 6

    def is_endgame(self, tab):
        """Verifica se o jogo está no fim de jogo (poucas peças restantes)."""
        # Contar peças usando bitboards
        white_men_count = bin(tab.bitboard_brancas).count("1")
        white_kings_count = bin(tab.bitboard_damas_brancas).count("1")
        black_men_count = bin(tab.bitboard_pretas).count("1")
        black_kings_count = bin(tab.bitboard_damas_pretas).count("1")
        
        total_pedras = white_men_count + black_men_count
        total_damas = white_kings_count + black_kings_count
        return total_pedras <= 2 or (total_pedras + total_damas) <= self.ENDGAME_PIECES

    def has_few_pieces(self, tab):
        """Verifica se há poucas peças no tabuleiro."""
        # Contar todas as peças usando bitboards
        total = bin(tab.get_all_pieces()).count("1")
        return total <= self.FEW_PIECES_TOTAL

    LMR_THRESHOLD = 2

    def can_null_move(self, tab, jog, prof) -> bool:
        return (
            prof > self.null_move_reduction(prof)
            and not self.is_endgame(tab)
            and not self.has_few_pieces(tab)
            and jog != self.cor_ia
            and not tab.encontrar_movimentos_possiveis(jog, apenas_capturas=True)
        )

    def null_move_reduction(self, prof) -> int:
        return 2 + prof // 4

    def futility_margin(self, prof) -> float:
        return VALOR_PEDRA * prof * 0.3

    def lmr_reduction(self, prof, move_index) -> int:
        import math
        return 1 + int(math.log(prof)) if move_index >= self.LMR_THRESHOLD and prof > 3 else 0

    def can_multi_cut(self, prof, movs_ordenados) -> bool:
        return prof >= 5 and len(movs_ordenados) >= self.MULTICUT_N

    def see(self, tab, pos, atacante_cor):
        """
        Static Exchange Evaluation completo: simula trocas recíprocas em 'pos', alternando os lados,
        sempre usando o atacante mais barato disponível de cada lado.
        Retorna o ganho líquido estimado para o lado que inicia (atacante_cor).
        """
        # Função auxiliar para obter todos os atacantes de uma casa
        def get_all_attackers(tab, pos, cor):
            atacantes = []
            for r in range(TAMANHO_TABULEIRO):
                for c in range(TAMANHO_TABULEIRO):
                    peca = tab.grid[r][c]
                    if Peca.get_cor(peca) == cor:
                        movs = tab.encontrar_movimentos_possiveis(cor, apenas_capturas=True)
                        for mov in movs:
                            if mov[-1] == pos:
                                atacantes.append((r, c))
            return atacantes
        # Função auxiliar para valor da peça
        def piece_value(v):
            return VALOR_DAMA if abs(v) == DAMA else VALOR_PEDRA
        # Função auxiliar para cor da peça
        def piece_color(v):
            return Peca.get_cor(v)
        # Inicializa
        tab_copia = tab.criar_copia()
        gain = []
        side = atacante_cor
        ocupante = tab_copia.get_peca(pos)
        if ocupante == VAZIO:
            return 0
        gain.append(piece_value(ocupante))
        atacantes = {BRANCO: get_all_attackers(tab_copia, pos, BRANCO), PRETO: get_all_attackers(tab_copia, pos, PRETO)}
        idx = 0
        while True:
            # Remove o atacante mais barato do lado atual
            candidatos = atacantes[side]
            if not candidatos:
                break
            # Escolhe o atacante mais barato
            candidatos.sort(key=lambda p: piece_value(tab_copia.get_peca(p)))
            attacker = candidatos[0]
            # Remove atacante do tabuleiro
            tab_copia.set_peca(attacker, VAZIO)
            atacantes[side].remove(attacker)
            # Remove peça capturada em pos
            tab_copia.set_peca(pos, VAZIO)
            # Alterna lado
            side = Tabuleiro.get_oponente(side)
            # Atualiza atacantes do novo lado
            atacantes[side] = get_all_attackers(tab_copia, pos, side)
            # Se houver novo atacante, adiciona valor ao ganho
            if atacantes[side]:
                next_attacker = min(atacantes[side], key=lambda p: piece_value(tab_copia.get_peca(p)))
                gain.append((-1)**(idx+1) * piece_value(tab_copia.get_peca(next_attacker)))
            idx += 1
        return sum(gain)

    def _validar_capturas_bitboard(self, cor: int) -> bool:
        """
        Valida as capturas simples de pedras (man) usando bitboards, comparando com o método tradicional.
        Para cada peça do tipo pedra, compara os movimentos de captura possíveis via bitboard com os capturas detectadas pelo método tradicional.
        Retorna True se todos os resultados forem idênticos, False caso contrário.
        """
        ok = True
        pecas = self.get_posicoes_pecas(cor)
        for pos in pecas:
            peca = self.get_peca(pos)
            if Peca.get_tipo(peca) != PEDRA:
                continue  # Só testa para pedras
            moves_bb, cap_bb = self.get_man_capture_moves_bitboard(pos, cor)
            # cap_bb: dict {dest_bit: captured_bit}
            capturas_bitboard = set()
            for dest_bit, captured_bit in cap_bb.items():
                origem = pos
                destino = self.bit_to_pos(dest_bit)
                capturada = self.bit_to_pos(captured_bit)
                capturas_bitboard.add((origem, destino, capturada))
            # Agora, capturas tradicionais
            capturas_trad = set()
            # O método tradicional retorna sequências de posições, mas para capturas simples, só interessa o primeiro salto
            for mov in self._encontrar_capturas_recursivo(pos, cor, PEDRA, [pos], []):
                if len(mov) == 2:
                    origem, destino = mov
                    # Descobrir a peça capturada
                    dr, dc = destino[0] - origem[0], destino[1] - origem[1]
                    capturada = (origem[0] + dr // 2, origem[1] + dc // 2)
                    capturas_trad.add((origem, destino, capturada))
            if capturas_bitboard != capturas_trad:
                logger.info(f"Divergência de capturas para a peça {pos} cor {cor}:")
                logger.info(f"  Bitboard: {capturas_bitboard}")
                logger.info(f"  Tradicional: {capturas_trad}")
                ok = False
        if ok:
            logger.info(f"Validação de capturas simples via bitboard OK para cor {cor}.")
        else:
            logger.info(f"Validação de capturas simples via bitboard FALHOU para cor {cor}.")
        return ok

    @staticmethod
    def clear_lsb(bb: int) -> int:
        """Remove o bit menos significativo ligado de um bitboard."""
        return bb & (bb - 1)

def main():
    """Função principal para testar os bitboards e a validação de movimentos."""
    tab = Tabuleiro()
    
    # Imprimir os bitboards iniciais
    logger.info("=== Bitboards Iniciais ===")
    tab.print_bitboards_hex()
    logger.info("\n=== Representação Visual ===")
    tab.print_all_bitboards()
    
    # Testar a geração de movimentos simples
    logger.info("\n=== Validação de Movimentos Simples ===")
    logger.info("Validando movimentos para BRANCO:")
    tab.validar_movimentos_simples(BRANCO)
    
    logger.info("\nValidando movimentos para PRETO:")
    tab.validar_movimentos_simples(PRETO)
    
    # Mostrar exemplo de movimentos gerados
    logger.info("\n=== Exemplo de Movimentos Simples para BRANCO ===")
    movs_branco = tab.gera_movimentos_simples(BRANCO)
    for i, (origem, destino) in enumerate(movs_branco[:5]):  # Mostrar apenas os 5 primeiros
        logger.info(f"Movimento {i+1}: {origem} -> {destino}")

    # Testar a validação de capturas simples via bitboards
    logger.info("\n=== Validação de Capturas Simples via Bitboards ===")
    tab._validar_capturas_bitboard(BRANCO)
    tab._validar_capturas_bitboard(PRETO)

if __name__ == "__main__":
    main()
    