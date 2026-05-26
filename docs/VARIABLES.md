# 关键变量与关系手册

> 配对代码版本：v0.5.0（2026-05-24 业务模型定稿）
> 输出日期：2026-05-26
> 用途：项目负责人、新加入开发者、财务/合规审计「字段-公式-权限」一站速查
>
> **改任何金额公式或 seed 前请先看本手册 §2，再回到 [README §1.7](../README.md) 对照。**

---

## 1. 核心实体字段速查

### 1.1 Project — 项目主表（最核心）

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `kind` | enum | `revenue`（有收入项目，默认）/ `no_revenue`（无收入：presales、内部咨询）|
| `status` | enum | 执行生命周期：`drafting → in_progress → accepting → closing → archived`（`cancelled` 已废，用 `bid_outcome=escaped` 替代）|
| `bid_outcome` | enum | **投标结果，决定是否计入驾驶舱 C 口径**：`pending` / `won`（已中标，C 立即计入）/ `lost` / `escaped`（中标后跑单）|
| `outsource_benchmark_amount` | float? | **外包估算金额**（C 口径分子）— 只来自真实询价，没询价就空 |
| `benchmark_basis` | enum? | 估算依据可信度：`vendor_quote`（真实询价）/ `historical_avg`（同类历史均价）|
| `benchmark_basis_note` | str? | 依据说明（报告链接、项目编号）|
| `value_created_basis` | enum? | 仅 no_revenue 项目：`outsource_equiv`（等同外包成本，默认）/ `other`（其他，必填备注）|
| `value_created_note` | str? | 无收入价值说明 |
| `district` | enum? | 港岛 `HK_ISLAND` / 九龙 `KOWLOON` / 新界东 `NT_EAST` / 新界西 `NT_WEST` / 离岛 `OUTLYING` |
| `rework_count` | int=0 | 返工次数（效率 KPI）|
| `change_count` | int=0 | 变更单次数（效率 KPI）|
| `renewal_of_project_id` | int? | 自引用：续单源项目 |
| `planned_start_date` / `planned_end_date` / `actual_start_date` / `actual_end_date` | date? | 计划/实际起止 |
| `summary` / `description` | str? | 摘要 / 详情 |

**外键**：
- `need_party_id` → NeedParty（客户/需求方，B 口径汇总维度之一）
- `sales_person_id` → SalesPerson（销售人员，B 口径汇总维度之二，单 FK）
- `pm_user_id` → User（项目经理）
- `contact_engineer_id` → Engineer（对接工程师）

---

### 1.2 ProjectRevenue — 4 字段资金流核心

每一行 = 一笔回款记录。**4 个必填金额** + 状态 + 元数据。

| 字段 | 类型 | 业务含义 | 敏感 |
|---|---|---|---|
| `gross_amount` | float | **客户付款总额**（销售切除前，公司毛利率分母）| ⭐ lead/finance |
| `non_service_expense` | float | **非服务开销**（硬件、第三方软件、物料；占 gross 约 65-75%）| ⭐ lead/finance |
| `amount` | float | **团队入账**（≈ pass-through 给 Vendor 的 VSF；占 gross 约 20%）| ⭐ lead/finance |
| `vendor_quote_amount` | float? | 服务商报价（FDE vs 外包比较用）| ⭐ lead/finance |
| `status` | enum | `pending`（待回款）/ `received`（已到账）/ `written_off`（坏账）— ⚠️ UI 已移除，DB column 保留为历史包袱 |
| `recognized_date` | date | 确认日期（财务核算时间）|
| `currency` | str=HKD | 货币 |
| `invoice_no` | str? | 发票号（UI 已移除显示）|

**关键比例**（已写入 seed 校准）：
```
gross_amount = non_service_expense(~70%) + amount(~20%) + 公司毛利(~10%)
amount ≈ VSF（pass-through ±1%）
amount / vendor_quote_amount ≈ 0.80-0.90（FDE 比外包便宜 10-20%）
```

