---
name: project-no-revenue-opportunity-cost
description: 口径 B 把 no_revenue 项目按机会成本（= outsource_benchmark）计入每销售/每客户利润视图
metadata: 
  node_type: memory
  type: project
  originSessionId: 911f86fc-f1cf-4968-be56-f9fd43df9a12
---

口径 B（`/profit/per-project` + 每销售利润 + 每客户利润 两个 admin 视图）**包含 no_revenue 项目**，规则：
- `revenue = 0`
- `cost = Project.outsource_benchmark_amount`（外部服务商报价当机会成本）
- `margin = -benchmark`（负值，反映「这个项目吃掉了多少预期外包成本」）

revenue 项目继续按原规则：`revenue = Σ ProjectRevenue.amount`，`cost = Σ VSF`。

**Why:** 用户（[[user-role]] 团队负责人）2026-05-24 明确："允许工程师在没收到钱时就给销售提供服务，所以会出现项目丢单或明确无收入但成本仍要守住的情况，这种成本 = 新增项目里的外部服务商报价"。pre-sales / 内部咨询 / 丢标后已投入的工时本来就是真实消耗，不能因为「没收入」就在销售/客户利润表里隐藏掉。之前的实现一刀切 `WHERE kind=revenue` 把这些项目排除在 B 口径外，导致销售/客户毛利**虚高**。

**How to apply:**
- 任何动 [[compute_per_project]] 或它的两个 group-by 衍生 (`compute_by_sales_person` / `compute_by_need_party`) 的改动，都要保留 no_revenue 分支；不能简单恢复 `WHERE kind=revenue`
- 口径 A team_margin（`compute_overall`）和口径 C savings（`compute_cockpit_savings_and_value`）**不要应用同一规则** — 用户明确只勾了 B 两页作为影响范围
- 前端 `ByClientView.vue` 和 `BySalesView.vue` 子表的「项目」列必须保留「无收入」黄色 tag，让用户看到为什么这个项目 margin 是负的
- 接口 `ProjectMarginRow` 必须保留 `kind` 字段，前端依赖它显示 tag
- benchmark 为空的 no_revenue 项目 → cost=0、margin=0，会在表里出现 0 行 — 这是可接受的行为（[[project-benchmark-workflow]] 里说 benchmark 必须真实询价才填，没询价就空）
