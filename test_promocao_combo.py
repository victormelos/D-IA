import sys
sys.path.append('.')
from damas_logic import Tabuleiro, PB, PP, BRANCO, DAMA, VAZIO

def teste_promocao_sem_combo():
    tab = Tabuleiro(estado_inicial=False)
    tab.grid = [[0]*8 for _ in range(8)]
    # Branco em c2 (2,1)
    tab.grid[2][1] = PB
    # Pretas em b3 (1,2) e b5 (3,2)
    tab.grid[1][2] = PP
    tab.grid[3][2] = PP
    # Preta em e7 (1,4)
    tab.grid[1][4] = PP
    # Destinos vazios
    tab.grid[0][3] = VAZIO
    tab.grid[4][3] = VAZIO

    # Movimento: c2 -> a4 (captura b3), a4 -> d8 (captura b5 e promove)
    mov = [(2,1), (0,3)]
    # Simula o lance
    estado = tab._fazer_lance(mov, troca_turno=False)
    # Após a promoção, a dama recém-promovida está em (0,3)
    # Testa se há capturas disponíveis para ela
    capturas = tab._encontrar_capturas_recursivo((0,3), BRANCO, DAMA, [(0,3)], [])
    print(f"Capturas disponíveis para dama recém-promovida: {capturas}")
    assert capturas == [], "Não deveria haver capturas disponíveis para dama recém-promovida no mesmo turno!"
    tab._desfazer_lance(estado)
    print("Teste de promoção sem combo passou!")

if __name__ == "__main__":
    teste_promocao_sem_combo() 