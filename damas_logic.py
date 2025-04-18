# -*- coding: utf-8 -*-
# damas_logic.py (v12.3: Iterative Deepening + Time Management)

import copy
import time
import random
from typing import List, Tuple, Optional, Dict, Set, NamedTuple
from collections import defaultdict

# --- Constantes ---
BRANCO = 1; PRETO = -1; VAZIO = 0; PEDRA = 1; DAMA = 2; PB = 1; PP = -1; DB = 2; DP = -2
DIRECOES_PEDRA = {BRANCO: [(-1, -1), (-1, 1)], PRETO: [(1, -1), (1, 1)]}
DIRECOES_CAPTURA_PEDRA = [(-1,-1),(-1,1),(1,-1),(1,1)] # Mantido para referência
DIRECOES_DAMA = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
TAMANHO_TABULEIRO = 8
PROFUNDIDADE_IA = 12 # Profundidade máxima (aumentada)
TEMPO_PADRAO_IA = 25.0 # Tempo padrão em segundos (ajustado para garantir até 25s)
TEMPO_MIN_PROFUNDIDADE = 0.1 # Tempo mínimo para completar uma profundidade (segundos)

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
EXTENSAO_CAPTURA = 1  # Pode ajustar para 2 se quiser mais agressivo

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

    def mover_peca(self, o: Posicao, d: Posicao): p=self.get_peca(o); self.set_peca(o, VAZIO); self.set_peca(d, p)
    def remover_peca(self, p: Posicao): self.set_peca(p, VAZIO)
    @staticmethod
    def is_valido(r: int, c: int) -> bool: return 0<=r<TAMANHO_TABULEIRO and 0<=c<TAMANHO_TABULEIRO
    @staticmethod
    def get_oponente(cor: int) -> int: return PRETO if cor==BRANCO else BRANCO
    def get_posicoes_pecas(self, c: int) -> List[Posicao]: return [(r,col) for r in range(TAMANHO_TABULEIRO) for col in range(TAMANHO_TABULEIRO) if Peca.get_cor(self.grid[r][col])==c]

    def _encontrar_capturas_recursivo(self, pos_a: Posicao, cor: int, tipo: int, cam_a: Movimento, caps_cam: list) -> List[Movimento]:
        key = (self.hash_atual, pos_a, cor, tipo, tuple(sorted(caps_cam)))
        if key in self._cache_capturas:
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
                    cont = self._encontrar_capturas_recursivo(pd, cor, tipo, novo_cam, novo_caps)
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
                            # verifica se todas as casas entre o inimigo (índice i) e o pouso (j) estão vazias
                            caminho_livre = True
                            for k in range(i+1, j):
                                interm = (pos_a[0] + k*dr, pos_a[1] + k*dc)
                                if self.get_peca(interm) != VAZIO:
                                    caminho_livre = False
                                    break
                            if caminho_livre and self.get_peca(pd) == VAZIO:
                                novo_cam = cam_a + [pd]
                                novo_caps = caps_cam + [pi]
                                # Reiniciar a recursão para todas as direções a partir de pd, exceto a direção de onde veio
                                cont = []
                                for dr2, dc2 in DIRECOES_DAMA:
                                    # Não volte para a casa de onde veio
                                    if (dr2, dc2) == (-dr, -dc):
                                        continue
                                    cont.extend(self._encontrar_capturas_recursivo(pd, cor, tipo, novo_cam, novo_caps))
                                if cont:
                                    seqs.extend(cont)
                                else:
                                    seqs.append(novo_cam)
                        break
                    elif peca_i != VAZIO:
                        break
        self._cache_capturas[key] = seqs
        return seqs

    def encontrar_movimentos_possiveis(self, cor: int, apenas_capturas: bool = False) -> List[Movimento]:
        all_capturas = []
        simples = []
        for pos_i in self.get_posicoes_pecas(cor):
            if pos_i in self.damas_recem_promovidas:
                continue
            pv = self.get_peca(pos_i)
            tipo = Peca.get_tipo(pv)
            caps_peca = self._encontrar_capturas_recursivo(pos_i, cor, tipo, [pos_i], [])
            if caps_peca:
                all_capturas.extend(caps_peca)
                pass
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
        o=mov[0]; d=mov[-1]; h_a=self.hash_atual; p_o=self.get_peca(o); c=Peca.get_cor(p_o); t_o=Peca.get_tipo(p_o)
        pc=self.identificar_pecas_capturadas(mov); self.mover_peca(o,d);
        for pos_c in pc: self.remover_peca(pos_c)
        pr=False; l_p=0 if c==BRANCO else TAMANHO_TABULEIRO-1;
        damas_adicionadas = set()
        if t_o==PEDRA and d[0]==l_p:
            nv=DB if c==BRANCO else DP;
            self.set_peca(d,nv);
            pr=True
            self.damas_recem_promovidas.add(d)
            damas_adicionadas.add(d)
        if troca_turno:
            self._atualizar_hash_turno()
        return EstadoLanceDesfazer(mov,p_o,pc,pr,h_a,damas_adicionadas, troca_turno)

    def _desfazer_lance(self, e: EstadoLanceDesfazer):
        self.hash_atual=e.hash_anterior; mov=e.movimento; o=mov[0]; d=mov[-1]; p_r=e.peca_movida_original
        self.grid[d[0]][d[1]]=VAZIO; self.grid[o[0]][o[1]]=p_r;
        for pos_c,val_c in e.pecas_capturadas.items(): self.grid[pos_c[0]][pos_c[1]] = val_c
        for pos in e.damas_recem_promovidas_adicionadas:
            if pos in self.damas_recem_promovidas:
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
                if self.tem_formacao_ponte(r, c) and self.detectar_bloqueio_avanco(r, c, cor_p):
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
        valor_caps = sum(VALOR_DAMA if abs(self.get_peca(m[0]))==DAMA else VALOR_PEDRA for m in caps)
        if valor_caps > 0:
            bonus += -valor_caps
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
        nova_copia.damas_recem_promovidas = set()  # Não propaga damas recém-promovidas para buscas
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
            self.damas_recem_promovidas.remove(pos)

    def eh_peca_vulneravel(self, r: int, c: int, cache_vulneravel: dict = None) -> bool:
        """
        Retorna True se a peça em (r, c) pode ser capturada
        no próximo lance do adversário (captura imediata).
        Usa cache local para evitar recomputação em nós de avaliação.
        """
        if cache_vulneravel is None:
            cache_vulneravel = {}
        chave = (self.hash_atual, r, c)
        if chave in cache_vulneravel:
            return cache_vulneravel[chave]
        cor_peca = Peca.get_cor(self.grid[r][c])
        if cor_peca == VAZIO:
            cache_vulneravel[chave] = False
            return False
        cor_oponente = self.get_oponente(cor_peca)
        posicoes_oponente = self.get_posicoes_pecas(cor_oponente)
        for pos_op in posicoes_oponente:
            peca_op = self.grid[pos_op[0]][pos_op[1]]
            tipo_op = Peca.get_tipo(peca_op)
            capturas_pos_op = self._encontrar_capturas_recursivo(pos_op, cor_oponente, tipo_op, [pos_op], [])
            for cap_seq in capturas_pos_op:
                pecas_capturadas = self.identificar_pecas_capturadas(cap_seq)
                if (r, c) in pecas_capturadas:
                    cache_vulneravel[chave] = True  # Early-exit e cache
                    return True
        cache_vulneravel[chave] = False
        return False

    def eh_peca_protegida(self, r: int, c: int) -> bool:
        """
        Retorna True se a peça em (r, c) está protegida,
        isto é, se qualquer captura do adversário que pegue essa peça
        resultaria em contra-captura imediata.
        """
        cor_peca = Peca.get_cor(self.grid[r][c])
        if cor_peca == VAZIO:
            return False
        cor_oponente = self.get_oponente(cor_peca)
        posicoes_oponente = self.get_posicoes_pecas(cor_oponente)
        for pos_op in posicoes_oponente:
            peca_op = self.grid[pos_op[0]][pos_op[1]]
            tipo_op = Peca.get_tipo(peca_op)
            capturas_pos_op = self._encontrar_capturas_recursivo(pos_op, cor_oponente, tipo_op, [pos_op], [])
            for cap_seq in capturas_pos_op:
                pecas_capturadas = self.identificar_pecas_capturadas(cap_seq)
                if (r, c) in pecas_capturadas:
                    # Essa jogada do adversário captura (r,c).
                    # Vamos simular no tabuleiro fictício
                    tab_temp = self.criar_copia()
                    state_desf = tab_temp._fazer_lance(cap_seq, troca_turno=True)  # Simulação: troca_turno=True pois é lance "normal"
                    nova_pos = cap_seq[-1]
                    # Checar se nós temos algum movimento de captura que pega nova_pos
                    posicoes_nossas = tab_temp.get_posicoes_pecas(cor_peca)
                    for p_nossa in posicoes_nossas:
                        peca_nossa = tab_temp.grid[p_nossa[0]][p_nossa[1]]
                        tipo_nossa = Peca.get_tipo(peca_nossa)
                        caps_nossas = tab_temp._encontrar_capturas_recursivo(
                            p_nossa, cor_peca, tipo_nossa, [p_nossa], []
                        )
                        for seq_nossa in caps_nossas:
                            pecas_capt_nossas = tab_temp.identificar_pecas_capturadas(seq_nossa)
                            if nova_pos in pecas_capt_nossas:
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
                        return True
        return False

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
    def __init__(self, profundidade: int, tempo_limite: float = TEMPO_PADRAO_IA, debug_heur: bool = False):
        self.profundidade_maxima = profundidade
        self.tempo_limite = tempo_limite
        self.nos_visitados = 0; self.nos_quiescence_visitados = 0; self.tt_hits = 0
        self.transposition_table: Dict[int, TTEntry] = {}
        self.killer_moves: List[List[Optional[Movimento]]] = [ [None, None] for _ in range(profundidade + 1)]
        self.history_heuristic: Dict[Tuple[Posicao, Posicao], int] = defaultdict(int)
        # Contadores de diagnóstico adicionados
        self.profundidade_real_atingida = 0
        self.podas_alpha = 0
        self.podas_beta = 0
        self.tempo_por_nivel = defaultdict(float)
        # Controle de tempo e iterative deepening
        self.tempo_inicio = 0.0
        self.tempo_acabou = False
        self.melhor_movimento_atual = None
        self.profundidade_completa = 0
        self.debug_heur = debug_heur

    def limpar_tt_e_historico(self):
        self.transposition_table = {}; self.killer_moves = [ [None, None] for _ in range(self.profundidade_maxima + 1)]; self.history_heuristic = defaultdict(int);
        # Resetar contadores de diagnóstico
        self.profundidade_real_atingida = 0
        self.podas_alpha = 0
        self.podas_beta = 0
        self.tempo_por_nivel = defaultdict(float)
        # Resetar controle de tempo
        self.tempo_inicio = 0.0
        self.tempo_acabou = False
        self.melhor_movimento_atual = None
        self.profundidade_completa = 0

    def _formatar_movimento(self, mov: Movimento) -> str: return " -> ".join([Tabuleiro.pos_para_alg(p) for p in mov]) if mov else "N/A"
    def _mov_para_chave_history(self, mov: Movimento) -> Optional[Tuple[Posicao, Posicao]]: return (mov[0], mov[-1]) if mov and len(mov) >= 2 else None

    def verificar_tempo(self) -> bool:
        """Verifica se o tempo de busca foi excedido."""
        if time.time() - self.tempo_inicio > self.tempo_limite:
            self.tempo_acabou = True
            return True
        return False

    def encontrar_melhor_movimento(self, partida: Partida, cor_ia: int, movimentos_legais: List[Movimento]) -> Optional[Movimento]:
        if not movimentos_legais: print("[IA] Nenhum movimento legal."); return None
        if len(movimentos_legais) == 1: unico=movimentos_legais[0]; print(f"[IA] Movimento único: {self._formatar_movimento(unico)}"); return unico

        self.limpar_tt_e_historico(); self.tempo_inicio = time.time()
        self.nos_visitados = 0; self.nos_quiescence_visitados = 0; self.tt_hits = 0
        self.melhor_movimento_atual = movimentos_legais[0] # Movimento padrão caso tempo acabe muito rápido

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
                
            tempo_inicio_prof = time.time()
            alpha = -float('inf'); beta = float('inf')
            movs_avaliados = {}
            
            # Ordenação raiz para esta profundidade
            mov_caps_raiz = [m for m in movimentos_legais if len(tab_copia.identificar_pecas_capturadas(m)) > 0]
            mov_simples_raiz = [m for m in movimentos_legais if m not in mov_caps_raiz]
            mov_simples_raiz.sort(key=lambda m: self.history_heuristic.get(self._mov_para_chave_history(m), 0), reverse=True)
            movs_ord_raiz = mov_caps_raiz + mov_simples_raiz
            
            # Usar último melhor movimento primeiro (se existir e não for captura)
            if self.melhor_movimento_atual in mov_simples_raiz:
                mov_simples_raiz.remove(self.melhor_movimento_atual)
                movs_ord_raiz = mov_caps_raiz + [self.melhor_movimento_atual] + mov_simples_raiz
                
            melhor_score_prof = -float('inf')
            melhor_mov_prof = None
            
            try:
                for mov in movs_ord_raiz:
                    if self.verificar_tempo(): raise TempoExcedidoError("Tempo excedido durante avaliação de movimentos")
                    # Determinar se haverá troca de turno
                    cp = bool(tab_copia.identificar_pecas_capturadas(mov))
                    pos_final = mov[-1]
                    peca_final = tab_copia.get_peca(pos_final)
                    tipo_final = Peca.get_tipo(peca_final)
                    capturas_combo = tab_copia._encontrar_capturas_recursivo(pos_final, cor_ia, tipo_final, [pos_final], []) if cp else []
                    troca_turno = not (cp and capturas_combo)
                    estado_d = tab_copia._fazer_lance(mov, troca_turno=troca_turno)
                    # --- FILTRO DE LANCES SUICIDAS ---
                    cor_op = Tabuleiro.get_oponente(cor_ia) if troca_turno else cor_ia
                    if tab_copia.encontrar_movimentos_possiveis(cor_op, apenas_capturas=True):
                        tab_copia._desfazer_lance(estado_d)
                        continue  # pula esse movimento inteiramente
                    # ... caso contrário, chama minimax normalmente
                    jog_apos = Tabuleiro.get_oponente(cor_ia) if troca_turno else cor_ia
                    pd = (Peca.get_tipo(estado_d.peca_movida_original)==PEDRA)
                    ct_p = 0
                    score = -self.minimax(tab_copia, ct_p, prof_atual - 1, -beta, -alpha, jog_apos, cor_ia) # NegaMax
                    tab_copia._desfazer_lance(estado_d)  # Desfazer o movimento após análise
                    
                    movs_avaliados[self._formatar_movimento(mov)] = score
                    
                    if score > melhor_score_prof:
                        melhor_score_prof = score
                        melhor_mov_prof = mov
                        
                    alpha = max(alpha, melhor_score_prof)
                    
                    if self.verificar_tempo(): raise TempoExcedidoError("Tempo excedido após avaliação de um movimento")
            
                # Atualizar melhor movimento se completou a profundidade sem erros
                if melhor_mov_prof:
                    self.melhor_movimento_atual = melhor_mov_prof
                    self.profundidade_completa = prof_atual
                    resultados_por_profundidade[prof_atual] = movs_avaliados
                
                tempo_prof = time.time() - tempo_inicio_prof
                print(f"[IA] Prof {prof_atual} completa em {tempo_prof:.2f}s: {self._formatar_movimento(melhor_mov_prof)} (Score: {melhor_score_prof:.3f})")
                tempo_restante = self.tempo_limite - (time.time() - self.tempo_inicio)
                if prof_atual > 1:
                    tempo_prev = self.tempo_por_nivel[prof_atual - 1]
                    estimativa_next = tempo_prof * (tempo_prof / tempo_prev if tempo_prev > 0 else 1)
                    if estimativa_next > tempo_restante:
                        print(f"[IA] Estimativa de tempo para próxima profundidade ({estimativa_next:.2f}s) excede o tempo restante ({tempo_restante:.2f}s). Parando em {prof_atual}.")
                        break
                    
                # Verificar novamente se o tempo acabou
                if self.verificar_tempo():
                    print(f"[IA] Tempo limite atingido após completar profundidade {prof_atual}")
                    break
                    
            except TempoExcedidoError as e:
                print(f"[IA] {str(e)} na profundidade {prof_atual}")
                break
                
        end_time_total = time.time()
        
        # Mostrar último resultado completo
        if self.profundidade_completa > 0 and self.profundidade_completa in resultados_por_profundidade:
            print(f"\n[IA] Avaliação final (profundidade {self.profundidade_completa}):")
            res_ord = sorted(resultados_por_profundidade[self.profundidade_completa].items(), key=lambda item: item[1], reverse=True)
            for mov_s, score_m in res_ord[:5]: # Mostrar apenas os 5 melhores para não poluir
                print(f"  - Movimento: {mov_s:<15} -> Score: {score_m:.3f}")
                
        if self.melhor_movimento_atual:
            print(f"\n[IA] Escolhido: {self._formatar_movimento(self.melhor_movimento_atual)} (Prof: {self.profundidade_completa})")
        else:
            print("[IA] Nenhum movimento válido encontrado/escolhido.")
            self.melhor_movimento_atual = random.choice(movimentos_legais) if movimentos_legais else None
            
        # Estatísticas detalhadas
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
            val = tab_copia.avaliar_heuristica(cor_ia, debug_aval=True)
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

    def minimax(self, tab: Tabuleiro, cont_emp: int, prof: int, alpha: float, beta: float, jog: int, cor_ia: int) -> float:
        # if self.debug:
        #     print(f"[minimax] prof={prof} cont_emp={cont_emp} jogador={jog} hash={tab.hash_atual:x}")
        # if self.debug:
        #     print(f"[minimax]   Nó prof={prof} jogador={jog}: {len(movs)} movimentos gerados")
        # Verificar tempo periodicamente (a cada 100 nós)
        if self.nos_visitados % 100 == 0 and self.verificar_tempo():
            raise TempoExcedidoError("Tempo excedido durante minimax")
        # Registrar a profundidade máxima atingida
        prof_atual = self.profundidade_completa + 1 - prof
        self.profundidade_real_atingida = max(self.profundidade_real_atingida, prof_atual)
        # Registrar tempo do nível (para diagnóstico)
        nivel_inicio = time.time()
        a_orig = alpha; hash_pos = tab.hash_atual; is_ia = (jog == cor_ia)
        melhor_mov_tt = None
        # Consulta TT
        entry = self.transposition_table.get(hash_pos)
        if entry and entry.profundidade >= prof:
            self.tt_hits += 1; melhor_mov_tt = entry.melhor_movimento
            if entry.flag == TT_FLAG_EXACT: return entry.score
            elif entry.flag == TT_FLAG_LOWERBOUND: alpha = max(alpha, entry.score)
            elif entry.flag == TT_FLAG_UPPERBOUND: beta = min(beta, entry.score)
            if beta <= alpha: return entry.score
        self.nos_visitados += 1
        if cont_emp >= 40: return 0.0
        # Quiescência
        if prof <= 0: return self.quiescence_search(tab, MAX_QUIESCENCE_DEPTH, alpha, beta, jog, cor_ia)
        # Movimentos
        tab.limpar_cache_capturas()  # Limpa o cache de capturas a cada nó
        movs = tab.encontrar_movimentos_possiveis(jog)
        # if self.debug:
        #     print(f"[minimax]   Nó prof={prof} jogador={jog}: {len(movs)} movimentos gerados")
        if not movs: score_fim = float('-inf') if is_ia else float('inf'); self.transposition_table[hash_pos]=TTEntry(prof, score_fim, TT_FLAG_EXACT, None); return score_fim
        # Ordenação (TT, Killer, Captures, History)
        movs_ordenados = []; killer_list = []
        kd = self.profundidade_completa + 1 - prof
        if melhor_mov_tt is not None and melhor_mov_tt in movs: movs_ordenados.append(melhor_mov_tt); movs.remove(melhor_mov_tt)
        if kd >= 0 and kd < len(self.killer_moves):
            for kmov in self.killer_moves[kd]:
                if kmov is not None and kmov in movs: killer_list.append(kmov); movs.remove(kmov)
        movs_ordenados.extend(killer_list)
        mov_caps = [m for m in movs if len(tab.identificar_pecas_capturadas(m)) > 0]
        # Ordenar capturas por valor do material capturado (MVV/LVA), penalizando capturas arriscadas
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
        mov_caps.sort(key=valor_captura, reverse=True)
        mov_nao_caps = [m for m in movs if m not in mov_caps]
        mov_nao_caps.sort(key=lambda m: self.history_heuristic.get(self._mov_para_chave_history(m), 0), reverse=True)
        movs_ordenados.extend(mov_caps); movs_ordenados.extend(mov_nao_caps)
        melhor_val = -float('inf'); melhor_mov_local = None
        # Loop Alpha-Beta NegaMax
        for mov in movs_ordenados:
            # Determinar se haverá troca de turno
            cp=bool(tab.identificar_pecas_capturadas(mov))
            pos_final = mov[-1]
            peca_final = tab.get_peca(pos_final)
            tipo_final = Peca.get_tipo(peca_final)
            capturas_combo = tab._encontrar_capturas_recursivo(pos_final, jog, tipo_final, [pos_final], []) if cp else []
            troca_turno = not (cp and capturas_combo)
            estado_d=tab._fazer_lance(mov, troca_turno=troca_turno)
            pd=Peca.get_tipo(estado_d.peca_movida_original)==PEDRA
            # Determinar próximo jogador e profundidade
            if cp and capturas_combo:
                prox_jogador = jog
                prox_prof = prof
            else:
                prox_jogador = Tabuleiro.get_oponente(jog)
                prox_prof = prof - 1
            # Ajuste correto do contador de empates
            if prox_jogador != jog:
                if cp or pd:
                    ct_p = 0
                else:
                    ct_p = cont_emp + 1
            else:
                ct_p = cont_emp
            score = -self.minimax(tab, ct_p, prox_prof, -beta, -alpha, prox_jogador, cor_ia)
            tab._desfazer_lance(estado_d)
            if score > melhor_val: melhor_val = score; melhor_mov_local = mov
            alpha = max(alpha, melhor_val);
            if beta <= alpha: # Poda Beta
                 self.podas_beta += 1  # Contador de podas beta
                 if kd >= 0 and kd < len(self.killer_moves) and not cp:
                     if mov not in self.killer_moves[kd]:
                         self.killer_moves[kd].insert(0, mov)
                         self.killer_moves[kd] = self.killer_moves[kd][:2]
                 chave_hist = self._mov_para_chave_history(mov)
                 if chave_hist and not cp: self.history_heuristic[chave_hist] += prof * prof
                 break
        # Armazenamento TT
        flag = TT_FLAG_EXACT;
        if melhor_val <= a_orig: 
            flag = TT_FLAG_UPPERBOUND
            self.podas_alpha += 1  # Contador de podas alpha
        elif melhor_val >= beta: 
            flag = TT_FLAG_LOWERBOUND
            self.podas_beta += 1  # Contador de podas beta
        self.transposition_table[hash_pos] = TTEntry(prof, melhor_val, flag, melhor_mov_local)
        # Registrar tempo gasto neste nível
        nivel_fim = time.time()
        self.tempo_por_nivel[prof_atual] += nivel_fim - nivel_inicio
        return melhor_val

    # Quiescence Search (ajustado para verificar tempo)
    def quiescence_search(self, tab: Tabuleiro, prof_q: int, a: float, b: float, jog_q: int, cor_ia: int) -> float:
        # Verificar tempo periodicamente (a cada 500 nós de quiescence)
        if self.nos_quiescence_visitados % 500 == 0 and self.verificar_tempo():
            raise TempoExcedidoError("Tempo excedido durante quiescence_search")
        hash_pos = tab.hash_atual
        entry = self.transposition_table.get(hash_pos)
        if entry and entry.flag == TT_FLAG_EXACT and entry.profundidade >= -1 : self.tt_hits+=1; return entry.score
        self.nos_quiescence_visitados += 1
        stand_pat = tab.avaliar_heuristica(cor_ia, debug_aval=True)
        mov_caps = tab.encontrar_movimentos_possiveis(jog_q, apenas_capturas=True)
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
                return stand_pat
        if prof_q <= 0: return stand_pat
        is_max = (jog_q == cor_ia)
        if is_max: a = max(a, stand_pat)
        else: b = min(b, stand_pat)
        if b <= a: return stand_pat
        if not mov_caps: return stand_pat
        score_final_q = stand_pat
        if is_max:
            for mov in mov_caps:
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
                val = self.quiescence_search(tab, prox_prof_q, a, b, prox_jog, cor_ia)
                tab._desfazer_lance(estado_d)
                score_final_q = max(score_final_q, val); a = max(a, score_final_q)
                if b <= a: break
        else:
            for mov in mov_caps:
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
                val = self.quiescence_search(tab, prox_prof_q, a, b, prox_jog, cor_ia)
                tab._desfazer_lance(estado_d)
                score_final_q = min(score_final_q, val); b = min(b, score_final_q)
                if b <= a: break
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

