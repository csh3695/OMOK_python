import socket
import src.protocol_codebook as code
import threading
from src.omok import Omok
from src.socket_interface import *
from threading import Timer

uname_list = ['admin', 'None']
room_list = []
user_by_room = {}
game_by_room = {}

listen_table = {}

uname_list_update = 0
room_list_update = 0
user_by_room_update = 0
game_by_room_update = 0

game = None
timer = None

clients = []
threads = []

room_info_thread, user_info_thread, game_info_thread = None, None, None


def uname_lock(func):
    def wrapper(*args, **kwargs):
        global uname_list_update
        func(*args, **kwargs)
        uname_list_update += 1
    return wrapper


def room_lock(func):
    def wrapper(*args, **kwargs):
        global room_list_update
        func(*args, **kwargs)
        room_list_update = 1
    return wrapper


def user_lock(func):
    def wrapper(*args, **kwargs):
        global user_by_room_update
        func(*args, **kwargs)
        user_by_room_update = 1
    return wrapper


def game_lock(func):
    def wrapper(*args, **kwargs):
        global game_by_room_update
        func(*args, **kwargs)
        game_by_room_update = 1
    return wrapper


def update_room_info():
    global room_list_update
    while True:
        if room_list_update > 0:
            for client in clients:
                if listen_table[client.getpeername()[1]]['room_list']:
                    send(client, code.PUT_ROOM_INFO, {'room_info': room_list, 'code': code.VALID})
            room_list_update = 0


def update_user_info():
    global user_by_room_update
    while True:
        if user_by_room_update > 0:
            if len(user_by_room) != 0:
                new_user_info = user_by_room[list(user_by_room.keys())[0]]
                for client in clients:
                    if listen_table[client.getpeername()[1]]['user_by_room']:
                        send(client, code.PUT_USER_INFO, {'user_info': new_user_info, 'code': code.VALID})
            user_by_room_update = 0


def update_game_info():
    global game_by_room_update
    while True:
        if game_by_room_update > 0:
            if len(game_by_room) != 0:
                new_game_info = game_by_room[list(game_by_room.keys())[0]]
                for client in clients:
                    if listen_table[client.getpeername()[1]]['game_by_room']:
                        response = {'game_id': new_game_info['id'], 'code': code.VALID}
                        response.update(new_game_info)
                        send(client, code.PUT_GAME_INFO, response)
            game_by_room_update = 0


@room_lock
@user_lock
def leave_room(rcv, client):
    id = rcv['room_id']
    uname = rcv['uname']
    if room_list[0]['id'] == id and (id in user_by_room.keys()):
        if client is not None:
            listen_table[client.getpeername()[1]]['room_list'] = True
        if len(user_by_room[id]) == 1:
            room_list.remove(room_list[0])  # delete room
            assert (len(room_list) == 0)
            user_by_room.pop(id)  # delete user dict
            print("[+] LEAVE AND DELETE")
        else:
            if room_list[0]['owner'] == uname:  # if owner leaves
                user_by_room[id].pop(uname)  # delete user element
                room_list[0]['owner'] = list(user_by_room[id].keys())[0]  # change owner
                print("[+] LEAVE AND CHANGE OWNER")
            else:  # if participant leaves
                user_by_room[id].pop(uname)
                print("[+] LEAVE ONLY")
            room_list[0]['state'] = 'enter'
        if client is not None:
            send(client, code.LEAVE_ROOM, {'code': code.VALID})
            listen_table[client.getpeername()[1]]['user_by_room'] = False
    else:
        if client is not None:
            send(client, code.LEAVE_ROOM, {'code': code.INVALID})


@uname_lock
def login(rcv, client):
    print("[+] LOGIN {}".format(rcv['uname']))
    if 'uname' not in rcv.keys() or rcv['uname'] in uname_list:
        send(client, code.LOGIN, {'code': code.INVALID})
    else:
        uname_list.append(rcv['uname'])
        listen_table[client.getpeername()[1]]['room_list'] = True
        send(client, code.LOGIN, {'code': code.VALID, 'uname': rcv['uname']})


