"""
象棋揭棋游戏 - 完整版
包含：双人对战、人机对战、网络对战
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import json
import os
from datetime import datetime
from typing import Optional, List, Tuple
import threading
import socket
import time


# ==================== 配置 ====================

class Config:
    # 窗口设置
    WINDOW_WIDTH = 1100
    WINDOW_HEIGHT = 750
    WINDOW_TITLE = "揭棋对战"

    # 棋盘设置
    CELL_SIZE = 60
    BOARD_PADDING = 40

    # 颜色 - 实木风格
    COLORS = {
        'board_bg': '#D2B48C',
        'board_line': '#5D3A1A',
        'piece_red': '#B43232',
        'piece_red_bg': '#FFEBCD',
        'piece_black': '#282828',
        'piece_black_bg': '#F5F5DC',
        'piece_hidden': '#8B5A2B',
        'piece_hidden_bg': '#D2B48C',
        'highlight': '#90EE90',
        'selected': '#FFD700',
        'capture': '#FF6B6B',
        'bg': '#F5DEB3',
        'button': '#CD853F',
        'button_active': '#A0522D',
    }

    RED_PIECES = ['帅', '仕', '仕', '相', '相', '俥', '俥', '傌', '傌', '炮', '炮', '兵', '兵', '兵', '兵', '兵']
    BLACK_PIECES = ['将', '士', '士', '象', '象', '车', '车', '马', '马', '砲', '砲', '卒', '卒', '卒', '卒', '卒']

    PIECE_VALUES = {
        '帅': 10000, '将': 10000, '俥': 900, '车': 900,
        '傌': 400, '马': 400, '炮': 450, '砲': 450,
        '相': 200, '象': 200, '仕': 200, '士': 200,
        '兵': 100, '卒': 100,
    }

    POSITION_TYPES = {
        (0, 0): '车', (0, 1): '马', (0, 2): '相', (0, 3): '仕', (0, 4): '帅',
        (0, 5): '仕', (0, 6): '相', (0, 7): '马', (0, 8): '车',
        (2, 1): '炮', (2, 7): '炮',
        (3, 0): '兵', (3, 2): '兵', (3, 4): '兵', (3, 6): '兵', (3, 8): '兵',
        (6, 0): '卒', (6, 2): '卒', (6, 4): '卒', (6, 6): '卒', (6, 8): '卒',
        (7, 1): '炮', (7, 7): '炮',
        (9, 0): '车', (9, 1): '马', (9, 2): '象', (9, 3): '士', (9, 4): '将',
        (9, 5): '士', (9, 6): '象', (9, 7): '马', (9, 8): '车',
    }

    # 网络端口
    NETWORK_PORT = 5555


# ==================== 棋子类 ====================

class Piece:
    def __init__(self, piece_type: str, color: str, row: int, col: int):
        self.piece_type = piece_type
        self.color = color
        self.row = row
        self.col = col
        self.is_flipped = False
        self.is_alive = True

    @property
    def position_type(self) -> str:
        if self.is_flipped:
            type_map = {
                '帅': '帅', '将': '帅', '仕': '仕', '士': '仕',
                '相': '相', '象': '相', '俥': '车', '车': '车',
                '傌': '马', '马': '马', '炮': '炮', '砲': '炮',
                '兵': '兵', '卒': '兵',
            }
            return type_map.get(self.piece_type, self.piece_type)
        return Config.POSITION_TYPES.get((self.row, self.col), '兵')

    def flip(self):
        self.is_flipped = True

    def move_to(self, row: int, col: int):
        self.row = row
        self.col = col

    def capture(self):
        self.is_alive = False

    def to_dict(self) -> dict:
        return {
            'type': self.piece_type, 'color': self.color,
            'row': self.row, 'col': self.col,
            'flipped': self.is_flipped, 'alive': self.is_alive
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Piece':
        p = cls(data['type'], data['color'], data['row'], data['col'])
        p.is_flipped = data['flipped']
        p.is_alive = data['alive']
        return p


# ==================== 棋盘类 ====================

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(9)] for _ in range(10)]
        self.pieces: List[Piece] = []
        self.captured_red: List[Piece] = []
        self.captured_black: List[Piece] = []

    def setup(self):
        """初始化棋盘 - 揭棋规则：所有暗子随机分配到所有位置"""
        self.pieces = []
        self.captured_red = []
        self.captured_black = []
        self.grid = [[None for _ in range(9)] for _ in range(10)]

        # 将帅固定为明棋
        red_king = Piece('帅', 'red', 0, 4)
        red_king.is_flipped = True
        self.grid[0][4] = red_king
        self.pieces.append(red_king)

        black_king = Piece('将', 'black', 9, 4)
        black_king.is_flipped = True
        self.grid[9][4] = black_king
        self.pieces.append(black_king)

        # 所有暗子位置（排除将帅位置）
        all_hidden_positions = [
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 5), (0, 6), (0, 7), (0, 8),  # 红方区域（排除(0,4)）
            (2, 1), (2, 7),  # 红方炮位
            (3, 0), (3, 2), (3, 4), (3, 6), (3, 8),  # 红方兵位
            (6, 0), (6, 2), (6, 4), (6, 6), (6, 8),  # 黑方卒位
            (7, 1), (7, 7),  # 黑方炮位
            (9, 0), (9, 1), (9, 2), (9, 3), (9, 5), (9, 6), (9, 7), (9, 8),  # 黑方区域（排除(9,4)）
        ]

        # 创建所有暗子（红黑各15个，排除将帅）
        red_hidden = [Piece(t, 'red', -1, -1) for t in Config.RED_PIECES if t != '帅']
        black_hidden = [Piece(t, 'black', -1, -1) for t in Config.BLACK_PIECES if t != '将']

        # 合并所有暗子并随机打乱
        all_hidden_pieces = red_hidden + black_hidden
        random.shuffle(all_hidden_pieces)
        random.shuffle(all_hidden_positions)

        # 随机分配暗子到位置
        for piece, (row, col) in zip(all_hidden_pieces, all_hidden_positions):
            piece.row, piece.col = row, col
            self.grid[row][col] = piece
            self.pieces.append(piece)

    def get_piece_at(self, row: int, col: int) -> Optional[Piece]:
        if 0 <= row <= 9 and 0 <= col <= 8:
            return self.grid[row][col]
        return None

    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Optional[Piece]:
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.grid[from_row][from_col]
        if not piece:
            return None

        target = self.grid[to_row][to_col]
        if target:
            target.capture()
            if target.color == 'red':
                self.captured_red.append(target)
            else:
                self.captured_black.append(target)

        self.grid[from_row][from_col] = None
        self.grid[to_row][to_col] = piece
        piece.move_to(to_row, to_col)

        if not piece.is_flipped:
            piece.flip()
        return target

    def get_flipped_pieces(self, color: str = None) -> List[Piece]:
        pieces = [p for p in self.pieces if p.is_flipped and p.is_alive]
        if color:
            pieces = [p for p in pieces if p.color == color]
        return pieces

    def get_king(self, color: str) -> Optional[Piece]:
        for p in self.pieces:
            if p.color == color and p.piece_type in ['帅', '将'] and p.is_alive:
                return p
        return None

    def to_dict(self) -> dict:
        return {
            'pieces': [p.to_dict() for p in self.pieces],
            'captured_red': [p.piece_type for p in self.captured_red],
            'captured_black': [p.piece_type for p in self.captured_black],
        }

    def from_dict(self, data: dict):
        """从字典恢复棋盘状态（用于网络同步）"""
        self.pieces = []
        self.captured_red = []
        self.captured_black = []
        self.grid = [[None for _ in range(9)] for _ in range(10)]

        # 恢复棋子
        for p_data in data['pieces']:
            piece = Piece.from_dict(p_data)
            self.pieces.append(piece)
            if piece.is_alive:
                self.grid[piece.row][piece.col] = piece

        # 恢复已被吃的棋子
        for p_type in data.get('captured_red', []):
            p = Piece(p_type, 'red', -1, -1)
            p.is_alive = False
            self.captured_red.append(p)

        for p_type in data.get('captured_black', []):
            p = Piece(p_type, 'black', -1, -1)
            p.is_alive = False
            self.captured_black.append(p)


# ==================== 规则类 ====================

class Rules:
    RED_PALACE = [(0, 3), (0, 4), (0, 5), (1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5)]
    BLACK_PALACE = [(7, 3), (7, 4), (7, 5), (8, 3), (8, 4), (8, 5), (9, 3), (9, 4), (9, 5)]

    @staticmethod
    def get_piece_owner(piece: Piece) -> str:
        """
        获取棋子的表面归属（用于判断是否可以攻击）
        已翻开的棋子：返回真实颜色
        未翻开的暗子：根据位置判断归属（红方区域=row 0-4，黑方区域=row 5-9）
        """
        if piece.is_flipped:
            return piece.color
        # 未翻开的暗子根据位置判断
        return 'red' if piece.row <= 4 else 'black'

    @staticmethod
    def can_attack(attacker: Piece, target: Piece) -> bool:
        """
        判断攻击者是否可以攻击目标

        规则：
        1. 空位可以移动
        2. 明子攻击：
           - 不能攻击己方颜色的明子
           - 不能攻击己方区域的暗子
        3. 暗子攻击（在己方区域）：
           - 不能攻击己方区域的暗子
           - 不能攻击己方颜色的明子
        """
        # 空位可以移动
        if target is None:
            return True

        if attacker.is_flipped:
            # 明子攻击：按颜色判断归属
            attacker_color = attacker.color

            if target.is_flipped:
                # 目标是明子：不能攻击己方颜色的明子
                return target.color != attacker_color
            else:
                # 目标是暗子：不能攻击己方区域的暗子
                target_area = 'red' if target.row <= 4 else 'black'
                return target_area != attacker_color
        else:
            # 暗子攻击：按位置判断归属
            attacker_area = 'red' if attacker.row <= 4 else 'black'

            if target.is_flipped:
                # 目标是明子：不能攻击己方颜色的明子
                return target.color != attacker_area
            else:
                # 目标是暗子：不能攻击己方区域的暗子
                target_area = 'red' if target.row <= 4 else 'black'
                return target_area != attacker_area

    @staticmethod
    def get_valid_moves(piece: Piece, board: Board) -> List[Tuple[int, int]]:
        if not piece or not piece.is_alive:
            return []

        move_type = piece.position_type
        # 注意：method_map 包含红黑双方的所有棋子名称
        method_map = {
            '帅': Rules._get_king_moves, '将': Rules._get_king_moves,
            '仕': Rules._get_advisor_moves, '士': Rules._get_advisor_moves,
            '相': Rules._get_elephant_moves, '象': Rules._get_elephant_moves,
            '车': Rules._get_chariot_moves, '俥': Rules._get_chariot_moves,
            '马': Rules._get_horse_moves, '傌': Rules._get_horse_moves,
            '炮': Rules._get_cannon_moves, '砲': Rules._get_cannon_moves,
            '兵': Rules._get_soldier_moves, '卒': Rules._get_soldier_moves,
        }
        moves = method_map.get(move_type, Rules._get_soldier_moves)(piece, board)

        # 过滤掉不安全的移动（将帅不能被吃）
        moves = [pos for pos in moves if Rules._is_safe_move(piece, pos, board)]

        # 过滤掉不能攻击的目标
        filtered_moves = []
        for pos in moves:
            target = board.get_piece_at(pos[0], pos[1])
            if Rules.can_attack(piece, target):
                filtered_moves.append(pos)

        return filtered_moves

    @staticmethod
    def _get_king_moves(piece, board):
        """将帅走法：九宫内上下左右一格"""
        moves = []
        row, col = piece.row, piece.col
        palace = Rules.RED_PALACE if piece.color == 'red' else Rules.BLACK_PALACE
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if (nr, nc) in palace:
                moves.append((nr, nc))
        return moves

    @staticmethod
    def _get_advisor_moves(piece, board):
        """士仕走法：斜走一格（可过河）"""
        moves = []
        row, col = piece.row, piece.col
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr <= 9 and 0 <= nc <= 8:
                moves.append((nr, nc))
        return moves

    @staticmethod
    def _get_elephant_moves(piece, board):
        """象相走法：走"田"字，塞象眼无效（可过河）"""
        moves = []
        row, col = piece.row, piece.col
        for dr, dc in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            nr, nc = row + dr, col + dc
            if not (0 <= nr <= 9 and 0 <= nc <= 8):
                continue
            if board.get_piece_at(row + dr // 2, col + dc // 2):
                continue
            moves.append((nr, nc))
        return moves

    @staticmethod
    def _get_chariot_moves(piece, board):
        """车俥走法：直线任意距离"""
        moves = []
        row, col = piece.row, piece.col
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            while 0 <= nr <= 9 and 0 <= nc <= 8:
                target = board.get_piece_at(nr, nc)
                if target:
                    moves.append((nr, nc))  # 可以吃子
                    break
                moves.append((nr, nc))  # 空位可以移动
                nr += dr
                nc += dc
        return moves

    @staticmethod
    def _get_horse_moves(piece, board):
        """马傌走法：走"日"字，蹩马腿无效"""
        moves = []
        row, col = piece.row, piece.col
        for dr, dc, lr, lc in [(-2, -1, -1, 0), (-2, 1, -1, 0), (2, -1, 1, 0), (2, 1, 1, 0),
                               (-1, -2, 0, -1), (1, -2, 0, -1), (-1, 2, 0, 1), (1, 2, 0, 1)]:
            nr, nc = row + dr, col + dc
            if not (0 <= nr <= 9 and 0 <= nc <= 8):
                continue
            if board.get_piece_at(row + lr, col + lc):
                continue
            moves.append((nr, nc))
        return moves

    @staticmethod
    def _get_cannon_moves(piece, board):
        """炮砲走法：直线移动，吃子需要隔一个棋子（炮架）"""
        moves = []
        row, col = piece.row, piece.col
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            found = False
            while 0 <= nr <= 9 and 0 <= nc <= 8:
                target = board.get_piece_at(nr, nc)
                if not found:
                    if target is None:
                        moves.append((nr, nc))
                    else:
                        found = True  # 找到炮架
                else:
                    if target:
                        moves.append((nr, nc))  # 可以吃子
                        break
                nr += dr
                nc += dc
        return moves

    @staticmethod
    def _get_soldier_moves(piece, board):
        """
        兵卒走法：向前（对方面向）或左右移动，不能后退
        红兵：向前是row增加（向下），无论在哪个位置
        黑卒：向前是row减少（向上），无论在哪个位置
        未翻开的暗子：根据位置判断（红方区域=row 0-4按红兵规则，黑方区域=row 5-9按黑卒规则）
        """
        moves = []
        row, col = piece.row, piece.col

        # 根据棋子真实颜色判断前进方向（已翻开的明子）
        # 未翻开的暗子根据位置判断
        if piece.is_flipped:
            # 已翻开：根据真实颜色判断
            if piece.color == 'red':
                forward = 1  # 红兵向前是row增加
            else:
                forward = -1  # 黑卒向前是row减少
        else:
            # 未翻开：根据位置判断
            if row <= 4:
                forward = 1  # 在红方区域，按红兵规则
            else:
                forward = -1  # 在黑方区域，按黑卒规则

        # 可以向前、左、右移动
        for dr, dc in [(forward, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr <= 9 and 0 <= nc <= 8:
                moves.append((nr, nc))
        return moves

    @staticmethod
    def _is_safe_move(piece, target_pos, board) -> bool:
        from_pos = (piece.row, piece.col)
        target = board.get_piece_at(*target_pos)

        board.grid[from_pos[0]][from_pos[1]] = None
        board.grid[target_pos[0]][target_pos[1]] = piece
        piece.row, piece.col = target_pos
        if target:
            target.is_alive = False

        in_check = Rules.is_in_check(piece.color, board)
        kings_facing = Rules.is_kings_facing(board)

        board.grid[target_pos[0]][target_pos[1]] = target
        board.grid[from_pos[0]][from_pos[1]] = piece
        piece.row, piece.col = from_pos
        if target:
            target.is_alive = True

        return not in_check and not kings_facing

    @staticmethod
    def is_in_check(color: str, board: Board) -> bool:
        king = board.get_king(color)
        if not king:
            return False
        enemy = 'black' if color == 'red' else 'red'
        for piece in board.get_flipped_pieces(enemy):
            moves = Rules._get_raw_moves(piece, board)
            if (king.row, king.col) in moves:
                return True
        return False

    @staticmethod
    def _get_raw_moves(piece, board):
        method_map = {
            '帅': Rules._get_king_moves, '将': Rules._get_king_moves,
            '仕': Rules._get_advisor_moves, '士': Rules._get_advisor_moves,
            '相': Rules._get_elephant_moves, '象': Rules._get_elephant_moves,
            '车': Rules._get_chariot_moves, '俥': Rules._get_chariot_moves,
            '马': Rules._get_horse_moves, '傌': Rules._get_horse_moves,
            '炮': Rules._get_cannon_moves, '砲': Rules._get_cannon_moves,
            '兵': Rules._get_soldier_moves, '卒': Rules._get_soldier_moves,
        }
        return method_map.get(piece.position_type, Rules._get_soldier_moves)(piece, board)

    @staticmethod
    def is_kings_facing(board: Board) -> bool:
        red_king = board.get_king('red')
        black_king = board.get_king('black')
        if not red_king or not black_king or red_king.col != black_king.col:
            return False
        for row in range(min(red_king.row, black_king.row) + 1, max(red_king.row, black_king.row)):
            if board.get_piece_at(row, red_king.col):
                return False
        return True

    @staticmethod
    def is_checkmate(color: str, board: Board) -> bool:
        """判断是否被将死（被将军且无法解除）"""
        if not Rules.is_in_check(color, board):
            return False
        for piece in board.pieces:
            if piece.color == color and piece.is_alive and Rules.get_valid_moves(piece, board):
                return False
        return True

    @staticmethod
    def is_stalemate(color: str, board: Board) -> bool:
        """判断是否困毙（没有被将军但无法移动）"""
        if Rules.is_in_check(color, board):
            return False
        for piece in board.pieces:
            if piece.color == color and piece.is_alive and Rules.get_valid_moves(piece, board):
                return False
        return True


# ==================== AI类 ====================

class ChessAI:
    def __init__(self, difficulty: str = 'medium'):
        self.difficulty = difficulty
        self.depth = {'easy': 1, 'medium': 2, 'hard': 3}.get(difficulty, 2)

    def get_best_move(self, board: Board, color: str) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        moves = []

        # 已翻开的棋子
        for piece in board.get_flipped_pieces(color):
            for target in Rules.get_valid_moves(piece, board):
                moves.append(((piece.row, piece.col), target))

        # 未翻开的暗子（己方区域内的）
        # 红方区域：row 0-4，黑方区域：row 5-9
        for piece in board.pieces:
            if piece.is_alive and not piece.is_flipped:
                # 检查是否在己方区域（按位置判断，不是按颜色）
                if color == 'red' and piece.row <= 4:
                    for target in Rules.get_valid_moves(piece, board):
                        moves.append(((piece.row, piece.col), target))
                elif color == 'black' and piece.row >= 5:
                    for target in Rules.get_valid_moves(piece, board):
                        moves.append(((piece.row, piece.col), target))

        if not moves:
            return None

        if self.difficulty == 'easy':
            return random.choice(moves)

        best_move, best_score = None, float('-inf')
        for move in moves:
            score = self._evaluate_move(board, move, color)
            if score > best_score:
                best_score, best_move = score, move

        return best_move or random.choice(moves)

    def _evaluate_move(self, board: Board, move, color: str) -> float:
        from_pos, to_pos = move
        target = board.get_piece_at(*to_pos)
        score = Config.PIECE_VALUES.get(target.piece_type, 100) if target else 0
        piece = board.get_piece_at(*from_pos)
        if piece:
            score += 5 - abs(to_pos[1] - 4)
        return score


# ==================== 网络类 ====================

class NetworkManager:
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.is_host = False
        self.running = False
        self.on_message = None
        self.receive_thread = None

    def get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def create_room(self, on_connected, on_error) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', Config.NETWORK_PORT))
            self.socket.listen(1)
            self.is_host = True
            self.running = True

            def accept_loop():
                try:
                    self.socket.settimeout(1.0)
                    while self.running and not self.connected:
                        try:
                            client, addr = self.socket.accept()
                            self.client_socket = client
                            self.connected = True
                            self._start_receive(client)
                            if on_connected:
                                on_connected(addr)
                            break
                        except socket.timeout:
                            continue
                except Exception as e:
                    if on_error:
                        on_error(str(e))

            threading.Thread(target=accept_loop, daemon=True).start()
            return True
        except Exception as e:
            if on_error:
                on_error(str(e))
            return False

    def join_room(self, host_ip: str, on_connected, on_error) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host_ip, Config.NETWORK_PORT))
            self.is_host = False
            self.connected = True
            self.running = True
            self._start_receive(self.socket)
            if on_connected:
                on_connected((host_ip, Config.NETWORK_PORT))
            return True
        except Exception as e:
            if on_error:
                on_error(str(e))
            return False

    def _start_receive(self, sock):
        def receive_loop():
            while self.running and self.connected:
                try:
                    sock.settimeout(1.0)
                    data = sock.recv(4096)
                    if not data:
                        break
                    msg = json.loads(data.decode('utf-8'))
                    if self.on_message:
                        self.on_message(msg)
                except socket.timeout:
                    continue
                except:
                    break
            self.connected = False

        self.receive_thread = threading.Thread(target=receive_loop, daemon=True)
        self.receive_thread.start()

    def send(self, msg_type: str, data: dict):
        if not self.connected:
            return False
        msg = json.dumps({'type': msg_type, 'data': data, 'time': time.time()})
        try:
            sock = self.client_socket if self.is_host else self.socket
            sock.send(msg.encode('utf-8'))
            return True
        except:
            return False

    def close(self):
        self.running = False
        self.connected = False
        try:
            if self.is_host and hasattr(self, 'client_socket'):
                self.client_socket.close()
            if self.socket:
                self.socket.close()
        except:
            pass


# ==================== 排行榜类 ====================

class Leaderboard:
    def __init__(self):
        self.records = []
        self.file = 'data/records.json'
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.file):
                with open(self.file, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
        except:
            self.records = []

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.file), exist_ok=True)
            with open(self.file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except:
            pass

    def add(self, mode: str, result: str, opponent: str, duration: int = 0):
        self.records.append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'mode': mode, 'result': result, 'opponent': opponent, 'duration': duration,
        })
        self.save()

    def get_stats(self) -> dict:
        total = len(self.records)
        wins = sum(1 for r in self.records if r['result'] == '胜')
        return {'total': total, 'wins': wins, 'losses': total - wins,
                'win_rate': round(wins / total * 100, 1) if total > 0 else 0}


# ==================== 游戏主类 ====================

class JieqiGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(Config.WINDOW_TITLE)
        self.root.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.root.configure(bg=Config.COLORS['bg'])
        self.root.resizable(False, False)

        # 游戏状态
        self.board = Board()
        self.current_player = 'red'
        self.selected_piece: Optional[Piece] = None
        self.valid_moves: List[Tuple[int, int]] = []
        self.game_mode = 'pvp'
        self.ai_difficulty = 'medium'
        self.move_history = []
        self.game_active = False
        self.ai = ChessAI(self.ai_difficulty)
        self.leaderboard = Leaderboard()
        self.start_time = None

        # 人机对战执方
        self.player_color: Optional[str] = None
        self.ai_color: Optional[str] = None
        self.first_player: str = 'red'  # 先手方，默认红方

        # 倒计时
        self.turn_start_time: float = 0
        self.turn_timeout: int = 30  # 30秒超时
        self.timer_id: Optional[str] = None
        self.timer_label_id: Optional[int] = None
        self.is_paused: bool = False  # 暂停状态
        self.warning_shown: bool = False  # 是否已显示5秒警告
        self.pause_time: float = 0  # 暂停开始时间

        # 网络状态
        self.network = NetworkManager()
        self.my_color: Optional[str] = None
        self.opponent_connected = False
        self.room_ip = ""

        # 按钮列表
        self.buttons = []
        self.labels = []

        # 创建画布
        self.canvas = tk.Canvas(
            self.root, width=Config.WINDOW_WIDTH, height=Config.WINDOW_HEIGHT,
            bg=Config.COLORS['bg'], highlightthickness=0
        )
        self.canvas.pack()
        self.canvas.bind('<Button-1>', self.on_click)

        # 显示主菜单
        self.show_menu()

    def clear_widgets(self):
        """清除所有按钮和标签"""
        for btn in self.buttons:
            try:
                btn.destroy()
            except:
                pass
        for lbl in self.labels:
            try:
                lbl.destroy()
            except:
                pass
        self.buttons = []
        self.labels = []
        self.canvas.delete('all')

    def draw_button(self, x: int, y: int, w: int, h: int, text: str, cmd) -> tk.Button:
        btn = tk.Button(
            self.root, text=text, font=('SimHei', 14),
            bg=Config.COLORS['button'], fg='white',
            activebackground=Config.COLORS['button_active'], activeforeground='white',
            relief='flat', cursor='hand2', command=cmd
        )
        btn.place(x=x, y=y, width=w, height=h)
        self.buttons.append(btn)
        return btn

    def draw_label(self, x: int, y: int, text: str, font_size: int = 14, color: str = None) -> tk.Label:
        lbl = tk.Label(
            self.root, text=text, font=('SimHei', font_size),
            bg=Config.COLORS['bg'], fg=color or Config.COLORS['board_line']
        )
        lbl.place(x=x, y=y)
        self.labels.append(lbl)
        return lbl

    # ==================== 菜单界面 ====================

    def show_menu(self):
        self.clear_widgets()
        self.game_active = False
        self.network.close()

        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 80, text="揭 棋 对 战",
                                font=('SimHei', 36, 'bold'), fill=Config.COLORS['board_line'])
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 130, text="中国象棋揭棋变体",
                                font=('SimHei', 16), fill=Config.COLORS['board_line'])

        buttons_data = [
            ("双人对战", self.start_pvp),
            ("人机对战", self.show_difficulty_menu),
            ("网络对战", self.show_network_menu),
            ("游戏规则", self.show_rules),
            ("排行榜", self.show_leaderboard),
            ("退出游戏", self.quit_game),
        ]
        y = 200
        for text, cmd in buttons_data:
            self.draw_button(Config.WINDOW_WIDTH // 2 - 80, y, 160, 45, text, cmd)
            y += 60

    def start_pvp(self):
        self.game_mode = 'pvp'
        self.start_game()

    def show_difficulty_menu(self):
        self.clear_widgets()
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 100, text="选择AI难度",
                                font=('SimHei', 28, 'bold'), fill=Config.COLORS['board_line'])

        y = 200
        for text, diff in [("简单", 'easy'), ("中等", 'medium'), ("困难", 'hard')]:
            self.draw_button(Config.WINDOW_WIDTH // 2 - 80, y, 160, 45, text,
                             lambda d=diff: self.select_difficulty(d))
            y += 60
        self.draw_button(Config.WINDOW_WIDTH // 2 - 80, y + 20, 160, 40, "返回主菜单", self.show_menu)

    def select_difficulty(self, difficulty: str):
        self.ai_difficulty = difficulty
        self.ai = ChessAI(difficulty)
        self.game_mode = 'pve'
        # 玩家执黑方，玩家先手（人先手）
        self.player_color = 'black'
        self.ai_color = 'red'
        # 人机对战：黑方先手（玩家先走）
        self.first_player = 'black'
        self.start_game()

    # ==================== 网络对战 ====================

    def show_network_menu(self):
        self.clear_widgets()
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 80, text="网络对战",
                                font=('SimHei', 28, 'bold'), fill=Config.COLORS['board_line'])

        local_ip = self.network.get_local_ip()
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 140, text=f"本机IP: {local_ip}",
                                font=('SimHei', 14), fill='gray')

        # 房间ID输入框
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 200, text="输入对方IP地址:",
                                font=('SimHei', 14), fill=Config.COLORS['board_line'])

        self.ip_entry = tk.Entry(self.root, font=('SimHei', 14), width=15)
        self.ip_entry.place(x=Config.WINDOW_WIDTH // 2 - 60, y=225)
        self.buttons.append(self.ip_entry)  # 用buttons列表管理以便清除

        self.draw_button(Config.WINDOW_WIDTH // 2 - 80, 280, 160, 45, "创建房间", self.create_room)
        self.draw_button(Config.WINDOW_WIDTH // 2 - 80, 340, 160, 45, "加入房间", self.join_room)
        self.draw_button(Config.WINDOW_WIDTH // 2 - 80, 400, 160, 40, "返回主菜单", self.show_menu)

        # 状态显示
        self.status_label = self.draw_label(Config.WINDOW_WIDTH // 2 - 80, 460, "状态: 未连接", 12, 'gray')

    def show_rules(self):
        """显示游戏规则 - 多页显示"""
        self.clear_widgets()
        self.rules_page = 0  # 当前页码
        self.rules_pages = self._get_rules_pages()
        self._draw_rules_page()

    def _get_rules_pages(self):
        """获取规则页面内容"""
        pages = [
            {
                'title': '基本规则',
                'lines': [
                    "【棋盘与棋子】",
                    "• 棋子反扣随机放置，将帅为明棋",
                    "• 未翻开的棋子按位置类型走法移动",
                    "• 移动后棋子翻开，显示真实身份",
                    "• 翻开后按标准象棋规则走棋",
                    "",
                    "【特殊规则】",
                    "• 士象可以过河（与标准象棋不同）",
                    "• 将死或困毙对方帅将获胜",
                    "• 帅将照面判负",
                    "• 吃掉对方将帅立即获胜",
                    "",
                    "【倒计时规则】",
                    "• 每回合30秒倒计时",
                    "• 剩余5秒时弹出警告",
                    "• 超时未操作判负",
                    "• 点击'暂停'按钮可暂停倒计时",
                ]
            },
            {
                'title': '攻击与选择规则',
                'lines': [
                    "【暗子选择规则】",
                    "• 红方只能操作红方区域(row 0-4)的暗子",
                    "• 黑方只能操作黑方区域(row 5-9)的暗子",
                    "",
                    "【明子攻击规则】",
                    "• 不能攻击己方颜色的明子",
                    "• 不能攻击己方区域的暗子",
                    "",
                    "【暗子攻击规则】",
                    "• 不能攻击己方区域的暗子",
                    "• 不能攻击己方颜色的明子",
                    "",
                    "【人机对战】",
                    "• 玩家执黑方，玩家先手",
                    "• AI执红方，后手",
                ]
            },
            {
                'title': '棋子走法',
                'lines': [
                    "【将/帅】九宫内上下左右一格，不能照面",
                    "【士/仕】斜走一格，可过河",
                    "【相/象】走'田'字，塞象眼无效，可过河",
                    "【车/俥】直线任意距离",
                    "【马/傌】走'日'字，蹩马腿无效",
                    "【炮/砲】直线移动；吃子需隔一子",
                    "【兵/卒】向前或左右一格，不能后退",
                    "",
                    "【兵/卒移动方向】",
                    "• 已翻开的明子：按真实颜色判断",
                    "  红兵向下(row增加)，黑卒向上(row减少)",
                    "• 未翻开的暗子：按位置判断",
                    "  红方区域向下，黑方区域向上",
                ]
            },
            {
                'title': '网络对战说明',
                'lines': [
                    "【连接条件】",
                    "• 局域网内（连接同一个路由器/WiFi）",
                    "• 端口5555未被防火墙阻止",
                    "",
                    "【操作步骤】",
                    "• 创建房间方（红方，先手）：",
                    "  点击'创建房间'，等待对手连接",
                    "• 加入房间方（黑方，后手）：",
                    "  输入对方IP，点击'加入房间'",
                    "",
                    "【同步机制】",
                    "• 创建方初始化棋盘后发送状态",
                    "• 加入方接收后恢复相同棋盘状态",
                    "",
                    "【已知问题】",
                    "• 倒计时各自独立，不同步",
                    "• 断线无法重连",
                ]
            },
        ]
        return pages

    def _draw_rules_page(self):
        """绘制当前规则页"""
        self.clear_widgets()

        page = self.rules_pages[self.rules_page]

        # 标题
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 50,
                                text=f"游戏规则 ({self.rules_page + 1}/{len(self.rules_pages)})",
                                font=('SimHei', 28, 'bold'), fill=Config.COLORS['board_line'])

        # 副标题
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 100,
                                text=page['title'],
                                font=('SimHei', 18, 'bold'), fill=Config.COLORS['piece_red'])

        # 内容
        y = 150
        for line in page['lines']:
            if line.startswith('【'):
                # 小标题
                self.canvas.create_text(Config.WINDOW_WIDTH // 2, y, text=line,
                                        font=('SimHei', 14, 'bold'), fill=Config.COLORS['board_line'])
            else:
                # 普通文本
                self.canvas.create_text(Config.WINDOW_WIDTH // 2, y, text=line,
                                        font=('SimHei', 13), fill=Config.COLORS['board_line'])
            y += 28

        # 翻页按钮
        btn_y = Config.WINDOW_HEIGHT - 80

        if self.rules_page > 0:
            self.draw_button(Config.WINDOW_WIDTH // 2 - 250, btn_y, 100, 40, "上一页", self._prev_rules_page)

        if self.rules_page < len(self.rules_pages) - 1:
            self.draw_button(Config.WINDOW_WIDTH // 2 - 50, btn_y, 100, 40, "下一页", self._next_rules_page)
        else:
            self.draw_button(Config.WINDOW_WIDTH // 2 - 50, btn_y, 100, 40, "返回菜单", self.show_menu)

    def _next_rules_page(self):
        """下一页"""
        if self.rules_page < len(self.rules_pages) - 1:
            self.rules_page += 1
            self._draw_rules_page()

    def _prev_rules_page(self):
        """上一页"""
        if self.rules_page > 0:
            self.rules_page -= 1
            self._draw_rules_page()

    def show_leaderboard(self):
        """显示排行榜"""
        self.clear_widgets()
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 80, text="排行榜",
                                font=('SimHei', 28, 'bold'), fill=Config.COLORS['board_line'])

        stats = self.leaderboard.get_stats()
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 180,
                                text=f"总战绩: {stats['wins']}胜 {stats['losses']}负",
                                font=('SimHei', 18), fill=Config.COLORS['board_line'])
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 220,
                                text=f"胜率: {stats['win_rate']}%",
                                font=('SimHei', 18), fill=Config.COLORS['board_line'])
        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 260,
                                text=f"总对局: {stats['total']}局",
                                font=('SimHei', 18), fill=Config.COLORS['board_line'])

        self.canvas.create_text(Config.WINDOW_WIDTH // 2, 320, text="最近对局",
                                font=('SimHei', 16, 'bold'), fill=Config.COLORS['board_line'])

        y = 350
        for record in self.leaderboard.records[-5:][::-1]:
            text = f"{record['date']} {record['mode']} {record['result']}"
            self.canvas.create_text(Config.WINDOW_WIDTH // 2, y, text=text,
                                    font=('SimHei', 12), fill=Config.COLORS['board_line'])
            y += 25

        self.draw_button(Config.WINDOW_WIDTH // 2 - 80, 520, 160, 40, "返回主菜单", self.show_menu)

    def create_room(self):
        self.my_color = 'red'
        self.room_ip = self.network.get_local_ip()
        self.status_label.config(text=f"状态: 等待对手连接... 房间IP: {self.room_ip}")

        def on_connected(addr):
            self.root.after(0, lambda: self.on_opponent_connected(addr))

        def on_error(msg):
            self.root.after(0, lambda: self.status_label.config(text=f"错误: {msg}"))

        if self.network.create_room(on_connected, on_error):
            self.status_label.config(text=f"状态: 等待对手连接... 房间IP: {self.room_ip}")
        else:
            self.status_label.config(text="状态: 创建房间失败")

    def join_room(self):
        host_ip = self.ip_entry.get().strip()
        if not host_ip:
            self.status_label.config(text="请输入对方IP地址")
            return

        self.my_color = 'black'
        self.status_label.config(text="状态: 正在连接...")

        def on_connected(addr):
            self.root.after(0, lambda: self.on_join_connected(addr))

        def on_error(msg):
            self.root.after(0, lambda: self.status_label.config(text=f"连接失败: {msg}"))

        if self.network.join_room(host_ip, on_connected, on_error):
            self.opponent_connected = True
            self.network.on_message = self.on_network_message
            self.game_mode = 'online'
            # 加入方不立即开始游戏，等待接收棋盘状态
            # 清空棋盘，显示等待状态
            self.clear_widgets()
            self.canvas.create_text(Config.WINDOW_WIDTH // 2, Config.WINDOW_HEIGHT // 2,
                                    text="等待接收棋盘状态...",
                                    font=('SimHei', 24), fill=Config.COLORS['board_line'])
        else:
            self.status_label.config(text="连接失败")

    def on_join_connected(self, addr):
        """加入方连接成功"""
        self.opponent_connected = True
        self.network.on_message = self.on_network_message
        self.game_mode = 'online'

    def on_opponent_connected(self, addr):
        """创建方连接成功（对手加入）"""
        self.opponent_connected = True
        self.network.on_message = self.on_network_message
        self.game_mode = 'online'
        # 创建方初始化棋盘
        self.start_game()
        # 延迟发送棋盘状态，确保游戏已完全初始化
        self.root.after(1000, self.send_board_state)

    def send_board_state(self):
        """发送棋盘状态给对方"""
        self.network.send('board_state', {
            'board': self.board.to_dict(),
            'current_player': self.current_player
        })

    def on_network_message(self, msg):
        """处理网络消息"""
        msg_type = msg.get('type')
        data = msg.get('data', {})

        if msg_type == 'board_state':
            # 接收棋盘状态（加入方）
            print(f"[DEBUG] 收到棋盘状态: {len(data.get('board', {}).get('pieces', []))} 个棋子")
            self.board.from_dict(data['board'])
            self.current_player = data.get('current_player', 'red')
            self.game_active = True
            self.start_time = datetime.now()
            self.turn_start_time = time.time()
            self.warning_shown = False
            self.is_paused = False
            self.selected_piece = None
            self.valid_moves = []
            self.move_history = []
            # 初始化计时器
            self.timer_id = None
            self.draw_game()
            self.start_timer()

        elif msg_type == 'move':
            if not self.game_active:
                return
            from_pos = tuple(data['from'])
            to_pos = tuple(data['to'])
            self.execute_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1], network=False)
            self.root.after(0, self.draw_game)

        elif msg_type == 'resign':
            winner = 'red' if self.my_color == 'red' else 'black'
            self.root.after(0, lambda: self.end_game(winner, "对方认输"))

    def send_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        """发送走棋信息"""
        self.network.send('move', {
            'from': list(from_pos),
            'to': list(to_pos)
        })

    def send_resign(self):
        """发送认输"""
        self.network.send('resign', {})

    # ==================== 游戏界面 ====================

    def start_game(self):
        self.clear_widgets()
        self.board.setup()
        # 人机对战：黑方先手；其他模式：红方先手
        self.current_player = self.first_player if self.game_mode == 'pve' else 'red'
        self.selected_piece = None
        self.valid_moves = []
        self.move_history = []
        self.game_active = True
        self.start_time = datetime.now()

        # 初始化倒计时
        self.turn_start_time = time.time()
        self.turn_timeout = 30  # 30秒超时
        self.timer_id = None
        self.is_paused = False
        self.warning_shown = False

        self.draw_game()
        self.start_timer()

        # 人机对战模式：如果AI先手才需要AI先走
        if self.game_mode == 'pve' and self.current_player == self.ai_color:
            self.root.after(500, self.ai_move)

    def draw_game(self):
        self.clear_widgets()
        self.draw_board()
        self.draw_pieces()
        self.draw_info_panel()

    def draw_board(self):
        x0, y0 = Config.BOARD_PADDING, Config.BOARD_PADDING
        cell = Config.CELL_SIZE

        self.canvas.create_rectangle(
            x0 - 10, y0 - 10, x0 + 8 * cell + 10, y0 + 9 * cell + 10,
            fill=Config.COLORS['board_bg'], outline=Config.COLORS['board_line'], width=3
        )

        for i in range(10):
            y = y0 + i * cell
            self.canvas.create_line(x0, y, x0 + 8 * cell, y, fill=Config.COLORS['board_line'], width=2)

        for i in range(9):
            x = x0 + i * cell
            if i == 0 or i == 8:
                self.canvas.create_line(x, y0, x, y0 + 9 * cell, fill=Config.COLORS['board_line'], width=2)
            else:
                self.canvas.create_line(x, y0, x, y0 + 4 * cell, fill=Config.COLORS['board_line'], width=2)
                self.canvas.create_line(x, y0 + 5 * cell, x, y0 + 9 * cell, fill=Config.COLORS['board_line'], width=2)

        self.canvas.create_line(x0 + 3 * cell, y0, x0 + 5 * cell, y0 + 2 * cell, fill=Config.COLORS['board_line'], width=2)
        self.canvas.create_line(x0 + 5 * cell, y0, x0 + 3 * cell, y0 + 2 * cell, fill=Config.COLORS['board_line'], width=2)
        self.canvas.create_line(x0 + 3 * cell, y0 + 7 * cell, x0 + 5 * cell, y0 + 9 * cell, fill=Config.COLORS['board_line'], width=2)
        self.canvas.create_line(x0 + 5 * cell, y0 + 7 * cell, x0 + 3 * cell, y0 + 9 * cell, fill=Config.COLORS['board_line'], width=2)

        self.canvas.create_text(x0 + 2 * cell, y0 + 4.5 * cell, text="楚 河", font=('SimHei', 14), fill=Config.COLORS['board_line'])
        self.canvas.create_text(x0 + 6 * cell, y0 + 4.5 * cell, text="汉 界", font=('SimHei', 14), fill=Config.COLORS['board_line'])

    def draw_pieces(self):
        for piece in self.board.pieces:
            if piece.is_alive:
                self.draw_piece(piece)
        for pos in self.valid_moves:
            self.draw_move_hint(pos)

    def draw_piece(self, piece: Piece):
        x0, y0 = Config.BOARD_PADDING, Config.BOARD_PADDING
        cell, r = Config.CELL_SIZE, 25
        x = x0 + piece.col * cell
        y = y0 + piece.row * cell

        if piece == self.selected_piece:
            self.canvas.create_oval(x - r - 5, y - r - 5, x + r + 5, y + r + 5,
                                    outline=Config.COLORS['selected'], width=3)

        bg = Config.COLORS['piece_red_bg'] if piece.is_flipped and piece.color == 'red' else \
             Config.COLORS['piece_black_bg'] if piece.is_flipped else Config.COLORS['piece_hidden_bg']
        fg = Config.COLORS['piece_red'] if piece.is_flipped and piece.color == 'red' else \
             Config.COLORS['piece_black'] if piece.is_flipped else Config.COLORS['piece_hidden']

        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=bg, outline=Config.COLORS['board_line'], width=2)
        self.canvas.create_text(x, y, text=piece.piece_type if piece.is_flipped else '?',
                                font=('SimHei', 18, 'bold'), fill=fg)

    def draw_move_hint(self, pos: Tuple[int, int]):
        x0, y0, cell = Config.BOARD_PADDING, Config.BOARD_PADDING, Config.CELL_SIZE
        x, y = x0 + pos[1] * cell, y0 + pos[0] * cell
        target = self.board.get_piece_at(pos[0], pos[1])
        if target:
            self.canvas.create_oval(x - 28, y - 28, x + 28, y + 28, outline=Config.COLORS['capture'], width=3)
        else:
            self.canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill=Config.COLORS['highlight'])

    def draw_info_panel(self):
        panel_x = Config.BOARD_PADDING + 8 * Config.CELL_SIZE + 30

        # 回合
        turn_text = "红方回合" if self.current_player == 'red' else "黑方回合"
        turn_color = Config.COLORS['piece_red'] if self.current_player == 'red' else Config.COLORS['piece_black']
        self.canvas.create_text(panel_x + 50, 50, text=turn_text, font=('SimHei', 18, 'bold'), fill=turn_color)

        # 显示玩家执方
        if self.game_mode == 'pve':
            my_text = f"你是: {'红方' if self.player_color == 'red' else '黑方'}"
            self.canvas.create_text(panel_x + 50, 80, text=my_text, font=('SimHei', 12), fill='gray')
        elif self.game_mode == 'online':
            my_text = f"你是: {'红方' if self.my_color == 'red' else '黑方'}"
            self.canvas.create_text(panel_x + 50, 80, text=my_text, font=('SimHei', 12), fill='gray')

        # 倒计时显示
        if self.is_paused:
            self.canvas.create_text(
                panel_x + 50, 110,
                text="⏸ 已暂停",
                font=('SimHei', 14, 'bold'),
                fill=Config.COLORS['piece_red']
            )
        else:
            remaining = self.get_remaining_time()
            timer_color = Config.COLORS['piece_red'] if remaining <= 5 else Config.COLORS['board_line']
            self.timer_label_id = self.canvas.create_text(
                panel_x + 50, 110,
                text=f"剩余时间: {remaining}秒",
                font=('SimHei', 14, 'bold'),
                fill=timer_color
            )

        # 已吃棋子
        self.canvas.create_text(panel_x + 50, 140, text="已吃棋子", font=('SimHei', 14, 'bold'), fill=Config.COLORS['board_line'])
        black_captured = ' '.join([p.piece_type for p in self.board.captured_black])
        red_captured = ' '.join([p.piece_type for p in self.board.captured_red])
        self.canvas.create_text(panel_x + 50, 165, text=f"黑: {black_captured or '无'}", font=('SimHei', 12), fill=Config.COLORS['piece_black'])
        self.canvas.create_text(panel_x + 50, 190, text=f"红: {red_captured or '无'}", font=('SimHei', 12), fill=Config.COLORS['piece_red'])

        # 按钮
        btn_y = 250
        pause_text = "继续" if self.is_paused else "暂停"
        for text, cmd in [("悔棋", self.undo_move), ("提示", self.show_hint), (pause_text, self.toggle_pause),
                          ("认输", self.resign), ("重开", self.restart_game), ("返回菜单", self.show_menu)]:
            self.draw_button(panel_x, btn_y, 100, 35, text, cmd)
            btn_y += 40

    # ==================== 倒计时逻辑 ====================

    def start_timer(self):
        """启动回合倒计时"""
        self.turn_start_time = time.time()
        self.update_timer()

    def update_timer(self):
        """更新倒计时显示"""
        if not self.game_active or self.is_paused:
            return

        remaining = self.get_remaining_time()

        # 5秒警告提示
        if remaining == 5 and not self.warning_shown:
            self.warning_shown = True
            messagebox.showwarning("时间警告", "仅剩5秒！请尽快操作！")

        # 检查超时
        if remaining <= 0:
            self.handle_timeout()
            return

        # 更新显示
        self.draw_game()

        # 继续倒计时
        self.timer_id = self.root.after(1000, self.update_timer)

    def get_remaining_time(self) -> int:
        """获取剩余时间"""
        elapsed = time.time() - self.turn_start_time
        return max(0, self.turn_timeout - int(elapsed))

    def handle_timeout(self):
        """处理超时"""
        if not self.game_active:
            return

        # 超时判负
        winner = 'black' if self.current_player == 'red' else 'red'
        self.end_game(winner, f"{'红方' if self.current_player == 'red' else '黑方'}超时")

    def stop_timer(self):
        """停止倒计时"""
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def toggle_pause(self):
        """切换暂停状态"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_time = time.time()
            messagebox.showinfo("游戏暂停", "游戏已暂停，点击暂停按钮继续")
        else:
            # 恢复时调整开始时间，扣除暂停时间
            if hasattr(self, 'pause_time'):
                pause_duration = time.time() - self.pause_time
                self.turn_start_time += pause_duration
            self.update_timer()
        self.draw_game()

    # ==================== 游戏逻辑 ====================

    def on_click(self, event):
        if not self.game_active:
            return

        # 网络对战检查是否轮到我
        if self.game_mode == 'online' and self.current_player != self.my_color:
            return

        # AI回合不处理（人机对战模式）
        if self.game_mode == 'pve' and self.current_player == self.ai_color:
            return

        x0, y0, cell = Config.BOARD_PADDING, Config.BOARD_PADDING, Config.CELL_SIZE
        col = round((event.x - x0) / cell)
        row = round((event.y - y0) / cell)

        if not (0 <= row <= 9 and 0 <= col <= 8):
            return

        self.handle_board_click(row, col)

    def handle_board_click(self, row: int, col: int):
        pos = (row, col)
        if self.selected_piece:
            if pos in self.valid_moves:
                self.make_move(self.selected_piece.row, self.selected_piece.col, row, col)
            else:
                self.select_piece_at(row, col)
        else:
            self.select_piece_at(row, col)
        self.draw_game()

    def select_piece_at(self, row: int, col: int):
        piece = self.board.get_piece_at(row, col)
        if not piece:
            self.selected_piece, self.valid_moves = None, []
            return

        # 已翻开的棋子：只能选择当前回合玩家的棋子（按颜色）
        if piece.is_flipped:
            if piece.color != self.current_player:
                self.selected_piece, self.valid_moves = None, []
                return
        else:
            # 未翻开的暗子：只能选择己方区域内的
            # 红方区域：row 0-4，黑方区域：row 5-9
            # 这是根据棋盘位置判断，而不是棋子真实颜色
            if self.current_player == 'red' and row > 4:
                self.selected_piece, self.valid_moves = None, []
                return
            if self.current_player == 'black' and row < 5:
                self.selected_piece, self.valid_moves = None, []
                return

        self.selected_piece = piece
        self.valid_moves = Rules.get_valid_moves(piece, self.board)

    def make_move(self, from_row: int, from_col: int, to_row: int, to_col: int):
        # 网络对战发送走棋
        if self.game_mode == 'online':
            self.send_move((from_row, from_col), (to_row, to_col))

        self.execute_move(from_row, from_col, to_row, to_col)

    def execute_move(self, from_row: int, from_col: int, to_row: int, to_col: int, network: bool = True):
        """执行走棋"""
        piece = self.board.get_piece_at(from_row, from_col)
        target = self.board.get_piece_at(to_row, to_col)
        self.move_history.append({
            'piece': piece, 'from': (from_row, from_col),
            'to': (to_row, to_col), 'target': target, 'was_flipped': piece.is_flipped,
        })

        self.board.move_piece((from_row, from_col), (to_row, to_col))
        self.selected_piece, self.valid_moves = None, []

        # 检查是否吃掉了将/帅 - 立即结束游戏
        if target and target.piece_type in ['帅', '将']:
            self.end_game(self.current_player, f"吃掉{'红帅' if target.piece_type == '帅' else '黑将'}")
            return

        enemy = 'black' if self.current_player == 'red' else 'red'
        # 检查将死（被将军且无法解除）
        if Rules.is_checkmate(enemy, self.board):
            self.end_game(self.current_player, "将死")
            return

        # 检查困毙（没有被将军但无法移动）
        if Rules.is_stalemate(enemy, self.board):
            self.end_game(self.current_player, "困毙")
            return

        if Rules.is_kings_facing(self.board):
            winner = 'red' if self.current_player == 'black' else 'black'
            self.end_game(winner, "帅将照面")
            return

        self.current_player = 'black' if self.current_player == 'red' else 'red'

        # 重置计时器和警告标志
        self.stop_timer()
        self.turn_start_time = time.time()
        self.warning_shown = False
        self.start_timer()

        if self.game_mode == 'pve' and self.current_player == self.ai_color:
            self.root.after(500, self.ai_move)

    def ai_move(self):
        if not self.game_active:
            return
        move = self.ai.get_best_move(self.board, self.ai_color)
        if move:
            self.execute_move(move[0][0], move[0][1], move[1][0], move[1][1])
            self.draw_game()

    def undo_move(self):
        if not self.move_history:
            return

        for _ in range(2 if self.game_mode == 'pve' else 1):
            if not self.move_history:
                break
            record = self.move_history.pop()
            piece, target = record['piece'], record['target']
            self.board.grid[record['to'][0]][record['to'][1]] = target
            self.board.grid[record['from'][0]][record['from'][1]] = piece
            piece.row, piece.col = record['from']
            piece.is_flipped = record['was_flipped']
            if target:
                target.is_alive = True
                (self.board.captured_red if target.color == 'red' else self.board.captured_black).remove(target)
            self.current_player = 'black' if self.current_player == 'red' else 'red'

        self.selected_piece, self.valid_moves = None, []
        self.draw_game()

    def show_hint(self):
        """显示走棋提示"""
        for piece in self.board.pieces:
            if not piece.is_alive:
                continue

            # 检查是否是当前玩家可以操作的棋子
            if piece.is_flipped:
                # 已翻开的棋子：按颜色判断
                if piece.color != self.current_player:
                    continue
            else:
                # 未翻开的暗子：按位置判断归属
                if self.current_player == 'red' and piece.row > 4:
                    continue
                if self.current_player == 'black' and piece.row < 5:
                    continue

            # 获取有效移动
            moves = Rules.get_valid_moves(piece, self.board)
            if moves:
                self.selected_piece, self.valid_moves = piece, moves
                self.draw_game()
                return

    def resign(self):
        if self.game_mode == 'online':
            self.send_resign()
        winner = 'black' if self.current_player == 'red' else 'red'
        self.end_game(winner, "认输")

    def end_game(self, winner: str, reason: str = ""):
        self.game_active = False
        self.stop_timer()  # 停止计时器
        duration = int((datetime.now() - self.start_time).total_seconds()) if self.start_time else 0

        # 判断玩家胜负
        if self.game_mode == 'pve':
            # 人机对战：玩家执黑方，玩家先手
            result = '胜' if winner == self.player_color else '负'
        elif self.game_mode == 'online':
            # 网络对战：根据玩家颜色判断
            result = '胜' if winner == self.my_color else '负'
        else:
            # 双人对战：红方为玩家
            result = '胜' if winner == 'red' else '负'

        opponent = f"AI({self.ai_difficulty})" if self.game_mode == 'pve' else \
                   "网络对手" if self.game_mode == 'online' else "玩家"
        self.leaderboard.add(self.game_mode, result, opponent, duration)

        winner_text = "红方" if winner == 'red' else "黑方"
        messagebox.showinfo("游戏结束", f"{winner_text}胜利！\n{reason}")
        self.show_menu()

    def restart_game(self):
        self.stop_timer()
        self.start_game()

    def quit_game(self):
        self.network.close()
        self.root.quit()

    def run(self):
        self.root.mainloop()


# ==================== 主程序 ====================

if __name__ == '__main__':
    game = JieqiGame()
    game.run()