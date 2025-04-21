# -*- coding: utf-8 -*-
# damas_gui.py (v9.4: Compatibilidade com IA v12.3)

import pygame
import sys
import time
import traceback  # Importar o módulo traceback
from threading import Thread
from typing import List, Tuple, Optional, Dict, Set
import logging

# Importa a lógica do jogo
from damas_logic import (
    Tabuleiro, Partida, MotorIA, Peca, Movimento, Posicao,
    BRANCO, PRETO, VAZIO, PEDRA, DAMA,
    TAMANHO_TABULEIRO, PROFUNDIDADE_IA, TEMPO_PADRAO_IA, TempoExcedidoError
)
from damas_logic import logger
# Adiciona o import do visualizador de debug
from debug_visual import draw_debug_info, draw_debug_panel, render_log_panel

# --- Constantes ---
# PROFUNDIDADE_GUI = 10 # Não mais necessário, usa da lógica
# TEMPO_LIMITE_GUI = 18.0 # Não é mais necessário

BOARD_SIZE = 560; MARGIN_X = 40; MARGIN_Y = 40; INFO_AREA_HEIGHT = 60
LARGURA_TELA = BOARD_SIZE + 2 * MARGIN_X; ALTURA_TELA = BOARD_SIZE + 2 * MARGIN_Y + INFO_AREA_HEIGHT
TAMANHO_QUADRADO = BOARD_SIZE // TAMANHO_TABULEIRO
RAIO_PECA = int(TAMANHO_QUADRADO * 0.38); RAIO_COROA = int(RAIO_PECA * 0.5)
# Cores
COR_FUNDO_JANELA=(30,30,30); COR_QUADRADO_CLARO=(235,210,180); COR_QUADRADO_ESCURO=(140,90,60); COR_PECA_BRANCA_BASE=(245,245,245); COR_PECA_BRANCA_SOMBRA=(180,180,180); COR_PECA_PRETA_BASE=(45,45,45); COR_PECA_PRETA_LUZ=(100,100,100); COR_DAMA_SIMBOLO=(255,215,0); COR_DESTAQUE_SELECAO=(0,255,0,100); COR_DESTAQUE_MOVIMENTO=(0,150,255,100); COR_SUGESTAO_FUNDO=(255,165,0,90); COR_SUGESTAO_LINHA=(255,165,0); COR_TEXTO_COORDENADA=(200,200,200); COR_TEXTO_INFO=(230,230,230); COR_FUNDO_INFO=(50,50,50); COR_FIM_JOGO_FUNDO=(0,0,0,200); COR_FIM_JOGO_TEXTO_VITORIA_B=(255,255,255); COR_FIM_JOGO_TEXTO_VITORIA_P=(200,200,200); COR_FIM_JOGO_TEXTO_EMPATE=(180,180,180)

# --- Variáveis Globais para Fontes ---
FONTE_COORDENADA = None; FONTE_INFO = None; FONTE_FIM_JOGO = None; FONTE_MENU = None

# --- Nomes dos Jogadores ---
NOME_JOGADOR_BRANCO = "EU (Assistido)"; NOME_JOGADOR_PRETO = "Oponente"

