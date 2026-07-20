"""
棋子类模块
"""

import config


class Piece:
    """棋子类"""

    # 棋子类型列表
    RED_TYPES = ['帅', '仕', '相', '俥', '傌', '炮', '兵']
    BLACK_TYPES = ['将', '士', '象', '车', '马', '砲', '卒']

    def __init__(self, piece_type: str, color: str, row: int, col: int):
        """
        初始化棋子

        Args:
            piece_type: 棋子类型（帅/将/仕/士/等）
            color: 阵营（'red' 或 'black'）
            row: 行位置（0-9）
            col: 列位置（0-8）
        """
        self.piece_type = piece_type
        self.color = color
        self.row = row
        self.col = col
        self.is_flipped = False  # 是否已翻开
        self.is_alive = True     # 是否在棋盘上

    @property
    def position(self) -> tuple:
        """获取棋子位置"""
        return (self.row, self.col)

    @property
    def display_text(self) -> str:
        """
        获取显示文字
        未翻开时显示'?'，翻开后显示真实棋子名称
        """
        if self.is_flipped:
            return self.piece_type
        return '?'

    @property
    def position_type(self) -> str:
        """
        获取位置类型（用于盲棋走法）
        未翻开时按位置类型走法，翻开后按真实类型走法
        """
        if self.is_flipped:
            # 翻开后返回真实类型
            # 需要统一红黑方称呼
            return self._get_unified_type()
        else:
            # 未翻开时返回位置类型
            pos = (self.row, self.col)
            return config.POSITION_TYPES.get(pos, '兵')

    def _get_unified_type(self) -> str:
        """获取统一后的棋子类型（红黑方统一称呼）"""
        type_map = {
            '帅': '帅', '将': '帅',
            '仕': '仕', '士': '仕',
            '相': '相', '象': '相',
            '俥': '车', '车': '车',
            '傌': '马', '马': '马',
            '炮': '炮', '砲': '炮',
            '兵': '兵', '卒': '兵',
        }
        return type_map.get(self.piece_type, self.piece_type)

    def flip(self):
        """翻开棋子"""
        self.is_flipped = True

    def move_to(self, row: int, col: int):
        """移动棋子到新位置"""
        self.row = row
        self.col = col

    def capture(self):
        """棋子被吃"""
        self.is_alive = False
        self.row = -1
        self.col = -1

    def __repr__(self):
        status = '翻开' if self.is_flipped else '未翻开'
        return f"<{self.color}方 {self.piece_type} ({self.row},{self.col}) {status}>"


def create_all_pieces() -> list:
    """
    创建所有32枚棋子

    Returns:
        棋子列表
    """
    pieces = []

    # 红方棋子
    red_pieces = [
        ('帅', 1),
        ('仕', 2),
        ('相', 2),
        ('俥', 2),
        ('傌', 2),
        ('炮', 2),
        ('兵', 5),
    ]

    # 黑方棋子
    black_pieces = [
        ('将', 1),
        ('士', 2),
        ('象', 2),
        ('车', 2),
        ('马', 2),
        ('砲', 2),
        ('卒', 5),
    ]

    for piece_type, count in red_pieces:
        for _ in range(count):
            pieces.append(Piece(piece_type, 'red', -1, -1))

    for piece_type, count in black_pieces:
        for _ in range(count):
            pieces.append(Piece(piece_type, 'black', -1, -1))

    return pieces


def get_piece_value(piece_type: str) -> int:
    """
    获取棋子价值

    Args:
        piece_type: 棋子类型

    Returns:
        棋子价值
    """
    return config.PIECE_VALUES.get(piece_type, 100)