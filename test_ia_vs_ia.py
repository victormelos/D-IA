#!/usr/bin/env python
# -*- coding: utf-8 -*-
# test_ia_vs_ia.py - Testes da IA jogando contra si mesma

import time
import copy
import random
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
from damas_logic import *

class TestadorIA:
    """
    Classe para realizar testes da IA jogando contra si mesma e analisar os resultados.
    """
    def __init__(self, num_partidas=10, profundidade_ia=8, tempo_por_lance=3.0):
        self.num_partidas = num_partidas
        self.profundidade_ia = profundidade_ia
        self.tempo_por_lance = tempo_por_lance
        self.resultados = []
        self.estatisticas = {
            'brancas_vitorias': 0,
            'pretas_vitorias': 0,
            'empates': 0,
            'media_lances': 0,
            'capturas_brancas': 0,
            'capturas_pretas': 0,
            'promocoes_brancas': 0,
            'promocoes_pretas': 0,
            'sacrificios_brancas': 0,  # Quando uma peça é capturada sem retaliação
            'sacrificios_pretas': 0,
        }
        self.historico_partidas = []
    
    def executar_teste(self, salvar_resultados=True):
        """
        Executa várias partidas da IA contra si mesma e coleta estatísticas.
        """
        print(f"Iniciando teste com {self.num_partidas} partidas...")
        print(f"Configuração: Profundidade={self.profundidade_ia}, Tempo={self.tempo_por_lance}s")
        
        for i in range(self.num_partidas):
            print(f"\nPartida {i+1}/{self.num_partidas}")
            
            # Inicializar a partida e as IAs
            partida = Partida(jogador_branco="IA", jogador_preto="IA")
            ia_brancas = MotorIA(profundidade=self.profundidade_ia, tempo_limite=self.tempo_por_lance)
            ia_pretas = MotorIA(profundidade=self.profundidade_ia, tempo_limite=self.tempo_por_lance)
            
            # Estatísticas da partida atual
            infos_partida = {
                'id': i+1,
                'total_lances': 0,
                'capturas_brancas': 0,
                'capturas_pretas': 0,
                'promocoes_brancas': 0,
                'promocoes_pretas': 0,
                'sacrificios_brancas': 0,
                'sacrificios_pretas': 0,
                'lances_por_jogador': {BRANCO: [], PRETO: []},
                'estados_tabuleiro': []
            }
            
            # Salvar estado inicial
            infos_partida['estados_tabuleiro'].append(str(partida.tabuleiro))
            
            # Loop da partida
            while partida.vencedor is None:
                jogador_atual = partida.jogador_atual
                
                # Detectar possíveis sacrifícios antes do movimento
                pecas_antes = len(partida.tabuleiro.get_posicoes_pecas(jogador_atual))
                
                # Selecionar IA correta
                motor = ia_brancas if jogador_atual == BRANCO else ia_pretas
                
                # IA encontra melhor movimento
                inicio = time.time()
                movimento = motor.encontrar_melhor_movimento(
                    partida,
                    jogador_atual,
                    partida.movimentos_legais_atuais
                )
                fim = time.time()
                
                # Registrar lance
                tempo_lance = fim - inicio
                lancamento = {
                    'movimento': [Tabuleiro.pos_para_alg(p) for p in movimento],
                    'tempo': tempo_lance,
                    'score': motor.melhor_movimento_atual,
                    'profundidade': motor.profundidade_completa
                }
                infos_partida['lances_por_jogador'][jogador_atual].append(lancamento)
                
                # Identificar peças capturadas no movimento
                pecas_capturadas = partida.tabuleiro.identificar_pecas_capturadas(movimento)
                if jogador_atual == BRANCO:
                    infos_partida['capturas_brancas'] += len(pecas_capturadas)
                else:
                    infos_partida['capturas_pretas'] += len(pecas_capturadas)
                
                # Executar o lance
                lance_info_antes = copy.deepcopy(partida.tabuleiro)
                partida.executar_lance_completo(movimento)
                infos_partida['estados_tabuleiro'].append(str(partida.tabuleiro))
                infos_partida['total_lances'] += 1
                
                # Detecção de promoção
                origem, destino = movimento[0], movimento[-1]
                linha_promocao_b, linha_promocao_p = 0, TAMANHO_TABULEIRO-1
                
                if jogador_atual == BRANCO and destino[0] == linha_promocao_b:
                    infos_partida['promocoes_brancas'] += 1
                elif jogador_atual == PRETO and destino[0] == linha_promocao_p:
                    infos_partida['promocoes_pretas'] += 1
                
                # Detectar sacrifícios
                pecas_depois = len(partida.tabuleiro.get_posicoes_pecas(jogador_atual))
                if pecas_depois < pecas_antes and len(pecas_capturadas) == 0:  # Perdeu peça sem capturar
                    if jogador_atual == BRANCO:
                        infos_partida['sacrificios_brancas'] += 1
                    else:
                        infos_partida['sacrificios_pretas'] += 1
                
                # Verificar fim de jogo ou limite de lances
                if partida.vencedor is not None or infos_partida['total_lances'] >= 200:
                    if infos_partida['total_lances'] >= 200 and partida.vencedor is None:
                        partida.vencedor = VAZIO  # Empate por limite de lances
                    break
            
            # Registrar resultado final
            resultado = {
                'partida_id': i+1,
                'vencedor': 'Brancas' if partida.vencedor == BRANCO else 
                            ('Pretas' if partida.vencedor == PRETO else 'Empate'),
                'total_lances': infos_partida['total_lances'],
                'capturas_brancas': infos_partida['capturas_brancas'],
                'capturas_pretas': infos_partida['capturas_pretas'],
                'promocoes_brancas': infos_partida['promocoes_brancas'],
                'promocoes_pretas': infos_partida['promocoes_pretas'],
                'sacrificios_brancas': infos_partida['sacrificios_brancas'],
                'sacrificios_pretas': infos_partida['sacrificios_pretas']
            }
            self.resultados.append(resultado)
            
            # Atualizar estatísticas globais
            if partida.vencedor == BRANCO:
                self.estatisticas['brancas_vitorias'] += 1
            elif partida.vencedor == PRETO:
                self.estatisticas['pretas_vitorias'] += 1
            else:
                self.estatisticas['empates'] += 1
                
            self.estatisticas['capturas_brancas'] += infos_partida['capturas_brancas']
            self.estatisticas['capturas_pretas'] += infos_partida['capturas_pretas']
            self.estatisticas['promocoes_brancas'] += infos_partida['promocoes_brancas']
            self.estatisticas['promocoes_pretas'] += infos_partida['promocoes_pretas']
            self.estatisticas['sacrificios_brancas'] += infos_partida['sacrificios_brancas']
            self.estatisticas['sacrificios_pretas'] += infos_partida['sacrificios_pretas']
            
            # Adicionar ao histórico
            self.historico_partidas.append(infos_partida)
            
            # Exibir resultado da partida
            print(f"Resultado: {resultado['vencedor']} em {resultado['total_lances']} lances")
            print(f"Capturas: Brancas={resultado['capturas_brancas']}, Pretas={resultado['capturas_pretas']}")
            print(f"Promoções: Brancas={resultado['promocoes_brancas']}, Pretas={resultado['promocoes_pretas']}")
            print(f"Sacrifícios: Brancas={resultado['sacrificios_brancas']}, Pretas={resultado['sacrificios_pretas']}")
        
        # Calcular média de lances
        total_lances = sum(r['total_lances'] for r in self.resultados)
        self.estatisticas['media_lances'] = total_lances / self.num_partidas
        
        # Exibir estatísticas finais
        self.exibir_estatisticas()
        
        # Salvar resultados
        if salvar_resultados:
            self.salvar_resultados()
    
    def exibir_estatisticas(self):
        """
        Exibe as estatísticas dos testes realizados.
        """
        print("\n" + "="*50)
        print(f"ESTATÍSTICAS FINAIS ({self.num_partidas} partidas)")
        print("="*50)
        print(f"Vitórias das Brancas: {self.estatisticas['brancas_vitorias']} ({self.estatisticas['brancas_vitorias']/self.num_partidas*100:.1f}%)")
        print(f"Vitórias das Pretas: {self.estatisticas['pretas_vitorias']} ({self.estatisticas['pretas_vitorias']/self.num_partidas*100:.1f}%)")
        print(f"Empates: {self.estatisticas['empates']} ({self.estatisticas['empates']/self.num_partidas*100:.1f}%)")
        print(f"Média de lances por partida: {self.estatisticas['media_lances']:.1f}")
        print(f"Total de capturas: Brancas={self.estatisticas['capturas_brancas']}, Pretas={self.estatisticas['capturas_pretas']}")
        print(f"Total de promoções: Brancas={self.estatisticas['promocoes_brancas']}, Pretas={self.estatisticas['promocoes_pretas']}")
        print(f"Total de sacrifícios: Brancas={self.estatisticas['sacrificios_brancas']}, Pretas={self.estatisticas['sacrificios_pretas']}")
        
        # Taxa de sacrifício (percentual de capturas que foram sacrifícios)
        if self.estatisticas['capturas_brancas'] > 0:
            taxa_sacrificio_b = self.estatisticas['sacrificios_brancas'] / self.estatisticas['capturas_brancas'] * 100
            print(f"Taxa de sacrifício (Brancas): {taxa_sacrificio_b:.1f}%")
            
        if self.estatisticas['capturas_pretas'] > 0:
            taxa_sacrificio_p = self.estatisticas['sacrificios_pretas'] / self.estatisticas['capturas_pretas'] * 100
            print(f"Taxa de sacrifício (Pretas): {taxa_sacrificio_p:.1f}%")
        
        print("="*50)
    
    def salvar_resultados(self):
        """
        Salva os resultados dos testes em arquivos CSV e gera gráficos.
        """
        # Criar DataFrame com os resultados
        df = pd.DataFrame(self.resultados)
        
        # Salvar em CSV
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        df.to_csv(f'resultados_teste_ia_{timestamp}.csv', index=False)
        
        # Gerar gráficos
        self.gerar_graficos(timestamp)
        
        print(f"\nResultados salvos em 'resultados_teste_ia_{timestamp}.csv'")
        print(f"Gráficos salvos como 'graficos_teste_ia_{timestamp}.png'")
    
    def gerar_graficos(self, timestamp):
        """
        Gera gráficos das estatísticas coletadas.
        """
        try:
            fig, axs = plt.subplots(2, 2, figsize=(15, 10))
            
            # Gráfico de resultados
            labels = ['Vitórias Brancas', 'Vitórias Pretas', 'Empates']
            sizes = [
                self.estatisticas['brancas_vitorias'],
                self.estatisticas['pretas_vitorias'],
                self.estatisticas['empates']
            ]
            axs[0, 0].pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            axs[0, 0].set_title('Distribuição de Resultados')
            
            # Gráfico de capturas
            df = pd.DataFrame(self.resultados)
            partidas = list(range(1, self.num_partidas + 1))
            axs[0, 1].bar(partidas, df['capturas_brancas'], label='Brancas', alpha=0.7, color='blue')
            axs[0, 1].bar(partidas, df['capturas_pretas'], label='Pretas', alpha=0.7, color='red', bottom=df['capturas_brancas'])
            axs[0, 1].set_xlabel('Partida')
            axs[0, 1].set_ylabel('Número de Capturas')
            axs[0, 1].set_title('Capturas por Partida')
            axs[0, 1].legend()
            
            # Gráfico de promoções
            axs[1, 0].bar(partidas, df['promocoes_brancas'], label='Brancas', alpha=0.7, color='blue')
            axs[1, 0].bar(partidas, df['promocoes_pretas'], label='Pretas', alpha=0.7, color='red', bottom=df['promocoes_brancas'])
            axs[1, 0].set_xlabel('Partida')
            axs[1, 0].set_ylabel('Número de Promoções')
            axs[1, 0].set_title('Promoções por Partida')
            axs[1, 0].legend()
            
            # Gráfico de número de lances
            axs[1, 1].plot(partidas, df['total_lances'], marker='o', linestyle='-')
            axs[1, 1].axhline(y=self.estatisticas['media_lances'], color='r', linestyle='--', label=f'Média: {self.estatisticas["media_lances"]:.1f}')
            axs[1, 1].set_xlabel('Partida')
            axs[1, 1].set_ylabel('Número de Lances')
            axs[1, 1].set_title('Total de Lances por Partida')
            axs[1, 1].legend()
            
            plt.tight_layout()
            plt.savefig(f'graficos_teste_ia_{timestamp}.png')
            plt.close()
        except Exception as e:
            print(f"Erro ao gerar gráficos: {e}")
            
    def analisar_comportamento_anormal(self):
        """
        Analisa padrões de comportamento anormal, como sacrifícios excessivos.
        """
        print("\nANÁLISE DE COMPORTAMENTO ANORMAL")
        print("-"*40)
        
        # Identificar partidas com sacrifícios excessivos
        limiar_sacrificio = 3  # Considera anormal se houver mais de 3 sacrifícios
        
        partidas_anormais = []
        for i, resultado in enumerate(self.resultados):
            if (resultado['sacrificios_brancas'] > limiar_sacrificio or 
                resultado['sacrificios_pretas'] > limiar_sacrificio):
                partidas_anormais.append(i)
                
        if partidas_anormais:
            print(f"Partidas com comportamento anormal detectado: {len(partidas_anormais)}")
            for idx in partidas_anormais:
                resultado = self.resultados[idx]
                print(f"  Partida {idx+1}: Sacrifícios - Brancas={resultado['sacrificios_brancas']}, Pretas={resultado['sacrificios_pretas']}")
        else:
            print("Nenhum comportamento anormal detectado nos testes realizados.")
            
        # Verificar padrões de capturas/sacrifícios
        razao_sac_b = self.estatisticas['sacrificios_brancas'] / max(1, self.estatisticas['capturas_brancas'])
        razao_sac_p = self.estatisticas['sacrificios_pretas'] / max(1, self.estatisticas['capturas_pretas'])
        
        print(f"\nRazão sacrifícios/capturas:")
        print(f"  Brancas: {razao_sac_b:.3f} ({self.estatisticas['sacrificios_brancas']}/{self.estatisticas['capturas_brancas']})")
        print(f"  Pretas: {razao_sac_p:.3f} ({self.estatisticas['sacrificios_pretas']}/{self.estatisticas['capturas_pretas']})")
        
        if razao_sac_b > 0.2 or razao_sac_p > 0.2:
            print("\nALERTA: Taxa de sacrifícios elevada! Considere ajustar os pesos:")
            print("- Aumentar PENALIDADE_PECA_VULNERAVEL")
            print("- Reduzir BONUS_PRESTES_PROMOVER")
            print("- Ajustar BONUS_AVANCO_PEDRA")
        else:
            print("\nA taxa de sacrifícios está dentro de níveis aceitáveis.")

