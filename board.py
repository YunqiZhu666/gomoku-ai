"""
board.py — 五子棋棋盘核心逻辑
==============================
9×9 棋盘、落子、合法走法生成、五子连珠胜负检测
"""


class Board:
    """五子棋棋盘类"""

    EMPTY = 0
    BLACK = 1  # 先手（人类玩家）
    WHITE = 2  # 后手（AI）

    def __init__(self, size=9):
        self.size = size
        self._board = [[self.EMPTY] * size for _ in range(size)]
        self.last_move = None
        self.move_history = []  # [(row, col, player), ...]

    # ────────── 基础操作 ──────────

    def place(self, row: int, col: int, player: int) -> bool:
        """在 (row, col) 落子，成功返回 True"""
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        if self._board[row][col] != self.EMPTY:
            return False
        self._board[row][col] = player
        self.last_move = (row, col)
        self.move_history.append((row, col, player))
        return True

    def undo(self) -> bool:
        """撤销上一步落子，成功返回 True"""
        if not self.move_history:
            return False
        row, col, _ = self.move_history.pop()
        self._board[row][col] = self.EMPTY
        self.last_move = self.move_history[-1][:2] if self.move_history else None
        return True

    def get(self, row: int, col: int) -> int:
        """获取某位置的状态"""
        if 0 <= row < self.size and 0 <= col < self.size:
            return self._board[row][col]
        return -1

    def is_empty(self) -> bool:
        """棋盘是否为空"""
        for r in range(self.size):
            for c in range(self.size):
                if self._board[r][c] != self.EMPTY:
                    return False
        return True

    def is_full(self) -> bool:
        """棋盘是否已满（平局判定）"""
        for r in range(self.size):
            for c in range(self.size):
                if self._board[r][c] == self.EMPTY:
                    return False
        return True

    # ────────── 胜负检测 ──────────

    def check_win(self, row: int, col: int, player: int) -> bool:
        """
        检测 (row, col) 落子后 player 是否获胜
        从该点向 4 个方向扫描（横、竖、对角线、反对角线）
        """
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            # 正方向
            r, c = row + dr, col + dc
            while 0 <= r < self.size and 0 <= c < self.size and self._board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # 反方向
            r, c = row - dr, col - dc
            while 0 <= r < self.size and 0 <= c < self.size and self._board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 5:
                return True
        return False

    # ────────── 走法生成 ──────────

    def get_legal_moves(self) -> list:
        """
        生成合法走法列表
        优化：只返回已有棋子周围 1 格范围内的空位（大幅减少搜索空间）
        """
        if self.is_empty():
            center = self.size // 2
            return [(center, center)]

        moves_set = set()
        neighbor_offsets = [(-1, -1), (-1, 0), (-1, 1),
                            (0, -1),           (0, 1),
                            (1, -1),  (1, 0),  (1, 1)]
        for r in range(self.size):
            for c in range(self.size):
                if self._board[r][c] != self.EMPTY:
                    for dr, dc in neighbor_offsets:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.size and 0 <= nc < self.size:
                            if self._board[nr][nc] == self.EMPTY:
                                moves_set.add((nr, nc))
        return list(moves_set)

    # ────────── 工具方法 ──────────

    def copy(self) -> "Board":
        """深拷贝棋盘（用于搜索时的状态复制）"""
        new_board = Board(self.size)
        for r in range(self.size):
            for c in range(self.size):
                new_board._board[r][c] = self._board[r][c]
        new_board.last_move = self.last_move
        new_board.move_history = list(self.move_history)
        return new_board

    def to_matrix(self):
        """返回二维数组副本（方便可视化）"""
        return [row[:] for row in self._board]

    def display(self):
        """命令行打印棋盘"""
        symbols = {self.EMPTY: "·", self.BLACK: "●", self.WHITE: "○"}
        # 列标
        print("  " + " ".join(str(i) for i in range(self.size)))
        for r in range(self.size):
            row_str = f"{r} "
            for c in range(self.size):
                row_str += symbols[self._board[r][c]] + " "
            print(row_str)
        print()


# ────────── 单元测试 ──────────

if __name__ == "__main__":
    # 简单自测
    b = Board()
    assert b.is_empty()
    assert b.place(4, 4, Board.BLACK)
    assert not b.place(4, 4, Board.BLACK)  # 重复落子失败
    b.place(4, 5, Board.BLACK)
    b.place(4, 6, Board.BLACK)
    b.place(4, 7, Board.BLACK)
    b.place(4, 8, Board.BLACK)
    assert b.check_win(4, 8, Board.BLACK)  # 横向五子连珠
    print("[OK] board.py 所有测试通过")
    b.display()
