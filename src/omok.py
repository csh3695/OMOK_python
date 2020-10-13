from src.socket_interface import *


class Omok(object):
    def __init__(self, id):
        self.id = id
        self.player = []
        self.size = 11
        self.board = generate_matrix([self.size, self.size])
        self.turn_count = 0
        self.start = code.BLACK
        self.next_turn = code.BLACK
        self.who_timeout = None
        self.state_by_server = None
        self.wrong_place_count = {code.BLACK: 0, code.WHITE: 0}

    def init_game(self):
        self.board = np.zeros([self.size, self.size], np.uint8)
        self.turn_count = 0
        self.next_turn = code.BLACK
        self.wrong_place_count = {code.BLACK: 0, code.WHITE: 0}

    def to_dict(self):
        return {'board': board_to_str(self.board),
                'turn_count': self.turn_count,
                'next_turn': self.next_turn,
                'state': self.state(),
                'wrong_place_count': self.wrong_place_count
                }

    def set_state_by_server(self, state):
        self.state_by_server = state

    def set_timeout(self):
        self.who_timeout = self.next_turn

    def state(self):
        if self.state_by_server is not None:
            return self.state_by_server
        if self.who_timeout is not None:
            return code.BLACK if self.who_timeout == code.WHITE else code.WHITE
        if self.wrong_place_count[code.BLACK] > 1:
            return code.WHITE
        if self.wrong_place_count[code.WHITE] > 1:
            return code.BLACK
        if self.turn_count >= 25:
            return code.DRAW
        result = self.check_end(self.board)
        if result == 0:
            return code.ON_GAME
        else:
            return result

    def put_stone(self, x, y, color):
        if self.board[x][y] == 0:
            self.board[x][y] = color
            if color != self.start:
                self.turn_count += 1
            self.next_turn = code.BLACK if self.next_turn == code.WHITE else code.WHITE
            return code.PUT_STONE_SUCCESS
        else:
            self.wrong_place_count[color] += 1
            return code.PUT_STONE_FAIL

    def in_range(self, x, y):
        return (0 <= x < self.size) & (0 <= y < self.size)

    def check_end(self, board):
        if self.turn_count >= 50:
            return -1
        for x in range(len(board)):
            for y in range(len(board[0])):
                if board[x][y] == 0:
                    continue
                if self.in_range(x, y - 1) and board[x][y - 1] != board[x][y]:
                    result = self._check_end(board, x, y, dir=0)
                    if result > 0:
                        return result

                if self.in_range(x - 1, y - 1) and board[x - 1][y - 1] != board[x][y]:
                    result = self._check_end(board, x, y, dir=1)
                    if result > 0:
                        return result

                if self.in_range(x - 1, y) and board[x - 1][y] != board[x][y]:
                    result = self._check_end(board, x, y, dir=2)
                    if result > 0:
                        return result

                if self.in_range(x - 1, y + 1) and board[x - 1][y + 1] != board[x][y]:
                    result = self._check_end(board, x, y, dir=3)
                    if result > 0:
                        return result
        return 0

    def _check_end(self, board, x, y, dir):
        p_id = board[x][y]
        i = 1
        if dir == 0:
            while i < 5:
                if (not self.in_range(x, y + i)) or (board[x][y + i] != p_id):
                    return 0
                i += 1
            return p_id

        elif dir == 1:
            while i < 5:
                if (not self.in_range(x + i, y + i)) or (board[x + i][y + i] != p_id):
                    return 0
                i += 1
            return p_id

        elif dir == 2:
            while i < 5:
                if (not self.in_range(x + i, y)) or (board[x + i][y] != p_id):
                    return 0
                i += 1
            return p_id

        elif dir == 3:
            while i < 5:
                if (not self.in_range(x + i, y - i)) or (board[x + i][y - i] != p_id):
                    return 0
                i += 1
            return p_id

        return 0
