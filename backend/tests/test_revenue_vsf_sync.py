"""ProjectRevenue → VSF 镜像同步锁定测试。

⛔ pass-through 不变量（2026-05-28 Akiva 锁定）：
    每笔 ProjectRevenue 都同步一笔等额 VSF 镜像（同 project + 同 vendor + 同 amount）。
    create/update/delete 必须维护这个不变量。

如果这个测试 fail，说明有人改了 project_revenues.py 的 hook 逻辑（或 model）。
**fail 后绝对不要"修测试让它过"**——找 git blame，跟 Akiva 反复确认。
"""
import inspect

from app.api.admin import project_revenues
from app.api.admin.project_revenues import (
    MIRROR_DESC,
    _create_mirror_vsf,
    _find_mirror_vsf,
    create_revenue,
    delete_revenue,
    update_revenue,
)


def test_mirror_helpers_exist() -> None:
    """同步 hook 的 3 个 helper 必须存在并被 endpoint 调用。"""
    create_src = inspect.getsource(create_revenue)
    update_src = inspect.getsource(update_revenue)
    delete_src = inspect.getsource(delete_revenue)

    # create endpoint 必须建镜像
    assert "_create_mirror_vsf" in create_src, "create_revenue 必须调 _create_mirror_vsf 建 VSF 镜像"

    # update endpoint 必须先删旧镜像再建新镜像（处理 vendor / amount / date 改动）
    assert "_find_mirror_vsf" in update_src, "update_revenue 必须先找老 VSF 镜像"
    assert "_create_mirror_vsf" in update_src, "update_revenue 必须重建新 VSF 镜像"

    # delete endpoint 必须删镜像
    assert "_find_mirror_vsf" in delete_src, "delete_revenue 必须找镜像 VSF"
    assert "db.delete" in delete_src, "delete_revenue 必须删 ProjectRevenue 和镜像 VSF"


def test_mirror_marker_string_stable() -> None:
    """MIRROR_DESC 是识别镜像 VSF 的 key——不能随便改。
    如果改了，迁移脚本和现有 _find_mirror_vsf 都会拿不到镜像，导致脏数据。
    """
    assert MIRROR_DESC == "自动镜像自 ProjectRevenue (pass-through)", (
        "MIRROR_DESC 标识不能改。如必须改，要同时更新 migration s9t0u1v2w3x4 和 _find_mirror_vsf。"
    )


def test_vendor_id_is_required_on_revenue() -> None:
    """ProjectRevenueBase.vendor_id 必须是必填（不是 Optional）。"""
    from app.schemas.project_revenue import ProjectRevenueBase

    fields = ProjectRevenueBase.model_fields
    assert "vendor_id" in fields, "ProjectRevenueBase 必须有 vendor_id 字段"
    assert fields["vendor_id"].is_required(), (
        "vendor_id 必须是必填——pass-through 模型每笔收入都得明确流向哪家 vendor。"
    )


def test_module_constants_intact() -> None:
    """关键常量/函数名稳定."""
    assert hasattr(project_revenues, "MIRROR_DESC")
    assert hasattr(project_revenues, "_create_mirror_vsf")
    assert hasattr(project_revenues, "_find_mirror_vsf")
