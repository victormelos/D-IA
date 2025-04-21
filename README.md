# Projeto Damas AI - Otimizações

Este projeto implementa um motor de IA para o jogo de Damas com várias otimizações avançadas.

## Otimizações Recentes

### Otimização da Heurística

#### Função `eh_peca_ameacada_em_2_lances`

A função `eh_peca_ameacada_em_2_lances` foi identificada como um gargalo significativo na heurística do jogo. Esta função analisa se uma peça pode ser capturada após 2 lances, o que é um cálculo importante para a avaliação da posição.

A implementação original era muito custosa:
- Gerava cópias completas do tabuleiro para cada movimento possível
- Realizava uma busca minimax de profundidade 2 para cada peça
- Criava várias cópias de tabuleiros durante a análise
- Consumia uma parte significativa do tempo de execução da heurística

A nova implementação foi otimizada para:
1. Utilizar um cache para evitar recálculos de posições já analisadas
2. Fazer uma verificação rápida de ameaça direta (em 1 lance) antes de fazer análises mais profundas
3. Verificar se a peça está protegida, o que reduz a chance de ser ameaçada em 2 lances
4. Substituir a busca minimax por uma análise estatística da presença de atacantes e defensores nas diagonais próximas
5. Considerar apenas as diagonais relevantes, já que damas só se movem nessas direções

As melhorias resultaram em:
- Redução significativa no tempo de execução da função
- Diminuição da sobrecarga de criação de cópias do tabuleiro
- Melhoria na taxa de nós por segundo processados pelo motor de busca

### Ferramentas de Análise de Desempenho

Foi desenvolvido um script `analisa_perfil.py` que permite analisar detalhadamente o perfil de desempenho do motor, identificando:
- Funções mais custosas em termos de tempo
- Quantidade de chamadas por função
- Tempo médio por chamada
- Percentual do tempo total consumido por cada função

Este script é particularmente útil para identificar gargalos e direcionar esforços de otimização. 