#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from damas_logic import Tabuleiro, BRANCO, PRETO

class TestBitboardValidations(unittest.TestCase):
    def setUp(self):
        self.tab = Tabuleiro()

    def test_movimentos_simples_inicial(self):
        # Valida movimentos simples na posição inicial
        self.assertTrue(self.tab.validar_movimentos_simples(BRANCO), "Movimentos simples (BRANCO) divergentes na posição inicial")
        self.assertTrue(self.tab.validar_movimentos_simples(PRETO), "Movimentos simples (PRETO) divergentes na posição inicial")

    def test_capturas_simples_inicial(self):
        # Valida capturas simples na posição inicial (não deve haver capturas)
        self.assertTrue(self.tab._validar_capturas_bitboard(BRANCO), "Capturas simples (BRANCO) divergentes na posição inicial")
        self.assertTrue(self.tab._validar_capturas_bitboard(PRETO), "Capturas simples (PRETO) divergentes na posição inicial")

    def test_movimentos_simples_intermediario(self):
        # Monta uma posição intermediária manualmente
        self.tab.configuracao_inicial()
        # Remove algumas peças para criar buracos
        self.tab.set_peca((5, 0), 0)
        self.tab.set_peca((2, 1), 0)
        self.tab.set_peca((6, 1), 0)
        self.tab.set_peca((1, 2), 0)
        self.assertTrue(self.tab.validar_movimentos_simples(BRANCO), "Movimentos simples (BRANCO) divergentes em posição intermediária")
        self.assertTrue(self.tab.validar_movimentos_simples(PRETO), "Movimentos simples (PRETO) divergentes em posição intermediária")

    def test_capturas_simples_intermediario(self):
        # Monta uma posição intermediária com possibilidade de captura
        self.tab.configuracao_inicial()
        # Branco pode capturar preto
        self.tab.set_peca((5, 0), 0)
        self.tab.set_peca((4, 1), PRETO)
        self.tab.set_peca((3, 2), 0)
        self.assertTrue(self.tab._validar_capturas_bitboard(BRANCO), "Capturas simples (BRANCO) divergentes em posição intermediária")
        self.assertTrue(self.tab._validar_capturas_bitboard(PRETO), "Capturas simples (PRETO) divergentes em posição intermediária")

if __name__ == "__main__":
    import sys
    if '--profile' in sys.argv:
        import cProfile
        import pstats
        from damas_logic import Tabuleiro, BRANCO
        tab = Tabuleiro()
        print("Rodando profiling de tab.gera_movimentos_simples(BRANCO)...")
        cProfile.run('tab.gera_movimentos_simples(BRANCO)', 'profiling.out')
        p = pstats.Stats('profiling.out')
        p.sort_stats('cumtime').print_stats(20)
    else:
        unittest.main() 