**外键**：`project_id` → Project（强制 `kind=revenue` 才允许登记）

---

### 1.3 VendorServiceFee — Vendor 服务费（三层成本第一层）

电信付给 Vendor 的钱。

| 字段 | 类型 | 业务含义 | 敏感 |
|---|---|---|---|
| `fee_type` | enum | `monthly_per_engineer`（按工程师月度）/ `project_milestone`（按里程碑）/ `other` |
| `period_start` / `period_end` | date | 服务周期 |
| `amount` | float | **服务费金额** | ⭐ lead/finance |
| `status` | enum | `draft` / `billed` / `paid` |
| `invoice_no` / `paid_at` / `description` | — | 发票/到账时间/备注 |

**外键**：
- `vendor_id` → Vendor（必填）
- `engineer_id` → Engineer（可空，按月按工程师可挂）
- `project_id` → Project（可空，做项目成本归集）

---

### 1.4 Engineer — 外包工程师档案

| 字段 | 类型 | 业务含义 | 敏感 |
|---|---|---|---|
| `vendor_id` | FK | 所属 Vendor（必填）|
| `employment_form` | enum | **签约形态**：`vendor_direct`（Vendor 直签）/ `vendor_via_labor`（Vendor → 劳务公司）|
| `labor_company` | str? | 劳务公司名（仅 vendor_via_labor 填）|
| `full_name` / `english_name` / `gender` / `birth_date` / `mobile` / `email` | — | 基本信息 |
| `id_doc_type` | enum? | `HKID` / `passport` / `mainland_id` |
| `id_doc_number_enc` | str? | 证件号 AES-GCM 加密存储 | ⭐ lead/admin |
| `status` | enum | `active` / `departed` |
| `entry_date` / `exit_date` | date? | 入场/离场 |
| `monthly_cost_to_telecom` | float? | **电信月付服务费**（旧字段，已被 VSF 模型替代，保留向后兼容）| ⭐ lead/finance |

**关联**：
- `EngineerSkill`（多对多，工程师 × 技能字典 + 等级；旧字段 `level` 已停用 default=0，待 cleanup migration drop）
- `Certificate`（多对多，外部认证 CCIE/CISSP/PMP）

---

### 1.5 Certificate — 工程师外部认证

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `name` / `issuer` / `cert_number` / `issue_date` / `expiry_date` / `file_path` | — | 证书基本信息 |
| `cert_level` | enum? | **L1（初级）/ L2（中级）/ L3（高级）**（之前砍过，从 L1-L5 收回到 L1-L3）|
| `cert_category` | enum? | `网络能力` / `安全能力` / `弱电能力` / `云能力` / `数据能力` / `AI 能力` |

---

### 1.6 Vendor — 供人公司

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `name` | unique | 公司名 |
| `short_name` / `contact_*` / `payment_terms` / `notes` | — | 联系/付款条款 |
| `cooperation_status` | enum | `active` / `paused` / `closed` |

---

### 1.7 ExpenseRequest — 外部支出（6 类统一抽象）

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `expense_type` | enum | **6 类**：`material`（耗材）/ `subcontract`（对外分包）/ `temp_labor`（临时人力）/ `license`（许可证）/ `travel`（差旅）/ `training`（外部培训）/ `outsource_engineer`（外包工程师支出）/ `other` |
| `title` / `amount` / `currency` / `expense_date` / `description` | — | 支出元数据 |
| `status` | enum | `pending`（待审）/ `approved` / `rejected` / `paid` |
| `requested_by_user_id` / `approved_by_user_id` / `approved_at` / `approval_note` | — | 审批审计 |

**外键**：
- `project_id` → Project（**必关联**，否则成本无法归集）
- `supplier_id` → Supplier（可空）
- `vendor_id` → Vendor（vendor 角色提交时填发起方）

