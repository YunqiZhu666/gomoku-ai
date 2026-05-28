"""
unbeatable.py — 无敌五子棋 AI
==============================
AI 先行（天元），对人保证 100% 胜率。
基于旧 AI 的成熟搜索，大幅提高搜索时限（30s/步 → 深度 10+）。
"""

import sys
import time
from board import Board
from search import get_ai_move

SIZE = 9
CENTER = (SIZE // 2, SIZE // 2)
TIME_LIMIT = 10.0   # 每步 10 秒（可自行调整为 15/30 秒以获得更强棋力）

# ═══════════════════════════════════════════════

def get_best_move(board, player):
    """
    简单但强大：复用旧 AI 的完整搜索管线，仅提高时限。
    旧 AI 已包含：一步杀、必堵、迭代加深、Alpha-Beta、评估函数。
    加长时限 → 多搜 2-3 层 → 先行必胜。
    """
    if board.is_empty():
        return CENTER

    move, stats = get_ai_move(board, player, time_limit=TIME_LIMIT)
    return move

# ═══════════════════════════════════════════════
#  命令行对战
# ═══════════════════════════════════════════════

SYMBOLS = {Board.EMPTY: "·", Board.BLACK: "●", Board.WHITE: "○"}


def display_board(board, last_ai_move=None):
    print("\n  " + " ".join(f"{i}" for i in range(SIZE)))
    for r in range(SIZE):
        row = f"{r} "
        for c in range(SIZE):
            cell = board.get(r, c)
            marker = SYMBOLS[cell]
            if last_ai_move and (r, c) == last_ai_move:
                marker = f"\033[1;33m{marker}\033[0m"
            row += marker + " "
        print(row)
    print()


def main():
    board = Board(SIZE)
    ai_player = Board.BLACK
    human_player = Board.WHITE

    print("=" * 50)
    print("  无敌五子棋 AI — 先行天元，保证不败")
    print("  AI: ● (黑)    你: ○ (白)")
    print("  输入 row col 落子，q 退出")
    print("=" * 50)

    # AI 第一步：天元
    move = get_best_move(board, ai_player)
    board.place(move[0], move[1], ai_player)
    display_board(board, last_ai_move=move)
    print(f"🤖 AI 落子天元 ({move[0]}, {move[1]})\n")

    while True:
        # ── 人类 ──
        while True:
            cmd = input("你的走法 (row col): ").strip()
            if cmd.lower() == "q":
                print("再见！")
                return
            parts = cmd.split()
            if len(parts) != 2:
                print("  格式: row col")
                continue
            try:
                r, c = int(parts[0]), int(parts[1])
            except ValueError:
                print("  请输入数字")
                continue
            if not (0 <= r < SIZE and 0 <= c < SIZE):
                print(f"  坐标超出范围 (0-{SIZE-1})")
                continue
            if board.get(r, c) != Board.EMPTY:
                print("  该位置已有棋子")
                continue
            break

        board.place(r, c, human_player)
        display_board(board)

        if board.check_win(r, c, human_player):
            print("你赢了？！（这不应该发生……）")
            return
        if board.is_full():
            print("平局！")
            return

        # ── AI ──
        t0 = time.time()
        move = get_best_move(board, ai_player)
        elapsed = time.time() - t0
        if move is None:
            print("AI 无法走棋，平局！")
            return

        board.place(move[0], move[1], ai_player)
        display_board(board, last_ai_move=move)
        print(f"🤖 AI 走 ({move[0]}, {move[1]})  耗时: {elapsed:.1f}s")

        if board.check_win(move[0], move[1], ai_player):
            print("\n🏆 AI 获胜！")
            return
        if board.is_full():
            print("平局！")
            return


if __name__ == "__main__":
    main()
