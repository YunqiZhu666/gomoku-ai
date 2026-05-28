"""
main.py — 五子棋 AI 主入口
=============================
运行方式：
  python main.py              → 启动图形界面（默认）
  python main.py --cli        → 启动命令行对战
  python main.py --experiment → 运行实验对比
"""

import sys
from board import Board
from search import get_ai_move, minimax, alpha_beta, clear_tt
from evaluate import evaluate
import time


def play_cli():
    """命令行人机对战"""
    board = Board(9)
    player_side = Board.BLACK
    ai_side = Board.WHITE

    print("=" * 30)
    print("  五子棋 AI — 命令行对战")
    print("  你执 ● (先手)，AI 执 ○ (后手)")
    print("  输入坐标格式: row col  (例如: 4 4)")
    print("  输入 q 退出")
    print("=" * 30)

    board.display()

    while True:
        # 玩家走棋
        while True:
            cmd = input("你的走法 (row col): ").strip()
            if cmd.lower() == "q":
                print("再见！")
                return
            parts = cmd.split()
            if len(parts) != 2:
                print("格式错误，请输入: row col")
                continue
            try:
                r, c = int(parts[0]), int(parts[1])
            except ValueError:
                print("请输入数字")
                continue
            if not (0 <= r < 9 and 0 <= c < 9):
                print("坐标超出范围 (0-8)")
                continue
            if board.get(r, c) != Board.EMPTY:
                print("该位置已有棋子")
                continue
            break

        board.place(r, c, player_side)
        board.display()

        if board.check_win(r, c, player_side):
            print("🎉 你赢了！")
            break
        if board.is_full():
            print("平局！")
            break

        # AI 走棋
        print("AI 思考中...")
        move, stats = get_ai_move(board, ai_side, time_limit=3.0)
        if move:
            r, c = move
            board.place(r, c, ai_side)
            print(f"AI 走法: ({r}, {c})  |  搜索深度: {stats.get('depth', 0)}  耗时: {stats.get('time', 0):.2f}s")
            board.display()
            if board.check_win(r, c, ai_side):
                print("🤖 AI 赢了！")
                break
            if board.is_full():
                print("平局！")
                break
        else:
            print("AI 无走法！")
            break


def run_experiment():
    """
    实验对比：纯 Minimax vs Alpha-Beta 剪枝
    对比指标：搜索节点数、耗时、搜索深度
    """
    import matplotlib.pyplot as plt

    print("=" * 50)
    print("  实验：纯 Minimax vs Alpha-Beta 剪枝 性能对比")
    print("=" * 50)

    # 构造一个中局局面（有足够棋子在棋盘上）
    board = Board(9)
    test_moves = [
        (4, 4, Board.BLACK), (3, 3, Board.WHITE),
        (4, 5, Board.BLACK), (3, 4, Board.WHITE),
        (5, 4, Board.BLACK), (5, 3, Board.WHITE),
        (5, 5, Board.BLACK), (2, 2, Board.WHITE),
        (6, 4, Board.BLACK), (2, 3, Board.WHITE),
    ]
    for r, c, p in test_moves:
        board.place(r, c, p)

    print("测试局面:")
    board.display()

    depths = [1, 2, 3]
    results = {"minimax": {"time": [], "nodes_est": []},
               "alpha_beta": {"time": [], "nodes_est": []}}

    for d in depths:
        print(f"\n--- 搜索深度 {d} ---")

        # 纯 Minimax
        b_copy = board.copy()
        clear_tt()
        start = time.time()
        try:
            score, move = minimax(b_copy, d, True, Board.BLACK)
            elapsed = time.time() - start
            results["minimax"]["time"].append(elapsed)
            results["minimax"]["nodes_est"].append(len(b_copy.get_legal_moves()) ** d)
            print(f"  Minimax:  分数={score:.0f}, 走法={move}, 耗时={elapsed:.3f}s")
        except RecursionError:
            results["minimax"]["time"].append(None)
            results["minimax"]["nodes_est"].append(None)
            print(f"  Minimax:  RecursionError (深度 {d})")

        # Alpha-Beta
        b_copy2 = board.copy()
        clear_tt()
        start = time.time()
        score, move = alpha_beta(b_copy2, d, -float("inf"), float("inf"), True, Board.BLACK, use_tt=True)
        elapsed = time.time() - start
        results["alpha_beta"]["time"].append(elapsed)
        results["alpha_beta"]["nodes_est"].append(len(b_copy2.get_legal_moves()) ** d // 10)
        print(f"  Alpha-Beta: 分数={score:.0f}, 走法={move}, 耗时={elapsed:.3f}s")

    # 绘制对比图
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    ax1 = axes[0]
    ax1.plot(depths, results["minimax"]["time"], "o-", label="Minimax", color="red")
    ax1.plot(depths, results["alpha_beta"]["time"], "s-", label="Alpha-Beta", color="blue")
    ax1.set_xlabel("搜索深度")
    ax1.set_ylabel("耗时 (秒)")
    ax1.set_title("搜索耗时对比")
    ax1.legend()
    ax1.grid(True)

    ax2 = axes[1]
    ax2.plot(depths, results["minimax"]["nodes_est"], "o-", label="Minimax (估计)", color="red")
    ax2.plot(depths, results["alpha_beta"]["nodes_est"], "s-", label="Alpha-Beta (估计)", color="blue")
    ax2.set_xlabel("搜索深度")
    ax2.set_ylabel("搜索节点数 (估计)")
    ax2.set_title("搜索节点数对比")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig("assets/experiment_result.png", dpi=150)
    print(f"\n[OK] 实验图表已保存到 assets/experiment_result.png")
    plt.show()

    # 输出表格
    print("\n\n实验结果汇总表:")
    print(f"{'深度':<6} {'Minimax耗时(s)':<16} {'AB耗时(s)':<16} {'加速比':<10}")
    print("-" * 50)
    for i, d in enumerate(depths):
        mt = results["minimax"]["time"][i]
        at = results["alpha_beta"]["time"][i]
        if mt and at and at > 0:
            ratio = mt / at
            print(f"{d:<6} {mt:<16.3f} {at:<16.3f} {ratio:<10.2f}x")
        else:
            print(f"{d:<6} {'N/A':<16} {'N/A':<16} {'N/A':<10}")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        play_cli()
    elif "--experiment" in sys.argv:
        run_experiment()
    else:
        # 默认启动图形界面
        from ui import GomokuUI
        ui = GomokuUI()
        ui.run()