# --- Bloco Principal (Teste) ---
if __name__ == "__main__":
     print("--- Testando damas_logic.py v12.3 Iterative Deepening + Time Management ---")
     partida_teste = Partida(jogador_branco="IA", jogador_preto="Humano")
     ia_teste = MotorIA(profundidade=PROFUNDIDADE_IA, tempo_limite=TEMPO_PADRAO_IA) # Usa tempo e profundidade configuráveis
     print(f"Profundidade Máxima de Teste: {PROFUNDIDADE_IA}, Tempo Limite: {TEMPO_PADRAO_IA}s")
     print("Estado Inicial:"); print(partida_teste.tabuleiro)
     if partida_teste.jogador_atual == BRANCO:
         print("\nCalculando movimento inicial para Brancas...")
         start_time = time.time()
         movimento_escolhido = ia_teste.encontrar_melhor_movimento(
             partida_teste,
             BRANCO,
             partida_teste.movimentos_legais_atuais
         )
         end_time = time.time()
         print(f"\n[Teste] Tempo de cálculo: {end_time - start_time:.2f}s")
         if movimento_escolhido: print(f"[Teste] Movimento Sugerido: {ia_teste._formatar_movimento(movimento_escolhido)}")
         else: print("[Teste] IA não encontrou movimento.")
         
         # Salvar estatísticas em um arquivo separado
         with open("stats_ia.txt", "w") as f:
             f.write("=== ESTATÍSTICAS DA IA ===\n")
             f.write(f"Profundidade Máxima Configurada: {ia_teste.profundidade_maxima}\n")
             f.write(f"Profundidade Completada: {ia_teste.profundidade_completa}\n")
             f.write(f"Profundidade Real Atingida: {ia_teste.profundidade_real_atingida}\n")
             f.write(f"Nós Visitados (Minimax): {ia_teste.nos_visitados}\n")
             f.write(f"Nós Visitados (Quiescence): {ia_teste.nos_quiescence_visitados}\n")
             f.write(f"Total de Nós: {ia_teste.nos_visitados + ia_teste.nos_quiescence_visitados}\n")
             f.write(f"TT Hits: {ia_teste.tt_hits}\n")
             f.write(f"Podas Alpha: {ia_teste.podas_alpha}\n")
             f.write(f"Podas Beta: {ia_teste.podas_beta}\n")
             f.write(f"Tempo Total: {end_time - start_time:.2f}s\n")
             f.write(f"Nós por segundo: {(ia_teste.nos_visitados + ia_teste.nos_quiescence_visitados) / max(0.001, end_time - start_time):.0f}\n")
             f.write("\nTempo por Nível de Profundidade:\n")
             for nivel, tempo in sorted(ia_teste.tempo_por_nivel.items()):
                 f.write(f"  - Nível {nivel}: {tempo:.4f}s\n")
     print("\n--- Fim do Teste ---")

     # Testar avaliação de heurística
     tabuleiro = partida_teste.tabuleiro
     print("\n[DEBUG] Avaliação heurística para BRANCO:")
     tabuleiro.avaliar_heuristica(BRANCO, debug_aval=True)
     print("\n[DEBUG] Avaliação heurística para PRETO:")
     tabuleiro.avaliar_heuristica(PRETO, debug_aval=True)
    
     ia = MotorIA(profundidade=12, tempo_limite=25.0, debug_heur=True)
    