#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pstats
import sys
import io
import os

def analisar_detalhado(arquivo_perfil='perfil_detalhado.prof', arquivo_saida='analise_perfil_resultado.txt'):
    # Redirecionar a saída para um arquivo
    with open(arquivo_saida, 'w', encoding='utf-8') as f_out:
        f_out.write("\n===== ANÁLISE DETALHADA DO PERFIL =====\n")
        
        # Carregar as estatísticas do perfil
        p = pstats.Stats(arquivo_perfil)
        
        # 1. Visão geral: Top 15 funções por tempo total
        f_out.write("\n=== TOP 15 FUNÇÕES (TEMPO TOTAL) ===\n")
        stream = io.StringIO()
        ps = pstats.Stats(arquivo_perfil, stream=stream)
        ps.sort_stats('cumtime').print_stats(15)
        f_out.write(stream.getvalue())
        
        # 2. Top 15 funções por tempo interno
        f_out.write("\n=== TOP 15 FUNÇÕES (TEMPO INTERNO) ===\n")
        stream = io.StringIO()
        ps = pstats.Stats(arquivo_perfil, stream=stream)
        ps.sort_stats('tottime').print_stats(15)
        f_out.write(stream.getvalue())
        
        # 3. Funções específicas do damas_logic.py por tempo total
        f_out.write("\n=== FUNÇÕES DE DAMAS_LOGIC.PY (TEMPO TOTAL) ===\n")
        stream = io.StringIO()
        ps = pstats.Stats(arquivo_perfil, stream=stream)
        ps.sort_stats('cumtime').print_stats(r'damas_logic.py')
        f_out.write(stream.getvalue())
        
        # 4. Funções específicas do damas_logic.py por tempo interno
        f_out.write("\n=== FUNÇÕES DE DAMAS_LOGIC.PY (TEMPO INTERNO) ===\n")
        stream = io.StringIO()
        ps = pstats.Stats(arquivo_perfil, stream=stream)
        ps.sort_stats('tottime').print_stats(r'damas_logic.py')
        f_out.write(stream.getvalue())
        
        # 5. Funções específicas por número de chamadas
        f_out.write("\n=== FUNÇÕES POR NÚMERO DE CHAMADAS ===\n")
        stream = io.StringIO()
        ps = pstats.Stats(arquivo_perfil, stream=stream)
        ps.sort_stats('calls').print_stats(r'damas_logic.py')
        f_out.write(stream.getvalue())
        
        # 6. Verificar tempo por chamada
        f_out.write("\n=== FUNÇÕES POR TEMPO POR CHAMADA ===\n")
        stream = io.StringIO()
        ps = pstats.Stats(arquivo_perfil, stream=stream)
        ps.sort_stats('cumtime', 'calls').print_stats(r'damas_logic.py:')
        f_out.write(stream.getvalue())
        
        # 7. Verificar especificamente a função eh_peca_ameacada_em_2_lances
        f_out.write("\n=== VERIFICANDO eh_peca_ameacada_em_2_lances ===\n")
        stream = io.StringIO()
        ps = pstats.Stats(arquivo_perfil, stream=stream)
        ps.sort_stats('cumtime').print_stats('eh_peca_ameacada_em_2_lances')
        f_out.write(stream.getvalue())
        
        # 8. Verificar funções de avaliação heurística
        f_out.write("\n=== FUNÇÕES DE AVALIAÇÃO HEURÍSTICA ===\n")
        stream = io.StringIO()
        ps = pstats.Stats(arquivo_perfil, stream=stream)
        ps.sort_stats('cumtime').print_stats('avaliar_heuristica|_heuristica_para_cor')
        f_out.write(stream.getvalue())
        
        # 9. Verificar funções de busca
        f_out.write("\n=== FUNÇÕES DE BUSCA E MINIMAX ===\n")
        stream = io.StringIO()
        ps = pstats.Stats(arquivo_perfil, stream=stream)
        ps.sort_stats('cumtime').print_stats('minimax|quiescence|_search_root')
        f_out.write(stream.getvalue())
        
        f_out.write("\n===== FIM DA ANÁLISE =====\n")
    
    print(f"Análise detalhada salva em {os.path.abspath(arquivo_saida)}")
    return arquivo_saida

if __name__ == "__main__":
    # Se um argumento for fornecido, usa-o como arquivo de perfil
    arquivo_perfil = sys.argv[1] if len(sys.argv) > 1 else 'perfil_detalhado.prof'
    analisar_detalhado(arquivo_perfil) 