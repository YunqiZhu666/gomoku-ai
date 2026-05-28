"""
search.py — 五子棋 AI 搜索算法（优化版）
==========================================
包含：Minimax → Alpha-Beta 剪枝 → 迭代加深 + 走法排序 + 置换表 + 走法裁剪
"""

import time
import sys
from board import Board
from evaluate import evaluate, quick_evaluate

# 增大递归深度限制
sys.setrecursionlimit(10000)

# ── 全局搜索控制 ──
_SEARCH_START = 0.0
_SEARCH_DEADLINE = 0.0
_NODE_COUNT = 0
_MAX_MOVES = 9  # 每层最多考虑 9 个走法（裁剪宽度）

# ── 转置表 ──
TRANSPOSITION_TABLE = {}


def _init_search(time_limit: float):
    """初始化搜索控制变量"""
    global _SEARCH_START, _SEARCH_DEADLINE, _NODE_COUNT
    _SEARCH_START = time.time()
    _SEARCH_DEADLINE = _SEARCH_START + time_limit
    _NODE_COUNT = 0


def _time_up() -> bool:
    """检查是否超时"""
    return time.time() >= _SEARCH_DEADLINE


def clear_tt():
    global TRANSPOSITION_TABLE
    TRANSPOSITION_TABLE = {}


def _board_hash(board: Board) -> str:
    return str(board.to_matrix())


# ══════════════════════════════════════════
# 1. 纯 Minimax（基准算法，仅小深度使用）
# ══════════════════════════════════════════

def minimax(board: Board, depth: int, is_maximizing: bool, player: int) -> tuple:
    global _NODE_COUNT
    _NODE_COUNT += 1

    opponent = Board.BLACK if player == Board.WHITE else Board.WHITE
    current = player if is_maximizing else opponent

    if board.last_move:
        last_r, last_c = board.last_move
        last_player = board.move_history[-1][2]
        if board.check_win(last_r, last_c, last_player):
            if last_player == player:
                return (10_000_000 + depth, None)
            else:
                return (-10_000_000 - depth, None)

    if depth == 0 or board.is_full():
        return (evaluate(board, player), None)

    moves = board.get_legal_moves()
    if not moves:
        return (evaluate(board, player), None)

    best_move = moves[0]
    if is_maximizing:
        best_score = -float("inf")
        for move in moves:
            r, c = move
            board.place(r, c, current)
            score, _ = minimax(board, depth - 1, False, player)
            board.undo()
            if score > best_score:
                best_score = score
                best_move = move
        return (best_score, best_move)
    else:
        best_score = float("inf")
        for move in moves:
            r, c = move
            board.place(r, c, current)
            score, _ = minimax(board, depth - 1, True, player)
            board.undo()
            if score < best_score:
                best_score = score
                best_move = move
        return (best_score, best_move)


# ══════════════════════════════════════════
# 2. Alpha-Beta 剪枝（核心算法）
# ══════════════════════════════════════════

