# Data Schema

Phase 0 — 仅落实 User / DataDict 两张表。
Phase 1+ — 按 [PLAN §5](../PLAN.md#5-数据模型核心实体简版) 逐步建表 + Alembic 迁移。

## 现有表

### `users`
系统操作员账号。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int PK | |
| username | string(64) | unique |
| full_name | string(128) | |
| email | string(128) | unique |
| hashed_password | string(255) | bcrypt |
| role | string(32) | admin/lead/pm/finance/engineer |
| is_active | bool | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `data_dict`
通用数据字典 — 技能/岗位/支出类型/项目阶段等。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int PK | |
| category | string(64) | 字典分类（如 `skill`, `expense_type`） |
| code | string(64) | 字典项编码 |
| label | string(128) | 显示名称 |
| sort_order | int | |
| is_active | bool | |
| created_at | timestamptz | |

唯一约束：`(category, code)`
