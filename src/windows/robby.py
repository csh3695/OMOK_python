import time
import threading
import tkinter as tk
import tkinter.font as tkf
import tkinter.messagebox as messagebox

import src.protocol_codebook as code
from src.socket_interface import *


class Robby(object):
    def __init__(self, uname, server):
        self.server = server
        self.room_info = []
        self.uname = uname
        self.title = "오목 OMOK"
        self.btn = None
        self.next = {'type': code.DESTROY}

        self.get_room_info_thread = None

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

    def enter_room(self, window, response):
        """
        - 방에 입장 시도
        :param window: target tkinter window
        :param response: target room info from server
        :return: True if success
        """
        room = response['room']
        if response['code'] != code.VALID:
            messagebox.showerror('오목 OMOK',
                                 f'입장할 수 없습니다. {"게임 중입니다" if room["state"] == "play" else "방이 가득 찼습니다"}')
        else:
            self.next['type'] = code.ENTER_ROOM
            self.next['room'] = room
            self.next['uname'] = self.uname
            window.quit()
            return True

    def _load_room(self, window, response):
        """
        - 서버로부터 수신한 room_info로부터 방 버튼을 렌더링
        :param window: target tkinter window
        :param response: room info from server
        :return: None
        """
        self.room_info = response['room_info']

        if response['code'] == code.VALID:
            if self.btn is not None:
                self.btn.grid_forget()
                self.btn.destroy()

            if len(self.room_info) == 0:
                self.btn = tk.Button(window,
                                     text="방 만들기",
                                     font=tkf.Font(family='맑은 고딕', size=20),
                                     command=(lambda: send(self.server, code.CREATE_ROOM, {'uname': self.uname}))).grid(
                    row=1, sticky="nsew")

            else:
                room = self.room_info[0]
                self.btn = tk.Button(window,
                                     text=f"{room['id']}번 방: {room['state']}",
                                     font=tkf.Font(family='맑은 고딕', size=20),
                                     command=(lambda: send(self.server, code.ENTER_ROOM, {'uname': self.uname}))).grid(
                    row=1, sticky='nsew')
        else:
            messagebox.showerror('오목 OMOK', '서버 통신 실패')

    def receiver(self, window):
        """
        - 독립 Thread에서 작동하며 서버로부터의 정보를 수신하여 렌더링 함수를 호출한다.
        :param window: rendering target tkinter window
        :return: None
        """
        send(self.server, code.GET_ROOM_INFO, {})
        while not self.stop_thread:
            response = getall(self.server)
            if response['type'] == code.PUT_ROOM_INFO:
                self._load_room(window, response)
            elif response['type'] == code.CREATE_ROOM:
                send(self.server, code.ENTER_ROOM, {'uname': self.uname})
            elif response['type'] == code.ENTER_ROOM:
                if self.enter_room(window, response):
                    exit()

    def __call__(self, window: tk.Tk):
        self.clear(window)
        self.stop_thread = False
        window.title(self.title)
        window.columnconfigure(0, weight=1)
        window.columnconfigure(1, weight=0)
        window.rowconfigure(0, weight=1)
        window.rowconfigure(1, weight=10000)

        tk.Label(window,
                 text=f"{self.uname}님 환영합니다!",
                 font=tkf.Font(family='맑은 고딕', size=30)).grid(row=0, column=0)

        self.get_room_info_thread = threading.Thread(target=self.receiver, args=(window,))
        self.get_room_info_thread.start()
        window.mainloop()
        if self.next['type'] == code.DESTROY:
            self.stop_thread = True
            send(self.server, code.DUMMY, {})
        self.get_room_info_thread.join(timeout=1)
        return self.next
