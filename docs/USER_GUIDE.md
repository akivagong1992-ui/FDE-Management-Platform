# FDE 管理系统 · 用户手册（v0.6 beta）

> 适用版本：v0.6-beta（2026-05-24 freeze）
> 编写对象：管理后台用户 + 工程师端用户 + 驾驶舱观看者
> 配套文档：[README.md](../README.md) 业务定位 · [PLAN.md](../PLAN.md) 开发阶段 · [docs/deployment.md](deployment.md) 部署

---

## 目录

1. [系统总览](#1-系统总览)
2. [用户角色与权限矩阵](#2-用户角色与权限矩阵)
3. [业务模型与核心公式](#3-业务模型与核心公式)
4. [管理后台模块](#4-管理后台模块) — 10 个 sidebar 模块逐一说明
5. [工程师端门户](#5-工程师端门户)
6. [驾驶舱（大屏）](#6-驾驶舱大屏)
7. [关键业务流程](#7-关键业务流程)
8. [常见 FAQ](#8-常见-faq)
9. [部署与运维要点](#9-部署与运维要点)

---

## 1. 系统总览

**定位**：中国电信国际香港分公司 · FDE（Field Delivery Engineer）团队的外包工程师**内化管理平台**。把"外包给 vendor 服务"的传统模式，转成"团队自管派工 + 数据沉淀 + 驾驶舱给老板看"。

**三个前端**：

| 端 | 地址（dev） | 给谁看 | 主要功能 |
|---|---|---|---|
| 管理后台（admin-web） | http://localhost:5173 | admin / lead / pm / finance / engineer / vendor 6 类用户 | 录入 + 审批 + 看报表 |
| 工程师门户（同一 admin-web，按角色裁剪） | http://localhost:5173 | engineer 角色 | 只能看「我的派单 / 工时 / 支出」 |
| 驾驶舱（cockpit-screen） | http://localhost:5174 | 老板、客户来访演示 | 5 个 Tab 大屏，**永不展示团队真实利润** |

**默认账号**（seed_demo 创建）：

| 用户名 | 密码 | 角色 |
|---|---|---|
| `admin` | `admin123` | lead（团队负责人，看全部） |
| `finance` | `fin123` | finance |
| `pm1` | `pm123` | pm |
| `eng1` | `eng123` | engineer |
| `v1`～`v4` | `demo123` | vendor（各对应一家 vendor 公司） |

驾驶舱访问需要带 `X-Cockpit-Token: cockpit-dev-token` 头（默认前端已带）。

---

## 2. 用户角色与权限矩阵

系统有 **6 个角色**：

| 角色 | 中文 | 主要职责 | 关联实体 |
|---|---|---|---|
| `admin` | 超级管理员 | 全权限，仅一个内部账号 | — |
| `lead` | 团队负责人 | 看全部利润、改业务策略 | — |
| `pm` | 项目经理 | 立项、派单、改项目、审支出（不看利润） | — |
| `finance` | 财务 | 审支出、看利润、出报表 | — |
| `engineer` | 基层工程师 | 看自己派单、提工时、申支出 | `User.engineer_id → engineers` |
| `vendor` | Vendor 公司联系人 | 提交 vendor 名下支出（不审批） | `User.vendor_id → vendors` |

### 2.1 模块访问权限

| 模块 | admin | lead | pm | finance | engineer | vendor |
|---|---|---|---|---|---|---|
| 首页 | ✅ | ✅ | ✅ | ✅ | ✅（精简） | ❌（直接落 /expense） |
| 项目和客户管理 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 派单和工时管理 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 利润管理 | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| 成本和支出管理（看全部 + 审批） | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 成本和支出管理（**只看本 vendor 的，只能提交**） | — | — | — | — | — | ✅ |
| 项目效率管理 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| FDE 知识库 | ✅ | ✅ | ✅ | ✅ | ✅（不看机密项） | ❌ |
| 培训管理 | ✅ | ✅ | ✅ | ✅（独占看成本字段） | ❌ | ❌ |
| 关键项目复盘管理 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 系统设置 · 用户 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 我的派单 / 工时 / 支出申请 | — | — | — | — | ✅ | ❌ |

### 2.2 敏感字段权限

| 字段 | 看得到的角色 |
|---|---|
| 工程师月服务费 `monthly_cost_to_telecom` | admin / lead / finance |
| 证件号明文（解密 + 审计日志） | admin / lead |
| 项目「团队真实利润」 | admin / lead / finance |
| 培训记录的「成本」字段 | admin / lead / finance |
| 知识资产 confidential 级 | admin / lead / pm / finance |

### 2.3 关键操作权限

| 操作 | 谁能做 |
|---|---|
| 创建 / 切换 `no_revenue` 项目 | 仅 admin / lead |
| 转移销售归属（生成 SalesTransferLog） | 仅 admin / lead |
| 删除项目 / 用户 / vendor | 仅 admin / lead |
| 创建支出申请 | engineer（自己提）/ vendor（vendor 端提）/ pm（代提） |
| 审批支出（approve / reject / mark paid） | admin / lead / finance |
| 创建 vendor 用户 + 绑定 vendor_id | 仅 admin |

---

## 3. 业务模型与核心公式

> ⚠️ 本节是整个系统的「灵魂」，**业务模型若改要先改这里**。已 freeze 状态见 [README §1.7](../README.md#17)。

### 3.1 资金流：4 个核心字段

每个有收入项目都有 4 个数字：

| 字段 | 中文 | 数据库位置 | 谁录入 |
|---|---|---|---|
| `gross_amount` | 客户付款（含税总价） | `project_revenues.gross_amount` | finance 收款时填 |
| `non_service_expense` | 非服务开销（硬件 / 软件 / 通行费等） | `project_revenues.non_service_expense` | finance 录入 |
| `amount`（team_revenue） | 团队入账 | `project_revenues.amount` | finance 录入 |
| `outsource_benchmark_amount` | 外包估算（如果走老外包要多少） | `projects.outsource_benchmark_amount` | sales 立项时填，**只能填真实 vendor 询价** |

**典型比例**（每笔项目大约符合）：
- `non_service_expense ≈ 70% × gross_amount`
- `team_revenue ≈ 20% × gross_amount`（这部分由团队拿）
- 剩 `~10%` 是公司毛利（差额）

### 3.2 三种利润口径并存

| 口径 | 谁看 | 公式 | 永不出现的字段 |
|---|---|---|---|
| **A** 团队整体利润 | admin / lead / finance | `VSF − Σ 全部支出（含外包工程师支出）` | — |
| **B** 销售-项目-客户维度 | admin / lead / finance | `团队入账 − VSF`（有收入）/ `0 − 外包估算`（no_revenue） | — |
| **C** 驾驶舱降本 | 所有人 + 老板 | `外包估算 − 团队入账`（won）/ `外包估算`（no_revenue 已完成） | 绝对不能出现 revenue/cost/margin 等 A/B 关键字 |

> 🔒 CI 守门：`tests/test_cockpit_isolation.py` 强制断言 `/api/cockpit/*` 接口的 JSON response **不含** `revenue / cost / margin / team_margin / vendor_fees` 等字段名。

### 3.3 驾驶舱口径 C 完整计算逻辑 ⭐

文件：[backend/app/services/profit.py](../backend/app/services/profit.py) 的 `compute_cockpit_savings_and_value()`。

#### 有收入项目（PROJECT_KIND_REVENUE）

**门槛**：`bid_outcome == 'won'`（已中标，团队默认会拿到 team revenue）。

```
savings = Σ (outsource_benchmark_amount − Σ project_revenues.amount)
         per project where bid_outcome='won'
```

#### 无收入项目（PROJECT_KIND_NO_REVENUE）

**门槛**：`status ∈ {closing, archived}`（已完成，不含立项 / 进行中 / cancelled）。

```
value_created = Σ outsource_benchmark_amount per project where status in {closing, archived}
```

#### 总值

```
total_c_view = savings + value_created
```

#### `bid_outcome` 四种状态对 C 的影响

| 状态 | 含义 | 计入 savings？ |
|---|---|---|
| `pending` | 投标中 / 未定（默认） | ❌ 不计 |
| `won` | 已中标 | ✅ 立即计入（无需等回款） |
| `lost` | 已丢标 | ❌ 不计 |
| `escaped` | 中标后跑单 | ❌ 不计 |

#### 实际操作流程

```
1. sales 拍报价 + 立项                  → bid_outcome=pending, 驾驶舱不动
2. 投标中 ...                            → 不动
3. 客户告知中标，sales 改 bid_outcome=won → 驾驶舱立即加 (benchmark − team_revenue)
4. 财务录入 ProjectRevenue.amount       → 驾驶舱按新公式重算
5. 项目正常交付 closing / archived       → 驾驶舱不变（已计入）
6. 客户违约跑单，改 bid_outcome=escaped  → 驾驶舱立即扣除
```

**关键**：v0.6 起，savings 一旦中标即计入，**不再按实收封顶**（区别于 v0.4 老逻辑）。

### 3.4 公司毛利率提升公式

文件：[backend/app/services/profit.py](../backend/app/services/profit.py) `compute_company_margin_lift()`。

```
老外包模式毛利率 = (gross − benchmark − non_service_expense) / gross
                 # 没有 FDE 团队时，公司直接付外部 benchmark + non_service
                 
FDE 模式毛利率 = (gross − VSF − non_service_expense) / gross
               # 团队自管，公司付 VSF（含团队真实利润）+ non_service
               
利润率提升 = FDE 毛利率 − 老外包毛利率   # 单位：百分点
```

实测 seed 数据：老外包 6.34%，FDE 9.54%，**提升 +3.20 个百分点**。

---

## 4. 管理后台模块

10 个模块按 sidebar 顺序排（角色不同看到的会少几项，见 §2.1）。

### 4.1 首页 `/dashboard`

按 4 段呈现：
1. **业务规模**：在管项目数、已中标项目数、活跃客户数、本月支出
2. **利润健康**（仅 lead / finance / admin）：团队真实利润、公司毛利率对比、月度趋势
3. **风险预警**：已中标缺报价、过期 VSF、逾期项目
4. **快捷入口**：到 5 大模块

vendor / engineer 角色登录会直接跳到对应工作页（不看首页 KPI）。

### 4.2 项目和客户管理 `/project`

5 个 Tab：项目 / 客户 / 销售 / 收入 / 续单跟踪。

- **项目**：核心实体，含 kind（revenue/no_revenue）、status、bid_outcome、外包估算、对接工程师、摘要、互动留言等
- **客户（NeedParty）**：哪些公司 / 部门是需求方；可勾选「驾驶舱可见」决定 logo 是否上墙
- **销售（SalesPerson）**：销售人员；项目立项时必须挂一个；停用人员不能再被分配
- **收入（ProjectRevenue）**：finance 录入每笔回款 + gross_amount + non_service_expense
- **续单跟踪（RenewalAttempt）**：每次续单的尝试（pending/won/lost + 6 类输因），驾驶舱算续单胜率

操作：所有列表都支持 Excel 风格列可见性 + 列筛选下拉。

### 4.3 派单和工时管理 `/engineer`

4 个 Tab：

- **派单**：把工程师派到项目（Assignment）。含计划 / 实际工时、留言对话、接 / 拒流程
- **工时**：工程师录入工时（自动按规则加权），admin/pm 审批
- **工程师管理**：engineers 表 CRUD，含证件号脱敏 + 一键解密查看（带审计日志）
- **能力矩阵管理**：技能（Skill）字典 — 认证名称 + 类别 + 厂商 + L1/L2/L3 等级；支持批量导入

工程师挂技能时引用 Skill 字典；驾驶舱「团队能力视图」热力图就靠这里。

### 4.4 利润管理 `/profit`（仅 admin / lead / finance）

4 个 Tab：

- **整体**：口径 A KPI（团队真实利润 = VSF − 全部支出）+ 公司毛利率提升公式（含老外包 vs FDE 对比）
- **按销售人员**：口径 B 分组，每个销售看自己经手项目的盈亏
- **按客户**：口径 B 按需求方分组
- **驾驶舱对外**：预览给驾驶舱用的口径 C 数字（与 cockpit screen 一致）

> 💡 团队毛利略负是常见现象 — lost 项目的 pre-sales VSF 已经付了但没收回。可通过 tooltip 解释。

### 4.5 成本和支出管理 `/expense`

3 个 Tab（vendor 角色只看到第 1 个）：

- **Vendor 支出管理**：8 类支出（耗材 / 分包 / 临时人力 / 许可证 / 差旅 / 培训费 / 其他 / **外包工程师支出**）。审批流：pending → approved/rejected → paid
- **Vendor 服务费（VSF）**：每月给 vendor 的服务费记录，可挂项目
- **供应商（Supplier）**：支出对应的发票方公司

**vendor 角色规则**：
- 只能看到自己 vendor 名下的支出记录
- 只能提交（创建），不能 approve/reject/paid
- 顶栏其它 tab 不显示

### 4.6 项目效率管理 `/efficiency`

KPI 4 个 + 在管项目进度表：

- 在管项目数 / 本月完成 / 14 天内到期 / 累计已交付
- 表格列：项目名、状态、**对接工程师**（内联编辑）、**项目摘要**（内联编辑）、计划止、到期标签、**互动留言**

互动留言 = admin ↔ 工程师评论流，催办 / 反馈 / 备注。

### 4.7 FDE 知识库 `/knowledge`

知识资产（KnowledgeAsset）CRUD + 跨项目复用（AssetReference）。

- 7 个分类：代码片段 / 设计文档 / 技术方案 / 最佳实践 / 工艺标准 / 问题解决手册 / 其他
- 三级保密分级：public（全员可见） / internal（员工可见，engineer 也能看） / confidential（管理层才能看，engineer 不可见）
- 复用记录：填「这条资产被项目 X 引用，节省 N 工时」→ 驾驶舱算"复用节省总工时"

### 4.8 培训管理 `/capability`

3 个 Tab：

- **成长曲线**：季度快照（EngineerSkillSnapshot），SVG 折线展示团队人均技能数趋势；admin 可一键拍快照
- **培训记录**：TrainingRecord CRUD（成本字段仅 lead/finance 看得到）
- **IDP 个人发展计划**：每个工程师的 IDP CRUD（目标 / 进度 / 状态）

### 4.9 关键项目复盘管理 `/relationship`

2 个 Tab：

- **项目复盘（ProjectRetrospective）**：每个完成项目可填一份复盘报告（做对 / 要改 / 行动项 / 1-5 星满意度 / 闭环开关）
- **续单跟踪**：见 §4.2 同款，这里以"客户视角"打开

### 4.10 系统设置 · 用户 `/users`（仅 admin）

用户 CRUD：

- 创建用户：用户名 + 密码 + 角色
- engineer 角色要绑定 `engineer_id`（关联一条 engineers 记录）
- vendor 角色要绑定 `vendor_id`（关联一家 vendor 公司）
- 改密码 / 改角色 / 停用

---

## 5. 工程师端门户

engineer 角色登录后**只看到 4 个菜单**：首页 / 我的派单 / 我的工时 / 我的支出申请。后端守门：所有非 engineer 路由会被改写到 `/dashboard`。

### 5.1 我的派单 `/my-assignments`

显示当前用户名下的 Assignment 列表，按状态分组。

- **待接单**：admin/pm 派过来的新单，可点「接受」/「拒绝（带原因）」
- **进行中**：可在内联对话区跟 PM 沟通（消息流）
- **已结束**：归档查看

### 5.2 我的工时 `/my-timesheets`

录入工时（Timesheet）：日期 + 项目 + 工时数 + 类别。系统自动按规则加权（见 §7.3）。

- 提交后状态为 `pending`，等 pm/admin 审批
- 已审批的不能再改

### 5.3 我的支出申请 `/my-expenses`

创建支出申请（ExpenseRequest），见 §7.4 流程。看不到他人提交。

---

## 6. 驾驶舱（大屏）

地址：http://localhost:5174

5 个 Tab，自动轮播（点右上角按钮开启），每 60 秒自动刷数据。

| Tab | 名称 | 主要展示 |
|---|---|---|
| 01 | 总览视图 | KPI 五连 + HK 18 区项目分布地图 + 客户 logo 墙 + 数据健康面板 |
| 02 | 降本视图 | 老外包 vs FDE 对比、节省金额排行、贡献 vendor 排行 |
| 03 | 项目进度视图 | 在管 / 本月完成 / 14 天到期 / 累计交付 + 项目卡片墙 + 5 大效率 KPI |
| 04 | 技术沉淀视图 | 累计知识资产 / 复用次数 / 节省工时 / 项目覆盖 + 分类分布 + **最新沉淀滚动** |
| 05 | 团队能力视图 | **工程师总数（含在职）** + 累计证书 + 认证类别 + 人均技能 + Top 持证 + 6×3 热力图 |

**口径**：所有 Tab 数字均走 `/api/cockpit/*`，由 CI 守门确保不含 A/B 字段。

**配色规范**：
- 主色：`--cockpit-accent` 青 `#00e5ff`
- 紫色：`--cockpit-accent-2` `#7c4dff`
- 粉红 brag：`--cockpit-accent-3` `#ff4081`（最重要数字）
- 金黄 brag-2：`--cockpit-accent-gold` `#ffe082`（次重要 / 成长指标）
- 绿色 growth：`--cockpit-accent-green` `#67ff8a`（正向 delta）

---

## 7. 关键业务流程

### 7.1 立项 → 中标 → 交付完整流程

```
1. sales 在 /project 新增项目，填外包估算（必须真实询价依据）
   → kind=revenue (默认), bid_outcome=pending
   
2. 投标过程中，sales 可以改报价（外包估算）

3. 客户中标通知到达：
   sales 把 bid_outcome 改 won → 驾驶舱降本数字立即跳升
   
4. PM 在 /engineer 派单（Assignment），工程师在工程师端「接单」
   
5. 工程师在 /engineer 端录工时（按周或按月）
   PM/admin 审批工时
   
6. 项目过程中产生外部支出：
   工程师 / vendor 提交 expense → finance/lead 审批 → 付款
   
7. 客户分期付款时，finance 在 /project 收入 Tab 录入 ProjectRevenue
   含 gross_amount / amount(team_revenue) / non_service_expense
   
8. 项目交付完成：sales 改 status 为 closing / archived
   
9. PM/lead 在 /relationship 写复盘报告（含满意度）
   
10. 客户考虑续单：在 /project 续单 Tab 创建 RenewalAttempt 跟踪
```

### 7.2 派单流程

```
PM 创建 Assignment（指定工程师 + 项目 + 计划工时 + 起止日期）
  ↓ status = 'proposed'
工程师收到推送（站内信 / 飞书，Phase 4）
  ↓
工程师在「我的派单」里：
  ├── 接受 → status = 'active'，开始记工时
  └── 拒绝 → 必须填原因，状态回到 PM 看，PM 改派或撤销
  
project 完成时：
  PM 把 Assignment 改 status = 'ended'
```

### 7.3 工时加权规则（香港）

| 时段 | 系数 | 备注 |
|---|---|---|
| 工作日白天（周一～周五，09:00-18:00） | 1.0× | 标准工时 |
| 工作日晚上（周一～周五，18:00 后） | 1.5× | 加班 |
| 非工作日（周六 / 周日 / 香港公众假期） | 1.5× | 加班 |

工程师录入时填实际工时和类别，系统自动算加权工时。审批 = 锁定，不能再改。

### 7.4 支出审批流

```
提交（engineer / vendor / pm）
  → status = 'pending'
       ↓
  审批（admin / lead / finance）
       ├── approve → status = 'approved'
       │       ↓
       │   财务付款标记
       │   → status = 'paid'
       │
       └── reject (带 reject_reason) → status = 'rejected'
                                       不进 cost 累计
```

**vendor 角色特殊规则**：只能提交（不能 approve/reject/paid），只看到自己 vendor 公司名下的记录。

### 7.5 项目复盘流程

```
项目 closing / archived 后：
  PM 或 lead 在 /relationship 创建 ProjectRetrospective
    ├── 做对的事
    ├── 要改的事
    ├── 行动项列表（每项有责任人 + ddl）
    ├── 客户满意度 1-5 星
    └── 闭环开关：行动项全部跟到完成时勾上
  
驾驶舱 Tab 5（项目进度视图）按"闭环率"算团队执行力
```

---

## 8. 常见 FAQ

**Q：新员工入职怎么开账号？**
A：admin 在 `/users` 新增用户。若是基层工程师，先在 `/engineer` 工程师管理建一条 engineers 记录，再创建 User 时绑定 `engineer_id`。给 vendor 联系人开账号同理，绑 `vendor_id`。

**Q：项目跑单了（escape）怎么操作？**
A：在 `/project` 把项目的 `bid_outcome` 改成 `escaped`。驾驶舱的 savings 会立即减去这个项目原本的贡献。原有的 VSF 和支出**不会**自动撤回（已发生的成本就是发生了），所以团队真实利润会显得偏低 — 这是真实账。

**Q：客户回款分期怎么录？**
A：在 `/project` → 收入 Tab，**每收一笔录一条 ProjectRevenue**。同一项目可以有多条。`gross_amount`（客户总价）和 `non_service_expense`（非服务开销）按每笔填，系统累加。

**Q：培训费应该走哪个支出类型？**
A：用 `training` 类型（外部培训费）。如果是「给某个工程师的专项培训」可在 `/capability` → 培训记录 Tab 关联到 IDP 计划。

**Q：vendor 给我们一个新公司的工程师，怎么挂？**
A：先在 vendor 列表加这家公司，再在工程师管理新增工程师 + 选 vendor + 选签约形态（vendor 直签 / vendor 通过劳务公司）。如果走劳务公司还要填劳务公司名字。

**Q：能力矩阵的 L1/L2/L3 是什么意思？**
A：基于厂商认证等级，L1=初级 / L2=中级 / L3=高级。例如 CCNA=L1，CCNP=L2，CCIE=L3。能力矩阵热力图按「认证类别 × 等级」展示团队覆盖。

**Q：驾驶舱数字怎么实时刷？**
A：每个 Tab 自动 60 秒重新 fetch 一次。手动刷新浏览器也立即拉新数据。

**Q：忘记密码怎么办？**
A：让 admin 在 `/users` 重置该用户密码即可（系统暂无邮件找回流程，Phase 4 加）。

**Q：可以批量导入认证目录吗？**
A：`/engineer` 能力矩阵管理 → 「批量导入」按钮，按「分类 + 厂商, 名称, 等级」格式粘贴多行即可。

**Q：怎么看「这个项目到底赚了多少」？**
A：去 `/profit` → 按客户 Tab，找到这个客户，展开看每个项目的 revenue / cost / margin。注意这是口径 B 数字（团队入账 − VSF），不等于公司总利润。

---

## 9. 部署与运维要点

### 9.1 本地预览

```bash
docker compose -f docker-compose.local.yml up --build
```

详见 [docker-compose.local.yml](../docker-compose.local.yml) 顶部注释。

### 9.2 内网 / 离线部署

```bash
# 本机 export
docker save manpower-management-platform-{backend,admin-web,cockpit-screen} \
  postgres:16-alpine | gzip > manpower-images.tar.gz

# 目标机
gunzip -c manpower-images.tar.gz | docker load
docker compose -f docker-compose.offline.yml up -d
```

详见 [docker-compose.offline.yml](../docker-compose.offline.yml)。

### 9.3 生产 (天翼云) 部署

详见 [docs/deployment_ctyun.md](deployment_ctyun.md) 和 [docker-compose.prod.yml](../docker-compose.prod.yml)。

要点：
- `.env.production` 必须改：`JWT_SECRET` / `FIELD_ENCRYPTION_KEY` / `POSTGRES_PASSWORD` / `DEFAULT_ADMIN_PASSWORD` / `COCKPIT_TOKEN`
- `COCKPIT_ALLOWED_IPS` 配领导出口 IP 白名单，或者只通过 token 控制
- 数据备份：prod compose 含 pg-backup service，每日凌晨 pg_dump，保留 30 天
- HTTPS：nginx 配 `nginx/certs/` 放 Let's Encrypt 证书

### 9.4 备份与恢复

```bash
# 备份
docker exec manpower-pg pg_dump -U manpower -d manpower -Fc > backup-$(date +%F).dump

# 恢复
docker exec -i manpower-pg pg_restore -U manpower -d manpower -c < backup-2026-05-24.dump
```

### 9.5 升级流程

1. `git pull` 拉新代码
2. `docker compose -f docker-compose.prod.yml build`
3. `docker compose -f docker-compose.prod.yml up -d`
4. 容器启动会自动跑 `alembic upgrade head`（已存量数据不会丢）
5. 看日志确认 migration 全部 apply：`docker compose logs backend | grep alembic`

### 9.6 重要环境变量

| 变量 | 用途 | 必改？ |
|---|---|---|
| `DATABASE_URL` | postgres 连接串 | 改 |
| `JWT_SECRET` | JWT 签名密钥 | **必改** |
| `FIELD_ENCRYPTION_KEY` | 证件号等敏感字段对称加密 | **必改**（且改后老数据解不开） |
| `DEFAULT_ADMIN_USERNAME/PASSWORD` | 首次启动创建的 admin 账号 | **必改密码** |
| `COCKPIT_ALLOWED_IPS` | 驾驶舱 IP 白名单（逗号分隔） | 按需 |
| `COCKPIT_TOKEN` | 白名单外的兜底 token | **必改** |
| `CORS_ORIGINS` | 允许的前端来源 | 改 |
| `UPLOAD_DIR` | 上传文件目录 | 默认即可 |

---

## 附录 · 文档维护

- 业务模型若变 → 先改 [README §1.7](../README.md#17)，再改本手册 §3
- 新增模块 → 在本手册 §4 加一节，更新 §2.1 权限表
- 新增角色 → 改 §2，影响 §4 表格、权限矩阵
- 驾驶舱 Tab 数变 → 改 §6，同步前端 [CockpitFrame.vue](../cockpit-screen/src/components/CockpitFrame.vue)
