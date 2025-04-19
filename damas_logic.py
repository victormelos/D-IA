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

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.WARNING
)

# --- Constantes ---
BRANCO = 1; PRETO = -1; VAZIO = 0; PEDRA = 1; DAMA = 2; PB = 1; PP = -1; DB = 2; DP = -2
DIRECOES_PEDRA = {BRANCO: [(-1, -1), (-1, 1)], PRETO: [(1, -1), (1, 1)]}
DIRECOES_CAPTURA_PEDRA = [(-1,-1),(-1,1),(1,-1),(1,1)] # Mantido para referência
DIRECOES_DAMA = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
TAMANHO_TABULEIRO = 8
PROFUNDIDADE_IA = 12 # Profundidade máxima (aumentada)
TEMPO_PADRAO_IA = 25.0 # Tempo padrão em segundos (ajustado para garantir até 25s)

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
    def __init__(self, estado_inicial: bool = True):
        self.max_depth_reached = 0
        self._depth_warning_emitted = False
        self.grid = [[VAZIO] * TAMANHO_TABULEIRO for _ in range(TAMANHO_TABULEIRO)]
        self.casas_centro = {(r, c) for r in range(2, 6) for c in range(2, 6)}
        self.casas_centro_expandido = {(2,1),(2,3),(2,5),(3,2),(3,4),(4,3),(4,5),(5,2),(5,4),(5,6)}
        self.hash_atual: int = 0
        self.damas_recem_promovidas: Set[Posicao] = set()  # Conjunto para rastrear posições de damas recém-promovidas
        self._cache_capturas = {}  # Cache local para capturas
        if estado_inicial: self.configuracao_inicial(); self.hash_atual = self.calcular_hash_zobrist_inicial()

    def limpar_cache_capturas(self):
        self._cache_capturas.clear()

    def configuracao_inicial(self):
        for r in range(TAMANHO_TABULEIRO):
            for c in range(TAMANHO_TABULEIRO):
                if (r+c)%2!=0: self.grid[r][c]=PP if r<3 else (PB if r>4 else VAZIO)
                else: self.grid[r][c]=VAZIO
        self.limpar_cache_capturas()

    def calcular_hash_zobrist_inicial(self) -> int:
        h=0;
        for r in range(TAMANHO_TABULEIRO):
            for c in range(TAMANHO_TABULEIRO):
                p=self.grid[r][c];
                if p != VAZIO: h ^= ZOBRIST_TABELA[r][c][Peca.get_zobrist_indice(p)]
        return h

    def _atualizar_hash_zobrist(self, r: int, c: int, v: int):
         if self.is_valido(r,c): self.hash_atual ^= ZOBRIST_TABELA[r][c][Peca.get_zobrist_indice(v)]

    def _atualizar_hash_turno(self): self.hash_atual ^= ZOBRIST_VEZ_PRETA

    def __repr__(self) -> str:
        h="  "+" ".join(chr(ord('a')+i) for i in range(TAMANHO_TABULEIRO))+" "; l=[h];
        for r in range(TAMANHO_TABULEIRO): l.append(f"{TAMANHO_TABULEIRO-r:<2}"+"".join(Peca.get_char(self.grid[r][c])+" " for c in range(TAMANHO_TABULEIRO))+f"{TAMANHO_TABULEIRO-r:<2}");
        l.append(h); return "\n".join(l)
    def get_peca(self, p: Posicao)->int: r,c=p; return self.grid[r][c] if self.is_valido(r,c) else VAZIO

    def set_peca(self, p: Posicao, v: int):
        r,c=p;
        if self.is_valido(r,c):
            pa=self.grid[r][c]
            if pa!=VAZIO: self._atualizar_hash_zobrist(r,c,pa)
            self.grid[r][c]=v
            if v!=VAZIO: self._atualizar_hash_zobrist(r,c,v)
            self.limpar_cache_capturas()

    def mover_peca(self, o: Posicao, d: Posicao):
        p=self.get_peca(o)
        self.set_peca(o, VAZIO)
        self.set_peca(d, p)
        self.limpar_cache_capturas()

    def remover_peca(self, p: Posicao):
        self.set_peca(p, VAZIO)
        self.limpar_cache_capturas()

    @staticmethod
    def is_valido(r: int, c: int) -> bool: return 0<=r<TAMANHO_TABULEIRO and 0<=c<TAMANHO_TABULEIRO
    @staticmethod
    def get_oponente(cor: int) -> int: return PRETO if cor==BRANCO else BRANCO
    def get_posicoes_pecas(self, c: int) -> List[Posicao]: return [(r,col) for r in range(TAMANHO_TABULEIRO) for col in range(TAMANHO_TABULEIRO) if Peca.get_cor(self.grid[r][col])==c]

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
        all_capturas = []
        simples = []
        capturas_por_pos = {}
        for pos_i in self.get_posicoes_pecas(cor):
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
            return [seq for seq in all_capturas if len(seq)-1 == max_caps]
        if apenas_capturas:
            return []
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
        self.limpar_cache_capturas()
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
        self.limpar_cache_capturas()
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
                ameacada_2l = self.eh_peca_ameacada_em_2_lances(r, c)
                if ameacada_2l:
                    bonus += PENALIDADE_PECA_AMEACADA_2L
                    debug_piece['bônus']['PENALIDADE_PECA_AMEACADA_2L'] = PENALIDADE_PECA_AMEACADA_2L
                    val += PENALIDADE_PECA_AMEACADA_2L
                if self.tem_formacao_ponte(r, c):
                    bonus += BONUS_FORMACAO_PONTE
                    debug_piece['bônus']['BONUS_FORMACAO_PONTE'] = BONUS_FORMACAO_PONTE
                    val += BONUS_FORMACAO_PONTE
                if self.tem_formacao_lanca(r, c):
                    bonus += BONUS_FORMACAO_LANCA
                    debug_piece['bônus']['BONUS_FORMACAO_LANCA'] = BONUS_FORMACAO_LANCA
                    val += BONUS_FORMACAO_LANCA
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
            for info in debug_info:
                print(f"[DEBUG AVAL] Peça {info['tipo']} em {info['pos']}: ")
                for k, v in info['bônus'].items():
                    print(f"    {k}: {v}")
                print(f"    Score parcial bônus: {info['score_parcial']}")
        return score

    def avaliar_heuristica(self, cor_ref: int, debug_aval: bool = False) -> float:
        allied = self._heuristica_para_cor(cor_ref, debug_aval)
        opponent = self._heuristica_para_cor(self.get_oponente(cor_ref), False)
        return allied - opponent

    @staticmethod
    def pos_para_alg(p: Posicao)->str: r,c=p; return chr(ord('a')+c)+str(TAMANHO_TABULEIRO-r) if Tabuleiro.is_valido(r,c) else "Inv"
    @staticmethod
    def alg_para_pos(alg: str)->Optional[Posicao]: alg=alg.lower().strip(); return (lambda c,l: (l,c) if Tabuleiro.is_valido(l,c) else None)(ord(alg[0])-ord('a'), TAMANHO_TABULEIRO-int(alg[1])) if len(alg)==2 and 'a'<=alg[0]<='h' and '1'<=alg[1]<='8' else None

    def criar_copia(self) -> 'Tabuleiro':
        """Cria uma cópia profunda do tabuleiro atual."""
        nova_copia = Tabuleiro(estado_inicial=False)  # Cria um tabuleiro vazio
        nova_copia.grid = [linha[:] for linha in self.grid]  # Copia profunda da grade
        nova_copia.hash_atual = self.hash_atual
        nova_copia.damas_recem_promovidas = set(self.damas_recem_promovidas)  # Propaga flags de promoção
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
        """
        if not hasattr(self, '_cache_ameaca_2l'):
            self._cache_ameaca_2l = {}
        key = (self.hash_atual, r, c)
        if key in self._cache_ameaca_2l:
            return self._cache_ameaca_2l[key]
        cor_peca = Peca.get_cor(self.grid[r][c])
        if cor_peca == VAZIO:
            return False
        cor_oponente = self.get_oponente(cor_peca)
        # 1º lance: para cada movimento do oponente
        for mov1 in self.encontrar_movimentos_possiveis(cor_oponente):
            tab_temp1 = self.criar_copia()
            tab_temp1._fazer_lance(mov1, troca_turno=True)
            # 2º lance: para cada resposta do próprio jogador
            for mov_resp in tab_temp1.encontrar_movimentos_possiveis(cor_peca):
                tab_temp2 = tab_temp1.criar_copia()
                tab_temp2._fazer_lance(mov_resp, troca_turno=True)
                # Agora, o oponente tenta capturar em 2 lances
                for mov2 in tab_temp2.encontrar_movimentos_possiveis(cor_oponente):
                    capturas2 = tab_temp2.identificar_pecas_capturadas(mov2)
                    if (r, c) in capturas2:
                        result = True
                        self._cache_ameaca_2l[key] = result
                        return result
        result = False
        self._cache_ameaca_2l[key] = result
        return result

    def material_balance(self, cor_ref: int) -> float:
        """
        Retorna a diferença de material (pedras e damas) da cor `cor_ref`
        em relação ao oponente, usando apenas VALOR_PEDRA e VALOR_DAMA.
        """
        allied_p = 0
        allied_d = 0
        opp_p = 0
        opp_d = 0
        # Determina os valores das peças para a cor de referência e oponente
        if cor_ref == BRANCO:
            pedra_aliada, dama_aliada = PB, DB
            pedra_oponente, dama_oponente = PP, DP
        else:
            pedra_aliada, dama_aliada = PP, DP
            pedra_oponente, dama_oponente = PB, DB
        for r in range(TAMANHO_TABULEIRO):
            for c in range(TAMANHO_TABULEIRO):
                v = self.grid[r][c]
                if v == pedra_aliada:
                    allied_p += 1
                elif v == dama_aliada:
                    allied_d += 1
                elif v == pedra_oponente:
                    opp_p += 1
                elif v == dama_oponente:
                    opp_d += 1
        allied_score = allied_p * VALOR_PEDRA + allied_d * VALOR_DAMA
        opp_score = opp_p * VALOR_PEDRA + opp_d * VALOR_DAMA
        return allied_score - opp_score

    def chegou_para_promover(self, pos: Posicao, cor: int) -> bool:
        """Retorna True se a posição está na fileira de promoção para a cor dada."""
        l_promo = 0 if cor == BRANCO else TAMANHO_TABULEIRO - 1
        return pos[0] == l_promo

# --- Classe Partida ---
class Partida:
    def __init__(self, jogador_branco: str = "Humano", jogador_preto: str = "IA"):
        self.tabuleiro = Tabuleiro(); self.jogador_atual = BRANCO; self.movimentos_legais_atuais: List[Movimento] = []
        self.contador_lances_sem_progresso = 0; self.total_lances = 0; self.vencedor = None
        self.tipo_jogadores = {BRANCO: jogador_branco, PRETO: jogador_preto}; self._atualizar_movimentos_legais()
    def _atualizar_movimentos_legais(self):
        self.movimentos_legais_atuais = self.tabuleiro.encontrar_movimentos_possiveis(self.jogador_atual)
        if self.vencedor is None and not self.movimentos_legais_atuais:
             op = Tabuleiro.get_oponente(self.jogador_atual); self.vencedor = self.jogador_atual if not self.tabuleiro.get_posicoes_pecas(op) else op
             # print(f"[Partida] Fim detectado em _atualizar_movimentos_legais. Vencedor: {self.vencedor}")
    def _verificar_fim_de_jogo(self):
        if self.vencedor is not None: return True
        op = Tabuleiro.get_oponente(self.jogador_atual);
        if not self.tabuleiro.get_posicoes_pecas(op): self.vencedor = self.jogador_atual; print(f"[Partida] Fim (sem peças oponente)."); return True
        if self.contador_lances_sem_progresso >= 40: self.vencedor = VAZIO; print("[Partida] Fim (Empate)."); return True
        return False
    def trocar_turno(self): 
        # Primeiro armazena o jogador atual
        jogador_anterior = self.jogador_atual
        # Troca o turno
        self.jogador_atual = Tabuleiro.get_oponente(self.jogador_atual)
        # Agora limpa as damas recém-promovidas do jogador que vai jogar
        # (as que foram promovidas no turno anterior do mesmo jogador, quando o oponente jogou)
        self.tabuleiro.limpar_damas_recem_promovidas_por_cor(self.jogador_atual)
    def executar_lance_completo(self, movimento: Movimento) -> bool:
        if not self.movimentos_legais_atuais or movimento not in self.movimentos_legais_atuais:
            print(f"Erro: Mov inválido Partida: {movimento}"); return False
        jogador_antes = self.jogador_atual
        # Determinar se haverá troca de turno
        houve_captura = False
        foi_promovido = False
        tipo_final = None
        pos_final = movimento[-1]
        peca_final = self.tabuleiro.get_peca(pos_final)
        tipo_final = Peca.get_tipo(peca_final)
        # Verifica se há capturas possíveis a partir da posição final (combo)
        estado_desfazer = self.tabuleiro._fazer_lance(movimento, troca_turno=True)  # Default: troca_turno
        houve_captura = bool(estado_desfazer.pecas_capturadas)
        foi_movimento_pedra = (Peca.get_tipo(estado_desfazer.peca_movida_original) == PEDRA)
        foi_promovido = estado_desfazer.foi_promovido
        if houve_captura or foi_movimento_pedra:
            self.contador_lances_sem_progresso = 0
        else:
            self.contador_lances_sem_progresso += 1
        self.total_lances += 1
        if foi_promovido:
            print(f"[REGRA] Peça promovida a dama em {Tabuleiro.pos_para_alg(movimento[-1])}. Turno passa para o adversário.")
            # método único que troca de jogador _e_ limpa flags do jogador que vai jogar agora
            self.trocar_turno()
            self._atualizar_movimentos_legais()
            self._verificar_fim_de_jogo()
            return True
        if houve_captura:
            pos_final = movimento[-1]
            peca_final = self.tabuleiro.get_peca(pos_final)
            tipo_final = Peca.get_tipo(peca_final)
            capturas_combo = self.tabuleiro._encontrar_capturas_recursivo(pos_final, self.jogador_atual, tipo_final, [pos_final], [])
            if capturas_combo:
                # Combo: não troca turno nem hash
                self.movimentos_legais_atuais = [c for c in capturas_combo if len(c) > 1]
                # Refaz o lance sem troca de turno/hash
                self.tabuleiro._desfazer_lance(estado_desfazer)
                estado_desfazer = self.tabuleiro._fazer_lance(movimento, troca_turno=False)
                return True
        # fim de lance "normal" — troca e limpa flags de recém‑promovidas
        self.trocar_turno()
        self._atualizar_movimentos_legais()
        self._verificar_fim_de_jogo()
        return True

    def criar_copia(self) -> 'Partida':
        """Cria uma cópia profunda da partida atual."""
        copia = Partida(
            jogador_branco=self.tipo_jogadores[BRANCO], 
            jogador_preto=self.tipo_jogadores[PRETO]
        )
        copia.tabuleiro = self.tabuleiro.criar_copia()
        copia.jogador_atual = self.jogador_atual
        copia.contador_lances_sem_progresso = self.contador_lances_sem_progresso
        copia.total_lances = self.total_lances
        copia.vencedor = self.vencedor
        copia.movimentos_legais_atuais = [movimento[:] for movimento in self.movimentos_legais_atuais]
        return copia

# --- Classe MotorIA (Versão com Iterative Deepening + Time Management) ---
class MotorIA:
    def __init__(self, profundidade: int, tempo_limite: float = TEMPO_PADRAO_IA, debug_heur: bool = False, usar_lmr: bool = True):
        self.profundidade_maxima = profundidade
        self.tempo_limite = tempo_limite
        self.debug_heur = debug_heur
        self.usar_lmr = usar_lmr
        # Estatísticas
        self.nos_visitados = 0; self.nos_quiescence_visitados = 0; self.tt_hits = 0
        self.null_cuts = 0; self.null_attempts = 0
        self.lmr_attempts = 0; self.lmr_recalls = 0
        # Transposition table, killers, history
        self.transposition_table: OrderedDict[int,TTEntry] = OrderedDict()
        self.killer_moves = [[None,None] for _ in range(profundidade+1)]
        self.history_heuristic = defaultdict(int)
        self.MULTICUT_N = 4
        self.MULTICUT_K = 2
        self.MULTICUT_R = 2
        self.multicuts_attempted = 0
        self.multicuts_cut = 0
        self.tempo_acabou = False
        # Inicializações ausentes
        self.tempo_por_nivel = {}
        self.profundidade_real_atingida = 0
        self.podas_alpha = 0
        self.podas_beta = 0
        # Monitoramento de profundidade global
        self.max_depth_reached = 0
        self._depth_warning_emitted = False

    def limpar_tt_e_historico(self):
        self.transposition_table.clear(); self.killer_moves = [[None,None] for _ in range(self.profundidade_maxima+1)]
        self.history_heuristic.clear(); self.null_cuts = 0; self.null_attempts = 0
        self.lmr_attempts = 0; self.lmr_recalls = 0
        self.tempo_acabou = False
        # *** reset de estatísticas de poda e tempo por nível ***
        self.podas_alpha = 0
        self.podas_beta  = 0
        self.tempo_por_nivel = {}

    def _formatar_movimento(self, mov: Movimento) -> str: return " -> ".join([Tabuleiro.pos_para_alg(p) for p in mov]) if mov else "N/A"
    def _mov_para_chave_history(self, mov: Movimento) -> Optional[Tuple[Posicao, Posicao]]: return (mov[0], mov[-1]) if mov and len(mov) >= 2 else None

    def verificar_tempo(self):
        if time.time() - self.tempo_inicio > self.tempo_limite:
            self.tempo_acabou = True
            return True
        return False

    def encontrar_melhor_movimento(self, partida, cor_ia, movimentos_legais):
        self.cor_ia = cor_ia
        if not movimentos_legais: print("[IA] Nenhum movimento legal."); return None
        if len(movimentos_legais) == 1: unico=movimentos_legais[0]; print(f"[IA] Movimento único: {self._formatar_movimento(unico)}"); return unico

        self.limpar_tt_e_historico(); self.tempo_inicio = time.time()
        self.nos_visitados = 0; self.nos_quiescence_visitados = 0; self.tt_hits = 0
        self.melhor_movimento_atual = movimentos_legais[0] # Movimento padrão caso tempo acabe muito rápido

        # Inicialização de Aspiration Windows
        self.melhor_score_prev = 0.0
        self.aspiration_delta = 15.0

        # print(f"\n[IA] Buscando melhor mov para {Peca.get_char(cor_ia)} (Iterative Deepening, max={self.profundidade_maxima}, t={self.tempo_limite}s)")
        # print(f"[IA] Tempo limite atingido. Usando melhor mov da prof {self.profundidade_completa}")
        # Trabalhar com uma cópia do tabuleiro para evitar modificações no original
        tab_copia = partida.tabuleiro.criar_copia()
        start_time_total = time.time()

        # Dicionário para armazenar pontuações dos movimentos em cada profundidade
        resultados_por_profundidade = {}
        
        # Implementação de Iterative Deepening
        for prof_atual in range(1, self.profundidade_maxima + 1):
            if self.tempo_acabou:
                print(f"[IA] Tempo limite atingido. Usando melhor mov da prof {self.profundidade_completa}")
                break

            # --- Aspiration Windows ---
            # Para profundidade 1, sempre janela total; só usa aspiration a partir de 2
            if prof_atual == 1:
                alpha, beta = -float('inf'), float('inf')
            else:
                alpha = self.melhor_score_prev - self.aspiration_delta
                beta  = self.melhor_score_prev + self.aspiration_delta
            alpha_asp = alpha
            beta_asp = beta

            tempo_inicio_prof = time.time()
            movs_avaliados = {}
            melhor_score_prof = -float('inf')
            melhor_mov_prof   = None

            cache_capturas_oponente = {}
            try:
                # Ordenação raiz para esta profundidade
                mov_caps_raiz = [m for m in movimentos_legais if len(tab_copia.identificar_pecas_capturadas(m)) > 0]
                mov_simples_raiz = [m for m in movimentos_legais if m not in mov_caps_raiz]

                # 1) MVV/LVA: custo zero, já joga as "boas" lá no topo
                mov_caps_raiz.sort(
                    key=lambda m: (
                        max(abs(v) for v in tab_copia.identificar_pecas_capturadas(m).values()), 
                        -abs(tab_copia.get_peca(m[0]))
                    ), 
                    reverse=True
                )

                # 2) SEE: refina ainda mais as K melhores
                K = 4
                top_k = mov_caps_raiz[:K]
                rest  = mov_caps_raiz[K:]
                top_k.sort(key=lambda m: self.see(tab_copia, m[-1], cor_ia), reverse=True)

                mov_caps_raiz = top_k + rest
                mov_simples_raiz.sort(key=lambda m: self.history_heuristic.get(self._mov_para_chave_history(m), 0), reverse=True)
                movs_ord_raiz = mov_caps_raiz + mov_simples_raiz

                # Usar último melhor movimento primeiro (se existir e não for captura)
                if self.melhor_movimento_atual in movs_ord_raiz:
                    movs_ord_raiz.remove(self.melhor_movimento_atual)
                    movs_ord_raiz = [self.melhor_movimento_atual] + movs_ord_raiz
                # Inserir TT-move no topo, se existir e for legal
                tt_entry = self.transposition_table.get(tab_copia.hash_atual)
                if tt_entry and tt_entry.melhor_movimento and tt_entry.melhor_movimento in movimentos_legais:
                    if tt_entry.melhor_movimento in movs_ord_raiz:
                        movs_ord_raiz.remove(tt_entry.melhor_movimento)
                    movs_ord_raiz = [tt_entry.melhor_movimento] + movs_ord_raiz

                # Busca principal com janela aspiration
                melhor_score_prof, melhor_mov_prof, movs_avaliados = self._search_root(
                    tab_copia, prof_atual, alpha, beta, movs_ord_raiz, cor_ia, cache_capturas_oponente)
                self.profundidade_completa = prof_atual
                resultados_por_profundidade[prof_atual] = movs_avaliados
                self.melhor_movimento_atual = melhor_mov_prof

                # Aspiration fail: relança com janela ampla
                if melhor_score_prof <= alpha_asp or melhor_score_prof >= beta_asp:
                    print(f"[IA] Aspiration fail na prof {prof_atual} (score={melhor_score_prof:.2f} fora de [{alpha_asp:.2f},{beta_asp:.2f}]), relançando com janela ampla")
                    melhor_score_prof, melhor_mov_prof, movs_avaliados = self._search_root(
                        tab_copia, prof_atual, -float('inf'), float('inf'), movs_ord_raiz, cor_ia, cache_capturas_oponente)
                    resultados_por_profundidade[prof_atual] = movs_avaliados
                    self.melhor_movimento_atual = melhor_mov_prof

                # Ajuste dinâmico do aspiration_delta com base na dispersão dos scores
                scores = list(movs_avaliados.values())
                if len(scores) > 1:
                    m = sum(scores) / len(scores)
                    var = sum((x - m) ** 2 for x in scores) / (len(scores) - 1)
                    stddev = math.sqrt(var)
                    self.aspiration_delta = max(2.0, min(30.0, stddev * 2.5))
                else:
                    # sem variação ou sem scores, manter delta padrão
                    self.aspiration_delta = 15.0

                # Atualiza melhor_score_prev para próxima profundidade
                self.melhor_score_prev = melhor_score_prof

                tempo_prof = time.time() - tempo_inicio_prof
                self.tempo_por_nivel[prof_atual] = tempo_prof
                # --- Estimativa de tempo para próxima profundidade ---
                if prof_atual > 1:
                    tempo_prev = self.tempo_por_nivel[prof_atual - 1]
                    taxa = tempo_prof / tempo_prev if tempo_prev > 0 else 1
                    estimativa_next = tempo_prof * min(taxa, 2)
                    tempo_restante = self.tempo_limite - (time.time() - self.tempo_inicio)
                    if estimativa_next > tempo_restante:
                        print(f"[IA] Estimativa de tempo para próxima profundidade ({estimativa_next:.2f}s) excede o tempo restante ({tempo_restante:.2f}s). Parando em {prof_atual}.")
                        break
            except TempoExcedidoError as e:
                print(f"[IA] {str(e)} na profundidade {prof_atual}")
                break
                
        end_time_total = time.time()
        
        # Mostrar último resultado completo
        if self.debug_heur and self.profundidade_completa > 0 and self.profundidade_completa in resultados_por_profundidade:
            print(f"\n[IA] Avaliação final (profundidade {self.profundidade_completa}):")
            res_ord = sorted(resultados_por_profundidade[self.profundidade_completa].items(), key=lambda item: item[1], reverse=True)
            for mov_s, score_m in res_ord[:5]: # Mostrar apenas os 5 melhores para não poluir
                print(f"  - Movimento: {mov_s:<15} -> Score: {score_m:.3f}")
                
        if self.melhor_movimento_atual:
            if self.debug_heur:
                print(f"\n[IA] Escolhido: {self._formatar_movimento(self.melhor_movimento_atual)} (Prof: {self.profundidade_completa})")
        else:
            if self.debug_heur:
                print("[IA] Nenhum movimento válido encontrado/escolhido.")
            self.melhor_movimento_atual = random.choice(movimentos_legais) if movimentos_legais else None
            
        # Estatísticas detalhadas
        if self.debug_heur:
            print(f"[IA] Nós (Minimax): {self.nos_visitados}, (Quiescence): {self.nos_quiescence_visitados}, TT Hits: {self.tt_hits}")
            print(f"[IA] Profundidade Máxima Configurada: {self.profundidade_maxima}, Profundidade Completada: {self.profundidade_completa}")
            print(f"[IA] Profundidade Real Atingida: {self.profundidade_real_atingida}")
            print(f"[IA] Podas Alpha: {self.podas_alpha}, Podas Beta: {self.podas_beta}")
            print(f"[IA] Tempo Total da Busca: {end_time_total - start_time_total:.2f}s")
            print(f"[IA] Média de nós por segundo: {(self.nos_visitados + self.nos_quiescence_visitados) / max(0.001, end_time_total - start_time_total):.0f}")
            print("-" * 30)

        # Instrumentação: heurística pura para cada root move
        print("=== Heurística pura (depth=0) para cada root move ===")
        for mov in movimentos_legais:
            estado = tab_copia._fazer_lance(mov, troca_turno=True)
            val = tab_copia.avaliar_heuristica(cor_ia, debug_aval=False)
            tab_copia._desfazer_lance(estado)
            print(f"  {self._formatar_movimento(mov):10} -> {val:.3f}")
        print("=============================================")

        # --- debug heurístico final ---
        if self.debug_heur:
            print("\n=== DEBUG HEURÍSTICO DO TABULEIRO ATUAL ===")
            mat = partida.tabuleiro.material_balance(cor_ia)
            stat = partida.tabuleiro.avaliar_heuristica(cor_ia, debug_aval=True)
            print(f"Material balance: {mat:.2f}")
            print(f"Static eval   : {stat:.2f}")
            print(f"Heur extra    : {stat - mat:.2f}  (tudo o que não é só material)\n")
        return self.melhor_movimento_atual

    def minimax(self, tab, cont_emp, prof, alpha, beta, jog, cor_ia, depth=0):
        # 1) verificação de tempo
        if self.verificar_tempo():
            raise TempoExcedidoError("Tempo excedido durante minimax")
        # Chamada de quiescência quando prof <= 0
        if prof <= 0:
            return self.quiescence_search(tab, MAX_QUIESCENCE_DEPTH, alpha, beta, jog, cor_ia, depth)
        self.nos_visitados += 1
        # Monitoramento de profundidade global
        if depth > self.max_depth_reached:
            self.max_depth_reached = depth
            if self.debug_heur and not self._depth_warning_emitted and depth > 900:
                logging.warning(f"Alerta de profundidade: {depth}")
                self._depth_warning_emitted = True
        # Atualizar profundidade real atingida
        if depth > self.profundidade_real_atingida:
            self.profundidade_real_atingida = depth
        # TT lookup, quiescência, etc...
        # --- Null-move pruning (usando helper) ---
        if self.can_null_move(tab, jog, prof):
            self.null_attempts += 1
            R = self.null_move_reduction(prof)
            tab._atualizar_hash_turno()  # simula passe
            score = -self.minimax(tab, cont_emp, prof-R-1, -beta, -beta+1, Tabuleiro.get_oponente(jog), cor_ia, depth=depth+1)
            tab._atualizar_hash_turno()
            if score >= beta:
                self.null_cuts += 1
                self.podas_beta += 1
                return beta

        movs = tab.encontrar_movimentos_possiveis(jog)
        # Futility pruning: só em prof == 1, sem forcing moves, margem dinâmica
        if prof == 1:
            has_forcing_moves = any(len(tab.identificar_pecas_capturadas(m)) > 0 for m in movs)
            if not has_forcing_moves:
                margin = self.futility_margin(prof)
                static = tab.avaliar_heuristica(cor_ia)
                movs_antes = len(movs)
                movs = [m for m in movs if len(tab.identificar_pecas_capturadas(m)) > 0 or static + margin > alpha]
                # Se descartamos movimentos, contamos como poda alpha
                if len(movs) < movs_antes:
                    self.podas_alpha += 1

        # Ordenação: TT, killer, captures, history
        movs_ordenados = []
        melhor_mov_tt = None
        entry = self.transposition_table.get(tab.hash_atual)
        if entry and entry.melhor_movimento and entry.melhor_movimento in movs:
            melhor_mov_tt = entry.melhor_movimento
            movs_ordenados.append(melhor_mov_tt)
            movs.remove(melhor_mov_tt)
        kd = self.profundidade_maxima - prof
        killer_list = []
        if kd >= 0 and kd < len(self.killer_moves):
            for kmov in self.killer_moves[kd]:
                if kmov is not None and kmov in movs:
                    killer_list.append(kmov)
                    movs.remove(kmov)
        movs_ordenados.extend(killer_list)
        mov_caps = [m for m in movs if len(tab.identificar_pecas_capturadas(m)) > 0]
        # MVV/LVA
        mov_caps.sort(
            key=lambda m: (
                max(abs(v) for v in tab.identificar_pecas_capturadas(m).values()), 
                -abs(tab.get_peca(m[0]))
            ), 
            reverse=True
        )
        # SEE refine
        K = 4
        top_k = mov_caps[:K]
        rest  = mov_caps[K:]
        top_k.sort(key=lambda m: self.see(tab, m[-1], self.cor_ia), reverse=True)
        mov_caps = top_k + rest
        mov_nao_caps = [m for m in movs if m not in mov_caps]
        mov_nao_caps.sort(key=lambda m: self.history_heuristic.get((m[0], m[-1]), 0), reverse=True)
        movs_ordenados.extend(mov_caps)
        movs_ordenados.extend(mov_nao_caps)

        # --- Multi-Cut Pruning (usando helper) ---
        # Ajuste dinâmico dos parâmetros
        N = min(self.MULTICUT_N, max(2, len(movs_ordenados)//3))
        K = min(self.MULTICUT_K, N)
        R = 2 if prof < 8 else 3
        if self.can_multi_cut(prof, movs_ordenados):
            self.multicuts_attempted += 1
            beta_cut_count = 0
            multicut_cache = {}
            for mov in movs_ordenados[:N]:
                key = tuple(mov)  # usa tupla, que é hashable
                if key in multicut_cache:
                    score = multicut_cache[key]
                else:
                    score = -self.minimax(tab, cont_emp, prof-R, -beta, -beta+1, Tabuleiro.get_oponente(jog), cor_ia, depth=depth+1)
                    multicut_cache[key] = score
                if score >= beta:
                    beta_cut_count += 1
                    if beta_cut_count >= K:
                        self.multicuts_cut += 1
                        self.podas_beta += 1
                        return beta

        melhor_val = -float('inf'); a_orig = alpha
        LMR_THRESHOLD = 2
        LMR_MARGIN = VALOR_PEDRA * 1.5  # fácil de ajustar
        best_move_tt = None
        for i, mov in enumerate(movs_ordenados):
            # Checagem de tempo periódica (agora a cada 8 movimentos)
            if i % 8 == 0 and self.verificar_tempo():
                raise TempoExcedidoError("Tempo excedido durante minimax")
            # 2.1) detecta se houve captura e se ainda há combo possível
            caps_origem = tab.identificar_pecas_capturadas(mov)
            continuacoes = []
            if caps_origem:
                continuacoes = tab._encontrar_capturas_recursivo(
                    mov[-1],
                    jog,                              # o jogador atual
                    Peca.get_tipo(tab.get_peca(mov[-1])),
                    [mov[-1]], []
                )
            # 2.2) só troca de turno se NÃO tiver combo
            troca = not (caps_origem and continuacoes)
            # 2.3) faz o lance usando a flag certa
            estado = tab._fazer_lance(mov, troca_turno=troca)

            # --- Recalcula extensão a partir do zero ---
            is_promo = (Peca.get_tipo(tab.get_peca(mov[-1])) == PEDRA and tab.chegou_para_promover(mov[-1], jog))
            is_capture = bool(caps_origem)
            extension = 2 if is_promo else (1 if is_capture else 0)
            # Extensão tática: dupla-ameaça
            # caps_ia = tab.encontrar_movimentos_possiveis(self.cor_ia, apenas_capturas=True)
            # if len(caps_ia) >= 3:  # ajuste esse número conforme desejado
            #     extension += 1
            # Bloqueio total do oponente
            # movs_op = tab.encontrar_movimentos_possiveis(Tabuleiro.get_oponente(jog))
            # if not movs_op:
            #     extension += 2
            # elif len(movs_op) <= 2:
            #     extension += 1
            # Log de depuração das extensões
            logging.debug(f"[EXT] mov={self._formatar_movimento(mov)} ext={extension}")

            # Ajusta profundidade
            next_prof = prof - 1 + extension
            next_prof = max(0, min(next_prof, self.profundidade_maxima))
            static_eval = tab.avaliar_heuristica(self.cor_ia)
            # --- Principal Variation Search (PVS) ---
            if i == 0:
                # PV move: busca full-window
                score = -self.minimax(tab, cont_emp, next_prof, -beta, -alpha, Tabuleiro.get_oponente(jog), self.cor_ia, depth=depth+1)
            else:
                # LMR só em não-PV, não-captura, heurística fria
                do_lmr = self.lmr_reduction(prof, i) > 0 and not is_capture and static_eval + LMR_MARGIN <= alpha
                if do_lmr:
                    self.lmr_attempts += 1
                    R_lmr = self.lmr_reduction(prof, i)
                    # pesquisa rasa adaptativa, zero-window
                    score = -self.minimax(tab, cont_emp, next_prof-R_lmr, -alpha-1, -alpha, Tabuleiro.get_oponente(jog), self.cor_ia, depth=depth+1)
                    if score > alpha:
                        self.lmr_recalls += 1
                        # pesquisa normal completa, zero-window
                        score = -self.minimax(tab, cont_emp, next_prof, -alpha-1, -alpha, Tabuleiro.get_oponente(jog), self.cor_ia, depth=depth+1)
                else:
                    # Zero-window search
                    score = -self.minimax(tab, cont_emp, next_prof, -alpha-1, -alpha, Tabuleiro.get_oponente(jog), self.cor_ia, depth=depth+1)
                # Se passar alpha, relance full-window
                if score > alpha:
                    score = -self.minimax(tab, cont_emp, next_prof, -beta, -alpha, Tabuleiro.get_oponente(jog), self.cor_ia, depth=depth+1)
            # Desfaz o lance
            tab._desfazer_lance(estado)

            if score > melhor_val:
                melhor_val = score
                best_move_tt = mov
                # Atualiza history heuristic para o movimento
                chave_hist = (mov[0], mov[-1])
                self.history_heuristic[chave_hist] += prof * prof
            alpha = max(alpha, melhor_val)
            if beta <= alpha:
                # Atualiza killer moves no beta-cut
                self.podas_beta += 1
                if kd >= 0 and kd < len(self.killer_moves):
                    if mov not in self.killer_moves[kd]:
                        self.killer_moves[kd][1] = self.killer_moves[kd][0]
                        self.killer_moves[kd][0] = mov
                break

        # Preencher a transposition table (TT)
        flag = 0  # TT_FLAG_EXACT
        if melhor_val <= a_orig:
            flag = 2  # TT_FLAG_UPPERBOUND
        elif melhor_val >= beta:
            flag = 1  # TT_FLAG_LOWERBOUND
        self.transposition_table[tab.hash_atual] = TTEntry(
            profundidade=prof,
            score=melhor_val,
            flag=flag,
            melhor_movimento=best_move_tt
        )

        return melhor_val

    def quiescence_search(self, tab: Tabuleiro, prof_q: int, a: float, b: float, jog_q: int, cor_ia: int, depth=0) -> float:
        # Checagem de tempo no início da quiescência
        if self.verificar_tempo():
            raise TempoExcedidoError("Tempo excedido durante quiescence_search")
        # Monitoramento de profundidade global
        if depth > self.max_depth_reached:
            self.max_depth_reached = depth
            if depth > 900 and not self._depth_warning_emitted:
                logging.warning(f"Alerta de profundidade (quiescence): {depth}")
                self._depth_warning_emitted = True
        # Verificar tempo periodicamente (a cada 500 nós de quiescence)
        if self.nos_quiescence_visitados % 500 == 0 and self.verificar_tempo():
            raise TempoExcedidoError("Tempo excedido durante quiescence_search")
        hash_pos = tab.hash_atual
        entry = self.transposition_table.get(hash_pos)
        if entry and entry.flag == TT_FLAG_EXACT and entry.profundidade >= -1 : self.tt_hits+=1; return entry.score
        self.nos_quiescence_visitados += 1
        stand_pat = tab.avaliar_heuristica(cor_ia, debug_aval=False)
        mov_caps = tab.encontrar_movimentos_possiveis(jog_q, apenas_capturas=True)
        # Cache local para capturas e peça de origem
        capturadas_cache = {tuple(m): tab.identificar_pecas_capturadas(m) for m in mov_caps}
        peca_origem_cache = {tuple(m): tab.get_peca(m[0]) for m in mov_caps}
        # Ordenação híbrida MVV/LVA + SEE para capturas na quiescence
        mov_caps.sort(
            key=lambda m: (
                max(abs(v) for v in capturadas_cache[tuple(m)].values()) if capturadas_cache[tuple(m)] else 0,
                -abs(peca_origem_cache[tuple(m)])
            ),
            reverse=True
        )
        K = 4
        top_k = mov_caps[:K]
        rest = mov_caps[K:]
        # Cache para SEE (opcional, mas recomendado se top_k for grande)
        see_cache = {tuple(m): self.see(tab, m[-1], jog_q) for m in top_k}
        top_k.sort(key=lambda m: see_cache[tuple(m)], reverse=True)
        mov_caps = top_k + rest
        # SEE completo para cortes
        def see_gain(tab, mov, jog_q):
            pos = mov[-1]
            return self.see(tab, pos, jog_q)
        if mov_caps:
            def valor_captura(m):
                capturadas = tab.identificar_pecas_capturadas(m)
                if not capturadas:
                    return 0
                atacante = tab.get_peca(m[0])
                tipo_atacante = abs(atacante)
                valor = 0
                for v in capturadas.values():
                    tipo_capturado = abs(v)
                    if tipo_capturado == DAMA and tipo_atacante == PEDRA:
                        valor += VALOR_DAMA + 10  # Pedra captura dama: ótimo
                    elif tipo_capturado == DAMA and tipo_atacante == DAMA:
                        valor += VALOR_DAMA
                    elif tipo_capturado == PEDRA:
                        valor += VALOR_PEDRA
                return valor
            max_gain = max(valor_captura(m) for m in mov_caps)
            if stand_pat + max_gain <= a:
                self.podas_alpha += 1
                return stand_pat
        if prof_q <= 0: return stand_pat
        is_max = (jog_q == cor_ia)
        if is_max: a = max(a, stand_pat)
        else: b = min(b, stand_pat)
        if b <= a: 
            self.podas_beta += 1
            return stand_pat
        if not mov_caps: return stand_pat
        score_final_q = stand_pat
        if is_max:
            for mov in mov_caps:
                # SEE pruning completo
                if see_gain(tab, mov, jog_q) + stand_pat <= a:
                    continue
                cp=bool(tab.identificar_pecas_capturadas(mov))
                pos_final = mov[-1]
                peca_final = tab.get_peca(pos_final)
                tipo_final = Peca.get_tipo(peca_final)
                capturas_combo = tab.encontrar_movimentos_possiveis(jog_q, apenas_capturas=True) if cp else []
                troca_turno = not (cp and capturas_combo)
                estado_d = tab._fazer_lance(mov, troca_turno=troca_turno)
                if cp and capturas_combo:
                    prox_prof_q = prof_q
                    prox_jog = jog_q
                else:
                    prox_prof_q = prof_q - 1
                    prox_jog = Tabuleiro.get_oponente(jog_q)
                # Extensão para combos (captura múltipla)
                is_combo = len(tab.identificar_pecas_capturadas(mov)) > 1
                ext = 1 if is_combo else 0
                next_q = prox_prof_q + ext
                next_q = min(next_q, MAX_QUIESCENCE_DEPTH)  # Proteção contra profundidade excessiva
                val = self.quiescence_search(tab, next_q, a, b, prox_jog, cor_ia, depth=depth+1)
                tab._desfazer_lance(estado_d)
                score_final_q = max(score_final_q, val); a = max(a, score_final_q)
                if b <= a: 
                    self.podas_beta += 1
                    break
        else:
            for mov in mov_caps:
                # SEE pruning completo
                if see_gain(tab, mov, jog_q) + stand_pat <= a:
                    continue
                cp=bool(tab.identificar_pecas_capturadas(mov))
                pos_final = mov[-1]
                peca_final = tab.get_peca(pos_final)
                tipo_final = Peca.get_tipo(peca_final)
                capturas_combo = tab.encontrar_movimentos_possiveis(jog_q, apenas_capturas=True) if cp else []
                troca_turno = not (cp and capturas_combo)
                estado_d = tab._fazer_lance(mov, troca_turno=troca_turno)
                if cp and capturas_combo:
                    prox_prof_q = prof_q
                    prox_jog = jog_q
                else:
                    prox_prof_q = prof_q - 1
                    prox_jog = Tabuleiro.get_oponente(jog_q)
                # Extensão para combos (captura múltipla)
                is_combo = len(tab.identificar_pecas_capturadas(mov)) > 1
                ext = 1 if is_combo else 0
                next_q = prox_prof_q + ext
                next_q = min(next_q, MAX_QUIESCENCE_DEPTH)  # Proteção contra profundidade excessiva
                val = self.quiescence_search(tab, next_q, a, b, prox_jog, cor_ia, depth=depth+1)
                tab._desfazer_lance(estado_d)
                score_final_q = min(score_final_q, val); b = min(b, score_final_q)
                if b <= a: 
                    self.podas_beta += 1
                    break
        return score_final_q

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
        total_pedras = sum(1 for r in range(TAMANHO_TABULEIRO) for c in range(TAMANHO_TABULEIRO)
                           if abs(tab.grid[r][c]) == PEDRA)
        total_damas = sum(1 for r in range(TAMANHO_TABULEIRO) for c in range(TAMANHO_TABULEIRO)
                          if abs(tab.grid[r][c]) == DAMA)
        return total_pedras <= 2 or (total_pedras + total_damas) <= self.ENDGAME_PIECES

    def has_few_pieces(self, tab):
        total = sum(1 for r in range(TAMANHO_TABULEIRO) for c in range(TAMANHO_TABULEIRO) if tab.grid[r][c] != 0)
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

# --- Bloco Principal (Teste) ---
if __name__ == "__main__":
    print("--- Testando damas_logic.py v12.3 Iterative Deepening + Time Management ---")
    partida_teste = Partida(jogador_branco="IA", jogador_preto="Humano")
    # POSIÇÃO COMPLEXA DE TESTE (ajustada para garantir movimentos válidos)
    tab = partida_teste.tabuleiro
    tab.grid = [[0]*8 for _ in range(8)]
    # Brancas
    tab.grid[2][1] = PB
    tab.grid[2][3] = PB
    tab.grid[3][2] = PB
    tab.grid[4][5] = DB
    tab.grid[5][0] = PB
    tab.grid[5][4] = PB
    tab.grid[6][3] = DB
    # Pretas
    tab.grid[1][2] = PP
    tab.grid[1][4] = PP
    tab.grid[2][5] = DP
    tab.grid[3][4] = PP
    tab.grid[4][1] = DP
    tab.grid[5][6] = PP
    tab.grid[6][5] = DP
    tab.grid[7][2] = PP
    tab.grid[7][4] = PP
    tab.grid[7][6] = PP
    # Espaços para garantir mobilidade
    tab.grid[4][3] = 0
    tab.grid[3][6] = 0
    tab.grid[5][2] = 0
    tab.grid[6][1] = 0
    tab.hash_atual = tab.calcular_hash_zobrist_inicial()
    print(f"Profundidade Máxima de Teste: {PROFUNDIDADE_IA}, Tempo Limite: {TEMPO_PADRAO_IA}s")
    print("Tabuleiro de teste complexo:"); print(tab)
    print("Movimentos legais para as brancas:", tab.encontrar_movimentos_possiveis(BRANCO))
    if partida_teste.jogador_atual == BRANCO:
        print("\n[COM LMR] Calculando movimento inicial para Brancas...")
        ia_lmr = MotorIA(profundidade=PROFUNDIDADE_IA, tempo_limite=TEMPO_PADRAO_IA, debug_heur=True, usar_lmr=True)
        start_time_lmr = time.time()
        mov_lmr = ia_lmr.encontrar_melhor_movimento(
            partida_teste,
            BRANCO,
            partida_teste.movimentos_legais_atuais
        )
        end_time_lmr = time.time()
        print(f"\n[COM LMR] Tempo de cálculo: {end_time_lmr - start_time_lmr:.2f}s")
        if mov_lmr: print(f"[COM LMR] Movimento Sugerido: {ia_lmr._formatar_movimento(mov_lmr)}")
        else: print("[COM LMR] IA não encontrou movimento.")
        print(f"[COM LMR] Nós Visitados (Minimax): {ia_lmr.nos_visitados}")
        print(f"[COM LMR] Nós Visitados (Quiescence): {ia_lmr.nos_quiescence_visitados}")
        print(f"[COM LMR] Profundidade Completada: {ia_lmr.profundidade_completa}")
        print(f"[COM LMR] Profundidade Real Atingida: {ia_lmr.profundidade_real_atingida}")
        print(f"[COM LMR] TT Hits: {ia_lmr.tt_hits}")
        print(f"[COM LMR] Podas Alpha: {ia_lmr.podas_alpha}")
        print(f"[COM LMR] Podas Beta: {ia_lmr.podas_beta}")
        print(f"[COM LMR] Nós por segundo: {(ia_lmr.nos_visitados + ia_lmr.nos_quiescence_visitados) / max(0.001, end_time_lmr - start_time_lmr):.0f}")

        print("\n[SEM LMR] Calculando movimento inicial para Brancas...")
        ia_nolmr = MotorIA(profundidade=PROFUNDIDADE_IA, tempo_limite=TEMPO_PADRAO_IA, debug_heur=True, usar_lmr=False)
        start_time_nolmr = time.time()
        mov_nolmr = ia_nolmr.encontrar_melhor_movimento(
            partida_teste,
            BRANCO,
            partida_teste.movimentos_legais_atuais
        )
        end_time_nolmr = time.time()
        print(f"\n[SEM LMR] Tempo de cálculo: {end_time_nolmr - start_time_nolmr:.2f}s")
        if mov_nolmr: print(f"[SEM LMR] Movimento Sugerido: {ia_nolmr._formatar_movimento(mov_nolmr)}")
        else: print("[SEM LMR] IA não encontrou movimento.")
        print(f"[SEM LMR] Nós Visitados (Minimax): {ia_nolmr.nos_visitados}")
        print(f"[SEM LMR] Nós Visitados (Quiescence): {ia_nolmr.nos_quiescence_visitados}")
        print(f"[SEM LMR] Profundidade Completada: {ia_nolmr.profundidade_completa}")
        print(f"[SEM LMR] Profundidade Real Atingida: {ia_nolmr.profundidade_real_atingida}")
        print(f"[SEM LMR] TT Hits: {ia_nolmr.tt_hits}")
        print(f"[SEM LMR] Podas Alpha: {ia_nolmr.podas_alpha}")
        print(f"[SEM LMR] Podas Beta: {ia_nolmr.podas_beta}")
        print(f"[SEM LMR] Nós por segundo: {(ia_nolmr.nos_visitados + ia_nolmr.nos_quiescence_visitados) / max(0.001, end_time_nolmr - start_time_nolmr):.0f}")

        print("\n=== COMPARATIVO LMR x SEM LMR ===")
        print(f"Tempo (LMR): {end_time_lmr - start_time_lmr:.2f}s | (SEM LMR): {end_time_nolmr - start_time_nolmr:.2f}s")
        print(f"Nós (LMR): {ia_lmr.nos_visitados} | (SEM LMR): {ia_nolmr.nos_visitados}")
        print(f"Quiescence (LMR): {ia_lmr.nos_quiescence_visitados} | (SEM LMR): {ia_nolmr.nos_quiescence_visitados}")
        print(f"Profundidade Completada (LMR): {ia_lmr.profundidade_completa} | (SEM LMR): {ia_nolmr.profundidade_completa}")
        print(f"Movimento Sugerido (LMR): {ia_lmr._formatar_movimento(mov_lmr)} | (SEM LMR): {ia_nolmr._formatar_movimento(mov_nolmr)}")
        print(f"Score final (LMR): {ia_lmr.melhor_score_prev:.2f} | (SEM LMR): {ia_nolmr.melhor_score_prev:.2f}")
    print("\n--- Fim do Teste ---")
    