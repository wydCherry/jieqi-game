"""
棋盘类模块
"""

import random
import config
from .piece import Piece, create_all_pieces
from .rules import Rules
from typing import List, Optional, Tuple


class Board:
    """棋盘类"""

    def __init__(self):
        """初始化棋盘"""
        self.grid = [[None for _ in range(9)] for _ in range(10)]
        self.pieces = []  # 所有棋子列表
        self.captured_red = []  # 被吃红方棋子
        self.captured_black = []  # 被吃黑方棋子

    def setup(self):
        """
        初始化摆棋
        将所有棋子洗混后反扣放置在各自半场的原始位置
        """
        # 创建所有棋子
        self.pieces = create_all_pieces()
        self.captured_red = []
        self.captured_black = []
        self.grid = [[None for _ in range(9)] for _ in range(10)]

        # 分离红黑方棋子
        red_pieces = [p for p in self.pieces if p.color == 'red']
        black_pieces = [p for p in self.pieces if p.color == 'black']

        # 红方位置（第0、2、3行）
        red_positions = [
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8),
            (2, 1), (2, 7),
            (3, 0), (3, 2), (3, 4), (3, 6), (3, 8),
        ]

        # 黑方位置（第6、7、9行）
        black_positions = [
            (6, 0), (6, 2), (6, 4), (6, 6), (6, 8),
            (7, 1), (7, 7),
            (9, 0), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6), (9, 7), (9, 8),
        ]

        # 将帅固定在正常位置（明棋）
        # 红帅固定在 (0, 4)，黑将固定在 (9, 4)
        red_king = None
        black_king = None
        for p in red_pieces:
            if p.piece_type == '帅':
                red_king = p
                break
        for p in black_pieces:
            if p.piece_type == '将':
                black_king = p
                break

        # 将帅放到固定位置并翻开
        red_king.row, red_king.col = 0, 4
        red_king.is_flipped = True
        self.grid[0][4] = red_king
        red_pieces.remove(red_king)
        red_positions.remove((0, 4))

        black_king.row, black_king.col = 9, 4
        black_king.is_flipped = True
        self.grid[9][4] = black_king
        black_pieces.remove(black_king)
        black_positions.remove((9, 4))

        # 随机洗混其他棋子
        random.shuffle(red_pieces)
        random.shuffle(black_pieces)

        # 放置红方棋子（反扣）
        for piece, (row, col) in zip(red_pieces, red_positions):
            piece.row, piece.col = row, col
            piece.is_flipped = False
            self.grid[row][col] = piece

        # 放置黑方棋子（反扣）
        for piece, (row, col) in zip(black_pieces, black_positions):
            piece.row, piece.col = row, col
            piece.is_flipped = False
            self.grid[row][col] = piece

    def get_piece_at(self, row: int, col: int) -> Optional[Piece]:
        """获取指定位置的棋子"""
        if 0 <= row <= 9 and 0 <= col <= 8:
            return self.grid[row][col]
        return None

    def flip_piece(self, row: int, col: int) -> Optional[Piece]:
        """
        翻开指定位置的棋子

        Args:
            row: 行
            col: 列

        Returns:
            翻开的棋子，如果位置无棋子或已翻开则返回None
        """
        piece = self.get_piece_at(row, col)
        if piece and not piece.is_flipped:
            piece.flip()
            return piece
        return None

    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Tuple[bool, Optional[Piece]]:
        """
        移动棋子

        Args:
            from_pos: 起始位置
            to_pos: 目标位置

        Returns:
            (是否成功, 被吃的棋子)
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        piece = self.get_piece_at(from_row, from_col)
        if not piece:
            return False, None

        target = self.get_piece_at(to_row, to_col)

        # 如果移动到有棋子的位置，吃子
        captured = None
        if target:
            target.capture()
            captured = target
            if target.color == 'red':
                self.captured_red.append(target)
            else:
                self.captured_black.append(target)

        # 移动棋子
        self.grid[from_row][from_col] = None
        self.grid[to_row][to_col] = piece
        piece.move_to(to_row, to_col)

        # 如果棋子未翻开，翻开它
        if not piece.is_flipped:
            piece.flip()

        return True, captured

    def get_all_pieces(self, color: str = None) -> List[Piece]:
        """
        获取所有棋子（或指定颜色的棋子）

        Args:
            color: 阵营，None表示获取所有

        Returns:
            棋子列表
        """
        if color:
            return [p for p in self.pieces if p.color == color and p.is_alive]
        return [p for p in self.pieces if p.is_alive]

    def get_flipped_pieces(self, color: str = None) -> List[Piece]:
        """
        获取所有已翻开的棋子

        Args:
            color: 阵营，None表示获取所有

        Returns:
            已翻开的棋子列表
        """
        if color:
            return [p for p in self.pieces if p.color == color and p.is_flipped and p.is_alive]
        return [p for p in self.pieces if p.is_flipped and p.is_alive]

    def get_unflipped_pieces(self, color: str = None) -> List[Piece]:
        """
        获取所有未翻开的棋子

        Args:
            color: 阵营，None表示获取所有

        Returns:
            未翻开的棋子列表
        """
        if color:
            return [p for p in self.pieces if p.color == color and not p.is_flipped and p.is_alive]
        return [p for p in self.pieces if not p.is_flipped and p.is_alive]

    def get_king(self, color: str) -> Optional[Piece]:
        """获取指定方的帅/将"""
        for p in self.pieces:
            if p.color == color and p.piece_type in ['帅', '将'] and p.is_alive:
                return p
        return None

    def copy(self) -> 'Board':
        """创建棋盘的深拷贝（用于AI搜索）"""
        new_board = Board()
        new_board.grid = [[None for _ in range(9)] for _ in range(10)]
        new_board.pieces = []
        new_board.captured_red = []
        new_board.captured_black = []

        # 复制棋子
        for p in self.pieces:
            new_piece = Piece(p.piece_type, p.color, p.row, p.col)
            new_piece.is_flipped = p.is_flipped
            new_piece.is_alive = p.is_alive
            new_board.pieces.append(new_piece)

            if p.is_alive:
                new_board.grid[p.row][p.col] = new_piece

        # 复制被吃棋子
        for p in self.captured_red:
            new_board.captured_red.append(new_board.pieces[self.pieces.index(p)])
        for p in self.captured_black:
            new_board.captured_black.append(new_board.pieces[self.pieces.index(p)])

        return new_board