import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'  # Hide pygame support message


import sys
import pygame
from pygame.locals import QUIT, KEYUP, K_ESCAPE
from PIL import Image, ImageTk
from fentoboardimage import fenToImage, loadPiecesFolder
import chess
from pygame._sdl2.video import Window

pieceSet=loadPiecesFolder("/media/luis/48A0CF8FA0CF8244/luis/codigo phyton lubuntu/ajedrez/fenn_board/pieces")



STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
WINDOW_CAPTION="CHESS GUI"
MARGIN = 20
class ChessGui:
    def __init__(self, board_size=640, fen=STARTING_FEN):

        
        self.board_size=board_size
        self._wnd_width=board_size + MARGIN *2
        self._wnd_height=board_size + MARGIN *3         
        self.FPS=2
        self.pause=False
        

##        os.environ['SDL_VIDEO_CENTERED'] = '1'  # Centre display window.
        WINDOW_X=100
        WINDOW_Y=50
        os.environ['SDL_VIDEO_WINDOW_POS'] = f'{WINDOW_X},{WINDOW_Y}'
        
        self.fps_clock = pygame.time.Clock()
        
        
        self._show_window(fen)
        
    def draw_text(self,cad):
        
        # create the text
        font = pygame.font.Font(None, 36)
        text = font.render(cad, 1, (50, 170, 50))
        self.surface.blit(text, (100, 5))
    def get_window_pos(self):
        window = Window.from_display_module()
        
        return window.position # tuple
    def get_window_size(self):
        window = Window.from_display_module()
        return window.size # tuple
    
    def get_image_pygame(self,fen,casillas_resaltadas=[],casillas_maquina=[]):    
    ##    fen = board.fen()    
    ##    if board.turn == chess.BLACK:        
    ##        flipped=True
    ##    else:
    ##        flipped=False    
        pil_image = fenToImage(
            fen=fen,
            squarelength=self.board_size//8,
            pieceSet=pieceSet,
            flipped=False,
            darkColor="#D18B47",
            lightColor="#FFCE9E",
            highlighting={("#00c568","#008538"): casillas_resaltadas,
                          ("#808000","#808000"): casillas_maquina})
            
        # Convertir la imagen PIL a una superficie de Pygame
        image_string = pil_image.tobytes("raw", "RGB")
        pygame_image = pygame.image.fromstring(image_string, pil_image.size, "RGB")
        return pygame_image


    def terminate(self):
        pygame.quit()
        sys.exit()


    def _check_for_quit(self):
        for _ in pygame.event.get(QUIT):
            self.terminate()
        for event in pygame.event.get(KEYUP):
            if event.key == pygame.K_ESCAPE:
                self.terminate()
            elif event.key == pygame.K_p:                
                self.pause = not self.pause                
                if self.pause:
                    pygame.display.set_caption("PAUSED")
                else:
                    pygame.display.set_caption(WINDOW_CAPTION)                    
            else:
                pygame.event.post(event)
            
            
            

    def _show_window(self,fen=STARTING_FEN, caption=WINDOW_CAPTION):
        
        pygame.init()
        pygame.mixer.init()
        
        self.wav_move = pygame.mixer.Sound("move.wav")
        self.wav_capture = pygame.mixer.Sound("capture.wav")
        
        self.surface = pygame.display.set_mode((self._wnd_width, self._wnd_height))

        
