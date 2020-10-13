import threading
import tkinter as tk
import tkinter.font as tkf
import tkinter.messagebox as messagebox

import src.protocol_codebook as code
from src.socket_interface import *


class Game(object):
    def __init__(self, id, uname, server):
        self.server = server
        self.uname = uname
        self.id = id
        self.user = {uname: False, 'opponent': True}
        self.title = "오목 OMOK - GAME"
        self.my_stone = code.BLACK
        self.stone_image = [None,
                            tk.PhotoImage(file='src/assets/black_stone.png'),
                            tk.PhotoImage(file='src/assets/white_stone.png')
                            ]
        self.result_image = [tk.PhotoImage(file='src/assets/draw.png'),
                             tk.PhotoImage(file='src/assets/black_win.png'),
                             tk.PhotoImage(file='src/assets/white_win.png')
                             ]
        self.board_image = tk.PhotoImage(file='src/assets/board.png')
        self.next_turn = code.BLACK
        self.state = code.ON_GAME

        self.board = generate_matrix([11, 11])
        self.stone_spot = generate_matrix([11, 11, 2])
        for i in range(11):
            for j in range(11):
                self.stone_spot[i][j] = [int((2 * i + 1) * 625 / 22), int((2 * j + 1) * 625 / 22)]

        self.myinfo_font = tkf.Font(family='맑은 고딕', size=30)
        self.txtarea_font = tkf.Font(family='맑은 고딕', size=10)
        self.btn_font = tkf.Font(family='맑은 고딕', size=20)

        self.next = {'type': code.DESTROY}

        self.get_game_info_thread = None

    def get_all_widget(self, wdget):
        _list = []

        for w in wdget.winfo_children():
            if w.winfo_children():
                _list += self.get_all_widget(w)
            else:
                _list.append(w)
        return _list

    def clear(self, window):
        for item in self.get_all_widget(window):
            item.grid_forget()
            item.destroy()

    def _load_user(self, window):
        for uname in self.user.keys():
            if uname == self.uname:
                item = tk.Label(window,
                                text=f"{uname}" + ("의 차례" if self.next_turn == self.my_stone else ""),
                                font=self.btn_font,
                                fg="green",
                                bg="black" if self.my_stone == code.BLACK else "white")
                item.grid(row=1, column=1, sticky='news')

            else:
                item = tk.Label(window,
                                text=f"{uname}" + ("" if self.next_turn == self.my_stone else "의 차례"),
                                font=self.btn_font,
                                fg="green",
                                bg="white" if self.my_stone == code.BLACK else "black")
                item.grid(row=0, column=1, sticky='news')

    def put_stone(self, event):
        # 57 ~= 625/11
        if self.next_turn == self.my_stone:
            send(self.server, code.PUT_STONE,
                 {'game_id': self.id, 'stone': self.my_stone, 'x': event.x // 57, 'y': event.y // 57})
        else:
            messagebox.showerror('오목 OMOK', '자네의 차례가 아니네. 경거망동하지 말게나.')

    def update_board(self, window, new_board):
        for i in range(len(self.board)):
            for j in range(len(self.board[0])):
                if self.board[i][j] != new_board[i][j]:
                    spot = self.stone_spot[i][j]
                    self.canvas.create_image(spot[0], spot[1], image=self.stone_image[new_board[i][j]])
                    self.board[i][j] = new_board[i][j]

    def parse_game_state(self, window, response):
        assert (response['game_id'] == self.id)
        game_dict = response['game']
        self.user = response['user_info']
        self.my_stone = code.BLACK if response['black'] == self.uname else code.WHITE
        self.next_turn = game_dict['next_turn']
        self.state = game_dict['state']
        self._load_user(window)
        self.update_board(window, str_to_board(game_dict['board']))
        # self.turn_count = response['turn_count']
        # self.wrong_place_count = response['wrong_place_count']

    def show_result(self, result_flag):
        self.canvas.create_image(312, 312, image=self.result_image[result_flag])

    def check_winner(self, window):
        if self.state == code.ON_GAME:
            return False
        elif self.state == code.BLACK:
            self.show_result(1)
        elif self.state == code.WHITE:
            self.show_result(2)
        elif self.state == code.DRAW:
            self.show_result(0)

        window.after(5000, window.quit)
        return True

    def receiver(self, window):
        send(self.server, code.GET_GAME_INFO, {'game_id': self.id})
        while not self.stop_thread:
            response = getall(self.server)
            if response['type'] == code.PUT_GAME_INFO or response['type'] == code.PLAY:
                self.parse_game_state(window, response)
                if self.check_winner(window):
                    send(self.server, code.GET_ROOM_INFO, {})
                    response = getall(self.server)
                    while response['type'] != code.PUT_ROOM_INFO:
                        response = getall(self.server)
                    self.next = {'type': code.TO_ROOM, 'room': response['room_info'][0], 'uname': self.uname,
                                 'game_id': self.id}
                    exit()
            elif response['type'] == code.PUT_STONE:
                if response['result'] == code.PUT_STONE_FAIL and response['stone'] == self.my_stone:
                    messagebox.showerror('오목 OMOK', '잘못 두었네!!!')
            else:
                pass

    def __call__(self, window: tk.Tk):
        self.clear(window)
        self.stop_thread = False
        window.title(self.title)
        window.grid_columnconfigure(0, weight=0)
        window.grid_columnconfigure(1, weight=1)
        window.grid_rowconfigure(0, weight=1)
        window.grid_rowconfigure(1, weight=1)

        self.canvas = tk.Canvas(window, width=625, height=625, highlightthickness=0)
        self.canvas.grid(column=0, rowspan=2)
        self.canvas.create_image(312, 312, image=self.board_image)
        self.canvas.bind('<Button-1>', self.put_stone)

        self.get_game_info_thread = threading.Thread(target=self.receiver, args=(window,))
        self.get_game_info_thread.start()

        self._load_user(window)

        window.mainloop()
        if self.next['type'] == code.DESTROY:
            self.stop_thread = True
            send(self.server, code.DUMMY, {})
        self.get_game_info_thread.join(timeout=1)
        return self.next
