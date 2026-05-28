"""
evaluate.py — 五子棋局面评估函数（第一版：窗口扫描）
===========================================
采用窗口滑动法扫描每条线上的棋型，能识别跳活三等非连续模式。
"""

from board import Board

# ── 方向向量 ──
DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]

# ── 棋型枚举 ──
FIVE = 0
LIVE_FOUR = 1
RUSH_FOUR = 2
LIVE_THREE = 3
SLEEP_THREE = 4
LIVE_TWO = 5
SLEEP_TWO = 6

SCORES = {
    FIVE: 10_000_000,
    LIVE_FOUR: 8_000_000,   # 接近连五——活四几乎必胜
    RUSH_FOUR: 2_500_000,   # 冲四和活三同等重要（×5）
    LIVE_THREE: 2_500_000,  # 活三价值大幅提高（×5）——连活三/跳活三都很关键
    SLEEP_THREE: 200_000,   # 对应提高
    LIVE_TWO: 5_000,        # 对应提高
    SLEEP_TWO: 500,         # 对应提高
}

# 防守权重（可外部修改用于实验对比）
DEFENSE_WEIGHT = 1.1


def _analyze_line(board: Board, row: int, col: int, dr: int, dc: int, player: int):
    """
    沿 (dr,dc) 方向分析一条线上 player 的棋型。
    按棋子间距分组（gap≤1 视为同组），每组评估一次。
    返回 (patterns, covered) — covered 是棋盘点位列表，用于在 evaluate 中防止重复计数。
    """
    size = board.size

    # 收集整条线 + 记录每个格子的棋盘坐标
    line = []
    coords = []  # [(r,c), ...]
    r, c = row, col
    while 0 <= r < size and 0 <= c < size:
        r -= dr
        c -= dc
    r += dr; c += dc
    while 0 <= r < size and 0 <= c < size:
        line.append(board.get(r, c))
        coords.append((r, c))
        r += dr; c += dc

    patterns = []
    covered = set()
    n = len(line)

    stone_pos = [i for i in range(n) if line[i] == player]
    if not stone_pos:
        return patterns, covered

    # 按间距 ≤ 2 分组
    groups = []
    cur = [stone_pos[0]]
    for i in range(1, len(stone_pos)):
        if stone_pos[i] - stone_pos[i - 1] <= 2:
            cur.append(stone_pos[i])
        else:
            groups.append(cur)
            cur = [stone_pos[i]]
    groups.append(cur)

    for group in groups:
        start = group[0]
        end = group[-1]
        seg = line[start:end + 1]
        stone_cnt = seg.count(player)

        left_open = start > 0 and line[start - 1] == Board.EMPTY
        right_open = end + 1 < n and line[end + 1] == Board.EMPTY

        # 记录该组覆盖的所有棋盘坐标
        for idx in range(start, end + 1):
            covered.add((coords[idx][0], coords[idx][1], dr, dc, player))

        if stone_cnt >= 5:
            patterns.append(FIVE)
            return patterns, covered
        elif stone_cnt == 4:
            patterns.append(LIVE_FOUR if left_open and right_open else RUSH_FOUR)
        elif stone_cnt == 3:
            patterns.append(LIVE_THREE if left_open and right_open else SLEEP_THREE)
        elif stone_cnt == 2:
            patterns.append(LIVE_TWO if left_open and right_open else SLEEP_TWO)

    return patterns, covered


def evaluate(board: Board, player: int) -> int:
    """
    评估当前局面。
    分数 = 己方棋型总和 - 对方棋型总和 × 1.1
    """
    size = board.size
    opponent = Board.BLACK if player == Board.WHITE else Board.WHITE
    my_score = 0
    opp_score = 0
    scored = set()

    for r in range(size):
        for c in range(size):
            cell = board.get(r, c)
            if cell == Board.EMPTY:
                continue
            for dr, dc in DIRECTIONS:
                pr, pc = r - dr, c - dc
                if 0 <= pr < size and 0 <= pc < size and board.get(pr, pc) == cell:
                    continue
                key = (r, c, dr, dc, cell)
                if key in scored:
                    continue
                scored.add(key)
                patterns, covered = _analyze_line(board, r, c, dr, dc, cell)
                for p in patterns:
                    if cell == player:
                        my_score += SCORES.get(p, 0)
                    else:
                        opp_score += SCORES.get(p, 0)
                # 标记该组的所有棋子已处理，防止跳连重复计数
                for ck in covered:
                    scored.add(ck)

    return my_score - opp_score * DEFENSE_WEIGHT


