import cProfile
import pstats
import time
from damas_logic import Tabuleiro, MotorIA, Partida

def main():
    # Criar um tabuleiro padrão e inicializar o motor
    tabuleiro = Tabuleiro()
    motor = MotorIA(profundidade=4, tempo_limite=20.0)  # Aumento da profundidade e tempo
    partida = Partida()
    
    # Executar uma busca
    movimentos_legais = tabuleiro.encontrar_movimentos_possiveis(1)  # 1 = brancas
    if movimentos_legais:
        inicio = time.time()
        melhor_movimento = motor.encontrar_melhor_movimento(partida, 1, movimentos_legais)
        fim = time.time()
        print(f"Tempo para encontrar melhor movimento: {fim - inicio:.2f} segundos")
    
    # Exibir estatísticas
    print(f"TT hits: {motor.tt_hits}")
    print(f"Nós visitados: {motor.nos_visitados}")
    print(f"Nós quiescence: {motor.nos_quiescence_visitados}")
    print(f"Profundidade máxima: {motor.profundidade_maxima}")
    print(f"Profundidade real atingida: {motor.profundidade_real_atingida}")

# Executar com profiling
if __name__ == "__main__":
    cProfile.run('main()', 'perfil_teste.prof')
    
    # Analisar o perfil
    p = pstats.Stats('perfil_teste.prof')
    p.strip_dirs().sort_stats('cumulative').print_stats(20)
    
    # Mostrar funções que consomem mais tempo
    print("\nTop 10 funções por tempo cumulativo:")
    print("-" * 80)
    
    # Criar um dicionário para armazenar as estatísticas
    stats_dict = {}
    for func, (cc, nc, tt, ct, callers) in p.stats.items():
        stats_dict[func] = (cc, nc, tt, ct, callers)
    
    # Ordenar por tempo cumulativo
    sorted_stats = sorted(stats_dict.items(), key=lambda x: x[1][3], reverse=True)
    
    # Imprimir os 10 primeiros
    for i, ((file, line, func_name), (cc, nc, tt, ct, callers)) in enumerate(sorted_stats[:10], 1):
        print(f"{i:2}. {func_name:40} - {ct:.6f}s ({nc} chamadas) em {file}:{line}") 