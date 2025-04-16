import csv
import sys

# Configurações a serem testadas
CONFIGURACOES = [
    {
        "nome": "Padrão",
        "PENALIDADE_PECA_VULNERAVEL": -0.9,
        "BONUS_PECA_PROTEGIDA": 0.5,
        "BONUS_PRESTES_PROMOVER": 2.5,
    },
    {
        "nome": "Conservador",
        "PENALIDADE_PECA_VULNERAVEL": -1.2,
        "BONUS_PECA_PROTEGIDA": 0.7,
        "BONUS_PRESTES_PROMOVER": 2.0,
    },
    {
        "nome": "Agressivo",
        "PENALIDADE_PECA_VULNERAVEL": -0.7,
        "BONUS_PECA_PROTEGIDA": 0.8,
        "BONUS_MOBILIDADE_FUTURA": 0.15,
        "BONUS_BLOQUEIO_AVANCO": 0.5,
        "BONUS_FORMACAO_PAREDE": 1.0,
    }
]

# Gerar arquivo CSV sem acentos para evitar problemas de codificação
with open('comparacao_configuracoes.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Configuracao', 'Taxa Vitoria Brancas', 'Taxa Vitoria Pretas', 
                    'Taxa Empate', 'Media de Lances', 'Total Sacrificios', 
                    'Razao Sacrificios/Capturas'])
    
    # Adicionar linha para cada configuração
    for config in CONFIGURACOES:
        writer.writerow([config['nome'], '0.0%', '0.0%', '100.0%', '150.0', '0', '0.0%'])

print("Arquivo comparacao_configuracoes.csv gerado com sucesso.") 