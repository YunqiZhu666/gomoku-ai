"""
unbeatable_gui.py — 无敌五子棋 AI 图形界面
=============================================
AI 先行天元（执黑），人类后手（执白）。
基于 unbeatable 深度搜索引擎。
"""

import pygame
import sys
from board import Board
import unbeatable

# ── 颜色常量 ──
COLOR_BG = (210, 180, 140)
COLOR_LINE = (100, 80, 60)
COLOR_BLACK = (30, 30, 30)
COLOR_WHITE = (240, 240, 240)
COLOR_HOVER = (200, 200, 100, 80)
COLOR_LAST_MOVE = (255, 50, 50)
COLOR_TEXT = (50, 50, 50)
COLOR_WIN = (255, 215, 0)
COLOR_BTN = (100, 150, 200)
COLOR_BTN_HOVER = (130, 180, 230)

# ── 布局参数 ──
MARGIN = 40
CELL_SIZE = 55
STONE_RADIUS = 22
BOARD_SIZE = 9

WIN_WIDTH = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1) + 200
WIN_HEIGHT = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)
INFO_WIDTH = 200

BTN_Y = WIN_HEIGHT - 120
BTN_W, BTN_H = 140, 40


class UnbeatableUI:
    """无敌 AI 五子棋 GUI"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.display.set_caption("五子棋 AI — 无敌模式")
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
        self.ai_side = Board.BLACK     # AI 执黑先行
        self.player_side = Board.WHITE  # 人类执白后手
        self.last_ai_move = None
        self.ai_timer = 0

        # 按钮
        self.restart_btn = pygame.Rect(WIN_WIDTH - INFO_WIDTH + 30, BTN_Y, BTN_W, BTN_H)
        self.undo_btn = pygame.Rect(WIN_WIDTH - INFO_WIDTH + 30, BTN_Y + 50, BTN_W, BTN_H)

    @staticmethod
    def _init_font(size):
        try:
            return pygame.font.SysFont("simhei", size)
        except Exception:
            pass
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

    def _board_to_screen(self, row, col):
        return (MARGIN + col * CELL_SIZE, MARGIN + row * CELL_SIZE)

    def _screen_to_board(self, px, py):
        col = round((px - MARGIN) / CELL_SIZE)
        row = round((py - MARGIN) / CELL_SIZE)
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            sx, sy = self._board_to_screen(row, col)
            if abs(px - sx) < CELL_SIZE // 2 and abs(py - sy) < CELL_SIZE // 2:
                return (row, col)
        return (None, None)

    # ── 绘制 ──

    def _draw_board(self):
        self.screen.fill(COLOR_BG)
        for i in range(BOARD_SIZE):
            start = self._board_to_screen(i, 0)
            end = self._board_to_screen(i, BOARD_SIZE - 1)
            pygame.draw.line(self.screen, COLOR_LINE, start, end, 1)
            start = self._board_to_screen(0, i)
            end = self._board_to_screen(BOARD_SIZE - 1, i)
            pygame.draw.line(self.screen, COLOR_LINE, start, end, 1)
        star_points = [(4, 4), (2, 2), (2, 6), (6, 2), (6, 6)]
        for r, c in star_points:
            pos = self._board_to_screen(r, c)
            pygame.draw.circle(self.screen, COLOR_LINE, pos, 4)

    def _draw_stones(self):
        board_matrix = self.board.to_matrix()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                val = board_matrix[r][c]
                if val == Board.EMPTY:
                    continue
                pos = self._board_to_screen(r, c)
                color = COLOR_BLACK if val == Board.BLACK else COLOR_WHITE
                shadow_pos = (pos[0] + 2, pos[1] + 2)
                pygame.draw.circle(self.screen, (50, 50, 50, 100), shadow_pos, STONE_RADIUS)
                pygame.draw.circle(self.screen, color, pos, STONE_RADIUS)
                highlight = (80, 80, 80) if val == Board.BLACK else (255, 255, 255)
                pygame.draw.circle(self.screen, highlight, (pos[0] - 4, pos[1] - 4), 6)

    def _draw_last_move(self):
        if self.board.last_move:
            r, c = self.board.last_move
            pos = self._board_to_screen(r, c)
            pygame.draw.circle(self.screen, COLOR_LAST_MOVE, pos, 6, 2)

    def _draw_hover(self):
        if self.hover_pos and not self.game_over and not self.ai_thinking:
            r, c = self.hover_pos
            if self.board.get(r, c) == Board.EMPTY:
                pos = self._board_to_screen(r, c)
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                s.fill((200, 200, 100, 60))
                self.screen.blit(s, (pos[0] - CELL_SIZE // 2, pos[1] - CELL_SIZE // 2))

    def _draw_info_panel(self):
        x_start = MARGIN + CELL_SIZE * (BOARD_SIZE - 1) + 20
        pygame.draw.line(self.screen, COLOR_LINE,
                         (x_start, MARGIN), (x_start, WIN_HEIGHT - MARGIN), 2)

        # 标题
        title = self.font.render("无敌模式", True, COLOR_TEXT)
        self.screen.blit(title, (x_start + 20, MARGIN + 20))

        # 当前回合
        if not self.game_over:
            if self.ai_thinking:
                turn_text = "AI 思考中 ●..."
                color = (200, 100, 100)
            else:
                turn_text = "你的回合 ○"
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
        if not self.game_over or self.winner is None:
            return
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
                            start = self._board_to_screen(positions[0][0], positions[0][1])
                            end = self._board_to_screen(positions[-1][0], positions[-1][1])
                            pygame.draw.line(self.screen, COLOR_WIN, start, end, 4)
                            return

    # ── 游戏逻辑 ──

    def _player_move(self, row, col):
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
            return True

        self.ai_thinking = True
        return True

    def _ai_move(self):
        if self.game_over:
            self.ai_thinking = False
            return

        import time
        t0 = time.time()
        move = unbeatable.get_best_move(self.board, self.ai_side)
        elapsed = time.time() - t0

        self.ai_stats = {
            "耗时": f"{elapsed:.1f}s",
            "时限": f"{unbeatable.TIME_LIMIT:.0f}s",
        }
        if move:
            r, c = move
            self.board.place(r, c, self.ai_side)
            self.move_count += 1
            self.last_ai_move = move
            if self.board.check_win(r, c, self.ai_side):
                self.game_over = True
                self.winner = self.ai_side
            elif self.board.is_full():
                self.game_over = True
                self.winner = None
        self.ai_thinking = False

    def _restart(self):
        self.board = Board(BOARD_SIZE)
        self.game_over = False
        self.winner = None
        self.ai_thinking = True   # AI 先行
        self.ai_stats = {}
        self.move_count = 0
        self.last_ai_move = None
        self.ai_timer = pygame.time.get_ticks()

    def _undo(self):
        if self.game_over or self.ai_thinking:
            return
        if len(self.board.move_history) < 2:
            return
        self.board.undo()
        self.board.undo()
        self.move_count = max(0, self.move_count - 2)

    # ── 主循环 ──

    def run(self):
        running = True
        # AI 先手：开局即进入思考
        self.ai_thinking = True
        self.ai_timer = pygame.time.get_ticks()

        while running:
            # AI 回合
            if self.ai_thinking and not self.game_over:
                now = pygame.time.get_ticks()
                if now - self.ai_timer > 300:  # 延迟让画面渲染
                    self._ai_move()
                    self.ai_timer = now

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEMOTION:
                    row, col = self._screen_to_board(event.pos[0], event.pos[1])
                    self.hover_pos = (row, col) if row is not None else None

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.restart_btn.collidepoint(event.pos):
                            self._restart()
                            continue
                        if self.undo_btn.collidepoint(event.pos):
                            self._undo()
                            continue
                        row, col = self._screen_to_board(event.pos[0], event.pos[1])
                        if row is not None:
                            self._player_move(row, col)

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


if __name__ == "__main__":
    ui = UnbeatableUI()
    ui.run()
