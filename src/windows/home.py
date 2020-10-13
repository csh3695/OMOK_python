import tkinter as tk
import tkinter.font as tkf
import tkinter.messagebox as messagebox

import src.protocol_codebook as code
from src.socket_interface import *


class Home(object):
    def __init__(self, server):
        self.server = server
        self.title = "오목 OMOK - Log in"
        self.label_font = tkf.Font(family='맑은 고딕', size=30)
        self.txtarea_font = tkf.Font(family='맑은 고딕', size=10)
        self.btn_font = tkf.Font(family='맑은 고딕', size=20)
        self.next = {'type': code.DESTROY}

    def log_in(self, window):
        uname = self.txt.get('1.0', tk.END).replace('\n', '')
        if len(uname) == 0:
            messagebox.showerror('오목 OMOK', '사용자 아이디를 입력하세요')
            return

        send(self.server, code.LOGIN, {'uname': uname})

        response = get(self.server, code.LOGIN)

        if response['type'] == code.LOGIN and response['code'] == code.VALID:
            self.next['type'] = code.LOGIN
            self.next['uname'] = uname
            window.destroy()
        elif response['type'] != code.LOGIN:
            messagebox.showerror('오목 OMOK', '서버 통신 실패')
        elif response['code'] != code.VALID:
            messagebox.showerror('오목 OMOK', '다른 사용자 이름을 입력하세요')

    def __call__(self, window: tk.Tk):
        window.title(self.title)
        tk.Label(window,
                 text="서울대학교 컴퓨터공학부\n컴퓨터네트워크 PA1\n오목",
                 font=self.label_font,
                 height=5).pack(side='top', fill='x')

        self.txt = tk.Text(window,
                           font=self.txtarea_font,
                           height=0)

        self.txt.pack(side='top', fill='x')

        tk.Button(window, height=5,
                  command=(lambda: self.log_in(window)),
                  bg='yellow',
                  text='클릭하여 입장',
                  font=self.btn_font).pack(side='bottom', fill='x')
        window.mainloop()
        return self.next
