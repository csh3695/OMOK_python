import threading
import tkinter as tk
import tkinter.font as tkf
import tkinter.messagebox as messagebox

import src.protocol_codebook as code
from src.socket_interface import *


class Room(object):
    def __init__(self, id, owner, uname, server):
        self.server = server
        self.uname = uname
        self.id = id
        self.owner = owner
        self.user = {}
        self.state = "enter"  ## enter / full / play
        self.title = "오목 OMOK - ROOM"

        self.board_image = tk.PhotoImage(file='src/assets/board.png')

        self.myinfo_font = tkf.Font(family='맑은 고딕', size=30)
        self.txtarea_font = tkf.Font(family='맑은 고딕', size=10)
        self.btn_font = tkf.Font(family='맑은 고딕', size=20)
        self.next = {'type': code.DESTROY}

        self.get_user_info_thread = None

    def get_all_widget(self, wdget):
        _list = []

        for w in wdget.winfo_children():
            if w.winfo_children():
                _list += self.get_all_widget(w)
            else:
                _list.append(w)
        return _list

    def clear(self, window):
        # 화면 초기화
        for item in self.get_all_widget(window):
            item.grid_forget()
            item.destroy()

    def leave_room(self, window, response):
        """
        - 방 나가기
        :param window: target tkinter window
        :param response: 시도 결과
        :return: True if success else False
        """
        if response['code'] == code.VALID:
            self.next['type'] = code.LEAVE_ROOM
            self.next['uname'] = self.uname
            window.quit()
            return True
        else:
            messagebox.showerror('오목 OMOK', '서버 통신 실패')
            return False

    def start_game(self, window, response):
        """
        - 게임 시작
        :param window: target tkinter window
        :param response: 시도 결과
        :return: True if success else False
        """
        if response['code'] == code.VALID:
            self.next['type'] = code.PLAY
            self.next['uname'] = self.uname
            self.next['game_id'] = response['game_id']
            window.quit()
            return True
        else:
            messagebox.showerror('오목 OMOK', '게임을 시작할 수 없습니다')
            return False

    def do_ready(self, response):
        """
        - 준비
        :param window: target tkinter window
        :param response: 시도 결과
        :return: None
        """
        if response['code'] == code.VALID:
            self.user = response['user_info']
        else:
            messagebox.showerror('오목 OMOK', '서버 통신 실패')

    def _load_user(self, window, response):
        """
        - 서버로부터 수신한 유저 정보를 바탕으로 유저 정보 화면을 렌더링
        :param window: target tkinter window
        :param response: 서버로부터 수신한 방에 따른 유저 정보
        :return: None
        """
        if response['code'] == code.VALID:
            self.user = response['user_info']

            for item in self.user_grid_item:
                item.grid_forget()
                item.destroy()
            self.user_grid_item = []

            if len(self.user) == 1:
                item = tk.Label(window,
                                text=f"참가자가 없습니다",
                                font=self.btn_font)
                self.user_grid_item.append(item)
                item.grid(row=0, column=1, sticky='news')
                assert (self.uname in self.user.keys())
                item = tk.Button(window,
                                 text=f"{self.uname} {'Ready' if self.user[self.uname] else ''}",
                                 font=self.btn_font,
                                 fg="green" if self.user[self.uname] else "red",
                                 command=(
                                     lambda: send(self.server, code.READY, {'room_id': self.id, 'uname': self.uname})))
                self.user_grid_item.append(item)
                item.grid(row=1, column=1, sticky='news')

            else:
                for uname in self.user.keys():
                    if uname == self.uname:
                        item = tk.Button(window,
                                         text=f"{uname} {'Ready' if self.user[uname] else ''}",
                                         font=self.btn_font,
                                         fg="green" if self.user[uname] else "red",
                                         command=(lambda: send(self.server, code.READY,
                                                               {'room_id': self.id, 'uname': self.uname})))
                        self.user_grid_item.append(item)
                        item.grid(row=1, column=1, sticky='news')

                    else:
                        item = tk.Label(window,
                                        text=f"{uname} {'Ready' if self.user[uname] else ''}",
                                        font=self.btn_font,
                                        fg="green" if self.user[uname] else "red")
                        self.user_grid_item.append(item)
                        item.grid(row=0, column=1, sticky='news')

            item = tk.Button(window,
                             text=f"방 나가기",
                             font=self.btn_font,
                             command=(
                                 lambda: send(self.server, code.LEAVE_ROOM, {'room_id': self.id, 'uname': self.uname})))
            self.user_grid_item.append(item)
            item.grid(row=2, column=1, sticky='news')

            if len(self.user) == sum(list(self.user.values())) == 2:
                send(self.server, code.PLAY, {'room_id': self.id, 'uname': self.uname})

        else:
            messagebox.showerror('오목 OMOK', '서버 통신 실패')

    def receiver(self, window):
        """
        - 독립 Thread에서 작동하며 서버로부터의 정보를 수신하여 렌더링 함수를 호출한다.
        :param window: rendering target tkinter window
        :return: None
        """
        send(self.server, code.GET_USER_INFO, {'room_id': self.id, })
        while not self.stop_thread:
            response = getall(self.server)
            if response['type'] == code.PUT_USER_INFO:
                self._load_user(window, response)
            elif response['type'] == code.LEAVE_ROOM:
                if self.leave_room(window, response):
                    exit()
            elif response['type'] == code.READY:
                self.do_ready(response)
            elif response['type'] == code.PLAY:
                if self.start_game(window, response):
                    exit()

    def __call__(self, window: tk.Tk):
        self.clear(window)
        self.stop_thread = False
        window.title(self.title)
        window.columnconfigure(0, weight=0)
        window.columnconfigure(1, weight=1)
        window.rowconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)

        board = tk.Label(window, image=self.board_image)
        board.grid(column=0, rowspan=3)

        self.user_grid_item = []
        self.get_user_info_thread = threading.Thread(target=self.receiver, args=(window,))
        self.get_user_info_thread.start()
        window.mainloop()
        if self.next['type'] == code.DESTROY:
            self.stop_thread = True
            send(self.server, code.DUMMY, {})
        self.get_user_info_thread.join(timeout=1)
        return self.next