##        sd2.SDL_SetWindowAlwaysOnTop(sdl_window, sdl2.SDL_TRUE)
        
        self.update(fen)        

    def on_pause(self):        
        pygame.display.update()        
        self._check_for_quit()
        self.fps_clock.tick(2)
    
    def draw_square_box(self,chess_board,casilla_x,casilla_y, is_from=False):
        color = (180, 0, 0)
        grosor = 5
        casilla_size = self.board_size / 8
        casilla_x -= MARGIN
        casilla_y -= MARGIN * 2        
        col = int(casilla_x / casilla_size)
        fila = int(casilla_y / casilla_size)
        
        if is_from:
            square = chess.square(col,7-fila)
            if chess_board.color_at(square) != chess_board.turn:
                return False            
            
        x = col *  casilla_size + MARGIN 
        y = fila *  casilla_size + MARGIN *2
        
        pygame.draw.rect(self.surface, color, (x, y, casilla_size, casilla_size), grosor)
        pygame.display.update()
        return True
        
    def convertir_coordenadas_a_uci(self,chess_board, x_from, y_from, x_to, y_to):
        casilla_size = self.board_size / 8
        x_from_ajustado = x_from - MARGIN
        y_from_ajustado = y_from - MARGIN * 2
        x_to_ajustado = x_to - MARGIN
        y_to_ajustado = y_to - MARGIN * 2

        col_from = int(x_from_ajustado / casilla_size)
        fila_from = 7 - int(y_from_ajustado / casilla_size)
        col_to = int(x_to_ajustado / casilla_size)
        fila_to = 7 - int(y_to_ajustado / casilla_size)
        
        spromo=""
        square = chess.square(col_from,fila_from)
        piece=chess_board.piece_at(square)
        if piece:            
            if piece.piece_type == chess.PAWN and (fila_to ==0 or fila_to==7):
                spromo="q"
        
        x_display=col_from * casilla_size + MARGIN
        y_display=fila_from * casilla_size + MARGIN * 2
        
        columnas = 'abcdefgh'
        from_cuadro = columnas[col_from] + str(fila_from + 1)
        to_cuadro = columnas[col_to] + str(fila_to + 1)

        movimiento_uci = from_cuadro + to_cuadro + spromo
        return movimiento_uci                
    def uci_to_chess_move(self,uci):
        try:
            movimiento = chess.Move.from_uci(uci)
        except ValueError:
            print("Movimiento UCIInvalido")
            movimiento = None
        return movimiento
    
    def make_player_move(self,chess_board):
        x_from = None
        y_from = None
        x_to = None
        y_to = None
        
        
        
        while True:            
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.terminate()
                    return
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    # Obtiene las coordenadas del ratón
                    if x_from == None:
                        x_from, y_from = evento.pos
                        if not self.draw_square_box(chess_board,x_from,y_from,True):
                            x_from, y_from= None, None
                            
                    else:
                        try:
                            x_to, y_to = evento.pos                        
                            self.draw_square_box(chess_board,x_to,y_to)
                            uci_move=self.convertir_coordenadas_a_uci(chess_board,x_from, y_from,x_to, y_to)                                                
                            
                            move = self.uci_to_chess_move(uci_move)
                            
                            if move in chess_board.legal_moves:                     
                                if chess_board.is_capture(move):
                                    wav_to_play= "capture"
                                else:
                                    wav_to_play= "move"
                                chess_board.push(move)
                                self.update(chess_board.fen(), wav_to_play)
                                return                        
                            else:
                                print(uci_move, " is not legal")
                                x_from = None
                                y_from = None
                                x_to = None
                                y_to = None
                                self.update(chess_board.fen())
                        except Exception as e:
                            print(f"Error: {e}")
                            self.terminate()
                            return
            pygame.display.update()            

                        
                        
                        
                    
    def update(self,fen,play_wav=None, sinfo=" ", casillas_resaltadas=[]):


        self.surface.fill((50, 50, 50))            
        pygame_image = self.get_image_pygame(fen,casillas_resaltadas)
        self.surface.blit(pygame_image, (MARGIN, MARGIN*2))  # Posiciona la imagen en (100, 100)
        self.draw_text(sinfo)
        
        if play_wav == "move":        
            self.wav_move.play()
        elif play_wav == "capture":
            
            self.wav_capture.play()
        
            
        pygame.display.update()
        self._check_for_quit()
        
        self.fps_clock.tick(self.FPS)
    def atope(self):
        window = Window.from_display_module()
        window.always_on_top(True)

##b=chess.Board()
##g=ChessGui()
##print(pygame.version.ver) 
##g.atope()

##def flip(game_board: Board):
##    check_for_quit()
####    game_board.flip()
##    
##    pygame.display.update()
##    fps_clock.tick(FPS)


##gui= ChessGui(board_size=640)
