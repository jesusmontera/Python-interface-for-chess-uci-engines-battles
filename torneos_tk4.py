
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog,messagebox
from fentoboardimage import fenToImage, loadPiecesFolder
from PIL import Image, ImageTk
import chess
import chess.engine
import threading

import chess.polyglot
import time
import pygame
import os
print("version tkinter ",tk.Tcl().eval('info patchlevel'))

BOARD_SIZE=640
HILO_IDLE=0
HILO_STOP=1
HILO_CLOSE=2
HILO_PLAY=3


class Config_file:
    def __init__(self,file_name):
        self.nombres =[]
        self.rutas =[]
        self.index1=-1
        self.index2=-1
        self.book_index=-1
        self.books_names=[]
        self.books_paths=[]
        self._leer_ordenar_motores(file_name)

    def _leer_ordenar_motores(self,file_name):    
        motores = []
        
        parsing_books=False
        try:
            with open(file_name, 'r') as f:                
                for linea in f:
                    if linea.startswith("/"):
                        if "openning books" in linea:
                            parsing_books=True
                        continue
                    if not parsing_books:
                        if self.index1 == -1:
                            self.index1 = int(linea.strip())
                        elif self.index2 == -1:
                            self.index2 = int(linea.strip())
                        else:
                            nombre = linea.strip()                    
                            ruta = next(f).strip()
                            motores.append((nombre, ruta))
                    else:
                        if self.book_index == -1:
                            self.book_index = int(linea.strip())
                        else:
                            nombre = linea.strip()                    
                            ruta = next(f).strip()
                            self.books_names.append(nombre)
                            self.books_paths.append(ruta)

            motores.sort(key=lambda x: x[0])  # Ordenar por nombre
        except FileNotFoundError:
            print("configuration file engines.txt does not exist")
            
        except AttributeError:
            print("config file empty. NO engines")
            

        
        self.nombres = [motor[0] for motor in motores]
        self.rutas = [motor[1] for motor in motores]
    def get_name1(self):
        if self.nombres and self.index1 < len(self.nombres):
            return self.nombres[self.index1]
        return ""
    def get_name2(self):
        if self.nombres and self.index2 < len(self.nombres):
            return self.nombres[self.index2]
        return ""
    def get_cur_book(self):
        if self.books_names and self.book_index < len(self.books_names):
            return self.books_names[self.book_index]
        return ""
        
    
    def get_path1(self):
        if self.rutas and self.index1 < len(self.rutas):
            return self.rutas[self.index1]
        return ""
    def get_path2(self):
        if self.rutas and self.index2 < len(self.rutas):
            return self.rutas[self.index2]
        return ""
    def get_cur_book_path(self):
        if self.books_paths and self.book_index < len(self.books_paths):
            return self.books_paths[self.book_index]
        return ""
    def set_indexs(self,index1,index2,book_index):
        self.index1,self.index2 = index1 , index2
        self.book_index=book_index

    
    

class ChessGuiTk:
    def __init__(self, board_size=BOARD_SIZE):
        self.board_size=  BOARD_SIZE

        self.board= chess.Board()
        self.flipped=False
        self.pieceSet=loadPiecesFolder("/media/luis/48A0CF8FA0CF8244/luis/codigo phyton lubuntu/ajedrez/fenn_board/pieces")
        self.configuration=Config_file("engines.txt")
        self.engine1=None
        self.engine2=None
        self.use_book=True
        self.undos=0
        self.hilo = None
        self.state=HILO_IDLE
        
        self.human_move=None
        self.opening_book=None
                
    def get_image_pygame(self,casillas_resaltadas=[],casillas_maquina=[]):
        
        pil_image = fenToImage(
            fen=self.board.fen(),
            squarelength=BOARD_SIZE//8,
            pieceSet=self.pieceSet,
            flipped=False,
            darkColor="#D18B47",
            lightColor="#FFCE9E",
            highlighting={("#00c568","#008538"): casillas_resaltadas,
                          ("#808000","#808000"): casillas_maquina})
        
        # Convertir la imagen PIL a una superficie de Pygame
        image_string = pil_image.tobytes("raw", "RGB")
        pygame_image = pygame.image.fromstring(image_string, pil_image.size, "RGB")
        return pygame_image
         
    def init_controls(self):
        self.frame_left = tk.Frame(self.ventana)
        self.frame_left.grid(row=0, column=0, sticky="nsew")
        self.frame_right = tk.Frame(self.ventana)
        self.frame_right.grid(row=0, column=1, sticky="nsew")

        self.label_play = tk.Label(self.frame_left, text="TABLERO",font=("Arial", 16))                
        self.label_play.grid(row=0, column=0, padx=20, pady=(10,10), sticky="nw")

        
        self.canvas = tk.Canvas(self.frame_left, width=BOARD_SIZE, height=BOARD_SIZE)
        

        self.canvas.grid(row=1, column=0, padx=10, pady=(40,20), sticky="nsew")


        self.label1 = tk.Label(self.frame_right, text="WHITE PLAYER",font=("Arial", 14), fg="blue", bg="white")
        self.label1.grid(row=0, column=0, padx=10, pady=(70,10), sticky="nw")
        
        self.combo1= ttk.Combobox(self.frame_right, font=("Arial", 16), state='readonly')
        self.combo1.grid(row=1, column=0, padx=10, pady=1, sticky="nw")

