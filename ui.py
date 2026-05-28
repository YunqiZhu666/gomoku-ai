"""
ui.py — 五子棋 pygame 图形界面
==================================
功能：绘制棋盘/棋子、鼠标交互、AI 对战、游戏状态管理
"""

import pygame
import sys
from board import Board
from search import get_ai_move

# ── 颜色常量 ──
COLOR_BG = (210, 180, 140)       # 木纹底色
COLOR_LINE = (100, 80, 60)       # 网格线
COLOR_BLACK = (30, 30, 30)       # 黑子
COLOR_WHITE = (240, 240, 240)    # 白子
COLOR_HOVER = (200, 200, 100, 80)  # 悬浮提示
COLOR_LAST_MOVE = (255, 50, 50)  # 最后一步标记
COLOR_TEXT = (50, 50, 50)
COLOR_WIN = (255, 215, 0)        # 胜利文字
COLOR_BTN = (100, 150, 200)
COLOR_BTN_HOVER = (130, 180, 230)

# ── 布局参数 ──
MARGIN = 40          # 棋盘边距
CELL_SIZE = 55       # 格子大小
STONE_RADIUS = 22    # 棋子半径
BOARD_SIZE = 9       # 9×9

# 窗口尺寸
WIN_WIDTH = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1) + 200  # 右侧留信息栏
WIN_HEIGHT = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)
INFO_WIDTH = 200

# 按钮区域
BTN_Y = WIN_HEIGHT - 120
BTN_W, BTN_H = 140, 40