def testar_diferentes_configuracoes():
    """
    Testa diferentes configurações de pesos e compara os resultados.
    """
    print("\n" + "="*60)
    print(" TESTES DE DIFERENTES CONFIGURAÇÕES DE PESOS ")
    print("="*60)
    
    configuracoes = [
        {
            'nome': 'Padrão',
            'pesos': {
                'PENALIDADE_PECA_VULNERAVEL': -0.9,
                'BONUS_PECA_PROTEGIDA': 0.5,
                'BONUS_PRESTES_PROMOVER': 2.5
            }
        },
        {
            'nome': 'Conservador',
            'pesos': {
                'PENALIDADE_PECA_VULNERAVEL': -1.2,
                'BONUS_PECA_PROTEGIDA': 0.7,
                'BONUS_PRESTES_PROMOVER': 2.0
            }
        },
        {
            'nome': 'Agressivo',
            'pesos': {
                'PENALIDADE_PECA_VULNERAVEL': -0.7,
                'BONUS_PECA_PROTEGIDA': 0.4,
                'BONUS_PRESTES_PROMOVER': 3.0
            }
        }
    ]
    
    resultados_config = {}
    
    # Salvar pesos originais
    pesos_originais = {
        'PENALIDADE_PECA_VULNERAVEL': PENALIDADE_PECA_VULNERAVEL,
        'BONUS_PECA_PROTEGIDA': BONUS_PECA_PROTEGIDA,
        'BONUS_PRESTES_PROMOVER': BONUS_PRESTES_PROMOVER
    }
    
    # Testar cada configuração
    for config in configuracoes:
        print(f"\nTestando configuração: {config['nome']}")
        print("Pesos:")
        for param, valor in config['pesos'].items():
            print(f"  {param} = {valor}")
            
        # Aplicar novos pesos
        for param, valor in config['pesos'].items():
            globals()[param] = valor
            
        # Executar testes
        teste = TestadorIA(num_partidas=5, profundidade_ia=6, tempo_por_lance=2.0)
        teste.executar_teste(salvar_resultados=False)
        
        # Registrar resultados
        resultados_config[config['nome']] = {
            'taxa_vitoria_brancas': teste.estatisticas['brancas_vitorias'] / teste.num_partidas,
            'taxa_vitoria_pretas': teste.estatisticas['pretas_vitorias'] / teste.num_partidas,
            'taxa_empate': teste.estatisticas['empates'] / teste.num_partidas,
            'media_lances': teste.estatisticas['media_lances'],
            'total_sacrificios': teste.estatisticas['sacrificios_brancas'] + teste.estatisticas['sacrificios_pretas'],
            'razao_sacr_capt': (teste.estatisticas['sacrificios_brancas'] + teste.estatisticas['sacrificios_pretas']) / 
                               max(1, teste.estatisticas['capturas_brancas'] + teste.estatisticas['capturas_pretas'])
        }
        
        # Analisar comportamento específico
        teste.analisar_comportamento_anormal()
    
    # Restaurar pesos originais
    for param, valor in pesos_originais.items():
        globals()[param] = valor
    
    # Comparar resultados
    print("\n" + "="*60)
    print(" COMPARAÇÃO DE RESULTADOS ")
    print("="*60)
    
    # Criar tabela de comparação
    tabela_comparacao = {
        'Configuração': [],
        'Taxa Vitória Brancas': [],
        'Taxa Vitória Pretas': [],
        'Taxa Empate': [],
        'Média de Lances': [],
        'Total Sacrifícios': [],
        'Razão Sacrifícios/Capturas': []
    }
    
    for nome, resultado in resultados_config.items():
        tabela_comparacao['Configuração'].append(nome)
        tabela_comparacao['Taxa Vitória Brancas'].append(f"{resultado['taxa_vitoria_brancas']*100:.1f}%")
        tabela_comparacao['Taxa Vitória Pretas'].append(f"{resultado['taxa_vitoria_pretas']*100:.1f}%")
        tabela_comparacao['Taxa Empate'].append(f"{resultado['taxa_empate']*100:.1f}%")
        tabela_comparacao['Média de Lances'].append(f"{resultado['media_lances']:.1f}")
        tabela_comparacao['Total Sacrifícios'].append(str(resultado['total_sacrificios']))
        tabela_comparacao['Razão Sacrifícios/Capturas'].append(f"{resultado['razao_sacr_capt']*100:.1f}%")
    
    # Exibir tabela
    df_comparacao = pd.DataFrame(tabela_comparacao)
    print(df_comparacao.to_string(index=False))
    
    # Recomendação final
    melhor_config = min(resultados_config.items(), key=lambda x: x[1]['razao_sacr_capt'])
    print(f"\nRecomendação: A configuração '{melhor_config[0]}' apresentou melhor equilíbrio,")
    print(f"com menor taxa de sacrifícios ({melhor_config[1]['razao_sacr_capt']*100:.1f}%) e média de {melhor_config[1]['media_lances']:.1f} lances por partida.")
    
    return df_comparacao