@uname_lock
@game_lock
def logout(rcv, client):
    print("[+] LOGOUT {}".format(rcv['uname']))
    uname = rcv['uname']
    listen_table.pop(client.getpeername()[1])
    clients.remove(client)
    if game is not None and game.to_dict()['state'] == code.ON_GAME:
        game_dict = list(game_by_room.values())[0]
        if game_dict['black'] == uname:
            winner = code.WHITE
        else:
            winner = code.BLACK
        game.set_state_by_server(winner)
        game_dict['game'] = game.to_dict()
        print('[+] User {} out game, winner {}'.format(uname, winner))
        for c in clients:
            response = {'code': code.VALID, 'game_id': game_dict['id']}
            response.update(game_dict)
            send(c, code.PUT_GAME_INFO, response)
    if len(room_list) > 0 and uname in user_by_room[room_list[0]['id']].keys():
        leave_room({'room_id': room_list[0]['id'], 'uname': uname}, None)
    if uname in uname_list:
        uname_list.remove(uname)
    client.close()
    exit(0)



@room_lock
@user_lock
def create_room(rcv, client):
    uname = rcv['uname']
    room_list.append({'id': len(room_list), 'owner': uname, 'state': 'enter'})
    user_by_room[room_list[0]['id']] = {}
    print("[+] CREATE_ROOM {}".format(room_list))
    send(client, code.CREATE_ROOM, {'room': room_list[-1], 'code': code.VALID})


@room_lock
@user_lock
def enter_room(rcv, client):
    uname = rcv['uname']
    if room_list[0]['state'] == 'enter':
        listen_table[client.getpeername()[1]]['user_by_room'] = True
        send(client, code.ENTER_ROOM, {'code': code.VALID, 'room': room_list[0]})
        user_by_room[room_list[0]['id']][uname] = False
        if len(user_by_room[room_list[0]['id']]) >= 2:
            room_list[0]['state'] = 'full'
        print("[+] ENTER_ROOM {}".format(room_list))
        listen_table[client.getpeername()[1]]['room_list'] = False
    else:
        send(client, code.ENTER_ROOM, {'code': code.INVALID, 'room': room_list[0]})


@room_lock
@user_lock
def get_user_info(rcv, client):
    id = rcv['room_id']
    if room_list[0]['id'] == id and (id in user_by_room.keys()):
        print("[+] GET_USER_INFO {}".format(user_by_room[id]))
        send(client, code.PUT_USER_INFO, {'code': code.VALID, 'user_info': user_by_room[id]})
    else:
        send(client, code.PUT_USER_INFO, {'code': code.INVALID, 'user_info': None})


@room_lock
@user_lock
def ready(rcv, client):
    id = rcv['room_id']
    uname = rcv['uname']
    if room_list[0]['id'] == id and (id in user_by_room.keys()):
        user_by_room[id][uname] = not user_by_room[id][uname]
        print("[+] READY {}".format(user_by_room[id]))
        send(client, code.READY, {'code': code.VALID, 'user_info': user_by_room[id]})
    else:
        send(client, code.READY, {'code': code.INVALID, 'user_info': None})


@user_lock
@game_lock
def play(rcv, client):
    global game, timer
    id = rcv['room_id']
    uname = rcv['uname']
    if room_list[0]['id'] == id and (id in user_by_room.keys()):
        listen_table[client.getpeername()[1]]['game_by_room'] = True
        if room_list[0]['owner'] == uname:
            game = Omok(len(game_by_room))
            game_by_room[id] = {'id': len(game_by_room),
                                'user_info': user_by_room[id],
                                'black': uname,
                                'game': game.to_dict()
                                }
        else:
            while id not in game_by_room.keys():
                pass
            for key in user_by_room[id]:
                user_by_room[id][key] = False
            game_by_room[id]['white'] = uname
            if timer is not None and timer.is_alive():
                timer.cancel()
                timer = None
                print('timer cancelled')

            timer = Timer(60, set_timeout)
            timer.start()
            print('timer started')
        response = {'code': code.VALID, 'game_id': game_by_room[id]['id']}
        response.update(game_by_room[id])
        send(client, code.PLAY, response)
        listen_table[client.getpeername()[1]]['user_by_room'] = False
    else:
        send(client, code.PLAY, {'code': code.INVALID, 'game_id': None})

