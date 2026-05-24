# Claude Code 自动记忆 — 快照

这是 Claude Code 跨对话理解本项目的关键上下文文件，复制自：

```
~/.claude/projects/-Users-akivagong-projects-Manpower-management-platform/memory/
```

**冻结时间**：2026-05-24（v0.6-beta 锁版同期）

## 文件说明

- [MEMORY.md](MEMORY.md) — 索引，Claude 每次会话开头加载
- [user_role.md](user_role.md) — 你（中国电信国际香港分公司工程师团队负责人）的身份和视角
- [project_background.md](project_background.md) — 甲方视角的外包工程师内化管理平台背景
- [project_finalized_business_model.md](project_finalized_business_model.md) — **业务模型定稿**（资金流 4 字段 + 公司毛利率公式 + 典型比例）⭐
- [project_benchmark_workflow.md](project_benchmark_workflow.md) — 外包估算录入流程（benchmark 只来自真实 vendor 询价）
- [project_no_revenue_opportunity_cost.md](project_no_revenue_opportunity_cost.md) — no_revenue 机会成本口径 B 说明

## 这份快照的用途

- **本地备份**：换电脑 / 重装系统时，把这 6 个文件复制回 `~/.claude/projects/.../memory/` 即可恢复 Claude 的全部上下文记忆
- **环境迁移**：天翼云上的 Claude 实例若想读到同样的上下文，把这些文件放到对应路径
- **审计追溯**：未来业务模型再改时，可以回查这版的定稿口径

## 注意

Claude 运行时仍从 `~/.claude/...` home 路径读，不读这里的副本。这里只是「源文件的快照」。
源文件会随对话持续更新；如要刷新此快照，重新执行 `cp` 即可。