if __name__ == "__main__":
    print("="*60)
    print(" TESTE AUTOMÁTICO DA IA DE DAMAS ")
    print("="*60)
    print("""
Este script executa testes automatizados da IA jogando contra si mesma
para avaliar seu desempenho e comportamento estratégico.

Opções disponíveis:
1. Executar teste padrão (IA vs IA)
2. Comparar diferentes configurações de pesos
3. Sair
""")
    
    while True:
        try:
            opcao = int(input("Escolha uma opção (1-3): "))
            if opcao == 1:
                num_partidas = int(input("Número de partidas para teste: "))
                prof = int(input("Profundidade de busca da IA (recomendado 6-8): "))
                tempo = float(input("Tempo por lance em segundos (recomendado 2-5): "))
                
                testador = TestadorIA(num_partidas=num_partidas, profundidade_ia=prof, tempo_por_lance=tempo)
                testador.executar_teste()
                testador.analisar_comportamento_anormal()
                
            elif opcao == 2:
                df_resultado = testar_diferentes_configuracoes()
                df_resultado.to_csv('comparacao_configuracoes.csv', index=False)
                print("\nResultados da comparação salvos em 'comparacao_configuracoes.csv'")
                
            elif opcao == 3:
                print("Encerrando programa.")
                break
                
            else:
                print("Opção inválida. Escolha entre 1 e 3.")
                
        except ValueError:
            print("Entrada inválida. Digite um número.")
        except Exception as e:
            print(f"Erro: {e}")
            
    print("\nPrograma finalizado.") 