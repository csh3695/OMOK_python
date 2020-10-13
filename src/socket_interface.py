import queue
from ast import literal_eval

import src.protocol_codebook as code
from src.matrix import *

rcv_queue = queue.Queue()


def send(sock, type, data={}):
    # send message after attaching type
    assert ('type' not in data.keys())
    data['type'] = type
    # print('SEND {}'.format(data))
    sock.sendall(str(data).encode())


def getall(conn):
    # get all type message and implement queueing
    if rcv_queue.empty():
        dstr = conn.recv(2048).decode("utf-8")
        dlist = divide(dstr)
        if len(dlist) > 0:
            dstr = dlist[0]
            if len(dlist) > 1:
                for d in dlist[1:]:
                    rcv_queue.put(d)
    else:
        dstr = rcv_queue.get()

    # print('RECEIVE {}'.format(dstr))
    try:
        ddic = literal_eval(dstr)
    except:
        raise ValueError("{} not eval_able.".format(dstr))
    return ddic


def get(conn, type):
    # get specific type message
    while True:
        # print("Waiting for Type {}".format(type))
        dstr = conn.recv(2048).decode("utf-8")
        # print('RECEIVE {}'.format(dstr))
        try:
            ddic = literal_eval(dstr)
        except:
            raise ValueError("{} not eval_able.".format(dstr))
        if ddic['type'] == type:
            return ddic


def board_to_str(board):
    """
    build string representation of board
    :param board: board array
    :return: board string
    """
    blist = []
    wlist = []
    for i in range(len(board)):
        for j in range(len(board[0])):
            if board[i][j] == code.BLACK:
                blist.append((i, j))
            elif board[i][j] == code.WHITE:
                wlist.append((i, j))

    bdic = {'shape': get_shape(board),
            'blist': blist,
            'wlist': wlist}

    return str(bdic)


def str_to_board(bstr: str):
    """
    parse string and reconstruct board
    :param bstr: board string
    :return: board array
    """
    try:
        bdic = literal_eval(bstr)
    except:
        raise ValueError("{} not eval_able.".format(bstr))

    board = generate_matrix(bdic['shape'])
    for bpoint in bdic['blist']:
        board[bpoint[0]][bpoint[1]] = code.BLACK
    for wpoint in bdic['wlist']:
        board[wpoint[0]][wpoint[1]] = code.WHITE

    return board


def divide(dstr):
    """
    - 여러 dictionary들이 하나의 string으로 concat되어 있는 입력을 dictionary 단위로 나눔
    :param dstr: dictionaries string
    :return: list of dictionary string
    """
    if len(dstr) == 0 or dstr[0] != '{':
        return []
    if dstr.find('{') == -1:
        return []
    i = 1
    ris = 1
    d_list = []
    while True:
        if dstr[i] == '{':
            ris += 1
        elif dstr[i] == '}':
            ris -= 1
        if ris == 0:
            d_list.append(dstr[:i + 1])
            dstr = dstr[i + 1:]
            next_ptr = dstr.find('{')
            if next_ptr == -1:
                return d_list
            dstr = dstr[next_ptr:]
            i = 0
            ris = 0
        else:
            i += 1
    return d_list
