"""
界面模块 - 游戏各界面
"""

import pygame
import sys
import config
from typing import Optional, Callable, List, Tuple


class Button:
    """按钮类"""

    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 callback: Optional[Callable] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False

    def draw(self, screen, font):
        """绘制按钮"""
        color = config.COLORS['ui_button_hover'] if self.hovered else config.COLORS['ui_button']
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, config.COLORS['board_border'], self.rect, 2, border_radius=10)

        text_surface = font.render(self.text, True, config.COLORS['ui_text'])
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event) -> bool:
        """处理事件"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and self.callback:
                self.callback()
                return True
        return False


class MenuScreen:
    """主菜单界面"""

    def __init__(self, screen, renderer):
        self.screen = screen
        self.renderer = renderer
        self.selected_mode = None
        self.selected_difficulty = config.AI_MEDIUM
        self.selected_timer = 0
        self.font = renderer.font_ui
        self.font_title = renderer.font_title

        # 创建按钮
        self._create_buttons()

    def _create_buttons(self):
        """创建菜单按钮"""
        center_x = config.WINDOW_WIDTH // 2

        self.buttons = {
            'pvp': Button(center_x - 100, 250, 200, 50, "双人对战", lambda: self._select_mode(config.MODE_PVP)),
            'pve': Button(center_x - 100, 320, 200, 50, "人机对战", lambda: self._select_mode(config.MODE_PVE)),
            'online': Button(center_x - 100, 390, 200, 50, "网络对战", lambda: self._select_mode(config.MODE_ONLINE)),
            'rules': Button(center_x - 100, 460, 200, 50, "游戏规则", self._show_rules),
            'quit': Button(center_x - 100, 530, 200, 50, "退出游戏", self._quit_game),
        }

        # 难度选择按钮（人机模式）
        self.difficulty_buttons = {
            'easy': Button(center_x - 150, 400, 80, 40, "简单", lambda: self._select_difficulty(config.AI_EASY)),
            'medium': Button(center_x - 40, 400, 80, 40, "中等", lambda: self._select_difficulty(config.AI_MEDIUM)),
            'hard': Button(center_x + 70, 400, 80, 40, "困难", lambda: self._select_difficulty(config.AI_HARD)),
        }

        # 计时器选择按钮
        self.timer_buttons = {
            '0': Button(center_x - 200, 500, 80, 40, "无限制", lambda: self._select_timer(0)),
            '300': Button(center_x - 100, 500, 80, 40, "5分钟", lambda: self._select_timer(300)),
            '600': Button(center_x, 500, 80, 40, "10分钟", lambda: self._select_timer(600)),
            '900': Button(center_x + 100, 500, 80, 40, "15分钟", lambda: self._select_timer(900)),
        }

        # 开始游戏按钮
        self.start_button = Button(center_x - 100, 600, 200, 50, "开始游戏", self._start_game)

    def _select_mode(self, mode):
        """选择游戏模式"""
        self.selected_mode = mode

    def _select_difficulty(self, difficulty):
        """选择AI难度"""
        self.selected_difficulty = difficulty

    def _select_timer(self, duration):
        """选择计时器时长"""
        self.selected_timer = duration

    def _show_rules(self):
        """显示游戏规则（暂用打印）"""
        print("游戏规则：揭棋是象棋变体，棋子反扣随机放置，翻开后按象棋规则走棋。")

    def _quit_game(self):
        """退出游戏"""
        pygame.quit()
        sys.exit()

    def _start_game(self):
        """开始游戏（由外部处理）"""
        pass

    def draw(self):
        """绘制主菜单"""
        # 背景
        self.screen.fill(config.COLORS['ui_bg'])

        # 标题
        title_text = self.font_title.render("揭 棋 对 战", True, config.COLORS['board_border'])
        title_rect = title_text.get_rect(center=(config.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title_text, title_rect)

        # 副标题
        subtitle_text = self.font.render("中国象棋揭棋变体", True, config.COLORS['ui_text'])
        subtitle_rect = subtitle_text.get_rect(center=(config.WINDOW_WIDTH // 2, 160))
        self.screen.blit(subtitle_text, subtitle_rect)

        # 游戏模式按钮
        for name, button in self.buttons.items():
            button.draw(self.screen, self.font)

        # 如果选择了人机模式，显示难度选择
        if self.selected_mode == config.MODE_PVE:
            difficulty_label = self.font.render("AI难度:", True, config.COLORS['ui_text'])
            self.screen.blit(difficulty_label, (config.WINDOW_WIDTH // 2 - 200, 350))

            for button in self.difficulty_buttons.values():
                button.draw(self.screen, self.font)

        # 计时器选择
        timer_label = self.font.render("计时器:", True, config.COLORS['ui_text'])
        self.screen.blit(timer_label, (config.WINDOW_WIDTH // 2 - 200, 450))

        for button in self.timer_buttons.values():
            button.draw(self.screen, self.font)

        # 开始按钮
        if self.selected_mode:
            self.start_button.draw(self.screen, self.font)

    def handle_event(self, event):
        """处理事件"""
        for button in self.buttons.values():
            button.handle_event(event)

        if self.selected_mode == config.MODE_PVE:
            for button in self.difficulty_buttons.values():
                button.handle_event(event)

        for button in self.timer_buttons.values():
            button.handle_event(event)

        if self.selected_mode and event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button.rect.collidepoint(event.pos):
                return {
                    'mode': self.selected_mode,
                    'difficulty': self.selected_difficulty,
                    'timer': self.selected_timer
                }

        return None


class GameScreen:
    """游戏界面"""

    def __init__(self, screen, renderer, game_manager):
        self.screen = screen
        self.renderer = renderer
        self.game_manager = game_manager
        self.font = renderer.font_ui

        # 按钮位置
        button_x = config.WINDOW_WIDTH - 200
        self.buttons = {
            'undo': Button(button_x, 400, 120, 40, "悔棋", self._undo),
            'hint': Button(button_x, 460, 120, 40, "提示", self._show_hint),
            'resign': Button(button_x, 520, 120, 40, "认输", self._resign),
            'restart': Button(button_x, 580, 120, 40, "重开", self._restart),
            'menu': Button(button_x, 640, 120, 40, "返回菜单", self._back_to_menu),
        }

        self.hint_positions = []  # 提示位置

    def _undo(self):
        """悔棋"""
        self.game_manager.undo_move()

    def _show_hint(self):
        """显示走棋提示"""
        hints = self.game_manager.get_hint()
        self.hint_positions = [(pos[1], pos[2]) for pos in hints]

    def _resign(self):
        """认输"""
        self.game_manager.resign(self.game_manager.current_player)

    def _restart(self):
        """重新开始"""
        self.game_manager.start_game(self.game_manager.game_mode, self.game_manager.timer_duration)

    def _back_to_menu(self):
        """返回主菜单"""
        self.game_manager.state = 'menu'

    def draw(self):
        """绘制游戏界面"""
        # 背景
        self.screen.fill(config.COLORS['ui_bg'])

        # 绘制棋盘
        self.renderer.draw_board()

        # 绘制棋子
        self.renderer.draw_pieces(
            self.game_manager.board,
            self.game_manager.selected_piece,
            self.game_manager.valid_moves
        )

        # 绘制已吃棋子
        self.renderer.draw_captured_pieces(
            self.game_manager.board,
            config.WINDOW_WIDTH - 200,
            50
        )

        # 绘制回合指示
        self.renderer.draw_turn_indicator(self.game_manager.current_player)

        # 绘制计时器
        self.renderer.draw_timer(self.game_manager)

        # 绘制提示消息
        if self.game_manager.message:
            self.renderer.draw_message(self.game_manager.message)

        # 绘制按钮
        for button in self.buttons.values():
            button.draw(self.screen, self.font)

        # 绘制走棋提示高亮
        for pos in self.hint_positions:
            screen_x, screen_y = self.renderer._get_screen_pos(pos[0], pos[1])
            pygame.draw.circle(self.screen, (0, 100, 255), (screen_x, screen_y), config.PIECE_RADIUS + 5, 3)

    def handle_event(self, event):
        """处理事件"""
        # 处理按钮事件
        for button in self.buttons.values():
            button.handle_event(event)

        # 处理棋盘点击
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 清除提示
            self.hint_positions = []

            # 获取点击位置
            board_pos = self.renderer.get_board_pos(*event.pos)
            if board_pos:
                self._handle_board_click(board_pos)

    def _handle_board_click(self, pos):
        """处理棋盘点击"""
        row, col = pos
        game = self.game_manager

        # 如果游戏结束，不处理
        if game.state != 'playing':
            return

        # 如果已选中棋子
        if game.selected_piece:
            # 检查是否是合法移动位置
            if pos in game.valid_moves:
                game.make_move(row, col)
            else:
                # 选择其他棋子
                game.select_piece(row, col)
        else:
            # 选择棋子
            game.select_piece(row, col)


class ResultScreen:
    """游戏结果界面"""

    def __init__(self, screen, renderer):
        self.screen = screen
        self.renderer = renderer
        self.font = renderer.font_title
        self.font_ui = renderer.font_ui
        self.result = None
        self.winner = None

        # 按钮
        center_x = config.WINDOW_WIDTH // 2
        self.restart_button = Button(center_x - 110, 400, 100, 40, "再来一局", None)
        self.menu_button = Button(center_x + 10, 400, 100, 40, "返回菜单", None)

    def set_result(self, result, winner):
        """设置结果"""
        self.result = result
        self.winner = winner

    def draw(self):
        """绘制结果界面"""
        # 半透明背景
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # 结果框
        result_rect = pygame.Rect(
            config.WINDOW_WIDTH // 2 - 150,
            200,
            300,
            280
        )
        pygame.draw.rect(self.screen, config.COLORS['ui_bg'], result_rect, border_radius=15)
        pygame.draw.rect(self.screen, config.COLORS['board_border'], result_rect, 3, border_radius=15)

        # 结果文字
        if self.winner == 'red':
            result_text = "红方胜利！"
            color = config.COLORS['text_red']
        else:
            result_text = "黑方胜利！"
            color = config.COLORS['text_black']

        text_surface = self.font.render(result_text, True, color)
        text_rect = text_surface.get_rect(center=(config.WINDOW_WIDTH // 2, 280))
        self.screen.blit(text_surface, text_rect)

        # 按钮
        self.restart_button.draw(self.screen, self.font_ui)
        self.menu_button.draw(self.screen, self.font_ui)

    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.restart_button.rect.collidepoint(event.pos):
                return 'restart'
            if self.menu_button.rect.collidepoint(event.pos):
                return 'menu'
        return None