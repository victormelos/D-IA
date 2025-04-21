import pygame

# Cores para o texto
TEXT_COLOR = (255, 0, 0)  # Vermelho para debug
PANEL_BG = (30, 30, 30)
FONT_SIZE = 12  # Fonte menor para não poluir
PANEL_WIDTH = 340


def draw_debug_info(screen: pygame.Surface,
                    debug_info: list,
                    tile_size: int,
                    board_offset: tuple):
    """
    Overlay simples: mostra só o score_parcial sobre cada peça
    """
    font = pygame.font.SysFont(None, FONT_SIZE)
    x_off, y_off = board_offset
    for piece in debug_info:
        pos = piece.get('pos')
        if not pos:
            continue  # Só desenha sobre peças
        row, col = pos
        x = x_off + col * tile_size + tile_size // 2
        y = y_off + row * tile_size + tile_size // 2
        valor = piece.get('score_parcial', 0)
        text = f"{valor:.1f}"
        text_surf = font.render(text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=(x, y))
        screen.blit(text_surf, text_rect)


def draw_debug_panel(screen: pygame.Surface,
                     debug_info: list,
                     tile_size: int,
                     board_offset: tuple,
                     panel_height: int,
                     scroll_offset: int = 0):
    """
    Desenha um painel lateral à direita do tabuleiro com o texto de debug detalhado.
    Suporta rolagem vertical via scroll_offset.
    """
    font = pygame.font.SysFont(None, FONT_SIZE)
    x_off, y_off = board_offset
    panel_x = x_off + tile_size * 8 + 20
    panel_y = y_off
    # Fundo do painel
    pygame.draw.rect(screen, PANEL_BG, (panel_x, panel_y, PANEL_WIDTH, panel_height))
    y_cursor = panel_y + 8 - scroll_offset
    for piece in debug_info:
        pos = piece.get('pos')
        tipo = piece.get('tipo', '?')
        if pos:
            pos_str = f"{chr(ord('a')+pos[1])}{8-pos[0]}"
        else:
            pos_str = "GLOBAL"
        header = f"{tipo} {pos_str}"
        header_surf = font.render(header, True, (255, 220, 100))
        screen.blit(header_surf, (panel_x + 8, y_cursor))
        y_cursor += FONT_SIZE + 2
        # Bônus detalhados
        for name, val in piece.get('bônus', {}).items():
            line = f"{name}: {val:.2f}"
            line_surf = font.render(line, True, TEXT_COLOR)
            screen.blit(line_surf, (panel_x + 16, y_cursor))
            y_cursor += FONT_SIZE
        # Score parcial
        score_line = f"P: {piece.get('score_parcial', 0):.2f}"
        score_surf = font.render(score_line, True, (180, 255, 180))
        screen.blit(score_surf, (panel_x + 16, y_cursor))
        y_cursor += FONT_SIZE + 4
        # Espaço extra entre peças
        if y_cursor > panel_y + panel_height:
            break  # Evita sair do painel


def render_log_panel(screen, lines, x0, y0, w, h):
    """
    Desenha um painel de logs (linhas de texto) na tela, na posição (x0, y0), com largura w e altura h.
    Mostra as últimas linhas que cabem no painel.
    """
    font = pygame.font.SysFont(None, FONT_SIZE)
    panel = pygame.Surface((w, h))
    panel.fill((20, 20, 20))
    max_lines = h // FONT_SIZE
    for i, line in enumerate(lines[-max_lines:]):
        txt = font.render(line, True, (200, 200, 200))
        panel.blit(txt, (5, i * FONT_SIZE))
    screen.blit(panel, (x0, y0)) 