⚠️ **注意**：6 类支出本来就含在 VSF 内（Vendor 用 VSF 去付的），用于 admin/team_margin 时不要再减一遍。详见 §2.5 `_project_vsf` vs `_project_costs`。

---

### 1.8 Timesheet — 工时记录（单位人天，0.5 步进上限 3）

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `engineer_id` / `project_id` / `assignment_id` | FK | 工程师 × 项目 × 派单 |
| `work_date` | date | 工作日期（unique with engineer + project）|
| `has_morning` / `has_afternoon` / `has_evening` | bool | 三时段选择（每段 = 0.5 天）|
| `is_workday` | bool=True | 是否工作日（周一-五默认 True，admin 可手动改假日）|
| `natural_days` | float | 自然人天 = 0.5 × 选中时段数 |
| `weighted_days` | float | **加权人天**：工作日上下午 1.0×，**工作日晚上 + 非工作日全时段 1.5×**（加班倍率）|
| `approval_status` | enum | `pending` / `approved` / `rejected`（含 `reject_reason`）|

**示例**：周一上午+下午+晚上 = 0.5×1.0 + 0.5×1.0 + 0.5×1.5 = **1.75 加权人天**

---

### 1.9 NeedParty — 需求方/客户

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `name` | unique | 客户/部门名 |
| `party_type` | enum | `internal_dept`（电信内部）/ `external_company`（外部合同方）|
| `show_in_cockpit` | bool=False | 是否在驾驶舱「已交付客户」区展示 |
| `logo_path` | str? | Logo 文件 |

---

### 1.10 SalesPerson — 销售人员

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `name` | unique | 销售姓名 |
| `employee_id` / `department` / `email` / `mobile` | — | 基本信息 |
| `is_active` | bool=True | 在职状态（离职 → False，用「转移销售」按钮把项目转给其他人，落 `SalesTransferLog`）|

---

### 1.11 Assignment — 派单（工程师 × 项目 × 时段 × 角色）

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `engineer_id` / `project_id` | FK | 工程师 × 项目 |
| `role` | str? | 派单角色（开发/测试/PM/架构师）|
| `planned_start_date` / `planned_end_date` / `actual_start_date` / `actual_end_date` | date? | 计划/实际起止 |
| `status` | enum | `planned`（已派待响应）/ `in_progress` / `ended` / `cancelled` |
| `approval_status` | enum | **工程师接派单**：`pending` / `accepted` / `rejected`（拒单需 PM 重派）|
| `engineer_responded_at` | datetime? | 响应时间 |

**关联**：`AssignmentMessage`（派单双向沟通留痕：PM ↔ 工程师）

---

### 1.12 KnowledgeAsset — 知识资产（三级保密）

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `category` | enum | 7 类：`design_doc` / `tech_solution` / `code_snippet` / `troubleshoot` / `standard` / `best_practice` / `other` |
| `title` / `summary` / `content` / `external_url` / `file_path` / `tags` | — | 资产元数据 |
| `confidentiality` | enum | **三级保密**：`public`（所有登录可见）/ `internal`（默认，所有登录可见）/ `confidential`（仅 admin/lead/finance/pm 可见，engineer 角色 403）|

**关联**：`AssetReference`（资产被项目复用记录，含 `estimated_hours_saved` 节省工时折算）

---

### 1.13 RenewalAttempt — 续单尝试

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `previous_project_id` | FK | 前一单 |
| `attempt_date` | date | 续单尝试日期 |
| `outcome` | enum | `pending` / `won`（成功）/ `lost`（失败）|
| `won_project_id` | FK? | 成功续单时的新项目 ID |
| `lost_reason` | enum? | 仅 lost 时：`lost_to_outsource`（输给外包）/ `price` / `quality` / `no_budget` / `internal_hire`（客户自建）/ `other` |
| `lost_reason_note` | str? | 失败原因说明 |

