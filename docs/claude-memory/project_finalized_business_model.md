---
name: project-finalized-business-model
description: 2026-05-24 用户校准后的最终业务模型 - 资金流 4 字段 / 公司毛利率公式 / 典型比例
metadata: 
  node_type: memory
  type: project
  originSessionId: 911f86fc-f1cf-4968-be56-f9fd43df9a12
---

业务模型在 2026-05-24 经过用户多轮校准后定稿。**改任何金额公式或 seed 数据前，必看 [README §1.7](README.md#17-业务模型最终态v04--2026-05-24-用户多轮确认后定稿)**。

## 资金流 4 字段

```
客户 → 公司 → 团队入账 → Vendor (100% pass-through)
gross_amount → non_service_expense + amount (≈ VSF) + 公司毛利
```

ProjectRevenue 表 4 个必填金额：
- `gross_amount` — 客户付款总额（销售切除前）
- `non_service_expense` — 非服务开销（硬件/第三方/物料）
- `amount` — 团队入账（= 转给 vendor 的钱 ≈ VSF）
- 缺一不可（前端已强制必填）

## 典型比例（seed 数据按此校准）

| 字段 | 占 gross 比例 |
|---|---|
| 非服务开销 | **65-75%** |
| 团队入账 | **~20%** |
| 公司毛利 | ~5-15% |
| 团队入账 / 服务商价格 | 0.80-0.90（FDE 比外包便宜 10-20%） |
| VSF / 团队入账 | ≈ 1.0（100% pass-through ±1%） |

## 公司毛利率公式（仅 admin lead/finance/admin 可见）

```
老外包模式毛利率 = (gross − benchmark − non_service_expense) / gross
FDE 模式毛利率   = (gross − amount    − non_service_expense) / gross
利润率提升       = FDE − 老外包 = (benchmark − amount) / gross
多挣 (extra_profit) = Σ benchmark − Σ amount
```

典型数字：老外包 ~6%，FDE ~10%，提升 +3-5 个百分点（行业典型 FDE vs 外包 benchmark）。

## 驾驶舱 C 口径 savings（cockpit 唯一允许的金额叙事）

- revenue 项目 (bid_outcome=won)：`savings = benchmark − Σ amount`
- no_revenue 项目 (status ∈ {closing,archived})：`value_created = benchmark`
- `total_c_view = Σ savings + Σ value_created`

## 投标结果 bid_outcome（决定哪些项目计入 C 口径）

- `won` — 唯一计入 C-tier 的状态；默认中标 = 团队拿到 team_revenue
- `pending` / `lost` / `escaped` — 不计入
- no_revenue 项目不适用（UI 显示 NA）

## 几个不要踩的坑

1. **不要把 ProjectRevenue.status 重新引入** — UI 已移除，DB column 保留是历史包袱
2. **改 compute_per_project 不能恢复 `WHERE kind=revenue`** — no_revenue 项目要在 B 口径里按 benchmark 算机会成本，见 [[project-no-revenue-opportunity-cost]]
3. **不要用 `_project_costs`（含 6 类支出）算 C 口径或 admin margin_lift** — 6 类已含在 VSF 内，用 `_project_vsf` 即可
4. **benchmark 永远来自真实询价**，没询价就空，不要瞎填，见 [[project-benchmark-workflow]]
5. **cert_level 是 L1-L3**，不是 L1-L5（之前砍过）

## 当前 enum 取值（已收缩，不要扩）

| 字段 | 取值 |
|---|---|
| `bid_outcome` | pending / won / lost / escaped |
| `Project.status` | drafting / in_progress / accepting / closing / archived / cancelled |
| `value_created_basis` | outsource_equiv / other |
| `benchmark_basis` | vendor_quote / historical_avg |
| `cert_level` | L1 / L2 / L3 |
