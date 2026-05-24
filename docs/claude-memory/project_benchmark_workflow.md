---
name: project-benchmark-workflow
description: 外包估算 (outsource_benchmark_amount) 的真实业务录入流程 — 来自 vendor 真实询价
metadata: 
  node_type: memory
  type: project
  originSessionId: 911f86fc-f1cf-4968-be56-f9fd43df9a12
---

外包估算金额 (`Project.outsource_benchmark_amount`) **只来自真实 vendor 询价**。团队拿到询价单后才回填到项目里 — 不存在"凭经验估个数"的场景。

**Why:** 用户（[[user-role]] 团队负责人）2026-05-24 明确说："我们认为外包价格是来自于真实询价，寻到了才会填上去"。这个金额是 C 口径降本叙事 (`savings = bench − 团队入账`) 的核心，benchmark 越可信叙事越站得住，所以业务上有意只在拿到真实报价后才录入。

**How to apply:**
- 模型里 `outsource_benchmark_amount` 可空是正确的 — 没询到价就是空，不要加 NOT NULL 约束
- `benchmark_basis` 4 个选项中实操几乎只用 `vendor_quote`，但其它（historical_avg / industry_benchmark / manual_estimate）保留无害，不必砍
- UI 上「估算依据」字段当前是「填了金额才显示」的条件渲染，已符合业务流；不需要改成始终显示或强制必填
- 任何想加强护栏的建议（如"vendor_quote basis 必须附文件"）先确认有没有现实必要 — 业务已经默认只填真实询价，再加流程会冗余