##        self.labelWelo = tk.Label(self.frame_right, text="limit ELO",font=("Arial", 14))
##        self.labelWelo.grid(row=2, column=0, sticky="nw",padx=(10,6),pady=(10,2))
        self.var_elo1 = tk.IntVar()
        self.check_eloW = tk.Checkbutton(self.frame_right, text=" limit ELO", variable=self.var_elo1,font=("Arial", 14))
        self.check_eloW.grid(row=2, column=0, sticky="nw",padx=(10,6),pady=(10,2))        
        self.tx_Welo = tk.Entry(self.frame_right,font=("Arial", 12),width=6,justify="right")                
        self.tx_Welo.grid(row=2, column=0, padx=(132,0), sticky="nw",pady=10)        
        self.tx_Welo.insert(0, "2500")
        
        self.label2 = tk.Label(self.frame_right, text="BLACK PLAYER",font=("Arial", 14), fg="blue", bg="white")
        self.label2.grid(row=3, column=0, padx=10, pady=(30,10), sticky="nw")
        
        self.combo2= ttk.Combobox(self.frame_right, font=("Arial", 16), state='readonly')
        self.combo2.grid(row=4, column=0, padx=10, pady=1, sticky="nw")

##        self.labelBelo = tk.Label(self.frame_right, text="limit ELO",font=("Arial", 14))
##        self.labelBelo.grid(row=5, column=0, sticky="nw",padx=(10,6),pady=(10,2))

        self.var_elo2 = tk.IntVar()
        self.check_eloB = tk.Checkbutton(self.frame_right, text=" limit ELO", variable=self.var_elo2,font=("Arial", 14))
        self.check_eloB.grid(row=5, column=0, sticky="nw",padx=(10,6),pady=(10,2))

        self.tx_Belo = tk.Entry(self.frame_right,font=("Arial", 12),width=6,justify="right")                
        self.tx_Belo.grid(row=5, column=0, padx=(132,0), sticky="nw",pady=10)
        self.tx_Belo.insert(0, "2500")
