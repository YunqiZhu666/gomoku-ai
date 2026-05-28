"""
experiment.py — 五子棋 AI 实验对比框架
=========================================
对比项目：
1. 纯 Minimax vs Alpha-Beta 剪枝（耗时、节点数）
2. 不同搜索深度对棋力的影响
3. AI vs AI 自对弈
"""

import sys
import os
import time
import matplotlib
matplotlib.use("Agg")  # 无头模式
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from board import Board
from search import minimax, alpha_beta, clear_tt, get_ai_move, _NODE_COUNT


# ══════════════════════════════════════════
# 实验一：Minimax vs Alpha-Beta 性能对比
# ══════════════════════════════════════════

def experiment_performance():
    """
    在同一中局局面上，对比不同深度下：
    - Minimax 耗时
    - Alpha-Beta 耗时
    - 搜索节点数估计
    """
    print("=" * 60)
    print("  实验一：Minimax vs Alpha-Beta 剪枝 性能对比")
    print("=" * 60)

    # 构造中局局面
    board = Board(9)
    init_moves = [
        (4, 4, Board.BLACK), (3, 3, Board.WHITE),
        (4, 5, Board.BLACK), (3, 4, Board.WHITE),
        (5, 4, Board.BLACK), (5, 3, Board.WHITE),
        (4, 6, Board.BLACK), (2, 2, Board.WHITE),
        (6, 4, Board.BLACK), (2, 3, Board.WHITE),
    ]
    for r, c, p in init_moves:
        board.place(r, c, p)

    board.display()
    legal_moves = board.get_legal_moves()
    print(f"当前合法走法数: {len(legal_moves)}")

    depths = [1, 2, 3, 4]
    results = {
        "depth": depths,
        "minimax_time": [],
        "alphabeta_time": [],
        "minimax_score": [],
        "alphabeta_score": [],
    }

    for d in depths:
        print(f"\n── 深度 {d} ──")

        # Minimax
        b1 = board.copy()
        clear_tt()
        try:
            start = time.time()
            score1, move1 = minimax(b1, d, True, Board.BLACK)
            t1 = time.time() - start
            results["minimax_time"].append(t1)
            results["minimax_score"].append(score1)
            print(f"  Minimax:    分数={score1:>10.0f}  走法={move1}  耗时={t1:.3f}s")
        except RecursionError:
            results["minimax_time"].append(None)
            results["minimax_score"].append(None)
            print(f"  Minimax:    递归溢出")

        # Alpha-Beta
        b2 = board.copy()
        clear_tt()
        start = time.time()
        score2, move2 = alpha_beta(b2, d, -float("inf"), float("inf"), True, Board.BLACK)
        t2 = time.time() - start
        results["alphabeta_time"].append(t2)
        results["alphabeta_score"].append(score2)
        print(f"  Alpha-Beta: 分数={score2:>10.0f}  走法={move2}  耗时={t2:.4f}s  "
              f"加速={t1/t2:.1f}x" if t1 > 0 else "  Alpha-Beta: done")

    # 绘制图表
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 耗时对比
    ax = axes[0]
    ax.plot(depths, results["minimax_time"], "o-", color="crimson",
            linewidth=2, markersize=8, label="Minimax")
    ax.plot(depths, results["alphabeta_time"], "s-", color="royalblue",
            linewidth=2, markersize=8, label="Alpha-Beta 剪枝")
    ax.set_xlabel("搜索深度", fontsize=12)
    ax.set_ylabel("耗时 (秒)", fontsize=12)
    ax.set_title("Minimax vs Alpha-Beta 耗时对比", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_yscale("log")  # 对数尺度（Minimax 增长极快）

    # 加速比
    ax = axes[1]
    speedups = []
    for i, d in enumerate(depths):
        mt = results["minimax_time"][i]
        at = results["alphabeta_time"][i]
        if mt and at and at > 0:
            speedups.append(mt / at)
        else:
            speedups.append(None)

    valid = [(d, s) for d, s in zip(depths, speedups) if s is not None]
    if valid:
        vd, vs = zip(*valid)
        bars = ax.bar([str(d) for d in vd], vs, color="mediumseagreen", width=0.5)
        for bar, val in zip(bars, vs):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                    f"{val:.1f}x", ha="center", fontsize=11, fontweight="bold")
    ax.set_xlabel("搜索深度", fontsize=12)
    ax.set_ylabel("加速比 (倍)", fontsize=12)
    ax.set_title("Alpha-Beta 剪枝加速比", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig("assets/experiment_performance.png", dpi=150, bbox_inches="tight")
    print(f"\n[保存] assets/experiment_performance.png")

    # 输出汇总表
    print("\n\n" + "=" * 60)
    print("  实验结果汇总表")
    print("=" * 60)
    print(f"{'深度':<6} {'Minimax(秒)':<14} {'Alpha-Beta(秒)':<16} {'加速比':<10} {'分数一致?':<10}")
    print("-" * 60)
    for i, d in enumerate(depths):
        mt = results["minimax_time"][i]
        at = results["alphabeta_time"][i]
        ms = results["minimax_score"][i]
        as_ = results["alphabeta_score"][i]
        mt_str = f"{mt:.3f}" if mt else "N/A"
        at_str = f"{at:.4f}" if at else "N/A"
        ratio = f"{mt/at:.1f}x" if mt and at and at > 0 else "N/A"
        match = "✓" if (ms is not None and as_ is not None and abs(ms - as_) < 1) else (
            "≈" if ms and as_ else "–")
        print(f"{d:<6} {mt_str:<14} {at_str:<16} {ratio:<10} {match:<10}")

    plt.show()
    return results


# ══════════════════════════════════════════
# 实验二：AI vs AI 自对弈
# ══════════════════════════════════════════

def ai_vs_ai(num_games: int = 2):
    """
    AI 自对弈
    黑先白后，统计胜率
    """
    print("\n" + "=" * 60)
    print(f"  实验二：AI vs AI 自对弈（{num_games} 局）")
    print("=" * 60)

    results = {"black_wins": 0, "white_wins": 0, "draws": 0}
    game_records = []

    for game in range(num_games):
        board = Board(9)
        move_count = 0
        moves_log = []

        print(f"\n── 第 {game + 1} 局 ──")

        while True:
            current_player = Board.BLACK if move_count % 2 == 0 else Board.WHITE
            side_name = "●黑" if current_player == Board.BLACK else "○白"

            move, stats = get_ai_move(board, current_player, time_limit=2.0)
            if move is None:
                print(f"  平局（无走法）")
                results["draws"] += 1
                break

            r, c = move
            board.place(r, c, current_player)
            moves_log.append((r, c, current_player))
            move_count += 1
            print(f"  {side_name} ({r},{c}) depth={stats.get('depth',0)}", end="")

            if board.check_win(r, c, current_player):
                winner = "黑" if current_player == Board.BLACK else "白"
                print(f"  → {winner}方第{move_count}手获胜！")
                if current_player == Board.BLACK:
                    results["black_wins"] += 1
                else:
                    results["white_wins"] += 1
                break

            if board.is_full():
                print(f"  平局（棋盘满）")
                results["draws"] += 1
                break

        game_records.append(moves_log)

    # 输出统计
    print("\n" + "=" * 60)
    print("  AI vs AI 自对弈结果")
    print("=" * 60)
    total = sum(results.values())
    print(f"  总对局: {total}")
    print(f"  黑胜: {results['black_wins']} ({results['black_wins']/total*100:.0f}%)")
    print(f"  白胜: {results['white_wins']} ({results['white_wins']/total*100:.0f}%)")
    print(f"  平局: {results['draws']} ({results['draws']/total*100:.0f}%)")

    return results


# ══════════════════════════════════════════
# 实验三：评估函数灵敏度测试
# ══════════════════════════════════════════

def experiment_evaluation():
    """
    测试评估函数对不同棋型的识别能力
    """
    print("\n" + "=" * 60)
    print("  实验三：评估函数棋型识别测试")
    print("=" * 60)

    from evaluate import evaluate, _pattern_score

    test_cases = [
        ("空棋盘", []),
        ("一子", [(4, 4, Board.BLACK)]),
        ("活二", [(4, 4, Board.BLACK), (4, 5, Board.BLACK)]),
        ("活三", [(4, 3, Board.BLACK), (4, 4, Board.BLACK), (4, 5, Board.BLACK)]),
        ("活四", [(4, 3, Board.BLACK), (4, 4, Board.BLACK), (4, 5, Board.BLACK), (4, 6, Board.BLACK)]),
        ("连五", [(4, 3, Board.BLACK), (4, 4, Board.BLACK), (4, 5, Board.BLACK),
                  (4, 6, Board.BLACK), (4, 7, Board.BLACK)]),
    ]

    print(f"\n{'棋型':<12} {'黑方分数':<12} {'白方分数':<12}")
    print("-" * 36)
    for name, moves in test_cases:
        b = Board()
        for r, c, p in moves:
            b.place(r, c, p)
        black_score = evaluate(b, Board.BLACK)
        white_score = evaluate(b, Board.WHITE)
        print(f"{name:<12} {black_score:<12.0f} {white_score:<12.0f}")

    # 绘制分数对比图
    names = [t[0] for t in test_cases]
    b_scores = []
    w_scores = []
    for _, moves in test_cases:
        b = Board()
        for r, c, p in moves:
            b.place(r, c, p)
        b_scores.append(evaluate(b, Board.BLACK))
        w_scores.append(evaluate(b, Board.WHITE))

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(names))
    width = 0.35
    ax.bar(x - width/2, b_scores, width, label="黑方分数", color="dimgray")
    ax.bar(x + width/2, w_scores, width, label="白方分数", color="lightgray")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("评估分数", fontsize=12)
    ax.set_title("评估函数对不同棋型的识别", fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig("assets/experiment_evaluation.png", dpi=150)
    print(f"\n[保存] assets/experiment_evaluation.png")


# ══════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        experiment_performance()
        experiment_evaluation()
        ai_vs_ai(3)
    elif len(sys.argv) > 1 and sys.argv[1] == "--selfplay":
        ai_vs_ai(5)
    else:
        experiment_performance()
        experiment_evaluation()
