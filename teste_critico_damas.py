# -*- coding: utf-8 -*-
"""
Script para testar posições críticas do tabuleiro de damas.
Mostra o material, avaliação estática e bônus/penalidades para BRANCO e PRETO.
Edite a matriz 'grid' para testar diferentes posições.
"""
from damas_logic import Tabuleiro, BRANCO, PRETO

def main():
    tab = Tabuleiro(estado_inicial=False)
    # Edite esta matriz para testar diferentes posições
    tab.grid = [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0, -1, 0,  0,  0,  0],
        [0,  0,  1,  0, 0,  0,  0,  0],
        [0,  0,  0,  0, 0,  0,  0,  0],
        [0,  0,  0,  0, 0,  0,  0,  0],
        [0,  0,  0,  0, 0,  0,  0,  0],
    ]
    print("Tabuleiro de teste:")
    print(tab)
    for cor, nome in [(BRANCO, "BRANCO"), (PRETO, "PRETO")]:
        print(f"\n[DEBUG] Avaliação para {nome}:")
        mat = tab.material_balance(cor)
        stat = tab.avaliar_heuristica(cor, debug_aval=True)
        print(f"[DEBUG] mat={mat}, stat={stat}, extra={stat-mat}")

if __name__ == "__main__":
    main() 