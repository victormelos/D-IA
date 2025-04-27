from enum import Enum
import sys
from typing import Union

# flag global para habilitar debug (desative em produção para não frear a pesquisa)
DEBUG = False

def debug_move(depth: int, move, score: Union[float, int], forced: bool):
    """
    Imprime linha de trace padronizada se DEBUG estiver True.

    depth   – profundidade do nó (raiz = 0)
    move    – instância de Move ou string
    score   – valor estático ou alfa-beta
    forced  – True se era captura forçada
    """
    if not DEBUG:
        return
    indent = "  " * depth
    tag = f"[d={depth}]"
    forced_tag = " forced_capture=True" if forced else ""
    print(f"{indent}{tag} move {move} score={score:.2f}{forced_tag}", file=sys.stderr) 