##        self.tx_time_openning.insert(0, "0.5")
        
        self.boton_game = tk.Button(self.frame_right, text="start playing",width="10",height="4",font=("Arial", 16))
        self.boton_game.grid(row=6, column=0, padx=10, pady=(40,5), sticky="nw")

        self.boton_undo = tk.Button(self.frame_right, text="take back",width="7",height="2",font=("Arial", 15))
        self.boton_undo.grid(row=6, column=0, padx=165, pady=(60,5), sticky="nw")

        self.label3 = tk.Label(self.frame_right, text="OPENING BOOKS",font=("Arial", 14))
        self.label3.grid(row=7, column=0, padx=10, pady=(40,5), sticky="nw")

        self.combo_book= ttk.Combobox(self.frame_right, font=("Arial", 16), state='readonly')
        self.combo_book.grid(row=8, column=0, padx=10, pady=(5,5), sticky="nw")

        # Crear y colocar el frame interior


        self.label4 = tk.Label(self.frame_right, text="time for engine move",font=("Arial", 14))
        self.label4.grid(row=9, column=0, padx=30, pady=(40,0), sticky="nw")
        self.frame_interior = tk.Frame(self.frame_right, borderwidth=3, relief=tk.RIDGE,width=210,height=110)        
        self.frame_interior.grid(row=10, column=0, sticky="nw",padx=10)
        self.frame_interior.grid_propagate(0)
                
                

        self.label5 = tk.Label(self.frame_interior, text="if book",font=("Arial", 14))
        self.label5.grid(row=1, column=0, sticky="nw",padx=(20,5),pady=10)
        
        self.tx_time_openning = tk.Entry(self.frame_interior,font=("Arial", 16),width=5,justify="right")                
        self.tx_time_openning.grid(row=1, column=1, padx=10, sticky="nw",pady=10)
        self.tx_time_openning.insert(0, "0.5")        
        

        self.label6 = tk.Label(self.frame_interior, text="if think",font=("Arial", 14))
        self.label6.grid(row=2, column=0, sticky="nw",padx=(20,5),pady=10)
        
        self.tx_time_engine = tk.Entry(self.frame_interior,font=("Arial", 16),width=5,justify="right")                
        self.tx_time_engine.grid(row=2, column=1, padx=10, sticky="nw",pady=10)
        self.tx_time_engine.insert(0, "5.0")        
        
        

        
        # cargar listas de engines para jugadores

##        str_engines=["user","engine 1","engine 2","engine 3"]
        self.combo1['values']=self.configuration.nombres
        self.combo2['values']=self.configuration.nombres
        self.combo_book['values']=self.configuration.books_names
        
        # valor prederterminado
        
        
        self.combo1.set(self.configuration.get_name1())
        self.combo2.set(self.configuration.get_name2())
        self.combo_book.set(self.configuration.get_cur_book())

                # eventos 
        self.boton_game.bind("<Button-1>", self.new_game)
        self.boton_undo.bind("<Button-1>", self.undo_move_click)
        self.canvas.bind("<Button-1>", self.click_canvas)    

    def undo_move_click(self,event):
        if self.state==HILO_PLAY:
            self.undos += 1            
            
            
    def init_pygame_embed(self,control_embed):
        os.environ['SDL_WINDOWID'] = str(control_embed.winfo_id())
        os.environ['SDL_VIDEODRIVER'] = 'x11'
        self.ventana.update_idletasks()
        pygame.init()
        pygame.mixer.init()
        
        self.wave_move = pygame.mixer.Sound("move.wav")
        self.wave_capture = pygame.mixer.Sound("capture.wav")
        
        self.board_surface = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))


    def on_focus(self):
        self.update_board_image()
    def update_pygame(self):
        self.update_board_image()
        if self.state==HILO_IDLE:
            self.ventana.after(200, self.update_pygame)
        
    def make_window(self):
        
        # Crear la ventana principal
        self.ventana = tk.Tk()
        self.ventana.title("Chess tkinter UCI (human and bots) ")
        self.ventana.geometry("950x780+40+20")
        self.init_controls()

        self.init_pygame_embed(self.canvas)        
        self.ventana.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.ventana.protocol("WM_TAKE_FOCUS", self.on_focus)
        self.ventana.after(200, self.update_pygame) #espera 100 milisegundos y despues ejecuta root.lift        
        self.ventana.mainloop()
        

    def get_fila_col_canvas_click(self,x,y):    
            
        # Calcular la fila y columna de la casilla clicada
        tamano_casilla = self.board_size/8    
        fila = y // tamano_casilla
        columna = x // tamano_casilla
        return fila, columna
    
    def click_canvas(self,event):
        
        if self.state!=HILO_PLAY:
            return
        
        fila, col = self.get_fila_col_canvas_click(event.x, event.y)
        SQUARE_SIZE  = self.board_size/8    
        x=col*SQUARE_SIZE;
        y=fila*SQUARE_SIZE;

        square = int(chess.square(col,7-fila))
        bdraw=False
        if self.human_move == None:            
            if self.board.color_at(square) == self.board.turn:                                
                self.human_move= chess.Move(square,square)                
                bdraw=True
        else:            
            self.human_move.to_square = square
            if not self.human_move in self.board.legal_moves:
                self.human_move=None
                
            else:
                bdraw=True
        if bdraw:
            color = (180, 0, 0)
            pygame.draw.rect(self.board_surface, color, (x, y, SQUARE_SIZE, SQUARE_SIZE), 5)            
            pygame.display.update()
            
            
                            
    def load_engine(self,path):        
        if path=="human no path":
            return "human"
            
        try:
            engine = chess.engine.SimpleEngine.popen_uci(path)
        except Exception as e:  # Captura la excepción y la guarda en la variable 'e'
            print(f"Error al iniciar el motor: {e}")  # Imprime un mensaje con el error    
            return None
        print("Loaded engine ok",engine.id["name"])
        return engine
        

    def load_opening_book(self):
        self.opening_book=None
        if self.configuration.book_index>0:
            book_path=self.configuration.get_cur_book_path()
            try:
                
                self.opening_book=chess.polyglot.open_reader(book_path)
                time.sleep(0.1)  #may need delay for some chess guis, i.e. cutechess                    
            except Exception as e:
                print("can't find openning book",book_path,"\n",e)
                self.opening_book=None

    def set_elo(self, engine, elo):
        if engine and engine!="human":
            try:            
                engine.configure({"UCI_LimitStrength": True, "UCI_Elo": elo})
                print(engine.id["name"], "limited ELO to", elo, "ok")
            except chess.engine.EngineError as e:
                print("could not set ELO to",engine.id["name"],str(e))

    def set_engine_param(self,engine,param, value):
        if engine and engine!="human":
            try:            
                engine.configure({param :value})                
            except chess.engine.EngineError as e:
                print("FAIl TO SET ENGINE PARAMETER", param,"TO", value,"\n",
                      engine.id["name"],str(e))

        
    def get_book_move(self):
        
        if  self.opening_book is None:        
            return None
        try:
            opening = self.opening_book.choice(self.board)            
            return opening.move
        except Exception as e:
##            print("get_book_move EXCEPCION",e)
##            self.opening_book=None
            return None

    # Obtener las opciones disponibles
    def print_engine_options(self, engine):
        print("\n",engine.id["name"], " options:")
        for clave,option in engine.options.items():
            print("\t",clave)
            
            for name, value in vars(option).items():
                print("\t\t",name,value)
                    
            
            

    def new_game(self,event):
        if self.state == HILO_PLAY:
            print("Esperando a que termine el hilo...")
            self.boton_game.config(text="wait ...")        
            self.state=HILO_STOP
            return
        sfen = simpledialog.askstring("INITIAL FEN position", "fenn string:\t\t\t\t\t",
                                      initialvalue="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        if not sfen:
            return
        self.undos=0
        self.board=chess.Board(sfen)
        
        self.close_engines()

        
        self.configuration.set_indexs(self.combo1.current(),self.combo2.current(),self.combo_book.current())
        self.engine1= self.load_engine(self.configuration.get_path1())
        self.engine2 = self.load_engine(self.configuration.get_path2())
        self.load_opening_book()
        
##        self.print_engine_options(self.engine2)
        if self.configuration.get_name1()=="mcts_dinora":
            respuesta = messagebox.askyesno("DINORA CONFIGURATION", "Set NNue for policy?\t\t\t")
            if respuesta:
                self.set_engine_param(self.engine1,"POLICY_NNUE", True)
            else:
                self.set_engine_param(self.engine1,"POLICY_NNUE", False)
                
        self.print_engine_options(self.engine1)
        self.print_engine_options(self.engine2)

        if self.var_elo1.get() ==1:
            self.set_elo(self.engine1,int(self.tx_Welo.get()))
        if self.var_elo2.get() ==1:
            self.set_elo(self.engine2,int(self.tx_Belo.get()))

        
        
        self.boton_game.config(text="Stop")        
        
        self.update_board_image()

        self.time_opening= float(self.tx_time_openning.get())
        self.time_engine= float(self.tx_time_engine.get())
        
        self.clock_white = 0
        self.clock_black = 0
        self.state =HILO_PLAY
        self.play_move()
    def update_board_image(self,casillas_resaltadas=[]):
        self.ventana.update_idletasks()
        pygame_image = self.get_image_pygame(casillas_resaltadas=casillas_resaltadas)        
        self.board_surface.blit(pygame_image, (0, 0))             
        pygame.display.flip()
    def draw_push_move(self, move):
        casillas_resaltadas=[]
        squares=(move.from_square, move.to_square)
        for square in squares:        
            nombre_casilla = chess.SQUARE_NAMES[square]
            casillas_resaltadas.append(nombre_casilla)
        if self.board.is_capture(move):
            self.wave_capture.play()
        else:
            self.wave_move.play()
            
        self.board.push(move)
        print(self.board.fen())
        self.update_board_image(casillas_resaltadas=casillas_resaltadas)

        
    def make_human_move(self):
        if self.undos > 0:
            self.take_back_moves()
            self.play_move()            
            return
        
        if self.human_move and self.human_move in self.board.legal_moves:                
            print(self.human_move)
            self.draw_push_move(self.human_move)
            self.human_move = None
            self.play_move()
        else:
            if self.state==HILO_CLOSE or self.state==HILO_STOP:
                print ("hilo terminado")
                self.boton_game.config(text="start playing")                            
            else:
                self.ventana.after(200, self.make_human_move) 

                
        
    def take_back_moves(self):
##        print("deshaciendo jugadas...")
        for i in range(self.undos):
            try:
                self.board.pop()
                self.update_board_image()
                time.sleep(0.01)
            except Exception as e:
                break
            
        self.undos=0
    
    def play_move(self):

        if self.board.is_game_over():
            print("\nGAME END",self.board.result())
            self.state=HILO_IDLE
            self.boton_game.config(text="start playing")        
            return

        if self.state==HILO_STOP:            
            print("hilo terminado")
            self.boton_game.config(text="start playing")
            return
        if self.undos > 0:
            self.take_back_moves()
          
            
            
            
        
        if self.state==HILO_CLOSE:
            print("hilo terminado")
            self.on_closing()
            return
        if self.board.turn==chess.WHITE:
            cur_player= self.engine1
        else:
            cur_player= self.engine2

        if cur_player == "human":
            self.human_move == chess.Move.null()            
            self.make_human_move()
        else:            
            self.hilo = threading.Thread(target=self.make_engine_move,args=(cur_player,))
            self.hilo.start()            
            
            
    def make_engine_move(self,engine):
        move=self.get_book_move()
        n=len(self.board.move_stack)
        num_movimientos = (n+1)//2
        if n%2==0:
            sname=" " + self.configuration.get_name1() +" " 
        else:
            sname=" " + self.configuration.get_name2() + " "
        if move:
            sinfo=str(num_movimientos) + sname +  "book move " + str(move) 
            self.label_play.config(text=sinfo)
            self.draw_push_move(move)
            twait=int(self.time_opening * 1000)
                
            self.ventana.after(twait, self.play_move)            
        else:            
            result = engine.play(self.board, limit=chess.engine.Limit(time=self.time_engine), info=chess.engine.Info.ALL)
            move=result.move
            self.draw_push_move(move)        
            score = result.info['score'].pov(chess.WHITE)
            depth= result.info['depth']
            nodes= result.info['nodes']
            
            sinfo=str(num_movimientos) + sname + str(move) +  " score "  + str(score) + \
                   " depth " + str(depth) + " nodes " + str(nodes)
    
            self.label_play.config(text=sinfo )                        
            self.ventana.after(100, self.play_move)
        if self.state==HILO_CLOSE or self.state==HILO_STOP:
                print("hilo terminado")
            
                                        
    def close_engines(self):
        if self.engine1 and self.engine1 != "human":
            self.engine1.quit()
        if self.engine2 and self.engine2 != "human":
            self.engine2.quit()
    
    def on_closing(self):

        self.state = HILO_CLOSE
        if self.hilo:                        
            if self.hilo.is_alive():
                print("Esperando a que termine el hilo...")
                return

        self.close_engines()
        self.ventana.destroy()
        print("chess program terminated ok")
        self.ventana=None

chess_gui = ChessGuiTk()
chess_gui.make_window()
pygame.quit()
