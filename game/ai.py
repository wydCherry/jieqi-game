"""
AI模块 - 人机对战逻辑
"""

import random
import time
from typing import List, Tuple, Optional
from .board import Board
from .piece import Piece, get_piece_value
from .rules import Rules
from .game_manager import GameManager
import config


class ChessAI:
    """象棋AI"""

    def __init__(self, difficulty: str = config.AI_MEDIUM):
        """
        初始化AI

        Args:
            difficulty: 难度等级 (easy/medium/hard)
        """
        self.difficulty = difficulty
        self.color = 'black'  # AI默认执黑

        # 根据难度设置搜索深度
        self.search_depth = {
            config.AI_EASY: 1,
            config.AI_MEDIUM: 3,
            config.AI_HARD: 5,
        }.get(difficulty, 3)

    def get_best_move(self, board: Board, color: str = 'black') -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        获取最佳走法

        Args:
            board: 棋盘对象
            color: AI阵营

        Returns:
            (起始位置, 目标位置) 或 None
        """
        self.color = color

        # 简单难度：随机走法
        if self.difficulty == config.AI_EASY:
            return self._random_move(board, color)

        # 中等和困难难度：使用Minimax + Alpha-Beta
        best_move = None
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        # 获取所有可能的走法
        moves = self._get_all_moves(board, color)

        if not moves:
            return None

        # 随机打乱顺序，增加变化
        random.shuffle(moves)

        for move in moves:
            # 模拟走棋
            new_board = self._simulate_move(board, move)
            if new_board is None:
                continue

            # 递归搜索
            score = self._minimax(new_board, self.search_depth - 1, alpha, beta, False)

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        return best_move

    def _random_move(self, board: Board, color: str) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """随机走法（简单难度）"""
        moves = self._get_all_moves(board, color)
        if moves:
            return random.choice(moves)
        return None

    def _get_all_moves(self, board: Board, color: str) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """获取所有可能的走法"""
        moves = []
        pieces = board.get_flipped_pieces(color)

        for piece in pieces:
            valid_moves = Rules.get_valid_moves(piece, board)
            for target in valid_moves:
                moves.append(((piece.row, piece.col), target))

        return moves

    def _simulate_move(self, board: Board, move: Tuple[Tuple[int, int], Tuple[int, int]]) -> Optional[Board]:
        """
        模拟走棋，返回新棋盘状态

        Args:
            board: 原棋盘
            move: 走法

        Returns:
            新棋盘状态
        """
        from_pos, to_pos = move
        new_board = board.copy()

        from_piece = new_board.get_piece_at(*from_pos)
        if not from_piece:
            return None

        # 执行移动
        new_board.move_piece(from_pos, to_pos)
        return new_board

    def _minimax(self, board: Board, depth: int, alpha: float, beta: float, is_maximizing: bool) -> float:
        """
        Minimax算法 + Alpha-Beta剪枝

        Args:
            board: 棋盘状态
            depth: 搜索深度
            alpha: Alpha值
            beta: Beta值
            is_maximizing: 是否是最大化玩家

        Returns:
            局面评分
        """
        # 到达搜索深度或游戏结束
        if depth == 0:
            return self._evaluate_board(board)

        # 检查游戏结束
        if Rules.is_checkmate(self.color, board):
            return float('-inf')
        if Rules.is_checkmate('red' if self.color == 'black' else 'black', board):
            return float('inf')

        current_color = self.color if is_maximizing else ('red' if self.color == 'black' else 'black')
        moves = self._get_all_moves(board, current_color)

        if not moves:
            # 无子可走
            return float('-inf') if is_maximizing else float('inf')

        if is_maximizing:
            max_eval = float('-inf')
            for move in moves:
                new_board = self._simulate_move(board, move)
                if new_board:
                    eval_score = self._minimax(new_board, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break  # Beta剪枝
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = self._simulate_move(board, move)
                if new_board:
                    eval_score = self._minimax(new_board, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break  # Alpha剪枝
            return min_eval

    def _evaluate_board(self, board: Board) -> float:
        """
        局面评估函数

        Args:
            board: 棋盘状态

        Returns:
            局面评分（正数对AI有利）
        """
        score = 0.0

        # 1. 棋子价值
        for piece in board.pieces:
            if not piece.is_alive:
                continue

            value = get_piece_value(piece.piece_type)

            # 只计算已翻开的棋子，未翻开的给予较低期望值
            if piece.is_flipped:
                if piece.color == self.color:
                    score += value
                else:
                    score -= value
            else:
                # 未翻开棋子期望值
                expected_value = 200  # 平均期望值
                if piece.color == self.color:
                    score += expected_value * 0.5
                else:
                    score -= expected_value * 0.5

        # 2. 位置价值（控制中心更好）
        for piece in board.get_flipped_pieces(self.color):
            # 中心位置加成
            center_bonus = self._get_position_bonus(piece.row, piece.col)
            score += center_bonus

        # 3. 机动性（可走步数）
        ai_moves = len(self._get_all_moves(board, self.color))
        enemy_moves = len(self._get_all_moves(board, 'red' if self.color == 'black' else 'black'))
        score += (ai_moves - enemy_moves) * 5

        # 4. 安全性（帅/将是否被将军）
        if Rules.is_in_check(self.color, board):
            score -= 500
        enemy_color = 'red' if self.color == 'black' else 'black'
        if Rules.is_in_check(enemy_color, board):
            score += 300

        return score

    def _get_position_bonus(self, row: int, col: int) -> float:
        """
        获取位置加成

        Args:
            row: 行
            col: 列

        Returns:
            位置加成值
        """
        # 中心区域更有价值
        center_col = abs(col - 4)
        center_row = abs(row - 4.5)
        bonus = max(0, 10 - center_col * 2 - center_row)

        # 过河加成
        if self.color == 'black' and row < 5:
            bonus += 5
        elif self.color == 'red' and row > 4:
            bonus += 5

        return bonus

    def _get_piece_position_bonus(self, piece: Piece) -> float:
        """获取棋子位置加成（根据棋子类型）"""
        bonus = 0
        row, col = piece.row, piece.col

        piece_type = piece._get_unified_type() if piece.is_flipped else piece.position_type

        # 车炮占据肋道有利
        if piece_type in ['车', '炮']:
            if col == 1 or col == 7:
                bonus += 10

        # 马占据中心有利
        elif piece_type == '马':
            if 2 <= col <= 6:
                bonus += 5

        # 兵卒过河加分
        elif piece_type == '兵':
            if piece.color == 'red' and row > 4:
                bonus += 20
            elif piece.color == 'black' and row < 5:
                bonus += 20

        return bonus