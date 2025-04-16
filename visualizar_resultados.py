"""
Script para visualizar os resultados do jogo de damas em diferentes formatos.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def localizar_arquivos_resultados():
    """Localiza e lista todos os arquivos de resultados no diretório"""
    arquivos = []
    
    # Verificar arquivo de comparação no diretório raiz
    if os.path.exists('comparacao_configuracoes.csv'):
        arquivos.append(('comparacao_configuracoes.csv', 'Comparação de Configurações (Raiz)'))
    
    # Verificar arquivo de comparação na pasta resultados
    if os.path.exists('resultados/comparacao_configuracoes.csv'):
        arquivos.append(('resultados/comparacao_configuracoes.csv', 'Comparação de Configurações (Pasta Resultados)'))
    
    # Verificar arquivos de estatísticas
    if os.path.exists('stats_ia.txt'):
        arquivos.append(('stats_ia.txt', 'Estatísticas da IA'))
    
    # Verificar arquivos de log
    for arquivo in Path('.').glob('*.log'):
        arquivos.append((str(arquivo), f'Arquivo de Log: {arquivo.name}'))
    
    # Verificar outros arquivos CSV
    for arquivo in Path('.').glob('*.csv'):
        if arquivo.name != 'comparacao_configuracoes.csv':
            arquivos.append((str(arquivo), f'Arquivo CSV: {arquivo.name}'))
    
    return arquivos

def mostrar_conteudo_csv(caminho):
    """Mostra o conteúdo de um arquivo CSV"""
    try:
        df = pd.read_csv(caminho)
        print(f"\n=== Conteúdo do arquivo {caminho} ===")
        print(df.to_string())
        
        # Perguntar se quer visualizar graficamente
        resposta = input("\nDeseja criar gráficos para visualizar estes dados? (s/n): ")
        if resposta.lower() == 's':
            criar_graficos(df, caminho)
        
    except Exception as e:
        print(f"Erro ao ler o arquivo {caminho}: {e}")

def mostrar_conteudo_txt(caminho):
    """Mostra o conteúdo de um arquivo de texto"""
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        print(f"\n=== Conteúdo do arquivo {caminho} ===")
        print(conteudo)
    except Exception as e:
        print(f"Erro ao ler o arquivo {caminho}: {e}")

def criar_graficos(df, caminho):
    """Cria gráficos a partir do DataFrame"""
    try:
        # Garantir que o diretório de gráficos existe
        os.makedirs('resultados/graficos', exist_ok=True)
        
        # Base do nome do arquivo
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        
        # Visualizar taxa de vitória
        if 'Configuração' in df.columns and 'Taxa Vitória Brancas' in df.columns:
            plt.figure(figsize=(12, 6))
            
            # Converter strings percentuais para números
            df_plot = df.copy()
            for col in ['Taxa Vitória Brancas', 'Taxa Vitória Pretas', 'Taxa Empate']:
                if col in df.columns:
                    df_plot[col] = df_plot[col].str.rstrip('%').astype(float)
            
            # Criar barras agrupadas
            bar_width = 0.25
            index = range(len(df_plot))
            plt.bar([i - bar_width for i in index], df_plot['Taxa Vitória Brancas'], 
                    width=bar_width, label='Brancas', color='lightblue')
            plt.bar(index, df_plot['Taxa Vitória Pretas'], 
                    width=bar_width, label='Pretas', color='darkblue')
            plt.bar([i + bar_width for i in index], df_plot['Taxa Empate'], 
                    width=bar_width, label='Empates', color='gray')
            
            plt.xlabel('Configuração')
            plt.ylabel('Taxa (%)')
            plt.title('Taxa de Vitória por Configuração')
            plt.xticks(index, df_plot['Configuração'], rotation=45)
            plt.legend()
            plt.tight_layout()
            
            # Salvar e mostrar
            caminho_grafico = f'resultados/graficos/{nome_base}_vitorias.png'
            plt.savefig(caminho_grafico)
            print(f"Gráfico de vitórias salvo em: {os.path.abspath(caminho_grafico)}")
            plt.show()
            
            # Gráfico de sacrifícios vs capturas
            if 'Razão Sacrifícios/Capturas' in df.columns:
                plt.figure(figsize=(10, 6))
                df_plot['Razão Sacrifícios/Capturas'] = df_plot['Razão Sacrifícios/Capturas'].str.rstrip('%').astype(float)
                plt.bar(df_plot['Configuração'], df_plot['Razão Sacrifícios/Capturas'], color='darkred')
                plt.xlabel('Configuração')
                plt.ylabel('Razão (%)')
                plt.title('Razão Sacrifícios/Capturas por Configuração')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                caminho_grafico = f'resultados/graficos/{nome_base}_sacrificios.png'
                plt.savefig(caminho_grafico)
                print(f"Gráfico de sacrifícios salvo em: {os.path.abspath(caminho_grafico)}")
                plt.show()
                
    except Exception as e:
        print(f"Erro ao criar gráficos: {e}")

def main():
    print("\n=== VISUALIZADOR DE RESULTADOS DO JOGO DE DAMAS ===\n")
    
    # Localizar arquivos de resultados
    arquivos = localizar_arquivos_resultados()
    
    if not arquivos:
        print("Nenhum arquivo de resultados foi encontrado!")
        print("\nPara gerar resultados, execute um dos seguintes comandos:")
        print("- python test_ia_vs_ia.py (para usar o menu interativo)")
        print("- python gerar_comparacao.py (para gerar arquivo de comparação diretamente)")
        return
    
    # Mostrar opções
    print("Arquivos disponíveis para visualização:")
    for i, (caminho, descricao) in enumerate(arquivos, 1):
        print(f"{i}. {descricao} ({caminho})")
    
    try:
        # Solicitar escolha
        opcao = int(input("\nEscolha o arquivo para visualizar (número): "))
        if 1 <= opcao <= len(arquivos):
            caminho, _ = arquivos[opcao-1]
            
            # Verificar o tipo de arquivo e mostrar conteúdo
            if caminho.endswith('.csv'):
                mostrar_conteudo_csv(caminho)
            elif caminho.endswith('.txt') or caminho.endswith('.log'):
                mostrar_conteudo_txt(caminho)
            else:
                print(f"Tipo de arquivo não suportado: {caminho}")
        else:
            print("Opção inválida!")
    except ValueError:
        print("Por favor, digite um número válido.")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main() 