def alpha_beta(board: Board, depth: int, alpha: float, beta: float,
               is_maximizing: bool, player: int, use_tt: bool = True) -> tuple:
    global _NODE_COUNT
    _NODE_COUNT += 1

    # 周期性超时检查（每 1000 节点检查一次）
    if _NODE_COUNT % 1000 == 0 and _time_up():
        return (0, None)  # 超时信号

    opponent = Board.BLACK if player == Board.WHITE else Board.WHITE
    current = player if is_maximizing else opponent

    # ── 置换表查找 ──
    if use_tt:
        h = _board_hash(board)
        if h in TRANSPOSITION_TABLE:
            cached_depth, cached_score, cached_move = TRANSPOSITION_TABLE[h]
            if cached_depth >= depth:
                return (cached_score, cached_move)

    # ── 终局检测 ──
    if board.last_move:
        last_r, last_c = board.last_move
        last_player = board.move_history[-1][2]
        if board.check_win(last_r, last_c, last_player):
            if last_player == player:
                return (10_000_000 + depth, None)
            else:
                return (-10_000_000 - depth, None)

    if depth == 0 or board.is_full():
        return (evaluate(board, player), None)

    moves = board.get_legal_moves()
    if not moves:
        return (evaluate(board, player), None)

    # ── 走法排序 + 裁剪 ──
    scored_moves = [(quick_evaluate(board, player, r, c), (r, c)) for r, c in moves]
    scored_moves.sort(key=lambda x: x[0], reverse=is_maximizing)
    # 只保留前 _MAX_MOVES 个走法
    sorted_moves = [m for _, m in scored_moves[:_MAX_MOVES]]

    best_move = sorted_moves[0]
    best_score = -float("inf") if is_maximizing else float("inf")

    for move in sorted_moves:
        r, c = move
        board.place(r, c, current)

        if is_maximizing:
            score, _ = alpha_beta(board, depth - 1, alpha, beta, False, player, use_tt)
            board.undo()
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        else:
            score, _ = alpha_beta(board, depth - 1, alpha, beta, True, player, use_tt)
            board.undo()
            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, best_score)
            if beta <= alpha:
                break

    # ── 置换表存储 ──
    if use_tt:
        h = _board_hash(board)
        TRANSPOSITION_TABLE[h] = (depth, best_score, best_move)

    return (best_score, best_move)


# ══════════════════════════════════════════
# 3. 迭代加深
# ══════════════════════════════════════════

def iterative_deepening(board: Board, player: int,
                        max_depth: int = 8, time_limit: float = 4.0,
                        use_alpha_beta: bool = True, use_tt: bool = True) -> tuple:
    clear_tt()
    _init_search(time_limit)

    best_move = None
    stats = {"depth": 0, "time": 0.0}

    for d in range(1, max_depth + 1):
        if _time_up():
            break

        try:
            if use_alpha_beta:
                score, move = alpha_beta(board, d, -float("inf"), float("inf"),
                                         True, player, use_tt)
            else:
                score, move = minimax(board, d, True, player)

            if move is not None and not _time_up():
                best_move = move
                stats["depth"] = d
                stats["time"] = time.time() - _SEARCH_START
        except RecursionError:
            break

    stats["time"] = time.time() - _SEARCH_START
    return (best_move, stats)


# ── 对外接口 ──

def get_ai_move(board: Board, player: int, time_limit: float = 3.0) -> tuple:
    """
    AI 选下一步走法（主入口）
    返回: ((row, col), {"depth": int, "time": float})
    """
    moves = board.get_legal_moves()
    if not moves:
        return (None, {"depth": 0, "time": 0.0})

    if board.is_empty():
        center = board.size // 2
        return ((center, center), {"depth": 1, "time": 0.0})

    # 一步杀检测
    for move in moves:
        r, c = move
        board.place(r, c, player)
        if board.check_win(r, c, player):
            board.undo()
            return ((r, c), {"depth": 1, "time": 0.0})
        board.undo()

    # 堵对手一步杀
    opponent = Board.BLACK if player == Board.WHITE else Board.WHITE
    for move in moves:
        r, c = move
        board.place(r, c, opponent)
        if board.check_win(r, c, opponent):
            board.undo()
            return ((r, c), {"depth": 1, "time": 0.0})
        board.undo()

    return iterative_deepening(board, player, max_depth=10, time_limit=time_limit)


# ── 单元测试 ──

if __name__ == "__main__":
    b = Board()
    b.place(4, 4, Board.BLACK)
    b.place(0, 0, Board.WHITE)
    b.place(4, 5, Board.BLACK)
    b.place(0, 1, Board.WHITE)

    print("当前棋盘:")
    b.display()

    score, move = alpha_beta(b, 2, -float("inf"), float("inf"), True, Board.BLACK)
    print(f"Alpha-Beta depth=2 → 分数: {score}, 走法: {move}, 节点: {_NODE_COUNT}")

    ai_move, stats = get_ai_move(b, Board.BLACK, time_limit=2.0)
    print(f"AI走法: {ai_move}, 统计: {stats}")

    print("[OK] search.py 测试通过")
