from typing import List

class Move:
    """
    Representa um movimento no tabuleiro.
    - path: lista de índices das casas visitadas (inclui origem, capturas e destino)
    - captured: lista de índices das peças capturadas
    """
    def __init__(self, path: List[int], captured: List[int] = None):
        self.path = path  # Exemplo: [12, 19, 26] (origem -> destino)
        self.captured = captured if captured is not None else []

    def is_capture(self) -> bool:
        """Retorna True se o movimento for uma captura."""
        return len(self.captured) > 0

    def __str__(self):
        if self.is_capture():
            return f"Capture: {' -> '.join(map(str, self.path))} | Captured: {self.captured}"
        else:
            return f"Move: {self.path[0]} -> {self.path[-1]}" 