---

### 1.14 IDP & TrainingRecord — 人员发展

**IDP**（个人发展计划）：
- `engineer_id` FK + `title` + `target_skills` + `target_certs` + `plan_actions` + `due_date`
- `status`：`draft` / `in_progress` / `completed` / `cancelled`
- `mentor_user_id` → User（导师）

**TrainingRecord**（培训记录）：
- `engineer_id` + `course_name` + `provider` + `category`（内训/外训/在线/会议）+ `training_date` + `hours`
- `cost` ⭐ 敏感字段，仅 lead/finance 可见
- `passed` bool

---

### 1.15 ProjectRetrospective — 项目复盘

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `project_id` | FK | 复盘项目 |
| `satisfaction_score` | int(1-5) | 满意度评分 |
| `what_went_well` / `what_to_improve` / `action_items` | str? | 做对的 / 要改的 / 行动项（一行一条）|
| `next_review_date` | date? | 下次复盘日期 |
| `is_closed` | bool=False | 行动项是否闭环 |

---

### 1.16 User & Role

| 字段 | 类型 | 业务含义 |
|---|---|---|
| `username` | unique | 用户名 |
| `role` | enum | **6 角色**：`admin`（系统管理员）/ `lead`（技术负责人）/ `pm`（项目经理）/ `finance`（财务）/ `engineer`（外包工程师）/ `vendor`（Vendor 公司）|
| `engineer_id` | FK? | role=engineer 时挂 |
| `vendor_id` | FK? | role=vendor 时挂 |
| `is_active` / `feishu_open_id` / `feishu_union_id` | — | 状态 + Feishu SSO |

---

### 1.17 次要表速查

| 表 | 用途 |
|---|---|
| `suppliers` | 外部供应商（与 Vendor 区分，含 `category` 字段）|
| `skill` | 技能/认证字典（name/category/issuer/level）|
| `engineer_skill_snapshots` | 工程师能力季度快照（skill_count + cert_count）|
| `asset_references` | 知识资产复用记录（含节省工时）|
| `project_comments` | 项目评论流 |
| `sales_transfer_logs` | 销售转移审计表 |
| `assignment_messages` | 派单对话留痕 |
| `data_dict` | 数据字典（category × code × label）|
| `notification_log` | 通知日志 |

---

## 2. 三大金额公式总览

### 2.1 口径 A · 团队真实利润（**严禁驾驶舱**）

**用途**：财务对账、内部 KPI。
**受众**：admin / lead / finance。
**API**：`/api/admin/profit/overall`

```
team_margin = Σ VendorServiceFee.amount − Σ ExpenseRequest.amount (status != rejected)
```

**业务模型说明**（2026-05-25 重构）：
- 团队入账（ProjectRevenue.amount）100% pass-through 给 Vendor
- Vendor 用收到的 VSF 去支付所有运营支出（含付给工程师/劳务公司的钱）
- Vendor 自留的 markup ≈ team_margin（团队真实利润）
- **若 ExpenseRequest 录入不全，margin 会偏高 → 需全量才反映真实情况**

**响应字段**：
```json
{
  "total_revenue": float,              // Σ ProjectRevenue.amount（团队入账）
  "total_vendor_service_fees": float,  // Σ VSF
  "total_external_expenses": float,    // Σ ExpenseRequest
  "team_margin": float,                // VSF − ExpenseRequest
  "currency": "HKD"
}
```

---

### 2.2 口径 B · 按销售/客户汇总（**严禁驾驶舱**）

**用途**：归因分析（哪个销售/客户净亏？是否催回款？是否止损？）。
**API**：`/api/admin/profit/by-sales-person`、`/api/admin/profit/by-need-party`

