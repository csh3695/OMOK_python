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
