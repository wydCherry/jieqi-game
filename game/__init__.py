"""
游戏模块初始化
"""

from .board import Board
from .piece import Piece, create_all_pieces
from .rules import Rules
from .game_manager import GameManager, GameState, GameResult
from .ai import ChessAI

__all__ = [
    'Board',
    'Piece',
    'create_all_pieces',
    'Rules',
    'GameManager',
    'GameState',
    'GameResult',
    'ChessAI',
]