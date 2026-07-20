"""
渲染器模块 - 实木风格界面
"""

import pygame
import math
import config
from typing import List, Tuple, Optional


class Renderer:
    """游戏渲染器"""

    def __init__(self, screen: pygame.Surface):
        """
        初始化渲染器

        Args:
            screen: Pygame屏幕对象
        """
        self.screen = screen
        self.font_piece = None
        self.font_ui = None
        self.font_title = None
        self.font_small = None

        # 棋盘区域位置
        self.board_x = 100
        self.board_y = 50

        # 预加载字体
        self._init_fonts()

        # 创建实木纹理背景
        self.board_surface = self._create_board_surface()

    def _init_fonts(self):
        """初始化字体"""
        try:
            # 尝试使用系统中文字体
            font_names = ['SimHei', 'Microsoft YaHei', 'STHeiti', 'Arial Unicode MS', None]
            for font_name in font_names:
                try:
                    self.font_piece = pygame.font.SysFont(font_name, config.FONT_SIZE_PIECE, bold=True)
                    self.font_ui = pygame.font.SysFont(font_name, config.FONT_SIZE_UI)
                    self.font_title = pygame.font.SysFont(font_name, config.FONT_SIZE_TITLE, bold=True)
                    self.font_small = pygame.font.SysFont(font_name, 16)
                    break
                except:
                    continue
        except:
            # 使用默认字体
            self.font_piece = pygame.font.Font(None, config.FONT_SIZE_PIECE)
            self.font_ui = pygame.font.Font(None, config.FONT_SIZE_UI)
            self.font_title = pygame.font.Font(None, config.FONT_SIZE_TITLE)
            self.font_small = pygame.font.Font(None, 16)

    def _create_board_surface(self) -> pygame.Surface:
        """创建棋盘表面（带实木纹理）"""
        width = config.CELL_SIZE * 8 + config.BOARD_PADDING * 2
        height = config.CELL_SIZE * 9 + config.BOARD_PADDING * 2

        surface = pygame.Surface((width, height))

        # 实木色背景
        base_color = config.COLORS['board_bg']
        surface.fill(base_color)

        # 添加木纹效果
        for i in range(height):
            # 随机波动模拟木纹
            offset = (i % 3) - 1
            shade = 10 if (i + offset) % 5 == 0 else 0
            color = tuple(max(0, min(255, c + shade)) for c in base_color)
            pygame.draw.line(surface, color, (0, i), (width, i))

        return surface

    def draw_board(self):
        """绘制棋盘"""
        # 绘制棋盘背景
        self.screen.blit(self.board_surface, (self.board_x, self.board_y))

        # 棋盘尺寸
        board_width = config.CELL_SIZE * 8
        board_height = config.CELL_SIZE * 9

        # 绘制棋盘边框
        border_rect = pygame.Rect(
            self.board_x - 5,
            self.board_y - 5,
            board_width + config.BOARD_PADDING * 2 + 10,
            board_height + config.BOARD_PADDING * 2 + 10
        )
        pygame.draw.rect(self.screen, config.COLORS['board_border'], border_rect, 5)

        # 绘制棋盘线条
        line_color = config.COLORS['board_line']

        # 横线
        for row in range(10):
            y = self.board_y + config.BOARD_PADDING + row * config.CELL_SIZE
            start_x = self.board_x + config.BOARD_PADDING
            end_x = start_x + board_width
            pygame.draw.line(self.screen, line_color, (start_x, y), (end_x, y), 2)

        # 竖线
        for col in range(9):
            x = self.board_x + config.BOARD_PADDING + col * config.CELL_SIZE
            start_y = self.board_y + config.BOARD_PADDING
            end_y = start_y + board_height

            # 楚河汉界处断开
            if col == 0 or col == 8:
                pygame.draw.line(self.screen, line_color, (x, start_y), (x, end_y), 2)
            else:
                pygame.draw.line(self.screen, line_color, (x, start_y), (x, start_y + 4 * config.CELL_SIZE), 2)
                pygame.draw.line(self.screen, line_color, (x, start_y + 5 * config.CELL_SIZE), (x, end_y), 2)

        # 绘制九宫格斜线
        palace_color = line_color

        # 红方九宫
        pygame.draw.line(self.screen, palace_color,
                         self._get_screen_pos(0, 3), self._get_screen_pos(2, 5), 2)
        pygame.draw.line(self.screen, palace_color,
                         self._get_screen_pos(0, 5), self._get_screen_pos(2, 3), 2)

        # 黑方九宫
        pygame.draw.line(self.screen, palace_color,
                         self._get_screen_pos(7, 3), self._get_screen_pos(9, 5), 2)
        pygame.draw.line(self.screen, palace_color,
                         self._get_screen_pos(7, 5), self._get_screen_pos(9, 3), 2)

        # 绘制楚河汉界文字
        river_y = self.board_y + config.BOARD_PADDING + 4.5 * config.CELL_SIZE

        # 楚河
        chuhe_text = self.font_ui.render("楚 河", True, line_color)
        chuhe_rect = chuhe_text.get_rect(center=(self.board_x + config.BOARD_PADDING + board_width // 4, river_y))
        self.screen.blit(chuhe_text, chuhe_rect)

        # 汉界
        hanjie_text = self.font_ui.render("汉 界", True, line_color)
        hanjie_rect = hanjie_text.get_rect(center=(self.board_x + config.BOARD_PADDING + 3 * board_width // 4, river_y))
        self.screen.blit(hanjie_text, hanjie_rect)

    def draw_pieces(self, board, selected_piece=None, valid_moves=None):
        """
        绘制所有棋子

        Args:
            board: 棋盘对象
            selected_piece: 选中的棋子
            valid_moves: 合法移动位置列表
        """
        for piece in board.pieces:
            if piece.is_alive:
                self.draw_piece(piece, piece == selected_piece)

        # 绘制合法移动位置高亮
        if valid_moves:
            for pos in valid_moves:
                self.draw_move_hint(pos, board)

    def draw_piece(self, piece, is_selected: bool = False):
        """
        绘制单个棋子

        Args:
            piece: 棋子对象
            is_selected: 是否被选中
        """
        screen_x, screen_y = self._get_screen_pos(piece.row, piece.col)

        # 棋子颜色
        if piece.is_flipped:
            if piece.color == 'red':
                bg_color = config.COLORS['piece_red_bg']
                text_color = config.COLORS['text_red']
            else:
                bg_color = config.COLORS['piece_black_bg']
                text_color = config.COLORS['text_black']
        else:
            bg_color = config.COLORS['piece_hidden_bg']
            text_color = config.COLORS['piece_hidden']

        # 绘制棋子背景（圆形）
        radius = config.PIECE_RADIUS

        # 选中效果
        if is_selected:
            pygame.draw.circle(self.screen, config.COLORS['highlight_selected'],
                               (screen_x, screen_y), radius + 5)

        # 棋子底色（带立体效果）
        pygame.draw.circle(self.screen, (139, 90, 43), (screen_x + 2, screen_y + 2), radius)  # 阴影
        pygame.draw.circle(self.screen, bg_color, (screen_x, screen_y), radius)  # 主体

        # 绘制棋子边框
        pygame.draw.circle(self.screen, (101, 67, 33), (screen_x, screen_y), radius, 2)

        # 绘制棋子文字
        text = piece.display_text
        text_surface = self.font_piece.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(screen_x, screen_y))
        self.screen.blit(text_surface, text_rect)

    def draw_move_hint(self, pos: Tuple[int, int], board):
        """
        绘制移动提示

        Args:
            pos: 位置
            board: 棋盘对象
        """
        screen_x, screen_y = self._get_screen_pos(pos[0], pos[1])

        # 检查目标位置是否有棋子（吃子提示）
        target = board.get_piece_at(pos[0], pos[1])

        if target:
            # 吃子提示 - 红色高亮
            pygame.draw.circle(self.screen, (255, 0, 0, 150), (screen_x, screen_y), config.PIECE_RADIUS + 3, 3)
        else:
            # 移动提示 - 绿色小点
            pygame.draw.circle(self.screen, (0, 200, 0), (screen_x, screen_y), 8)

    def draw_captured_pieces(self, board, start_x: int, start_y: int):
        """
        绘制被吃棋子区域

        Args:
            board: 棋盘对象
            start_x: 起始X
            start_y: 起始Y
        """
        # 绘制标题
        title = self.font_small.render("已吃棋子", True, config.COLORS['ui_text'])
        self.screen.blit(title, (start_x, start_y))

        # 黑方被吃棋子
        black_y = start_y + 25
        black_title = self.font_small.render("黑:", True, config.COLORS['text_black'])
        self.screen.blit(black_title, (start_x, black_y))

        for i, piece in enumerate(board.captured_black[:8]):
            x = start_x + 30 + i * 30
            text = self.font_small.render(piece.piece_type, True, config.COLORS['text_black'])
            self.screen.blit(text, (x, black_y))

        # 红方被吃棋子
        red_y = black_y + 20
        red_title = self.font_small.render("红:", True, config.COLORS['text_red'])
        self.screen.blit(red_title, (start_x, red_y))

        for i, piece in enumerate(board.captured_red[:8]):
            x = start_x + 30 + i * 30
            text = self.font_small.render(piece.piece_type, True, config.COLORS['text_red'])
            self.screen.blit(text, (x, red_y))

    def draw_timer(self, game_manager):
        """
        绘制计时器

        Args:
            game_manager: 游戏管理器
        """
        if not game_manager.timer_enabled:
            return

        # 计时器位置
        timer_x = self.board_x + config.CELL_SIZE * 8 + config.BOARD_PADDING * 2 + 50
        timer_y = self.board_y + 200

        # 黑方时间
        black_time = game_manager.get_current_time('black')
        black_minutes = int(black_time // 60)
        black_seconds = int(black_time % 60)
        black_text = f"黑方: {black_minutes:02d}:{black_seconds:02d}"
        black_color = (255, 0, 0) if black_time < 30 else config.COLORS['text_black']
        black_surface = self.font_ui.render(black_text, True, black_color)
        self.screen.blit(black_surface, (timer_x, timer_y))

        # 红方时间
        red_time = game_manager.get_current_time('red')
        red_minutes = int(red_time // 60)
        red_seconds = int(red_time % 60)
        red_text = f"红方: {red_minutes:02d}:{red_seconds:02d}"
        red_color = (255, 0, 0) if red_time < 30 else config.COLORS['text_red']
        red_surface = self.font_ui.render(red_text, True, red_color)
        self.screen.blit(red_surface, (timer_x, timer_y + 30))

    def draw_message(self, message: str, duration: float = 2.0):
        """
        绘制提示消息

        Args:
            message: 消息内容
            duration: 显示时长
        """
        # 消息背景
        text_surface = self.font_ui.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(config.WINDOW_WIDTH // 2, 30))

        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (50, 50, 50), bg_rect, border_radius=5)
        self.screen.blit(text_surface, text_rect)

    def draw_turn_indicator(self, current_player: str):
        """绘制回合指示"""
        text = "红方回合" if current_player == 'red' else "黑方回合"
        color = config.COLORS['text_red'] if current_player == 'red' else config.COLORS['text_black']

        text_surface = self.font_ui.render(text, True, color)
        text_rect = text_surface.get_rect(center=(config.WINDOW_WIDTH // 2, 15))
        self.screen.blit(text_surface, text_rect)

    def _get_screen_pos(self, row: int, col: int) -> Tuple[int, int]:
        """
        将棋盘坐标转换为屏幕坐标

        Args:
            row: 行
            col: 列

        Returns:
            (屏幕x, 屏幕y)
        """
        x = self.board_x + config.BOARD_PADDING + col * config.CELL_SIZE
        y = self.board_y + config.BOARD_PADDING + row * config.CELL_SIZE
        return (x, y)

    def get_board_pos(self, screen_x: int, screen_y: int) -> Optional[Tuple[int, int]]:
        """
        将屏幕坐标转换为棋盘坐标

        Args:
            screen_x: 屏幕x
            screen_y: 屏幕y

        Returns:
            (行, 列) 或 None
        """
        col = round((screen_x - self.board_x - config.BOARD_PADDING) / config.CELL_SIZE)
        row = round((screen_y - self.board_y - config.BOARD_PADDING) / config.CELL_SIZE)

        if 0 <= row <= 9 and 0 <= col <= 8:
            return (row, col)
        return None