#!/usr/bin/env python
# -*- coding: utf-8 -*-

from damas_logic import Tabuleiro, BRANCO, PRETO

def main():
    print("Testando validador de movimentos simples...")
    tab = Tabuleiro()
    
    # Testa para BRANCO
    print("\nValidando movimentos para BRANCO:")
    resultado_branco = tab.validar_movimentos_simples(BRANCO)
    assert resultado_branco, "Validação falhou para BRANCO"
    
    # Testa para PRETO
    print("\nValidando movimentos para PRETO:")
    resultado_preto = tab.validar_movimentos_simples(PRETO)
    assert resultado_preto, "Validação falhou para PRETO"
    
    print("\n✓ gera_movimentos_simples 100% ok para BRANCO e PRETO")
    
if __name__ == "__main__":
    main() 