**底表（compute_per_project）**：
```
若 kind=revenue：
  revenue = Σ ProjectRevenue.amount（该项目）
  cost    = Σ VendorServiceFee.amount + Σ ExpenseRequest.amount（该项目，非拒绝）
  margin  = revenue − cost   ← 可正可负

若 kind=no_revenue：
  revenue = 0
  cost    = outsource_benchmark_amount   ← 把外包估算当机会成本
  margin  = −benchmark                    ← 始终负数
```

⚠️ **不要恢复 `WHERE kind=revenue`**：no_revenue 项目要在 B 口径里按 benchmark 算机会成本（见 [project_no_revenue_opportunity_cost](../.claude/projects/-Users-akivagong-projects-Manpower-management-platform/memory/project_no_revenue_opportunity_cost.md)）。

**汇总（按销售）**：
```
per_sales_person:
  revenue = Σ revenue_per_project (该销售名下)
  cost    = Σ cost_per_project (该销售名下)
  margin  = revenue − cost
```

**汇总（按客户）**：同理按 `need_party_id` 分组。

---

### 2.3 口径 C · 驾驶舱降本 + 创造价值（**驾驶舱唯一允许的金额叙事**）

**用途**：对外向领导/客户 brag「内化为公司节省了多少钱」。
**API**：`/api/cockpit/savings-and-value`

**门槛**：
- 有收入项目：`kind=revenue` AND `bid_outcome=won`
- 无收入项目：`kind=no_revenue` AND `status ∈ {closing, archived}`

**公式**：
```
有收入项目降本：
  savings_per_project = outsource_benchmark_amount − Σ ProjectRevenue.amount(该项目)
  total_savings = Σ savings_per_project

无收入项目价值：
  value_created_per_project = outsource_benchmark_amount
  total_value_created = Σ value_created_per_project

驾驶舱总 C 视图：
  total_c_view = total_savings + total_value_created
```

**逻辑**：
- benchmark = 「如果走传统外包要花多少」（来自真实询价）
- ProjectRevenue.amount = 「FDE 内化模式实际花了多少」（团队入账 ≈ VSF）
- 差值 = 从转向 FDE 获得的降本（客户视角）

**响应字段（严格隔离）**：
```json
{
  "savings_from_revenue_projects": float,
  "value_created_from_no_revenue_projects": float,
  "total_c_view": float,
  "revenue_project_count": int,
  "no_revenue_project_count": int,
  "currency": "HKD"
}
```

⚠️ **禁止字段**：response 不得含 `revenue` / `cost` / `margin` / `team_margin` / `vendor_fees` / `real_cost` / `profit` / `gross_amount` / `non_service_expense` 等口径 A/B 关键字（CI 强制 assert）。

---

### 2.4 公司毛利率提升（含 non_service_expense，**仅 admin/lead/finance**）

**用途**：C-suite 决策——对比「传统外包」vs「FDE 内化」公司层级毛利率差异。
**API**：admin 利润管理「FDE 利润率对比」卡（不暴露驾驶舱）

**公式**（2026-05-24 校准）：
```
gross       = Σ ProjectRevenue.gross_amount        客户付款总额
bench       = Σ Project.outsource_benchmark_amount 外部报价
team_rev    = Σ ProjectRevenue.amount              FDE 模式团队入账
non_service = Σ ProjectRevenue.non_service_expense 硬件/第三方/物料

老外包毛利率 = (gross − bench − non_service) / gross
FDE 毛利率   = (gross − team_rev − non_service) / gross
利润率提升   = FDE − 老外包 = (bench − team_rev) / gross
多挣 extra   = bench − team_rev                    （Vendor markup）
```

**门槛**：
- `kind=revenue` AND `bid_outcome=won` AND 有 ProjectRevenue 记录

**典型数字**：老外包 ~6%，FDE ~10%，提升 +3-5 个百分点。

---

### 2.5 Helper 函数（关键差异）

