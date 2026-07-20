"""
规则验证模块
"""

import config
from typing import List, Tuple, Optional, Set


class Rules:
    """象棋规则类"""

    # 九宫格范围
    RED_PALACE = [(0, 3), (0, 4), (0, 5), (1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5)]
    BLACK_PALACE = [(7, 3), (7, 4), (7, 5), (8, 3), (8, 4), (8, 5), (9, 3), (9, 4), (9, 5)]

    @staticmethod
    def get_valid_moves(piece, board) -> List[Tuple[int, int]]:
        """
        获取棋子所有合法移动位置

        Args:
            piece: 棋子对象
            board: 棋盘对象

        Returns:
            合法位置列表 [(row, col), ...]
        """
        if not piece or not piece.is_alive:
            return []

        # 获取走法类型（盲棋用位置类型，明棋用真实类型）
        move_type = piece.position_type

        # 根据棋子类型获取可能移动位置
        if move_type == '帅':
            moves = Rules._get_king_moves(piece, board)
        elif move_type == '仕':
            moves = Rules._get_advisor_moves(piece, board)
        elif move_type == '相':
            moves = Rules._get_elephant_moves(piece, board)
        elif move_type == '车':
            moves = Rules._get_chariot_moves(piece, board)
        elif move_type == '马':
            moves = Rules._get_horse_moves(piece, board)
        elif move_type == '炮':
            moves = Rules._get_cannon_moves(piece, board)
        elif move_type == '兵':
            moves = Rules._get_soldier_moves(piece, board)
        else:
            moves = []

        # 过滤掉会导致己方帅将被吃的位置
        valid_moves = []
        for pos in moves:
            if Rules._is_safe_move(piece, pos, board):
                valid_moves.append(pos)

        return valid_moves

    @staticmethod
    def _get_king_moves(piece, board) -> List[Tuple[int, int]]:
        """获取将/帅的移动位置"""
        moves = []
        row, col = piece.row, piece.col

        # 九宫范围
        if piece.color == 'red':
            palace = Rules.RED_PALACE
        else:
            palace = Rules.BLACK_PALACE

        # 上下左右四个方向
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_row, new_col = row + dr, col + dc
            if (new_row, new_col) in palace:
                target = board.get_piece_at(new_row, new_col)
                if target is None or target.color != piece.color:
                    moves.append((new_row, new_col))

        return moves

    @staticmethod
    def _get_advisor_moves(piece, board) -> List[Tuple[int, int]]:
        """获取士的移动位置（揭棋中士可以过河）"""
        moves = []
        row, col = piece.row, piece.col

        # 斜走一格
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row <= 9 and 0 <= new_col <= 8:
                target = board.get_piece_at(new_row, new_col)
                if target is None or target.color != piece.color:
                    moves.append((new_row, new_col))

        return moves

    @staticmethod
    def _get_elephant_moves(piece, board) -> List[Tuple[int, int]]:
        """获取象的移动位置（揭棋中象可以过河）"""
        moves = []
        row, col = piece.row, piece.col

        # 走田字，检查象眼
        for dr, dc in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            new_row, new_col = row + dr, col + dc
            eye_row, eye_col = row + dr // 2, col + dc // 2

            # 检查是否在棋盘内
            if not (0 <= new_row <= 9 and 0 <= new_col <= 8):
                continue

            # 检查象眼是否被堵
            eye_piece = board.get_piece_at(eye_row, eye_col)
            if eye_piece is not None:
                continue

            # 检查目标位置
            target = board.get_piece_at(new_row, new_col)
            if target is None or target.color != piece.color:
                moves.append((new_row, new_col))

        return moves

    @staticmethod
    def _get_chariot_moves(piece, board) -> List[Tuple[int, int]]:
        """获取车的移动位置"""
        moves = []
        row, col = piece.row, piece.col

        # 四个方向直线移动
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_row, new_col = row + dr, col + dc
            while 0 <= new_row <= 9 and 0 <= new_col <= 8:
                target = board.get_piece_at(new_row, new_col)
                if target is None:
                    moves.append((new_row, new_col))
                elif target.color != piece.color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
                new_row += dr
                new_col += dc

        return moves

    @staticmethod
    def _get_horse_moves(piece, board) -> List[Tuple[int, int]]:
        """获取马的移动位置"""
        moves = []
        row, col = piece.row, piece.col

        # 八个方向，检查蹩马腿
        horse_moves = [
            (-2, -1, -1, 0),  # 上左
            (-2, 1, -1, 0),   # 上右
            (2, -1, 1, 0),    # 下左
            (2, 1, 1, 0),     # 下右
            (-1, -2, 0, -1),  # 左上
            (1, -2, 0, -1),   # 左下
            (-1, 2, 0, 1),    # 右上
            (1, 2, 0, 1),     # 右下
        ]

        for dr, dc, leg_r, leg_c in horse_moves:
            new_row, new_col = row + dr, col + dc
            leg_row, leg_col = row + leg_r, col + leg_c

            # 检查是否在棋盘内
            if not (0 <= new_row <= 9 and 0 <= new_col <= 8):
                continue

            # 检查蹩马腿
            leg_piece = board.get_piece_at(leg_row, leg_col)
            if leg_piece is not None:
                continue

            # 检查目标位置
            target = board.get_piece_at(new_row, new_col)
            if target is None or target.color != piece.color:
                moves.append((new_row, new_col))

        return moves

    @staticmethod
    def _get_cannon_moves(piece, board) -> List[Tuple[int, int]]:
        """获取炮的移动位置"""
        moves = []
        row, col = piece.row, piece.col

        # 四个方向
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_row, new_col = row + dr, col + dc
            found_piece = False

            while 0 <= new_row <= 9 and 0 <= new_col <= 8:
                target = board.get_piece_at(new_row, new_col)

                if not found_piece:
                    # 还没遇到炮架
                    if target is None:
                        # 可以移动到空位
                        moves.append((new_row, new_col))
                    else:
                        # 遇到棋子，作为炮架
                        found_piece = True
                else:
                    # 已经遇到炮架，只能吃子
                    if target is not None:
                        if target.color != piece.color:
                            moves.append((new_row, new_col))
                        break

                new_row += dr
                new_col += dc

        return moves

    @staticmethod
    def _get_soldier_moves(piece, board) -> List[Tuple[int, int]]:
        """获取兵/卒的移动位置"""
        moves = []
        row, col = piece.row, piece.col

        # 红兵向上走，黑卒向下走
        if piece.color == 'red':
            forward = -1
        else:
            forward = 1

        # 前进、左、右
        for dr, dc in [(forward, 0), (0, -1), (0, 1)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row <= 9 and 0 <= new_col <= 8:
                target = board.get_piece_at(new_row, new_col)
                if target is None or target.color != piece.color:
                    moves.append((new_row, new_col))

        return moves

    @staticmethod
    def _is_safe_move(piece, target_pos, board) -> bool:
        """
        检查移动是否安全（不会导致帅将被将军或照面）

        Args:
            piece: 移动的棋子
            target_pos: 目标位置
            board: 棋盘对象

        Returns:
            是否安全
        """
        # 模拟移动
        old_row, old_col = piece.row, piece.col
        target_piece = board.get_piece_at(*target_pos)

        # 临时更新位置
        piece.row, piece.col = target_pos
        if target_piece:
            target_piece.is_alive = False

        # 检查是否被将军
        in_check = Rules.is_in_check(piece.color, board)

        # 检查帅将是否照面
        kings_facing = Rules.is_kings_facing(board)

        # 恢复状态
        piece.row, piece.col = old_row, old_col
        if target_piece:
            target_piece.is_alive = True

        return not in_check and not kings_facing

    @staticmethod
    def is_in_check(color: str, board) -> bool:
        """
        检查指定方是否被将军

        Args:
            color: 阵营
            board: 棋盘对象

        Returns:
            是否被将军
        """
        # 找到己方帅/将位置
        king = board.get_king(color)
        if not king:
            return False

        king_pos = (king.row, king.col)

        # 检查对方所有已翻开的棋子是否能攻击到帅/将
        enemy_color = 'black' if color == 'red' else 'red'
        enemy_pieces = board.get_flipped_pieces(enemy_color)

        for piece in enemy_pieces:
            # 不考虑安全性，只看能否到达
            moves = Rules._get_raw_moves(piece, board)
            if king_pos in moves:
                return True

        return False

    @staticmethod
    def _get_raw_moves(piece, board) -> List[Tuple[int, int]]:
        """获取棋子的原始移动位置（不考虑安全性）"""
        move_type = piece._get_unified_type() if piece.is_flipped else piece.position_type

        if move_type == '帅':
            return Rules._get_king_moves(piece, board)
        elif move_type == '仕':
            return Rules._get_advisor_moves(piece, board)
        elif move_type == '相':
            return Rules._get_elephant_moves(piece, board)
        elif move_type == '车':
            return Rules._get_chariot_moves(piece, board)
        elif move_type == '马':
            return Rules._get_horse_moves(piece, board)
        elif move_type == '炮':
            return Rules._get_cannon_moves(piece, board)
        elif move_type == '兵':
            return Rules._get_soldier_moves(piece, board)
        return []

    @staticmethod
    def is_kings_facing(board) -> bool:
        """
        检查帅将是否照面（在同一列且中间无子）

        Args:
            board: 棋盘对象

        Returns:
            是否照面
        """
        red_king = board.get_king('red')
        black_king = board.get_king('black')

        if not red_king or not black_king:
            return False

        # 检查是否在同一列
        if red_king.col != black_king.col:
            return False

        # 检查中间是否有棋子
        col = red_king.col
        min_row = min(red_king.row, black_king.row)
        max_row = max(red_king.row, black_king.row)

        for row in range(min_row + 1, max_row):
            piece = board.get_piece_at(row, col)
            if piece is not None:
                return False

        return True

    @staticmethod
    def is_checkmate(color: str, board) -> bool:
        """
        检查是否被将死

        Args:
            color: 阵营
            board: 棋盘对象

        Returns:
            是否被将死
        """
        # 如果没有被将军，则不是将死
        if not Rules.is_in_check(color, board):
            return False

        # 检查是否有任何合法走法可以解救
        pieces = board.get_all_pieces(color)
        for piece in pieces:
            if piece.is_alive:
                valid_moves = Rules.get_valid_moves(piece, board)
                if valid_moves:
                    return False

        return True

    @staticmethod
    def is_stalemate(color: str, board) -> bool:
        """
        检查是否困毙（无子可走）

        Args:
            color: 阵营
            board: 棋盘对象

        Returns:
            是否困毙
        """
        pieces = board.get_all_pieces(color)
        for piece in pieces:
            if piece.is_alive:
                valid_moves = Rules.get_valid_moves(piece, board)
                if valid_moves:
                    return False
        return True