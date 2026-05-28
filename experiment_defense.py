"""
experiment_defense.py — 防守权重对弈实验
==========================================
让不同防守权重的 AI 与 baseline（权重 1.0）对弈，统计胜率。
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import evaluate as ev    # 可以改 ev.DEFENSE_WEIGHT
from board import Board
from search import get_ai_move, clear_tt


def play_one_game(black_weight: float, white_weight: float,
                  time_limit: float = 2.0, max_moves: int = 100) -> int:
    """
    对弈一局。返回：1=黑胜, 2=白胜, 0=平局
    """
    board = Board(9)

    for move_num in range(max_moves):
        if move_num % 2 == 0:
            ev.DEFENSE_WEIGHT = black_weight
            player = Board.BLACK
        else:
            ev.DEFENSE_WEIGHT = white_weight
            player = Board.WHITE

        move, _ = get_ai_move(board, player, time_limit)
        if move is None:
            return 0  # 平局
        r, c = move
        board.place(r, c, player)

        if board.check_win(r, c, player):
            return player
        if board.is_full():
            return 0

    return 0  # 超过步数限制算平局


def run_experiment(games_per_weight: int = 30):
    """
    跑完整实验：多组权重 vs baseline(1.0)
    """
    baseline = 1.0
    test_weights = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0]
    results = {}  # weight -> {black_win, white_win, draw, total}

    for w in test_weights:
        results[w] = {"black_win": 0, "white_win": 0, "draw": 0, "total": 0}

    total_games = len(test_weights) * games_per_weight
    played = 0

    for w in test_weights:
        # 测试权重 w 执黑 vs baseline 执白
        for _ in range(games_per_weight):
            clear_tt()
            result = play_one_game(w, baseline, time_limit=1.5)
            if result == Board.BLACK:
                results[w]["black_win"] += 1
            elif result == Board.WHITE:
                results[w]["white_win"] += 1
            else:
                results[w]["draw"] += 1
            results[w]["total"] += 1
            played += 1

        # 测试权重 w 执白 vs baseline 执黑
        for _ in range(games_per_weight):
            clear_tt()
            result = play_one_game(baseline, w, time_limit=1.5)
            if result == Board.BLACK:
                results[w]["black_win"] += 1
            elif result == Board.WHITE:
                results[w]["white_win"] += 1
            else:
                results[w]["draw"] += 1
            results[w]["total"] += 1
            played += 1

        print(f"  [{played}/{total_games}] 权重 {w:.1f} 完成")

    # 计算胜率
    summary = []
    for w in test_weights:
        r = results[w]
        total = r["total"]
        win_rate = (r["black_win"] + r["white_win"]) / total * 100
        draw_rate = r["draw"] / total * 100
        summary.append({
            "weight": w,
            "win_rate": win_rate,
            "draw_rate": draw_rate,
            "black_win": r["black_win"],
            "white_win": r["white_win"],
            "draw": r["draw"],
            "total": total,
        })
        print(f"    权重 {w:.1f}: 胜 {r['black_win']+r['white_win']}/{total} ({win_rate:.0f}%)  "
              f"平 {r['draw']}")

    return summary


def plot_results(summary):
    """绘制胜率 vs 防守权重图"""
    weights = [s["weight"] for s in summary]
    win_rates = [s["win_rate"] for s in summary]

    fig, ax = plt.subplots(figsize=(10, 6))

    # 柱状图
    colors = ["#e74c3c" if w < 1.0 else "#2ecc71" if w > 1.0 else "#3498db"
              for w in weights]
    bars = ax.bar([str(w) for w in weights], win_rates, color=colors,
                  width=0.5, edgecolor="gray", linewidth=1)

    # 标签
    for bar, val in zip(bars, win_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{val:.0f}%", ha="center", fontsize=11, fontweight="bold")

    # baseline 参考线
    baseline_idx = weights.index(1.0)
    ax.axhline(y=50, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.text(max(weights) + 0.1, 50, "50% (平手)", va="center", fontsize=10, color="gray")

    ax.set_xlabel("防守权重", fontsize=13)
    ax.set_ylabel("胜率 (%)", fontsize=13)
    ax.set_title("防守权重 vs AI 棋力 (对 baseline 权重 1.0)", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig("gomoku-ai/assets/fig_defense_experiment.png", dpi=150)
    print(f"\n[OK] 图表已保存: assets/fig_defense_experiment.png")


def print_markdown_table(summary):
    """输出 Markdown 表格（可直接复制到实验报告）"""
    print("\n\n## 防守权重对弈实验结果\n")
    print(f"| 防守权重 | 胜 | 负 | 平 | 总场次 | 胜率 |")
    print(f"|:-------:|:--:|:--:|:--:|:-----:|:----:|")
    for s in summary:
        w, wr = s["weight"], s["win_rate"]
        total = s["total"]
        wins = s["black_win"] + s["white_win"]
        losses = total - wins - s["draw"]
        draws = s["draw"]
        print(f"| {w:.1f} | {wins} | {losses} | {draws} | {total} | {wr:.0f}% |")


if __name__ == "__main__":
    print("=" * 50)
    print("  防守权重对弈实验")
    print("  每个权重 × 60 局（先手+后手各30）")
    print("  baseline = 权重 1.0")
    print("=" * 50)

    summary = run_experiment(games_per_weight=30)

    plot_results(summary)
    print_markdown_table(summary)