| 函数 | 公式 | 用途 | 注意 |
|---|---|---|---|
| `_project_revenues(pid)` | `Σ ProjectRevenue.amount` | 所有口径 | 团队入账 |
| `_project_vsf(pid)` | `Σ VendorServiceFee.amount` | **口径 C savings** | 6 类支出已含在 VSF 内，不再减 |
| `_project_costs(pid)` | `Σ VSF + Σ ExpenseRequest (非 rejected)` | **口径 A/B margin** | 含 6 类外部支出 |

🚨 **绝不混用**：
- 改 `compute_per_project` 不能恢复 `WHERE kind=revenue`
- 改 admin margin_lift 不能用 `_project_costs`（含 6 类支出会重复扣）

---

## 3. 枚举值大全（已收缩，不要再扩）

| 字段 | 取值 |
|---|---|
| `Project.kind` | revenue / no_revenue |
| `Project.status` | drafting / in_progress / accepting / closing / archived / ~~cancelled~~（用 bid_outcome=escaped 替代）|
| `Project.bid_outcome` | pending / won / lost / escaped |
| `Project.benchmark_basis` | vendor_quote / historical_avg ⚠️ 已从 4 收缩到 2 |
| `Project.value_created_basis` | outsource_equiv / other ⚠️ 已从 6 收缩到 2 |
| `Project.district` | HK_ISLAND / KOWLOON / NT_EAST / NT_WEST / OUTLYING |
| `ProjectRevenue.status` | pending / received / written_off（UI 已移除，DB 保留为历史包袱）|
| `VendorServiceFee.fee_type` | monthly_per_engineer / project_milestone / other |
| `VendorServiceFee.status` | draft / billed / paid |
| `Engineer.employment_form` | vendor_direct / vendor_via_labor |
| `Engineer.status` | active / departed |
| `Engineer.id_doc_type` | HKID / passport / mainland_id |
| `Certificate.cert_level` | L1 / L2 / L3 ⚠️ 已从 L1-L5 砍回 L1-L3 |
| `Certificate.cert_category` | 网络能力 / 安全能力 / 弱电能力 / 云能力 / 数据能力 / AI 能力 |
| `ExpenseRequest.expense_type` | material / subcontract / temp_labor / license / travel / training / outsource_engineer / other |
| `ExpenseRequest.status` | pending / approved / rejected / paid |
| `KnowledgeAsset.confidentiality` | public / internal / confidential |
| `KnowledgeAsset.category` | design_doc / tech_solution / code_snippet / troubleshoot / standard / best_practice / other |
| `RenewalAttempt.outcome` | pending / won / lost |
| `RenewalAttempt.lost_reason` | lost_to_outsource / price / quality / no_budget / internal_hire / other |
| `Assignment.status` | planned / in_progress / ended / cancelled |
| `Assignment.approval_status` | pending / accepted / rejected |
| `Timesheet.approval_status` | pending / approved / rejected |
| `IDP.status` | draft / in_progress / completed / cancelled |
| `NeedParty.party_type` | internal_dept / external_company |
| `Vendor.cooperation_status` | active / paused / closed |
| `User.role` | admin / lead / pm / finance / engineer / vendor |

---

## 4. 敏感字段权限矩阵

✓ = 可见，✗ = 不可见 / 脱敏

| 敏感字段 | 所在表 | admin | lead | finance | pm | engineer | vendor |
|---|---|---|---|---|---|---|---|
| `ProjectRevenue.amount`（团队入账）| project_revenues | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| `ProjectRevenue.gross_amount`（客户付款总额）| project_revenues | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| `ProjectRevenue.non_service_expense`（非服务开销）| project_revenues | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| `VendorServiceFee.amount` | vendor_service_fees | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| `Engineer.monthly_cost_to_telecom` | engineers | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| `Engineer.id_doc_number_enc`（解密原文）| engineers | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| `TrainingRecord.cost` | training_records | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| KnowledgeAsset(confidentiality=confidential) | knowledge_assets | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| `ExpenseRequest.amount`（vendor 角色仅看自家）| expense_requests | ✓ | ✓ | ✓ | ✗ | ✗ | 自家 |