@game_lock
def set_timeout():
    print('timer ended')
    global game
    game.set_timeout()
    game_dict = list(game_by_room.values())[0]
    game_dict['game'] = game.to_dict()

@game_lock
def get_game_info(rcv, client):
    pass


def end_game(rcv, client):
    print('game_by_room', game_by_room)
    global game
    global timer
    listen_table[client.getpeername()[1]]['user_by_room'] = True
    id = rcv['room_id']
    uname = rcv['uname']
    game_dict = game_by_room[id]
    if uname == game_dict['black']:
        game_dict['black'] = None
    elif uname == game_dict['white']:
        game_dict['white'] = None

        while game_dict['black'] is not None:
            pass

        game_by_room.pop(id)
        if timer is not None and timer.is_alive():
            timer.cancel()
            timer = None
            print('timer cancelled')
        game = None
    listen_table[client.getpeername()[1]]['game_by_room'] = False



@game_lock
def put_stone(rcv, client):
    global game, timer
    if timer is not None:
        timer.cancel()
        timer = None
        print('timer cancelled')
    id = rcv['game_id']
    stone = rcv['stone']
    game_dict = list(game_by_room.values())[0]
    assert(game_dict['id'] == id)
    result = game.put_stone(rcv['x'], rcv['y'], stone)
    game_dict['game'] = game.to_dict()
    send(client, code.PUT_STONE, {'game_id': game.id, 'stone': stone, 'result': result})
    if game_dict['game']['state'] == code.ON_GAME:
        if timer is None:
            timer = Timer(60, set_timeout)
            timer.start()
            print('timer started')


def process_query(client, rcv: dict):
    if rcv['type'] == code.LOGIN:
        login(rcv, client)

    elif rcv['type'] == code.LOGOUT:
        logout(rcv, client)

    elif rcv['type'] == code.GET_ROOM_INFO:
        print("[+] GET_ROOM_INFO {}".format(room_list))
        global room_list_update
        room_list_update += 1
        send(client, code.PUT_ROOM_INFO, {'room_info': room_list, 'code': code.VALID})

    elif rcv['type'] == code.CREATE_ROOM:
        create_room(rcv, client)

    elif rcv['type'] == code.ENTER_ROOM:
        enter_room(rcv, client)

    elif rcv['type'] == code.GET_USER_INFO:
        get_user_info(rcv, client)

    elif rcv['type'] == code.LEAVE_ROOM:
        leave_room(rcv, client)

    elif rcv['type'] == code.READY:
        ready(rcv, client)

    elif rcv['type'] == code.PLAY:
        play(rcv, client)

    elif rcv['type'] == code.GET_GAME_INFO:
        get_game_info(rcv, client)

    elif rcv['type'] == code.PUT_STONE:
        put_stone(rcv, client)

    elif rcv['type'] == code.END_GAME:
        end_game(rcv, client)

    elif rcv['type'] == code.DUMMY:
        print('{} out.'.format(client.getpeername()[1]))
        send(client, code.DUMMY, {})

    else:
        pass


def conn_thread(client):
    print('[+] Thread start for client {}'.format(client))
    while True:
        process_query(client, getall(client))


def run(s):
    room_info_thread = threading.Thread(target=update_room_info, args=())
    user_info_thread = threading.Thread(target=update_user_info, args=())
    game_info_thread = threading.Thread(target=update_game_info, args=())
    room_info_thread.start()
    user_info_thread.start()
    game_info_thread.start()

    while True:
        client, addr = s.accept()
        print("client: ", client)
        print("addr: ", addr)
        clients.append(client)
        print(client.getpeername())
        listen_table[client.getpeername()[1]] = {'room_list': False, 'user_by_room': False, 'game_by_room': False}
        print(listen_table)
        threads.append(threading.Thread(target=conn_thread, args=(clients[-1],)))
        threads[-1].start()


if __name__ == "__main__":
    HOST = '0.0.0.0'
    PORT = 20940
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.bind((HOST, PORT))
    print("Hello World! SNUCSE Computer Network PA1 - Seonghwan Choi")
    skt.listen(1)
    run(skt)
    skt.close()
