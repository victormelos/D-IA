#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback
from damas_logic import (
    Tabuleiro, BRANCO, PRETO, BIT_K, BIT_R, BIT_G, 
    BB_SHIFT_NE, BB_SHIFT_NW, BB_SHIFT_SE, BB_SHIFT_SW,
    BB_SHIFTS_WHITE, BB_SHIFTS_BLACK, DARK_SQUARES
)

def main():
    """
    Testa a função gera_movimentos_simples para peças brancas
    Versão simplificada para depuração
    """
    print("Iniciando teste simplificado para gera_movimentos_simples...")
    
    # Criar um tabuleiro com a configuração inicial
    tabuleiro = Tabuleiro()
    
    # Imprimir direções para brancas e pretas
    print("\nDireções:")
    print(f"BB_SHIFTS_WHITE = {BB_SHIFTS_WHITE}")
    print(f"BB_SHIFTS_BLACK = {BB_SHIFTS_BLACK}")
    
    # Verificar movimentos para brancas via implementação legada
    movs_legados = []
    for mov in tabuleiro.encontrar_movimentos_possiveis(BRANCO, apenas_capturas=False):
        # Filtrar apenas movimentos simples (sem captura)
        if len(mov) == 2 and not tabuleiro.identificar_pecas_capturadas(mov):
            movs_legados.append((mov[0], mov[1]))
    
    print(f"\nMovimentos legados para BRANCO: {movs_legados}")
    
    # Verificar os bitboards para peças brancas
    bb_pedras = tabuleiro.bitboard_brancas & ~tabuleiro.bitboard_damas_brancas
    
    # Mostrar peças brancas
    print("\nPosições das peças brancas:")
    while bb_pedras:
        ls_bit = tabuleiro.lsb(bb_pedras)
        origem = tabuleiro.bit_to_pos(ls_bit)
        print(f"  Peça branca na posição {origem}")
        
        # Tentar calcular as posições de destino manualmente
        for shift in BB_SHIFTS_WHITE:
            destino = None
            shift_name = "NE" if shift == BB_SHIFT_NE else "NW" if shift == BB_SHIFT_NW else "SE" if shift == BB_SHIFT_SE else "SW"
            
            if shift == BB_SHIFT_NE:  # Nordeste: linha-1, coluna+1
                if origem[0] > 0 and origem[1] < 7:  # Verifica limites do tabuleiro
                    destino = (origem[0] - 1, origem[1] + 1)
            elif shift == BB_SHIFT_NW:  # Noroeste: linha-1, coluna-1
                if origem[0] > 0 and origem[1] > 0:  # Verifica limites do tabuleiro
                    destino = (origem[0] - 1, origem[1] - 1)
            
            if destino:
                # Verificar se o destino está vazio
                dest_bit = tabuleiro.pos_to_bit(destino)
                bb_vazias = ~(tabuleiro.bitboard_brancas | tabuleiro.bitboard_pretas | 
                           tabuleiro.bitboard_damas_brancas | tabuleiro.bitboard_damas_pretas) & DARK_SQUARES
                
                if dest_bit & bb_vazias:
                    print(f"    Movimento possível para {shift_name}: {origem} -> {destino}")
                else:
                    peca_destino = tabuleiro.get_peca(destino)
                    print(f"    Destino {destino} não está vazio, contém: {peca_destino}")
        
        bb_pedras &= ~ls_bit
    
    # Executar gera_movimentos_simples sem logging
    movimentos_brancas = tabuleiro.gera_movimentos_simples(BRANCO)
    print(f"\nMovimentos gerados via bitboards para BRANCAS: {movimentos_brancas}")
    
    return True

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)