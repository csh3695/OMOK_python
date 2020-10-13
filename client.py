import socket
import tkinter as tk
import tkinter.messagebox as messagebox
import src.protocol_codebook as code
from src.socket_interface import *
from src.windows import *


def run(HOST, PORT):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((HOST, PORT))

    window = tk.Tk()
    window.geometry("1000x625")
    window.resizable(False, False)
    screen = Home(server)
    uname = None

    while True:
        """
        - windows/*의 class들로 생성된 window rendering 객체에 window를 넘겨 call한다.
        - 해당 class들이 사용자에게 각 화면을 띄운 후 종료 또는 화면 변화 시 next_work를 반환한다.
        - next_work
            code.DESTROY -> 종료(* -> exit)
            code.LOGIN -> 로그인하고 로비로 이동(home -> robby)
            code.ENTER_ROOM -> 방에 입장(robby -> room)
            code.LEAVE_ROOM -> 로비로 복귀(room -> robby)
            code.PLAY -> 게임 시작(room -> game)
            code.TO_ROOM -> 게임 후 방으로 복귀(game -> room)
        """
        next_work = screen(window)
        print('next work is', next_work)
        if next_work['type'] == code.DESTROY:
            if uname is not None:
                send(server, code.LOGOUT, {'uname': uname})
            print("Bye")
            exit()

        elif next_work['type'] == code.LOGIN:
            uname = next_work['uname']
            window = tk.Tk()
            window.geometry("1000x625")
            window.resizable(False, False)
            screen = Robby(uname, server)

        elif next_work['type'] == code.ENTER_ROOM:
            screen = Room(next_work['room']['id'], next_work['room']['owner'], next_work['uname'], server)

        elif next_work['type'] == code.LEAVE_ROOM:
            screen = Robby(next_work['uname'], server)

        elif next_work['type'] == code.PLAY:
            screen = Game(next_work['game_id'], next_work['uname'], server)

        elif next_work['type'] == code.TO_ROOM:
            send(server, code.END_GAME, {'room_id': next_work['room']['id'], 'uname': next_work['uname']})
            screen = Room(next_work['room']['id'], next_work['room']['owner'], next_work['uname'], server)


if __name__ == "__main__":
    HOST = 'cn1.snucse.org'
    #HOST = '127.0.0.1'
    PORT = 20940
    run(HOST, PORT)
