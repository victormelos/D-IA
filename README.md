# Damas Brasileiras - Bitboard Engine

Este projeto implementa as regras das Damas Brasileiras usando bitboards para máxima performance e clareza, seguindo Clean Code e Clean Architecture.

## Estrutura do Projeto
- `board.py`: Estruturas e funções principais do tabuleiro
- `move.py`: Representação e utilitários de movimentos
- `engine.py`: Geração de movimentos, aplicação e avaliação
- `tests/`: Testes unitários
- `benchmarks.py`: Benchmark de performance

## Exemplo de uso
```python
from board import Board

board = Board.initial()
print(board)
```

## Como rodar os testes

```bash
python -m unittest discover tests
```

## Próximos passos
- Implementar geração de movimentos e capturas
- Implementar heurística de avaliação
- Adicionar benchmarks

## Observações
- Todo o tratamento do tabuleiro é feito com operações binárias (bitwise) para garantir performance.
- O código está preparado para receber algoritmos de IA como Alpha-Beta, Iterative Deepening, etc. 