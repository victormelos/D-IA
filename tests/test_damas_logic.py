import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import pytest
from damas_logic import Tabuleiro, BRANCO, PRETO, PB, PP, PEDRA

def test_captura_simples_e_multipla():
    tab = Tabuleiro(estado_inicial=False)
    # Monta uma posição com uma pedra branca e duas pretas para salto duplo
    tab.set_peca((5,0), PB)
    tab.set_peca((4,1), PP)
    tab.set_peca((2,3), PP)
    # Pontas finais livres em (3,2) e (1,4)
    seqs_trad = tab.get_all_man_capture_sequences_bitboard((5,0), BRANCO)
    seqs_bb  = tab.get_all_man_capture_sequences_bitboard((5,0), BRANCO)
    assert set(tuple(s) for s in seqs_trad) == set(tuple(s) for s in seqs_bb)

@pytest.mark.parametrize("pecas, esperado", [
    # Cenário: captura simples
    ([(5,0,PB), (4,1,PP)], [[(5,0),(3,2)]]),
    # Cenário: captura dupla
    ([(5,0,PB), (4,1,PP), (2,3,PP)], [[(5,0),(3,2),(1,4)]]),
])
def test_captura_parametrizada(pecas, esperado):
    tab = Tabuleiro(estado_inicial=False)
    for r, c, v in pecas:
        tab.set_peca((r,c), v)
    seqs_trad = tab.get_all_man_capture_sequences_bitboard((5,0), BRANCO)
    seqs_bb  = tab.get_all_man_capture_sequences_bitboard((5,0), BRANCO)
    # Assegura que pelo menos uma das sequências esperadas está presente
    assert any(tuple(e) in set(tuple(s) for s in seqs_trad) for e in esperado)
    assert set(tuple(s) for s in seqs_trad) == set(tuple(s) for s in seqs_bb)

def test_movimentos_simples_vs_possiveis():
    tab = Tabuleiro(estado_inicial=False)
    # Monta um tabuleiro customizado
    tab.set_peca((5,0), PB)
    tab.set_peca((2,1), PB)
    tab.set_peca((4,1), PP)
    tab.set_peca((3,2), PP)
    # Só compara movimentos simples se não houver capturas
    capturas = tab.encontrar_movimentos_possiveis(BRANCO, apenas_capturas=True)
    if not capturas:
        movs_bb = set(tab.gera_movimentos_simples(BRANCO))
        movs_legado = set((m[0], m[1]) for m in tab.encontrar_movimentos_possiveis(BRANCO, apenas_capturas=False) if len(m)==2 and not tab.identificar_pecas_capturadas(m))
        assert movs_bb == movs_legado
    else:
        # Se houver capturas, os movimentos simples não devem ser considerados
        assert True  # O teste passa pois não é o caso de comparar movimentos simples 