# --- Funções Auxiliares e de Desenho ---
def get_pos_tabuleiro_from_pixel(pos_pixel: Tuple[int, int]) -> Optional[Posicao]: x_pixel,y_pixel=pos_pixel; x_board=x_pixel-MARGIN_X; y_board=y_pixel-MARGIN_Y; return (y_board//TAMANHO_QUADRADO, x_board//TAMANHO_QUADRADO) if 0<=x_board<BOARD_SIZE and 0<=y_board<BOARD_SIZE else None
def get_centro_quadrado_pixel(pos_tabuleiro: Posicao) -> Tuple[int, int]: linha,coluna=pos_tabuleiro; cx=MARGIN_X+coluna*TAMANHO_QUADRADO+TAMANHO_QUADRADO//2; cy=MARGIN_Y+linha*TAMANHO_QUADRADO+TAMANHO_QUADRADO//2; return cx,cy
def desenhar_gui_frame(tela): tela.fill(COR_FUNDO_JANELA); info_rect=pygame.Rect(0, BOARD_SIZE+2*MARGIN_Y, LARGURA_TELA, INFO_AREA_HEIGHT); pygame.draw.rect(tela, COR_FUNDO_INFO, info_rect); ... # Função completa como antes
def desenhar_tabuleiro(tela): ... # Função completa como antes
def desenhar_pecas(tela, tabuleiro: Tabuleiro): ... # Função completa como antes
def desenhar_destaques(tela, pos_sel: Optional[Posicao], destinos: List[Posicao]): ... # Função completa como antes
def desenhar_sugestao_ia(tela, mov_sug: Optional[Movimento]): ... # Função completa como antes
def desenhar_linha_sugestao_ia(tela, mov_sug: Optional[Movimento]): ... # Função completa como antes
def desenhar_area_info(tela, msg: str):
    area_y=BOARD_SIZE+2*MARGIN_Y; info_rect=pygame.Rect(0,area_y,LARGURA_TELA,INFO_AREA_HEIGHT); pygame.draw.rect(tela,COR_FUNDO_INFO,info_rect)
    if not FONTE_INFO: return
    
    # Verificar se a mensagem contém indicação de Aspiration Windows
    if "[IA] Usando Aspiration Windows" in msg:
        # Destacar visualmente quando estiver usando janelas de aspiração
        cor_texto = (255, 215, 0)  # Dourado para destacar
    else:
        cor_texto = COR_TEXTO_INFO
        
    texto_surf=FONTE_INFO.render(msg,True,cor_texto); texto_rect=texto_surf.get_rect(center=(LARGURA_TELA//2,area_y+INFO_AREA_HEIGHT//2)); tela.blit(texto_surf,texto_rect)
def mostrar_mensagem_fim_jogo(tela, vencedor: int): ... # Função completa como antes
def get_pos_tabuleiro_from_pixel(pos_pixel: Tuple[int, int]) -> Optional[Posicao]:
    x_pixel,y_pixel=pos_pixel; x_board=x_pixel-MARGIN_X; y_board=y_pixel-MARGIN_Y
    if 0<=x_board<BOARD_SIZE and 0<=y_board<BOARD_SIZE: return (y_board//TAMANHO_QUADRADO, x_board//TAMANHO_QUADRADO)
    return None
def get_centro_quadrado_pixel(pos_tabuleiro: Posicao) -> Tuple[int, int]:
    linha,coluna=pos_tabuleiro; cx=MARGIN_X+coluna*TAMANHO_QUADRADO+TAMANHO_QUADRADO//2; cy=MARGIN_Y+linha*TAMANHO_QUADRADO+TAMANHO_QUADRADO//2; return cx,cy
def desenhar_gui_frame(tela):
    tela.fill(COR_FUNDO_JANELA); info_rect=pygame.Rect(0, BOARD_SIZE+2*MARGIN_Y, LARGURA_TELA, INFO_AREA_HEIGHT); pygame.draw.rect(tela, COR_FUNDO_INFO, info_rect)
    if not FONTE_COORDENADA: return
    for i in range(TAMANHO_TABULEIRO):
        letra=chr(ord('a')+i); texto_surf=FONTE_COORDENADA.render(letra,True,COR_TEXTO_COORDENADA); cx=MARGIN_X+i*TAMANHO_QUADRADO+TAMANHO_QUADRADO//2
        rect_t=texto_surf.get_rect(center=(cx,MARGIN_Y//2)); rect_b=texto_surf.get_rect(center=(cx,MARGIN_Y+BOARD_SIZE+MARGIN_Y//2)); tela.blit(texto_surf,rect_t); tela.blit(texto_surf,rect_b)
        numero=str(TAMANHO_TABULEIRO-i); texto_surf=FONTE_COORDENADA.render(numero,True,COR_TEXTO_COORDENADA); cy=MARGIN_Y+i*TAMANHO_QUADRADO+TAMANHO_QUADRADO//2
        rect_l=texto_surf.get_rect(center=(MARGIN_X//2,cy)); rect_r=texto_surf.get_rect(center=(MARGIN_X+BOARD_SIZE+MARGIN_X//2,cy)); tela.blit(texto_surf,rect_l); tela.blit(texto_surf,rect_r)
def desenhar_tabuleiro(tela):
    for r in range(TAMANHO_TABULEIRO):
        for c in range(TAMANHO_TABULEIRO): x_t=MARGIN_X+c*TAMANHO_QUADRADO; y_t=MARGIN_Y+r*TAMANHO_QUADRADO; cor=COR_QUADRADO_CLARO if (r+c)%2==0 else COR_QUADRADO_ESCURO; pygame.draw.rect(tela,cor,(x_t,y_t,TAMANHO_QUADRADO,TAMANHO_QUADRADO))
def desenhar_pecas(tela, tabuleiro: Tabuleiro):
    for r in range(TAMANHO_TABULEIRO):
        for c in range(TAMANHO_TABULEIRO):
            pv=tabuleiro.grid[r][c]
            if pv!=VAZIO:
                cor=Peca.get_cor(pv); tipo=Peca.get_tipo(pv); cx,cy=get_centro_quadrado_pixel((r,c)); offset=2
                if cor==BRANCO: cb=COR_PECA_BRANCA_BASE; cs=COR_PECA_BRANCA_SOMBRA; pygame.draw.circle(tela,cs,(cx+offset,cy+offset),RAIO_PECA)
                else: cb=COR_PECA_PRETA_BASE; cl=COR_PECA_PRETA_LUZ; pygame.draw.circle(tela,cl,(cx-offset,cy-offset),RAIO_PECA)
                pygame.draw.circle(tela,cb,(cx,cy),RAIO_PECA)
                if tipo==DAMA: pygame.draw.circle(tela,COR_DAMA_SIMBOLO,(cx,cy),RAIO_COROA); pygame.draw.circle(tela,COR_FUNDO_JANELA,(cx,cy),RAIO_COROA,1)
def desenhar_destaques(tela, pos_sel: Optional[Posicao], destinos: List[Posicao]):
    if pos_sel:
        cx,cy=get_centro_quadrado_pixel(pos_sel); surf_sel=pygame.Surface((RAIO_PECA*2+10,RAIO_PECA*2+10),pygame.SRCALPHA); pygame.draw.circle(surf_sel,COR_DESTAQUE_SELECAO,(surf_sel.get_width()//2,surf_sel.get_height()//2),RAIO_PECA+4); tela.blit(surf_sel,(cx-surf_sel.get_width()//2,cy-surf_sel.get_height()//2))
    for pos_d in destinos:
        cx,cy=get_centro_quadrado_pixel(pos_d); surf_mov=pygame.Surface((RAIO_PECA,RAIO_PECA),pygame.SRCALPHA); pygame.draw.circle(surf_mov,COR_DESTAQUE_MOVIMENTO,(RAIO_PECA//2,RAIO_PECA//2),RAIO_PECA//2); tela.blit(surf_mov,(cx-RAIO_PECA//2,cy-RAIO_PECA//2))
def desenhar_sugestao_ia(tela, mov_sug: Optional[Movimento]):
    if mov_sug and len(mov_sug)>=2:
        for pos in mov_sug: r,c=pos; xt=MARGIN_X+c*TAMANHO_QUADRADO; yt=MARGIN_Y+r*TAMANHO_QUADRADO; surf_sug=pygame.Surface((TAMANHO_QUADRADO,TAMANHO_QUADRADO),pygame.SRCALPHA); surf_sug.fill(COR_SUGESTAO_FUNDO); tela.blit(surf_sug,(xt,yt))
def desenhar_linha_sugestao_ia(tela, mov_sug: Optional[Movimento]):
    if mov_sug and len(mov_sug)>=2: pontos=[get_centro_quadrado_pixel(pos) for pos in mov_sug]; pygame.draw.lines(tela,COR_SUGESTAO_LINHA,False,pontos,5)
def desenhar_area_info(tela, msg: str):
    area_y=BOARD_SIZE+2*MARGIN_Y; info_rect=pygame.Rect(0,area_y,LARGURA_TELA,INFO_AREA_HEIGHT); pygame.draw.rect(tela,COR_FUNDO_INFO,info_rect)
    if not FONTE_INFO: return
    
    # Verificar se a mensagem contém indicação de Aspiration Windows
    if "[IA] Usando Aspiration Windows" in msg:
        # Destacar visualmente quando estiver usando janelas de aspiração
        cor_texto = (255, 215, 0)  # Dourado para destacar
    else:
        cor_texto = COR_TEXTO_INFO
        
    texto_surf=FONTE_INFO.render(msg,True,cor_texto); texto_rect=texto_surf.get_rect(center=(LARGURA_TELA//2,area_y+INFO_AREA_HEIGHT//2)); tela.blit(texto_surf,texto_rect)
def mostrar_mensagem_fim_jogo(tela, vencedor: int):
    if not FONTE_FIM_JOGO: return
    if vencedor==VAZIO: msg="Empate!"
    elif vencedor==BRANCO: msg=f"{NOME_JOGADOR_BRANCO} Venceu!"
    else: msg=f"{NOME_JOGADOR_PRETO} Venceu!"
    cor_texto = COR_FIM_JOGO_TEXTO_EMPATE if vencedor == VAZIO else (COR_FIM_JOGO_TEXTO_VITORIA_B if vencedor == BRANCO else COR_FIM_JOGO_TEXTO_VITORIA_P)
    texto_surf=FONTE_FIM_JOGO.render(msg,True,cor_texto); texto_rect=texto_surf.get_rect(center=(LARGURA_TELA//2,ALTURA_TELA//2-20))
    fundo_rect=texto_rect.inflate(60,40); fundo_surf=pygame.Surface(fundo_rect.size,pygame.SRCALPHA); fundo_surf.fill(COR_FIM_JOGO_FUNDO); tela.blit(fundo_surf,fundo_rect.topleft); tela.blit(texto_surf,texto_rect)


# --- Função para Calcular Sugestão em Thread ---
def calcular_sugestao_thread(partida, motor_ia, resultado_calculo):
    """Thread para calcular movimento sugerido pela IA sem travar a interface."""
    try:
        # Interceptar mensagens de print para capturar informações de Aspiration Windows e reuso
        _stdout_original = sys.stdout
        _mensagens_aspiration = []
        _mensagens_reuso = []
        
        # Sistema de interceptação de prints
        class PrintInterceptor:
            def __init__(self):
                self.captured_text = ""
            
            def write(self, text):
                # Escrever no stdout original para não perder os logs
                _stdout_original.write(text)
                
                # Capturar mensagens específicas sobre Aspiration Windows
                if "Aspiration Windows" in text or "janela" in text.lower():
                    _mensagens_aspiration.append(text.strip())
                    resultado_calculo['status_aspiration'] = text.strip()
                
                # Capturar mensagens sobre reuso de resultados
                if "reuso" in text.lower() or "reusando" in text.lower() or "reaproveitando" in text.lower():
                    _mensagens_reuso.append(text.strip())
                    resultado_calculo['reuso_info'] = text.strip()
                
                self.captured_text += text
                
            def flush(self):
                _stdout_original.flush()
        
        # Substituir temporariamente o stdout para interceptar prints
        interceptor = PrintInterceptor()
        sys.stdout = interceptor
        
        # Iniciar timer
        tempo_inicio = time.time()
        
        # Encontrar melhor movimento - Corrigido para usar o método correto
        partida._atualizar_movimentos_legais()  # Garantir que os movimentos foram atualizados
        movimento = motor_ia.encontrar_melhor_movimento(partida, partida.jogador_atual, partida.movimentos_legais_atuais)
        
        # Restaurar stdout
        sys.stdout = _stdout_original
        
        # Calcular tempo gasto
        tempo_gasto = time.time() - tempo_inicio
        
        # Armazenar resultados
        resultado_calculo['movimento'] = movimento
        resultado_calculo['status'] = f"Tempo: {tempo_gasto:.2f}s"
        
        # Salvar estatísticas finais do motor para mostrar na interface
        resultado_calculo['estatisticas'] = motor_ia.obter_estatisticas_aspiration()
        
        print(f"Thread concluída. Movimento: {movimento}, Tempo: {tempo_gasto:.2f}s")
        
    except KeyboardInterrupt:
        sys.stdout = _stdout_original  # Restaurar em caso de interrupção
        print("Thread interrompida pelo usuário")
        resultado_calculo['status'] = "Interrompido"
        
    except Exception as e:
        sys.stdout = _stdout_original  # Restaurar em caso de erro
        print(f"Erro na thread de cálculo: {e}")
        traceback.print_exc()
        resultado_calculo['status'] = f"Erro: {e}"

# --- Função para Tela de Seleção Inicial ---
def tela_selecao_inicio(tela) -> int:
    global FONTE_MENU, FONTE_INFO
    botao_eu_rect=pygame.Rect(LARGURA_TELA//4, ALTURA_TELA//2-50, LARGURA_TELA//2, 60); botao_oponente_rect=pygame.Rect(LARGURA_TELA//4, ALTURA_TELA//2+30, LARGURA_TELA//2, 60)
    cor_botao=(70,70,90); cor_botao_hover=(100,100,120); cor_texto_botao=(220,220,255); clock=pygame.time.Clock()
    while True:
        mouse_pos=pygame.mouse.get_pos(); hover_eu=botao_eu_rect.collidepoint(mouse_pos); hover_oponente=botao_oponente_rect.collidepoint(mouse_pos)
        for event in pygame.event.get():
            if event.type==pygame.QUIT: pygame.quit(); sys.exit()
            if event.type==pygame.MOUSEBUTTONDOWN:
                if hover_eu: print("Jogador escolheu 'EU' para começar."); return BRANCO
                if hover_oponente: print("Jogador escolheu 'Oponente' para começar."); return PRETO
        tela.fill(COR_FUNDO_JANELA);
        fnt_menu = FONTE_MENU if FONTE_MENU else pygame.font.Font(None, 40)
        titulo_surf = fnt_menu.render("Quem Começa?", True, COR_TEXTO_INFO)
        titulo_rect=titulo_surf.get_rect(center=(LARGURA_TELA//2, ALTURA_TELA//4)); tela.blit(titulo_surf, titulo_rect)
        fnt_info = FONTE_INFO if FONTE_INFO else pygame.font.Font(None, 26)
        cor_atual_eu=cor_botao_hover if hover_eu else cor_botao; pygame.draw.rect(tela, cor_atual_eu, botao_eu_rect, border_radius=10);
        texto_eu_surf = fnt_info.render(NOME_JOGADOR_BRANCO, True, cor_texto_botao)
        texto_eu_rect=texto_eu_surf.get_rect(center=botao_eu_rect.center); tela.blit(texto_eu_surf, texto_eu_rect)
        cor_atual_oponente=cor_botao_hover if hover_oponente else cor_botao; pygame.draw.rect(tela, cor_atual_oponente, botao_oponente_rect, border_radius=10);
        texto_oponente_surf = fnt_info.render(NOME_JOGADOR_PRETO, True, cor_texto_botao)
        texto_oponente_rect=texto_oponente_surf.get_rect(center=botao_oponente_rect.center);
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # <<<<<<<<<<<<<<<<<<<<<< CORREÇÃO DA LINHA ABAIXO >>>>>>>>>>>>>>>>>>>>>>
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        tela.blit(texto_oponente_surf, texto_oponente_rect) # Usa as variáveis corretas
        pygame.display.flip(); clock.tick(30)

# --- Loop Principal do Jogo ---
def main():
    global FONTE_COORDENADA, FONTE_INFO, FONTE_FIM_JOGO, FONTE_MENU
    pygame.init()
    try:
        FONTE_COORDENADA = pygame.font.SysFont("Arial", 18); FONTE_INFO = pygame.font.SysFont("Verdana", 20); FONTE_FIM_JOGO = pygame.font.SysFont("Arial Black", 48); FONTE_MENU = pygame.font.SysFont("Arial", 36); print("Fontes do sistema carregadas.")
    except Exception as e:
        print(f"Aviso: Fontes não encontradas ({e})."); FONTE_COORDENADA = pygame.font.Font(None, 22); FONTE_INFO = pygame.font.Font(None, 26); FONTE_FIM_JOGO = pygame.font.Font(None, 60); FONTE_MENU = pygame.font.Font(None, 40)
        if not all([FONTE_COORDENADA, FONTE_INFO, FONTE_FIM_JOGO, FONTE_MENU]): print("ERRO CRÍTICO: Fontes não carregadas."); pygame.quit(); sys.exit()

    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA)); pygame.display.set_caption("Damas Brasileiras - EU vs Oponente"); clock = pygame.time.Clock()

    jogador_inicial = tela_selecao_inicio(tela)
    partida = Partida(jogador_branco=NOME_JOGADOR_BRANCO, jogador_preto=NOME_JOGADOR_PRETO)

    # Cria IA passando a profundidade e tempo limite definidos na lógica
    ia_assistente = MotorIA(profundidade=PROFUNDIDADE_IA, tempo_limite=TEMPO_PADRAO_IA)

    if jogador_inicial == PRETO: partida.jogador_atual = PRETO; partida._atualizar_movimentos_legais()

    peca_selecionada_pos: Optional[Posicao] = None; movimentos_validos_selecionada: List[Movimento] = []; destinos_possiveis_selecionada: List[Posicao] = []
    movimento_sugerido_ia: Optional[Movimento] = None; calculando_sugestao: bool = False; thread_calculo: Optional[Thread] = None
    resultado_calculo: dict = {'movimento': None, 'status': None, 'status_aspiration': None, 'reuso_info': None}; precisa_calcular_sugestao = (partida.jogador_atual == BRANCO)
    mensagem_info = ""; rodando = True
    scroll_offset = 0  # Para rolagem do painel lateral

    # Adicionar nova mensagem de ajuda sobre a tecla 'i'
    if resultado_calculo.get('status_aspiration'):
        mensagem_info = "Pressione 'I' para ver estatísticas de Aspiration Windows"

    log_lines = []  # Lista para armazenar logs

    # Handler customizado para capturar logs
    class GuiLogHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            log_lines.append(msg)
    gui_handler = GuiLogHandler()
    gui_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    if not any(isinstance(h, GuiLogHandler) for h in logger.handlers):
        logger.addHandler(gui_handler)

    while rodando:
        # Atualizar Mensagem
        if not calculando_sugestao and partida.vencedor is None:
            nome_vez = NOME_JOGADOR_BRANCO if partida.jogador_atual == BRANCO else NOME_JOGADOR_PRETO
            # prof_atingida_str = "" # Removido
            if partida.jogador_atual == BRANCO:
                if movimento_sugerido_ia: 
                    path="->".join([Tabuleiro.pos_para_alg(p) for p in movimento_sugerido_ia])
                    # Mostrar informações de Aspiration Windows se disponíveis
                    if resultado_calculo.get('status_aspiration'):
                        # Extrair as informações de janela da mensagem
                        msg_aspir = resultado_calculo.get('status_aspiration')
                        if "Usando Aspiration Windows" in msg_aspir:
                            msg = f"{msg_aspir} | Movimento: {path}"
                        else:
                            msg = f"IA Sugere: {path}. Vez de {nome_vez}."
                    else:
                        msg = f"IA Sugere: {path}. Vez de {nome_vez}."
                        
                    # Adicionar indicador de estatísticas quando disponíveis
                    if 'estatisticas' in resultado_calculo and resultado_calculo['estatisticas']:
                        stats = resultado_calculo['estatisticas']
                        if stats.get('movimentos_reusados', 0) > 0:
                            msg += f" | Reuso: {stats['movimentos_reusados']} movs em {stats['busca_otimizada']} buscas"
                            
                elif precisa_calcular_sugestao: msg = f"Vez de {nome_vez}. Calculando sugestão..."
                else: msg = f"Vez de {nome_vez}. Clique na peça e no destino."
            else: msg = f"Vez de {nome_vez}. Clique na peça e no destino."
            mensagem_info = msg
        elif calculando_sugestao: 
            # Verificar se temos informações de Aspiration Windows durante o cálculo
            if resultado_calculo.get('reuso_info'):
                # Informação de reuso mais recente tem prioridade
                mensagem_info = resultado_calculo.get('reuso_info')
            elif resultado_calculo.get('status_aspiration'):
                mensagem_info = resultado_calculo.get('status_aspiration')
            else:
                mensagem_info = f"{NOME_JOGADOR_BRANCO} (IA) está pensando..."

        # Cálculo Sugestão
        if precisa_calcular_sugestao and partida.jogador_atual == BRANCO and partida.vencedor is None and not calculando_sugestao and thread_calculo is None:
            partida._atualizar_movimentos_legais()
            if not partida.movimentos_legais_atuais: print("Aviso: EU sem movimentos"); precisa_calcular_sugestao = False; mensagem_info = f"Vez de {NOME_JOGADOR_BRANCO} - Sem movimentos."
            else: print("Iniciando thread..."); calculando_sugestao = True; precisa_calcular_sugestao = False; resultado_calculo = {'movimento': None, 'status': None, 'status_aspiration': None, 'reuso_info': None}; thread_calculo = Thread(target=calcular_sugestao_thread, args=(partida, ia_assistente, resultado_calculo), daemon=True); thread_calculo.start()
        if calculando_sugestao and thread_calculo is not None and not thread_calculo.is_alive(): print("Thread finalizada."); calculando_sugestao = False; thread_calculo = None; movimento_sugerido_ia = resultado_calculo.get('movimento'); peca_selecionada_pos=None; movimentos_validos_selecionada=[]; destinos_possiveis_selecionada=[]

        # Eventos
        eventos = pygame.event.get()
        for event in eventos:
            if event.type == pygame.QUIT: rodando = False; break
            
            # Tecla 'i' para mostrar estatísticas de Aspiration Windows
            if event.type == pygame.KEYDOWN and event.key == pygame.K_i and not calculando_sugestao:
                # Verificar se temos estatísticas para mostrar
                stats = ia_assistente.obter_estatisticas_aspiration()
                if stats and 'janelas_usadas' in stats and len(stats['janelas_usadas']) > 0:
                    mostrar_estatisticas_aspiration(tela, ia_assistente)
                else:
                    # Mostrar mensagem que não há estatísticas
                    mensagem = "Sem estatísticas de Aspiration Windows disponíveis"
                    fonte_info = FONTE_INFO if FONTE_INFO else pygame.font.Font(None, 24)
                    texto_surf = fonte_info.render(mensagem, True, (255, 100, 100))
                    texto_rect = texto_surf.get_rect(center=(LARGURA_TELA//2, ALTURA_TELA//2))
                    tela_anterior = tela.copy()  # Guardar tela atual
                    tela.fill((30, 30, 45))
                    tela.blit(texto_surf, texto_rect)
                    pygame.display.flip()
                    pygame.time.delay(1500)  # Mostrar a mensagem por 1.5 segundos
                    tela.blit(tela_anterior, (0, 0))  # Restaurar tela anterior
                    pygame.display.flip()  # Atualizar a tela com o conteúdo anterior
                continue
                
            if calculando_sugestao: continue
            if event.type == pygame.MOUSEBUTTONDOWN and partida.vencedor is None:
                pos_px = pygame.mouse.get_pos(); pos_tab = get_pos_tabuleiro_from_pixel(pos_px)
                if pos_tab:
                    jogador = partida.jogador_atual
                    if peca_selecionada_pos is None:
                        pv = partida.tabuleiro.get_peca(pos_tab)
                        if Peca.get_cor(pv) == jogador:
                            movs = [m for m in partida.movimentos_legais_atuais if m[0] == pos_tab]
                            if movs: peca_selecionada_pos=pos_tab; movimentos_validos_selecionada=movs; destinos_possiveis_selecionada=[m[-1] for m in movs]; movimento_sugerido_ia=None
                    else:
                        if pos_tab in destinos_possiveis_selecionada:
                            mov_exec = next((m for m in movimentos_validos_selecionada if m[-1]==pos_tab), None)
                            if mov_exec:
                                j_antes=partida.jogador_atual; peca_selecionada_pos=None; movimentos_validos_selecionada=[]; destinos_possiveis_selecionada=[]; movimento_sugerido_ia=None
                                sucesso=partida.executar_lance_completo(mov_exec)
                                if sucesso and j_antes == PRETO and partida.jogador_atual == BRANCO: precisa_calcular_sugestao = True
                        elif pos_tab == peca_selecionada_pos: peca_selecionada_pos=None; movimentos_validos_selecionada=[]; destinos_possiveis_selecionada=[]
                        else:
                            pv = partida.tabuleiro.get_peca(pos_tab)
                            if Peca.get_cor(pv) == jogador:
                                movs = [m for m in partida.movimentos_legais_atuais if m[0]==pos_tab]
                                if movs: peca_selecionada_pos=pos_tab; movimentos_validos_selecionada=movs; destinos_possiveis_selecionada=[m[-1] for m in movs]; movimento_sugerido_ia = None
                                else: peca_selecionada_pos=None; movimentos_validos_selecionada=[]; destinos_possiveis_selecionada=[]
                            else: peca_selecionada_pos=None; movimentos_validos_selecionada=[]; destinos_possiveis_selecionada=[]
                # else: Clicou fora
            # Suporte à rolagem do painel lateral
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    scroll_offset = max(scroll_offset - 30, 0)
                elif event.button == 5:  # Scroll down
                    scroll_offset = scroll_offset + 30
            # Toggle de verbosidade do logger com a tecla 'V'
            if event.type == pygame.KEYDOWN and event.key == pygame.K_v:
                if logger.level == logging.DEBUG:
                    logger.setLevel(logging.INFO)
                    print("[DEBUG] Logger set to INFO (modo silencioso)")
                else:
                    logger.setLevel(logging.DEBUG)
                    print("[DEBUG] Logger set to DEBUG (modo verboso)")

        if not rodando: break

        # Desenho
        desenhar_gui_frame(tela); desenhar_tabuleiro(tela)
        if not calculando_sugestao and partida.jogador_atual == BRANCO: desenhar_sugestao_ia(tela, movimento_sugerido_ia)
        desenhar_destaques(tela, peca_selecionada_pos, destinos_possiveis_selecionada)
        desenhar_pecas(tela, partida.tabuleiro)
        if not calculando_sugestao and partida.jogador_atual == BRANCO: desenhar_linha_sugestao_ia(tela, movimento_sugerido_ia)

        # === DEBUG VISUAL SOBRE O TABULEIRO ===
        partida.tabuleiro.avaliar_heuristica(BRANCO, debug_aval=True)
        debug_info = getattr(partida.tabuleiro, '_last_debug_info', [])
        draw_debug_info(
            tela,
            debug_info,
            TAMANHO_QUADRADO,
            (MARGIN_X, MARGIN_Y)
        )
        # Painel lateral detalhado com scroll
        draw_debug_panel(
            tela,
            debug_info,
            TAMANHO_QUADRADO,
            (MARGIN_X, MARGIN_Y),
            ALTURA_TELA,
            scroll_offset
        )
        # Painel de logs ao lado do painel de debug
        render_log_panel(
            tela,
            log_lines,
            MARGIN_X + TAMANHO_QUADRADO * 8 + 20 + 340 + 10,  # x0: após painel de debug
            MARGIN_Y,                                         # y0
            340,                                              # largura
            ALTURA_TELA                                       # altura
        )
        # ======================================

        # Adicionar dica sobre a tecla 'i' quando estatísticas estiverem disponíveis
        if not calculando_sugestao and ia_assistente.obter_estatisticas_aspiration()['janelas_usadas']:
            mensagem_info += " (I: Estatísticas)"
            
        desenhar_area_info(tela, mensagem_info)
        if partida.vencedor is not None: mostrar_mensagem_fim_jogo(tela, partida.vencedor)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

def mostrar_estatisticas_aspiration(tela, ia_assistente: MotorIA):
    """Exibe estatísticas detalhadas da técnica Aspiration Windows."""
    global FONTE_INFO, FONTE_COORDENADA, FONTE_MENU
    
    stats = ia_assistente.obter_estatisticas_aspiration()
    
    # Preparar fontes
    fonte_titulo = FONTE_MENU if FONTE_MENU else pygame.font.Font(None, 36)
    fonte_info = FONTE_INFO if FONTE_INFO else pygame.font.Font(None, 24)
    fonte_dados = FONTE_COORDENADA if FONTE_COORDENADA else pygame.font.Font(None, 20)
    
    # Cores
    cor_fundo = (30, 30, 45)
    cor_titulo = (255, 215, 0)  # Dourado
    cor_texto = (220, 220, 220)
    cor_sucesso = (100, 255, 100)
    cor_falha = (255, 100, 100)
    cor_reuso = (100, 200, 255)  # Azul claro para dados de reuso
    
    # Preencher o fundo
    tela.fill(cor_fundo)
    
    # Título com versão do algoritmo
    titulo_surf = fonte_titulo.render(f"Estatísticas - {getattr(ia_assistente, 'versao', 'Aspiration Windows')}", True, cor_titulo)
    titulo_rect = titulo_surf.get_rect(center=(LARGURA_TELA//2, 40))
    tela.blit(titulo_surf, titulo_rect)
    
    # Estatísticas gerais
    y_pos = 90
    info_geral_surf = fonte_info.render(
        f"Sucessos: {stats['sucessos']}   Falhas: {stats['falhas']}   Taxa de Sucesso: {stats['taxa_sucesso']:.1f}%", 
        True, cor_texto
    )
    info_geral_rect = info_geral_surf.get_rect(center=(LARGURA_TELA//2, y_pos))
    tela.blit(info_geral_surf, info_geral_rect)
    
    # Estatísticas de reuso
    if 'movimentos_reusados' in stats and stats['movimentos_reusados'] > 0:
        y_pos += 30
        info_reuso_surf = fonte_info.render(
            f"Reuso: {stats['movimentos_reusados']} movimentos reusados em {stats['busca_otimizada']} buscas", 
            True, cor_reuso
        )
        info_reuso_rect = info_reuso_surf.get_rect(center=(LARGURA_TELA//2, y_pos))
        tela.blit(info_reuso_surf, info_reuso_rect)
    
    # Cabeçalho da tabela
    y_pos += 50
    cabecalho = ["Prof", "Base", "Delta", "Janela (Alpha-Beta)"]
    x_pos = [100, 200, 300, 400]
    for i, texto in enumerate(cabecalho):
        cab_surf = fonte_info.render(texto, True, cor_titulo)
        cab_rect = cab_surf.get_rect(midleft=(x_pos[i], y_pos))
        tela.blit(cab_surf, cab_rect)
    
    # Dados da tabela - mostrar as últimas 15 janelas usadas (ou todas, se forem menos)
    y_pos += 30
    janelas = stats['janelas_usadas'][-15:] if len(stats['janelas_usadas']) > 15 else stats['janelas_usadas']
    
    for janela in janelas:
        prof = str(janela['profundidade'])
        base = f"{janela['base']:.2f}"
        delta = f"{janela['delta']:.2f}"
        janela_str = f"[{janela['alpha']:.2f}, {janela['beta']:.2f}]"
        
        dados = [prof, base, delta, janela_str]
        for i, texto in enumerate(dados):
            dado_surf = fonte_dados.render(texto, True, cor_texto)
            dado_rect = dado_surf.get_rect(midleft=(x_pos[i], y_pos))
            tela.blit(dado_surf, dado_rect)
        
        y_pos += 25
        if y_pos > ALTURA_TELA - 100:
            break  # Evitar exceder a altura da tela
    
    # Instruções de saída
    y_pos = ALTURA_TELA - 70
    instrucao_surf = fonte_info.render("Pressione ESC ou I para voltar ao jogo", True, cor_texto)
    instrucao_rect = instrucao_surf.get_rect(center=(LARGURA_TELA//2, y_pos))
    tela.blit(instrucao_surf, instrucao_rect)
    
    # Atualizar tela
    pygame.display.flip()
    
    # Loop para aguardar saída
    rodando = True
    while rodando:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_i:
                    rodando = False
                    break
        pygame.time.delay(30)  # Pequeno delay para não consumir CPU

def atualizar_informacoes(janela, valores, partida, resultado_sugestao=None):
    """Atualiza informações no painel lateral."""
    # Status do jogo
    janela['status'].update(f'Jogador Atual: {"EU (Brancas)" if partida.jogador_atual == BRANCO else "IA (Pretas)"}')
    janela['contador_jogadas'].update(f'Jogada: {partida.contador_jogadas}')
    
    if resultado_sugestao and 'status' in resultado_sugestao:
        # Exibir informações sobre o cálculo da IA
        if resultado_sugestao.get('movimento'):
            origem, destino = resultado_sugestao['movimento'][0], resultado_sugestao['movimento'][-1]
            movimento_formatado = " → ".join([Tabuleiro.pos_para_alg(p) for p in resultado_sugestao['movimento']])
            janela['sugestao'].update(
                f"Sugestão: {movimento_formatado}\n{resultado_sugestao['status']}"
            )
            
            # Mostrar estatísticas da IA quando disponíveis
            if 'estatisticas' in resultado_sugestao and resultado_sugestao['estatisticas']:
                estatisticas = resultado_sugestao['estatisticas']
                info_texto = (
                    f"Nós avaliados: {estatisticas.get('nos_avaliados', 'N/A')}\n"
                    f"Profundidade máx: {estatisticas.get('profundidade_max', 'N/A')}\n"
                    f"Cortes alfa-beta: {estatisticas.get('cortes_poda', 'N/A')}\n"
                )
                
                # Adicionar informações de reuso de resultados (quando disponível)
                if 'movimentos_reusados' in estatisticas and estatisticas['movimentos_reusados'] > 0:
                    info_texto += (
                        f"\nReuso: {estatisticas['movimentos_reusados']} movimentos\n"
                        f"Buscas otimizadas: {estatisticas['busca_otimizada']}\n"
                        f"Taxa de sucesso: {estatisticas['taxa_sucesso']:.1f}%"
                    )
                # Se não há reuso mas há info sobre aspiration windows
                elif resultado_sugestao.get('status_aspiration'):
                    info_texto += f"\nJanela: {resultado_sugestao['status_aspiration']}\n"
                
                janela['info_ia'].update(info_texto)
        else:
            janela['sugestao'].update(f"Aguardando cálculo...\n{resultado_sugestao['status']}")
    else:
        janela['sugestao'].update("Clique 'Sugerir Movimento' para receber ajuda.")
    
    # Atualizar contador de peças
    pecas_brancas, pecas_pretas = partida.tabuleiro.contar_pecas()
    janela['contador_pecas'].update(f'Peças: Brancas {pecas_brancas} × {pecas_pretas} Pretas')

if __name__ == "__main__":
    main()