---

## 5. 驾驶舱接口与守门规则

### 5.1 端点清单（`/api/cockpit/*`）

| 端点 | 功能 | 关键返回字段 |
|---|---|---|
| `/savings-and-value` | C 口径核心：降本 + 创造价值 | savings_from_revenue_projects, value_created_from_no_revenue_projects, total_c_view |
| `/overview` | 总览 KPI | active_projects, team_size, on_time_delivery_rate, capability_by_category |
| `/project-board` | 项目看板（地区分布）| by_status, by_district, items (项目名/状态/地区)|
| `/profit-compare` | C 扩展（Top 项目 + Vendor 排名）| top_savings_projects, top_value_projects, vendor_contribution_rank |
| `/engineer-stats` | 工程师统计 | total, active, by_vendor, top_allocated |
| `/efficiency-stats` | 交付效率 | on_time_rate, rework_rate, due_soon |
| `/capability-stats` | 能力矩阵 | cert_heatmap, by_issuer, top_certified_engineers |
| `/knowledge-stats` | 技术沉淀 | total_assets, recent_30d, project_coverage, by_category, reuse_count, hours_saved |
| `/growth-trend` | 季度成长曲线 | quarters, skill_avg, cert_avg |
| `/relationship-stats` | 客户口碑 | satisfaction_avg, closed_rate, renewal_funnel(won/lost/pending), lost_reasons |

### 5.2 守门规则（CI 强制）

```python
# tests/test_cockpit_isolation.py
FORBIDDEN_KEYS = {
  "revenue", "cost", "margin",
  "team_margin", "vendor_fees", "real_cost", "profit",
  "gross_amount", "non_service_expense",
}
# 任何 cockpit endpoint response 的字段名/字符串值都不得含上述关键字
```

### 5.3 访问控制（`cockpit_guard`）

- IP 白名单：`COCKPIT_ALLOWED_IPS` 环境变量（逗号分隔）
- 或 Token：`X-Cockpit-Token` header / `?token=` query param 与 `COCKPIT_TOKEN` 匹配
- 失败：401/403，无信息泄露

### 5.4 Vendor 贡献度分摊（profit-compare）

```python
# 一笔 savings 按各 Vendor 在该项目 VSF 中的占比分摊
for vid in project.vsf_by_vendor:
    vendor_savings[vid] += project.savings * (project.vsf_by_vendor[vid] / project.total_vsf)
```

避免双重计数：一个项目的 savings 一定 = Σ vendor_savings(该项目)。

---

## 6. 常见踩坑提示

| 坑 | 说明 |
|---|---|
| 1 | **不要把 `ProjectRevenue.status` 重新引入 UI** — 已移除，DB column 保留是历史包袱 |
| 2 | **改 `compute_per_project` 不能恢复 `WHERE kind=revenue`** — no_revenue 项目要算机会成本 |
| 3 | **不要用 `_project_costs`（含 6 类支出）算 C 口径或 admin margin_lift** — 6 类已含在 VSF 内 |
| 4 | **benchmark 永远来自真实询价**，没询价就空，不要瞎填 |
| 5 | **cert_level 是 L1-L3**，不是 L1-L5（之前砍过）|
| 6 | **不要把 ExpenseRequest 直接挂 `outsource_engineer` 当工程师工资支出** — 已废，工程师工资走 VSF |
| 7 | **驾驶舱不能展示口径 A/B 数字** — CI 守门会 fail，PR 不能 merge |
| 8 | **客户付款 ≠ 团队入账** — gross_amount（客户付款）和 amount（团队入账）是 ProjectRevenue 表两个不同字段，差值是公司毛利 + 非服务开销 |

---

*本手册随 schema 演进，每次改字段/公式/枚举请同步更新本文件。*
