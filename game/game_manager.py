"""
游戏管理器模块
"""

import time
from enum import Enum
from typing import Optional, List, Tuple
from .board import Board
from .piece import Piece
from .rules import Rules
import config


class GameState(Enum):
    """游戏状态"""
    MENU = 'menu'
    PLAYING = 'playing'
    PAUSED = 'paused'
    GAME_OVER = 'game_over'


class GameResult(Enum):
    """游戏结果"""
    RED_WIN = 'red_win'
    BLACK_WIN = 'black_win'
    DRAW = 'draw'


class MoveRecord:
    """走棋记录"""

    def __init__(self, piece: Piece, from_pos: Tuple[int, int], to_pos: Tuple[int, int],
                 captured: Optional[Piece] = None, was_flipped: bool = False):
        self.piece = piece
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.captured = captured
        self.was_flipped = was_flipped  # 移动前是否已翻开
        self.timestamp = time.time()


class GameManager:
    """游戏管理器"""

    def __init__(self):
        """初始化游戏管理器"""
        self.board = Board()
        self.state = GameState.MENU
        self.current_player = 'red'  # 当前回合
        self.game_mode = config.MODE_PVP  # 游戏模式
        self.ai_difficulty = config.AI_MEDIUM  # AI难度

        # 计时器
        self.timer_enabled = False
        self.timer_duration = 0  # 每方时间限制（秒）
        self.red_time = 0  # 红方剩余时间
        self.black_time = 0  # 黑方剩余时间
        self.last_move_time = 0  # 上次走棋时间

        # 走棋记录
        self.move_history: List[MoveRecord] = []

        # 选中的棋子
        self.selected_piece: Optional[Piece] = None
        self.valid_moves: List[Tuple[int, int]] = []

        # 游戏结果
        self.result: Optional[GameResult] = None
        self.winner: Optional[str] = None

        # 提示信息
        self.message = ""
        self.message_time = 0

    def start_game(self, mode: str = config.MODE_PVP, timer_duration: int = 0):
        """
        开始新游戏

        Args:
            mode: 游戏模式
            timer_duration: 计时器时长（秒），0表示无限制
        """
        self.board.setup()
        self.state = GameState.PLAYING
        self.current_player = 'red'
        self.game_mode = mode
        self.move_history = []
        self.selected_piece = None
        self.valid_moves = []
        self.result = None
        self.winner = None

        # 设置计时器
        self.timer_enabled = timer_duration > 0
        self.timer_duration = timer_duration
        self.red_time = timer_duration
        self.black_time = timer_duration
        self.last_move_time = time.time()

        self.show_message("红方先行")

    def select_piece(self, row: int, col: int) -> bool:
        """
        选择棋子

        Args:
            row: 行
            col: 列

        Returns:
            是否成功选中
        """
        piece = self.board.get_piece_at(row, col)
        if not piece:
            return False

        # 只能选择己方棋子（已翻开的）或己方未翻开的棋子
        if piece.is_flipped:
            if piece.color != self.current_player:
                return False

        self.selected_piece = piece
        self.valid_moves = Rules.get_valid_moves(piece, self.board)
        return True

    def make_move(self, to_row: int, to_col: int) -> bool:
        """
        执行走棋

        Args:
            to_row: 目标行
            to_col: 目标列

        Returns:
            是否成功
        """
        if not self.selected_piece:
            return False

        from_pos = (self.selected_piece.row, self.selected_piece.col)
        to_pos = (to_row, to_col)

        # 检查是否是合法移动
        if to_pos not in self.valid_moves:
            return False

        # 记录移动前的状态
        was_flipped = self.selected_piece.is_flipped
        captured = self.board.get_piece_at(to_row, to_col)

        # 执行移动
        success, captured_piece = self.board.move_piece(from_pos, to_pos)
        if not success:
            return False

        # 记录走棋历史
        record = MoveRecord(self.selected_piece, from_pos, to_pos, captured_piece, was_flipped)
        self.move_history.append(record)

        # 更新计时器
        if self.timer_enabled:
            current_time = time.time()
            elapsed = current_time - self.last_move_time
            if self.current_player == 'red':
                self.red_time -= elapsed
            else:
                self.black_time -= elapsed
            self.last_move_time = current_time

        # 清除选择
        self.selected_piece = None
        self.valid_moves = []

        # 检查将军
        enemy_color = 'black' if self.current_player == 'red' else 'red'
        if Rules.is_in_check(enemy_color, self.board):
            self.show_message("将军！")

        # 检查胜负
        if self.check_game_over():
            return True

        # 切换回合
        self.switch_turn()
        return True

    def flip_piece(self, row: int, col: int) -> bool:
        """
        翻开棋子（作为一步棋）

        Args:
            row: 行
            col: 列

        Returns:
            是否成功
        """
        piece = self.board.get_piece_at(row, col)
        if not piece or piece.is_flipped:
            return False

        # 检查是否是己方棋子（盲棋只能翻己方的）
        # 实际上揭棋规则是走盲棋时自动翻开，这里作为单独操作
        piece.flip()

        # 更新计时器
        if self.timer_enabled:
            current_time = time.time()
            elapsed = current_time - self.last_move_time
            if self.current_player == 'red':
                self.red_time -= elapsed
            else:
                self.black_time -= elapsed
            self.last_move_time = current_time

        # 切换回合
        self.switch_turn()
        return True

    def switch_turn(self):
        """切换回合"""
        self.current_player = 'black' if self.current_player == 'red' else 'red'

        # 显示回合提示
        if self.current_player == 'red':
            self.show_message("红方回合")
        else:
            self.show_message("黑方回合")

    def check_game_over(self) -> bool:
        """
        检查游戏是否结束

        Returns:
            游戏是否结束
        """
        # 检查计时器
        if self.timer_enabled:
            if self.red_time <= 0:
                self.end_game('black', "红方超时")
                return True
            if self.black_time <= 0:
                self.end_game('red', "黑方超时")
                return True

        # 检查将死
        enemy_color = 'black' if self.current_player == 'red' else 'red'
        if Rules.is_checkmate(enemy_color, self.board):
            self.end_game(self.current_player, "将死")
            return True

        # 检查困毙
        if Rules.is_stalemate(enemy_color, self.board):
            self.end_game(self.current_player, "困毙")
            return True

        # 检查帅将照面（走棋方导致照面判负）
        if Rules.is_kings_facing(self.board):
            self.end_game(enemy_color, "帅将照面")
            return True

        return False

    def end_game(self, winner: str, reason: str = ""):
        """
        结束游戏

        Args:
            winner: 获胜方
            reason: 获胜原因
        """
        self.state = GameState.GAME_OVER
        self.winner = winner
        if winner == 'red':
            self.result = GameResult.RED_WIN
        else:
            self.result = GameResult.BLACK_WIN

        self.show_message(f"{winner}方胜利！{reason}")

    def resign(self, color: str):
        """
        认输

        Args:
            color: 认输方
        """
        winner = 'black' if color == 'red' else 'red'
        self.end_game(winner, "对方认输")

    def undo_move(self) -> bool:
        """
        悔棋

        Returns:
            是否成功
        """
        if not self.move_history:
            return False

        # 取出最后一步
        record = self.move_history.pop()

        # 恢复棋子位置
        piece = record.piece
        to_row, to_col = record.to_pos

        # 移回原位
        self.board.grid[to_row][to_col] = None
        self.board.grid[record.from_pos[0]][record.from_pos[1]] = piece
        piece.row, piece.col = record.from_pos

        # 恢复翻开状态
        piece.is_flipped = record.was_flipped

        # 恢复被吃的棋子
        if record.captured:
            record.captured.is_alive = True
            record.captured.row, record.captured.col = to_row, to_col
            self.board.grid[to_row][to_col] = record.captured

            # 从被吃列表中移除
            if record.captured.color == 'red':
                self.board.captured_red.remove(record.captured)
            else:
                self.board.captured_black.remove(record.captured)

        # 切换回上家回合
        self.current_player = 'black' if self.current_player == 'red' else 'red'

        # 清除选择
        self.selected_piece = None
        self.valid_moves = []

        self.show_message("悔棋成功")
        return True

    def get_hint(self) -> List[Tuple[Piece, Tuple[int, int]]]:
        """
        获取走棋提示

        Returns:
            推荐的走法列表 [(棋子, 目标位置), ...]
        """
        hints = []
        pieces = self.board.get_flipped_pieces(self.current_player)

        for piece in pieces:
            moves = Rules.get_valid_moves(piece, self.board)
            if moves:
                # 简单评估：优先推荐能吃子的走法
                for move in moves:
                    target = self.board.get_piece_at(*move)
                    if target:
                        hints.append((piece, move))

        return hints[:3]  # 返回最多3个提示

    def show_message(self, message: str):
        """显示提示信息"""
        self.message = message
        self.message_time = time.time()

    def update_timer(self):
        """更新计时器"""
        if not self.timer_enabled or self.state != GameState.PLAYING:
            return

        current_time = time.time()
        elapsed = current_time - self.last_move_time

        if self.current_player == 'red':
            self.red_time = max(0, self.timer_duration - elapsed - (self.timer_duration - self.red_time))
            if self.red_time <= 0:
                self.end_game('black', "红方超时")
        else:
            self.black_time = max(0, self.timer_duration - elapsed - (self.timer_duration - self.black_time))
            if self.black_time <= 0:
                self.end_game('red', "黑方超时")

    def get_current_time(self, color: str) -> float:
        """获取指定方剩余时间"""
        if color == 'red':
            return self.red_time
        return self.black_time