class GomokuUI:
    """五子棋 GUI 主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.display.set_caption("五子棋 AI — 9×9")
        self.font = self._init_font(20)
        self.font_small = self._init_font(16)
        self.font_big = self._init_font(36)
        self.clock = pygame.time.Clock()

        self.board = Board(BOARD_SIZE)
        self.game_over = False
        self.winner = None
        self.hover_pos = None
        self.ai_thinking = False
        self.ai_stats = {}
        self.move_count = 0
        self.player_side = Board.BLACK   # 玩家执黑先行
        self.ai_side = Board.WHITE

        # 按钮
        self.restart_btn = pygame.Rect(WIN_WIDTH - INFO_WIDTH + 30, BTN_Y, BTN_W, BTN_H)
        self.undo_btn = pygame.Rect(WIN_WIDTH - INFO_WIDTH + 30, BTN_Y + 50, BTN_W, BTN_H)

    @staticmethod
    def _init_font(size):
        """安全初始化字体（绕过 pygame 2.6.1 Windows SysFont bug）"""
        try:
            return pygame.font.SysFont("simhei", size)
        except Exception:
            pass
        # 直接加载系统字体文件
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/Deng.ttf",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
        ]
        for path in font_paths:
            try:
                return pygame.font.Font(path, size)
            except Exception:
                continue
        return pygame.font.Font(None, size)

    # ── 坐标转换 ──

    def _board_to_screen(self, row: int, col: int) -> tuple:
        """棋盘坐标 → 屏幕像素坐标"""
        x = MARGIN + col * CELL_SIZE
        y = MARGIN + row * CELL_SIZE
        return (x, y)

    def _screen_to_board(self, px: int, py: int) -> tuple:
        """屏幕像素坐标 → 棋盘坐标（可能为 None）"""
        col = round((px - MARGIN) / CELL_SIZE)
        row = round((py - MARGIN) / CELL_SIZE)
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            sx, sy = self._board_to_screen(row, col)
            if abs(px - sx) < CELL_SIZE // 2 and abs(py - sy) < CELL_SIZE // 2:
                return (row, col)
        return (None, None)

    # ── 绘制 ──

    def _draw_board(self):
        """绘制棋盘网格"""
        self.screen.fill(COLOR_BG)

        # 绘制网格线
        for i in range(BOARD_SIZE):
            start = self._board_to_screen(i, 0)
            end = self._board_to_screen(i, BOARD_SIZE - 1)
            pygame.draw.line(self.screen, COLOR_LINE, start, end, 1)

            start = self._board_to_screen(0, i)
            end = self._board_to_screen(BOARD_SIZE - 1, i)
            pygame.draw.line(self.screen, COLOR_LINE, start, end, 1)

        # 画星位（天元、小目）
        star_points = [(4, 4), (2, 2), (2, 6), (6, 2), (6, 6)]
        for r, c in star_points:
            pos = self._board_to_screen(r, c)
            pygame.draw.circle(self.screen, COLOR_LINE, pos, 4)

    def _draw_stones(self):
        """绘制所有棋子"""
        board_matrix = self.board.to_matrix()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                val = board_matrix[r][c]
                if val == Board.EMPTY:
                    continue
                pos = self._board_to_screen(r, c)
                color = COLOR_BLACK if val == Board.BLACK else COLOR_WHITE
                # 棋子阴影
                shadow_pos = (pos[0] + 2, pos[1] + 2)
                pygame.draw.circle(self.screen, (50, 50, 50, 100), shadow_pos, STONE_RADIUS)
                # 棋子本体
                pygame.draw.circle(self.screen, color, pos, STONE_RADIUS)
                # 高光
                if val == Board.BLACK:
                    highlight = (80, 80, 80)
                else:
                    highlight = (255, 255, 255)
                pygame.draw.circle(self.screen, highlight, (pos[0] - 4, pos[1] - 4), 6)

    def _draw_last_move(self):
        """标记最后一步"""
        if self.board.last_move:
            r, c = self.board.last_move
            pos = self._board_to_screen(r, c)
            pygame.draw.circle(self.screen, COLOR_LAST_MOVE, pos, 6, 2)

    def _draw_hover(self):
        """鼠标悬浮高亮"""
        if self.hover_pos and not self.game_over and not self.ai_thinking:
            r, c = self.hover_pos
            if self.board.get(r, c) == Board.EMPTY:
                pos = self._board_to_screen(r, c)
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                s.fill((200, 200, 100, 60))
                self.screen.blit(s, (pos[0] - CELL_SIZE // 2, pos[1] - CELL_SIZE // 2))

    def _draw_info_panel(self):
        """绘制右侧信息栏"""
        x_start = MARGIN + CELL_SIZE * (BOARD_SIZE - 1) + 20
        # 分隔线
        pygame.draw.line(self.screen, COLOR_LINE,
                         (x_start, MARGIN), (x_start, WIN_HEIGHT - MARGIN), 2)

        # 标题
        title = self.font.render("五子棋 AI", True, COLOR_TEXT)
        self.screen.blit(title, (x_start + 20, MARGIN + 20))

        # 当前玩家
        if not self.game_over:
            turn_text = "你的回合 ●" if not self.ai_thinking else "AI 思考中 ○..."
            if self.ai_thinking:
                color = (200, 100, 100)
            else:
                color = COLOR_TEXT
            turn_label = self.font.render(turn_text, True, color)
            self.screen.blit(turn_label, (x_start + 20, MARGIN + 60))

        # 步数
        steps_text = f"步数: {self.move_count}"
        steps_label = self.font_small.render(steps_text, True, COLOR_TEXT)
        self.screen.blit(steps_label, (x_start + 20, MARGIN + 100))

        # AI 统计
        if self.ai_stats:
            y = MARGIN + 140
            for key, val in self.ai_stats.items():
                stat_text = f"{key}: {val}"
                stat_label = self.font_small.render(stat_text, True, COLOR_TEXT)
                self.screen.blit(stat_label, (x_start + 20, y))
                y += 25

        # 游戏结束
        if self.game_over:
            if self.winner == self.player_side:
                win_text = "你赢了！ 🎉"
                win_color = (50, 180, 50)
            elif self.winner == self.ai_side:
                win_text = "AI 赢了！ 🤖"
                win_color = (200, 50, 50)
            else:
                win_text = "平局！"
                win_color = COLOR_TEXT
            win_label = self.font_big.render(win_text, True, win_color)
            self.screen.blit(win_label, (x_start + 20, MARGIN + 200))

        # 按钮
        mouse_pos = pygame.mouse.get_pos()
        for btn, text in [(self.restart_btn, "重新开始"), (self.undo_btn, "悔棋")]:
            color = COLOR_BTN_HOVER if btn.collidepoint(mouse_pos) else COLOR_BTN
            pygame.draw.rect(self.screen, color, btn, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_LINE, btn, 2, border_radius=8)
            label = self.font_small.render(text, True, (255, 255, 255))
            label_rect = label.get_rect(center=btn.center)
            self.screen.blit(label, label_rect)

    def _draw_win_line(self):
        """连五高亮"""
        if not self.game_over or self.winner is None:
            return
        # 扫描棋盘找五子连珠
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board.get(r, c) == self.winner:
                    for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                        count = 0
                        positions = []
                        for i in range(5):
                            nr, nc = r + dr * i, c + dc * i
                            if (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE
                                    and self.board.get(nr, nc) == self.winner):
                                count += 1
                                positions.append((nr, nc))
                        if count >= 5:
                            # 画连线
                            start = self._board_to_screen(positions[0][0], positions[0][1])
                            end = self._board_to_screen(positions[-1][0], positions[-1][1])
                            pygame.draw.line(self.screen, COLOR_WIN, start, end, 4)
                            return

    # ── 游戏逻辑 ──

    def _player_move(self, row: int, col: int) -> bool:
        """玩家落子，返回是否成功"""
        if self.game_over or self.ai_thinking:
            return False
        if self.board.get(row, col) != Board.EMPTY:
            return False

        self.board.place(row, col, self.player_side)
        self.move_count += 1

        if self.board.check_win(row, col, self.player_side):
            self.game_over = True
            self.winner = self.player_side
            return True

        if self.board.is_full():
            self.game_over = True
            self.winner = None
            return True

        # AI 回合
        self.ai_thinking = True
        return True

    def _ai_move(self):
        """AI 走棋"""
        if self.game_over:
            self.ai_thinking = False
            return

        move, stats = get_ai_move(self.board, self.ai_side, time_limit=3.0)
        self.ai_stats = stats
        if move:
            r, c = move
            self.board.place(r, c, self.ai_side)
            self.move_count += 1
            if self.board.check_win(r, c, self.ai_side):
                self.game_over = True
                self.winner = self.ai_side
            elif self.board.is_full():
                self.game_over = True
                self.winner = None
        self.ai_thinking = False

    def _restart(self):
        """重新开始"""
        self.board = Board(BOARD_SIZE)
        self.game_over = False
        self.winner = None
        self.ai_thinking = False
        self.ai_stats = {}
        self.move_count = 0

    def _undo(self):
        """悔棋（撤回玩家和AI各一步）"""
        if self.game_over or self.ai_thinking:
            return
        if len(self.board.move_history) < 2:
            return
        self.board.undo()  # 撤 AI
        self.board.undo()  # 撤玩家
        self.move_count = max(0, self.move_count - 2)

    # ── 主循环 ──

    def run(self):
        """游戏主循环"""
        running = True
        ai_timer = 0

        while running:
            # 如果是 AI 回合且不在思考中
            if self.ai_thinking and not self.game_over:
                now = pygame.time.get_ticks()
                if now - ai_timer > 200:  # 稍微延迟让画面更新
                    self._ai_move()
                    ai_timer = now

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEMOTION:
                    row, col = self._screen_to_board(event.pos[0], event.pos[1])
                    self.hover_pos = (row, col) if row is not None else None

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键
                        # 检查按钮
                        if self.restart_btn.collidepoint(event.pos):
                            self._restart()
                            continue
                        if self.undo_btn.collidepoint(event.pos):
                            self._undo()
                            continue

                        # 落子
                        row, col = self._screen_to_board(event.pos[0], event.pos[1])
                        if row is not None:
                            self._player_move(row, col)

            # 绘制
            self._draw_board()
            self._draw_stones()
            self._draw_last_move()
            self._draw_win_line()
            self._draw_hover()
            self._draw_info_panel()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


# ── 启动 ──

if __name__ == "__main__":
    ui = GomokuUI()
    ui.run()