def quick_evaluate(board: Board, player: int, row: int, col: int) -> int:
    """
    快速评估在 (row,col) 落子的价值（走法排序用）。
    用窗口法分析该点 4 方向上的棋型。
    """
    if board.get(row, col) != Board.EMPTY:
        return -999_999_999

    opponent = Board.BLACK if player == Board.WHITE else Board.WHITE
    score = 0
    size = board.size

    for dr, dc in DIRECTIONS:
        # 收集该方向整条线
        line = []
        r, c = row, col
        while 0 <= r < size and 0 <= c < size:
            r -= dr
            c -= dc
        r += dr
        c += dc
        while 0 <= r < size and 0 <= c < size:
            line.append(board.get(r, c))
            r += dr
            c += dc

        n = len(line)
        center = -1
        for i, v in enumerate(line):
            if v == player or v == opponent:
                continue
            # 粗略定位 row,col 在 line 中的位置
            rr = row
            cc = col
            ri = 0
            tr, tc = rr, cc
            while 0 <= tr < size and 0 <= tc < size:
                tr -= dr
                tc -= dc
            tr += dr
            tc += dc
            while 0 <= tr < size and 0 <= tc < size:
                if tr == row and tc == col:
                    center = ri
                    break
                ri += 1
                tr += dr
                tc += dc
            break

        if center < 0:
            continue

        # 进攻：把 center 当作 player 的棋子
        line[center] = player
        for start in range(max(0, center - 4), min(n - 4, center) + 1):
            window = line[start:start + 5]
            pc = window.count(player)
            oc = window.count(opponent)
            if oc > 0:
                continue
            if pc >= 5:
                score += SCORES.get(FIVE, 0) * 2
            elif pc == 4:
                left = start > 0 and line[start - 1] == Board.EMPTY
                right = start + 5 < n and line[start + 5] == Board.EMPTY
                if left and right:
                    score += SCORES.get(LIVE_FOUR, 0) * 2
                else:
                    score += SCORES.get(RUSH_FOUR, 0) * 2
            elif pc == 3:
                left = start > 0 and line[start - 1] == Board.EMPTY
                right = start + 5 < n and line[start + 5] == Board.EMPTY
                if left and right:
                    score += SCORES.get(LIVE_THREE, 0) * 2
                else:
                    score += SCORES.get(SLEEP_THREE, 0) * 2
            elif pc == 2:
                left = start > 0 and line[start - 1] == Board.EMPTY
                right = start + 5 < n and line[start + 5] == Board.EMPTY
                if left and right:
                    score += SCORES.get(LIVE_TWO, 0) * 2
                else:
                    score += SCORES.get(SLEEP_TWO, 0) * 2

        # 防守：把 center 当作 opponent 的棋子
        line[center] = opponent
        for start in range(max(0, center - 4), min(n - 4, center) + 1):
            window = line[start:start + 5]
            pc = window.count(opponent)
            oc = window.count(player)
            if oc > 0:
                continue
            if pc >= 5:
                score += SCORES.get(FIVE, 0) * 2
            elif pc == 4:
                left = start > 0 and line[start - 1] == Board.EMPTY
                right = start + 5 < n and line[start + 5] == Board.EMPTY
                if left and right:
                    score += SCORES.get(LIVE_FOUR, 0) * 2
                else:
                    score += SCORES.get(RUSH_FOUR, 0) * 2
            elif pc == 3:
                left = start > 0 and line[start - 1] == Board.EMPTY
                right = start + 5 < n and line[start + 5] == Board.EMPTY
                if left and right:
                    score += SCORES.get(LIVE_THREE, 0) * 2
                else:
                    score += SCORES.get(SLEEP_THREE, 0) * 2
            elif pc == 2:
                left = start > 0 and line[start - 1] == Board.EMPTY
                right = start + 5 < n and line[start + 5] == Board.EMPTY
                if left and right:
                    score += SCORES.get(LIVE_TWO, 0) * 2
                else:
                    score += SCORES.get(SLEEP_TWO, 0) * 2

        line[center] = Board.EMPTY  # 恢复

    return score


# ── 单元测试 ──

if __name__ == "__main__":
    b = Board()
    b.place(4, 3, Board.BLACK)
    b.place(4, 4, Board.BLACK)
    b.place(4, 5, Board.BLACK)
    b.place(4, 6, Board.BLACK)
    score = evaluate(b, Board.BLACK)
    assert score > 900_000, f"活四得分低: {score}"
    print(f"[OK] 活四: {score:.0f}")

    b.place(4, 7, Board.BLACK)
    score = evaluate(b, Board.BLACK)
    assert score >= 10_000_000, f"连五得分低: {score}"
    print(f"[OK] 连五: {score:.0f}")

    # 跳活三测试
    b2 = Board()
    b2.place(4, 3, Board.WHITE)
    b2.place(4, 5, Board.WHITE)
    b2.place(4, 7, Board.WHITE)
    score2 = evaluate(b2, Board.WHITE)
    print(f"[OK] 跳活三(●_●_●): {score2:.0f}")

    print("[OK] evaluate.py 测试通过")
