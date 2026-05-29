"""口径 A 团队真实利润公式锁定测试。

⛔ 业务约束（2026-05-28 Akiva final 确认）：
    team_margin = Σ VSF − Σ 全部支出（vendor markup 视角）
    （README §1.4 pass-through 模型）

如果这个测试 fail，说明有人改了 compute_overall 的公式。**fail 后绝对不要"修测试"**——
找 git blame 看是谁动的，跟 Akiva 反复确认是不是真的要改业务模型。
历史教训：曾被错误改成 revenue − VSF − expenses，违反 pass-through 假设。
"""
import inspect

from app.services import profit
from app.services.profit import compute_overall


def test_compute_overall_formula_locked() -> None:
    """锁定 compute_overall 的核心计算行：margin = fees_d - exp_d"""
    src = inspect.getsource(compute_overall)

    # 核心公式必须存在
    assert "margin = fees_d - exp_d" in src, (
        "compute_overall 的核心公式被改了。"
        "正确公式：margin = fees_d - exp_d（vendor markup 视角，VSF − 全部支出）。"
        "改前请反复跟 Akiva 确认 ≥ 3 次。"
    )

    # 防止退化成"常规公司"模型
    forbidden_formulas = [
        "revenue_d - fees_d - exp_d",      # revenue − VSF − expenses 的错误退化
        "revenue_d -fees_d -exp_d",        # 同上压缩空格
        "margin = revenue_d -",            # 任何 margin 直接从 revenue 减起的公式
    ]
    for bad in forbidden_formulas:
        assert bad not in src, (
            f"检测到错误公式片段 `{bad}`。"
            "口径 A 的团队真实利润 = vendor markup = VSF − 全部支出，"
            "不是 revenue − VSF − expenses。"
            "如果业务模型真的变了，请 Akiva 确认后同步更新 README §1.4 / §1.5 / PLAN.md。"
        )


def test_compute_overall_warning_block_intact() -> None:
    """⛔ WARNING 注释块必须完整。删掉就 fail。"""
    src = inspect.getsource(compute_overall)
    required_markers = [
        "⛔ 业务公式锁定",
        "pass-through invariant",
        "反复跟 Akiva 确认",
        "vendor markup 视角",
    ]
    missing = [m for m in required_markers if m not in src]
    assert not missing, (
        f"compute_overall 的 WARNING 注释块缺失关键标记: {missing}。"
        "不要删 WARNING——它是给未来 reviewer / Claude / 自己看的护栏。"
    )


def test_module_imports_intact() -> None:
    """确认相关常量/函数没被 rename 走"""
    assert hasattr(profit, "compute_overall")
    assert hasattr(profit, "EXPENSE_STATUS_PAID")
