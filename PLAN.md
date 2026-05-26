# Manpower Management Platform — 项目规划 (PLAN)

> 版本: **v0.5** (2026-05-24 业务模型定稿后重写)
> 当前阶段: Phase 3-next-iii Round 3 已完成；Phase 5 用户手册已交付
> v0.1 / v0.2 / v0.3 / v0.4 已废弃（v0.5 业务模型校准前的视角，详见 §20 changelog）
>
> **阅读顺序**：
> 1. [README.md](README.md) § 1.7 — 业务模型最终态（4 字段资金流 + 公式）
> 2. [docs/VARIABLES.md](docs/VARIABLES.md) — 全字段 / 公式 / 枚举 / 权限手册
> 3. 本文档 §4 实施方案 + §8 阶段进度

---

## 0. 核心业务假设（已 freeze）

下列假设是 v0.5 业务模型定稿后的当前状态。**改任何金额公式或字段语义前，先看 [README §1.7](README.md#17)**。

| # | 假设项 | 当前状态 |
|---|---|---|
| A1 | **业务视角** | 甲方用工方（电信HK 自用） — 已锁定 |
| A2 | **供人结构** | 「电信 → Vendor → 劳务公司 → 工程师」三层链路，项目服务费形式 — 已锁定 |
| A3 | **项目来源** | 主要是电信集团内部工程订单；少量对外项目 |
| A4 | **利润口径** | **四种口径并存**（详见 §4.3）：A 团队真实利润 / B 销售-客户维度 / C 驾驶舱降本+创造价值 / D 公司毛利率提升。**驾驶舱仅暴露 C，CI 强制守门** |
| A4b | **资金流 4 字段** | ProjectRevenue 4 必填金额：`gross_amount`（客户付款总额）/ `non_service_expense`（非服务开销 ~70%）/ `amount`（团队入账 ~20% ≈ VSF）/ `vendor_quote_amount`（服务商报价） |
| A4c | **Vendor pass-through** | 团队入账 ≈ 100% pass-through 给 Vendor；Vendor 用 VSF 付全部运营支出（含 6 类外部支出 + 给工程师/劳务公司的钱）；Vendor markup ≈ 团队真实利润 |
| A4d | **项目分类 + 投标结果** | `kind=revenue/no_revenue`（影响 C 口径）+ `bid_outcome=pending/won/lost/escaped`（决定项目是否计入 C；won 才计入） |
| A4e | **销售/客户双维度** | 项目同时挂 `sales_person_id` + `need_party_id`，两个维度都可汇总 B 口径毛利 |
| A4f | **no_revenue 机会成本** | B 口径里 no_revenue 项目按 `outsource_benchmark_amount` 算成本，毛利 = −benchmark（吃掉的预期外包成本） |
| A5 | **货币** | 港币 HKD 为主，DB numeric(14,2)，UI `HK$` |
| A6 | **语言** | 简体中文，Phase 4 加繁中/英文 i18n |
| A7 | **驾驶舱认证** | 内网 IP 白名单 + 单次 token；不要求领导登录 |
| A8 | **部署** | 内网/云 Docker Compose 自部署（已支持本地预览 + 离线装载镜像）|
| A9 | **规模** | 50~200 工程师，10~50 并行项目，2~5 个 Vendor |
| A10 | **知识资产保密** | 三级分级 `public/internal/confidential`；机密资产 engineer 角色 403 |
| A11 | **角色矩阵** | 6 角色：`admin/lead/pm/finance/engineer/vendor`；敏感字段权限矩阵见 [docs/VARIABLES.md §4](docs/VARIABLES.md#4-敏感字段权限矩阵) |

---

## 1. 系统定位

**一句话**：让中国电信国际香港分公司工程师团队负责人，把外包工程师当自己人管理，并把成果用大屏方式向领导展示，用以争取更多资源。

**真实链路**（每次开发前必须看清楚）：

```
   电信HK (甲方 / 系统使用方)
        │ ①【项目服务费】← 数据模型中"项目人工成本"实际就是这一项
        ▼
   Vendor 供人公司
        │ ②【劳务费/人头费】← 数据模型中"Vendor真实成本"（估算/披露）
        ▼
   劳务公司
        │ 实际雇佣
        ▼
   外包工程师 ── 派到 ──► 电信项目
```

**两个前端、一个后端**：

```
┌────────────────────────────┐      ┌────────────────────────────┐
│  ① 管理后台 (admin-web)     │      │  ② 领导驾驶舱 (cockpit)     │
│  Vue3 + Element Plus       │      │  Vue3 + DataV-Vue3 + ECharts│
│  团队负责人 + 团队成员日用   │      │  16:9 大屏，深色科技风       │
└────────────┬───────────────┘      └──────────────┬─────────────┘
             │ JWT                                 │ IP白名单/token
             ▼                                     ▼
       ┌─────────────────────────────────────────────────┐
       │   后端 API (FastAPI)                            │
       │   /api/admin/*   （读写，需鉴权）                 │
       │   /api/cockpit/* （只读、预聚合）                 │
       └──────────────────┬──────────────────────────────┘
                          │
              ┌───────────┴──────────────┐
              ▼                          ▼
       PostgreSQL 16                Redis（缓存/任务）
```

---

## 2. 角色与权限

| 角色 | 主要职责 | 入口 |
|---|---|---|
| 团队负责人（你） | 全权限 | 管理后台 |
| 项目经理 (PM) | 自己负责的项目立项/派单/工时/支出 | 管理后台 |
| 财务 | 预算、Vendor服务费、成本、利润、报表 | 管理后台 |
| 工程师本人（Phase 3+） | 查派单、提工时、申领支出 | 管理后台精简视图 / Phase 4 H5 |
| 上级领导 | 看大屏 | 驾驶舱 |

权限粒度：**角色 + 数据范围**（PM 只看自己项目）+ **金额字段独立权限位**（非财务/负责人不可见 Vendor 服务费、真实人工成本）。

---

## 3. 核心业务流程

```
 [Vendor 入库] ─► [Vendor 工程师入库] ─► [档案/技能/培训记录]
                                              │
                                              ▼
 [内部需求 / 工程订单] ─► [立项 Project] ─► [预算 + 风险登记]
                                              │
                                              ▼
                                      [派单 Assignment]
                                      Vendor工程师 × 项目
                                              │
                              ┌───────────────┴───────────────┐
                              ▼                               ▼
                      [工时录入 Timesheet]            [外部支出申请/审批]
                              │                               │
                              └───────────┬───────────────────┘
                                          ▼
                              [项目成本归集 + Vendor服务费]
                                          │
                                          ▼
                                  [项目验收/收尾]
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                      [项目复盘 + 满意度]       [项目毛利 + 三层透视]
                              │                       │
                              └───────────┬───────────┘
                                          │
                              [知识资产归档（设计/代码/方案）]
                                          │
                                          ▼
                              [驾驶舱大屏：8 大维度全维展示]
```

---

## 4. 功能模块清单（**严格按 README §3 的 8 大维度组织**）

### 4.1 项目管理（README §3 维度 1）
- 项目立项：名称、**需求方 NeedParty**（电信内部部门 / 外部合同方）、**销售人员 SalesPerson**、起止、负责 PM、预算
- **项目分类**（见 README §1.6）：
  - `kind = revenue` — 有收入项目（默认）
  - `kind = no_revenue` — 无收入项目，必填"估算创造价值"（`value_created` 字段，单位 HKD）+ 依据说明
- 状态机：`立项 → 进行中 → 验收 → 收尾 → 归档`
- 里程碑、变更记录
- **风险与合规子维度**（合并 D）：风险登记（技术/进度/成本/合规）、合规事件（PDPO、母公司合规检查）、安全事故
- 项目文档暂存（与 §4.7 知识资产联动；项目归档时关键文档转入资产库）
- 项目列表 / 看板 / 甘特图
- **给驾驶舱**：在管项目数、按时完成率、项目地图分布、零事故天数（**不输出团队真实利润**）

### 4.2 员工派单（README §3 维度 3）
- **Vendor 档案**：公司信息、对接人、合作模式、协议、付款条件
- **工程师档案**（**归属 Vendor**）：个人信息、签约形态（Vendor 直签/Vendor 通过劳务公司）、紧急联系人
- **技能矩阵**：编程语言、网络/通信/安全等领域、等级 L1~L5
- **Vendor 服务单价 / 估算 Vendor 真实成本**（仅财务/负责人可见；与 §4.3 联动）
- **资源利用率子维度**（合并 E）：档期视图、本月/季度负载占比、闲置率、满负荷预警
- **派单 Assignment**：工程师 × 项目 × 时段 × 角色 × 工时占比
- **状态机**：`储备 → 待入场 → 在场 → 离场`
- **给驾驶舱**：团队规模、能力矩阵、满负荷率、Vendor 分布

### 4.3 利润管理（README §3 维度 2）— **四种口径并存**

> ⚠️ 四个口径数据**完全独立**展示，受众和用途不同。详细公式见 [docs/VARIABLES.md §2](docs/VARIABLES.md#2-三大金额公式总览)。
>
> ⚠️ 业务模型背景（关键）：团队入账 ~100% pass-through 给 Vendor；6 类外部支出已含在 VSF 内（vendor 用 VSF 去付），算 admin margin / 公司毛利率时不能再减一次。

#### 口径 A · 团队真实利润（admin/lead/finance 专享）
公式：
```
team_margin = Σ VendorServiceFee.amount  −  Σ ExpenseRequest.amount (非 rejected)
```
- 含 8 类支出，其中 `outsource_engineer` 是 vendor 付给工程师/劳务公司的钱（需手动录入）
- 不全量录入会让 margin 偏高
- 显示位置：admin → 利润管理 → "团队总览"卡片
- API：`/api/admin/profit/overall`

#### 口径 B · 销售/客户维度（admin/lead/finance 专享，可正可负）

**底表 compute_per_project**（cost helper 用 `_project_vsf`，**不含** 6 类支出，避免双重扣除）：
```
revenue 项目：
  revenue = Σ ProjectRevenue.amount（团队入账）
  cost    = Σ VendorServiceFee.amount
  margin  = revenue − cost   ← 可正可负

no_revenue 项目（业务模型修正：吃掉的机会成本）：
  revenue = 0
  cost    = outsource_benchmark_amount
  margin  = −benchmark   ← 始终负数，反映「无收入项目消耗的预期外包成本」
```

**两个聚合视图**：
- 「按销售人员汇总」按 `sales_person_id` 分组 → API `/api/admin/profit/by-sales-person`
- 「按客户汇总」按 `need_party_id` 分组 → API `/api/admin/profit/by-need-party`

用途：催回款、判断哪个销售/客户净亏、决定续约策略。

#### 口径 C · 驾驶舱降本 + 创造价值（驾驶舱唯一允许的金额叙事）

**门槛**：
- 有收入项目：`kind=revenue` AND `bid_outcome=won`（中标才计入）
- 无收入项目：`kind=no_revenue` AND `status ∈ {closing, archived}`（收尾/归档才计入）

**公式**：
```
有收入项目降本：
  savings_per_project    = outsource_benchmark_amount − Σ ProjectRevenue.amount
  total_savings          = Σ savings_per_project

无收入项目价值：
  value_created          = outsource_benchmark_amount   ← 工程师 pre-sales 投入的等值
  total_value_created    = Σ value_created

驾驶舱 C 总视图：
  total_c_view = total_savings + total_value_created
```
- benchmark **永远来自真实询价**（`benchmark_basis ∈ {vendor_quote, historical_avg}`）；没询价就空
- API：`/api/cockpit/savings-and-value` + `/api/cockpit/profit-compare`

#### 口径 D · 公司毛利率提升（admin/lead/finance 专享，**绝不驾驶舱**）

**用途**：C-suite 决策——对比"传统外包"vs"FDE 内化"公司层级毛利率差异。

**公式**（2026-05-24 校准含非服务开销）：
```
gross       = Σ ProjectRevenue.gross_amount        客户付款总额
bench       = Σ Project.outsource_benchmark_amount 外部报价
team_rev    = Σ ProjectRevenue.amount              FDE 模式团队入账
non_service = Σ ProjectRevenue.non_service_expense 硬件/第三方/物料

老外包毛利率 = (gross − bench − non_service) / gross
FDE 毛利率   = (gross − team_rev − non_service) / gross
利润率提升   = FDE − 老外包 = (bench − team_rev) / gross
多挣 extra   = bench − team_rev
```
- 门槛：`kind=revenue` AND `bid_outcome=won` AND 有 ProjectRevenue
- 典型数字：老外包 ~6%，FDE ~10%，提升 +3-5 个百分点
- 显示位置：admin → 利润管理 → "FDE 利润率对比"卡

#### 共用基础数据（ProjectRevenue 4 字段）

每笔回款必填 4 个金额（业务比例已在 seed 校准）：

| 字段 | 含义 | 占 gross 比例 | 敏感 |
|---|---|---|---|
| `gross_amount` | 客户付款总额 | 100% | ⭐ lead/finance |
| `non_service_expense` | 非服务开销（硬件/第三方/物料） | ~65-75% | ⭐ lead/finance |
| `amount` | 团队入账 ≈ VSF | ~20% | ⭐ lead/finance |
| `vendor_quote_amount` | 服务商报价（FDE vs 外包比较）| — | ⭐ lead/finance |

#### 关键约束
- 任何驾驶舱接口（`/api/cockpit/*`）**禁止返回 A/B/D 口径字段**（CI 强制 assert，见 `tests/test_cockpit_isolation.py`）
- 守门字段黑名单：`revenue / cost / margin / team_margin / vendor_fees / real_cost / profit / gross_amount / non_service_expense`
- 路由直接拆分：`/api/admin/*`（JWT + RBAC）vs `/api/cockpit/*`（cockpit_guard：IP 白名单 + token），不用 header 区分

### 4.4 外部支出管理（README §3 维度 4）— **扩展版**
- **支出分类字典**（6 类）：
  - 类型 1 — 耗材（线缆/工具/设备/物料）
  - 类型 2 — **对外分包高级服务**（特殊技术服务、安全测试、专业设计、第三方审计）
  - 类型 3 — 临时人力补充（短期外援工时）
  - 类型 4 — 第三方平台/许可证（云资源、SaaS、软件 license）
  - 类型 5 — 差旅/外勤报销
  - 类型 6 — **其他**（不在以上分类的开销，需在描述里说明）
- **统一流程**：申请 → 审批（PM/负责人/财务三级可配置）→ 采购单 → 入库/验收 → 领用/分摊 → 归集到项目
- **每笔支出必须挂项目**：否则成本无法归集
- **供应商管理**（与 §4.2 的 Vendor 不同！这是耗材/分包供应商）：档案、报价、付款记录
- **库存预警**（仅耗材类）：低于阈值提醒
- **给驾驶舱**：外部支出占比、Top 5 支出类型、分包服务占比

### 4.5 项目完成效率（README §3 维度 5）
- **工期对比**：计划 vs 实际、按时完成率
- **人均产出**：每工程师月毛利贡献、每工时产出
- **质量指标**：返工次数、变更单次数、验收一次通过率
- **团队 KPI 汇总**：月度/季度滚动
- **给驾驶舱**：按时交付率、人均产出排行、效率趋势

### 4.6 基础设施（横向支撑）
- 登录、JWT、RBAC、数据范围控制
- 操作日志 / 审计（金额相关必留痕）
- 数据字典（技能、岗位、支出类型、项目阶段、需求方、合规类型）
- 文件上传（合同、证件、工程文档、知识资产附件）
- 通知中心：站内信 + 邮件（Phase 1）；企微/飞书（Phase 4）

### 4.7 技术沉淀 / 知识资产（README §3 维度 6 ⭐新）
- **资产类型**：设计文档、技术方案、代码片段/模板、问题解决手册、工艺标准、最佳实践
- **分类体系**：按技术领域（网络/通信/安全/数据/AI...）× 资产类型 × 项目来源
- **保密分级**：公开 / 内部 / 机密（按 A10 假设）
- **录入**：项目验收时强制提示"是否产生可沉淀资产"，转入资产库
- **检索 + 引用**：全文搜索、标签筛选；下次新项目立项时可"引用"相关资产
- **复用追踪**：每次引用记录 → 估算"复用为团队节省的工时"
- **给驾驶舱**：累计资产数（按类别）、跨项目复用次数、节省工时折算金额

### 4.8 工程师能力建设（README §3 维度 7 ⭐新）
- **培训计划**：年度/季度培训日历、必修/选修
- **培训记录**：参训工程师、时长、讲师、考核结果
- **外部认证管理**：证书申报、考试报销、有效期提醒（CCIE/CISSP/PMP/AWS/CKA 等）
- **技能成长曲线**：每工程师技能矩阵的历史快照（季度滚动）
- **团队能力地图**：所有工程师 × 所有技能的热力矩阵
- **个人发展计划 (IDP)**：目标技能、培训路径、负责人
- **给驾驶舱**：累计获得证书数、技能矩阵热力图、季度能力成长指数

### 4.9 需求方关系 / 项目复盘（README §3 维度 8 ⭐新）
- **需求方档案**：电信内部部门/外部合同方、对接人、合作历史
- **项目验收满意度问卷**：5 维度评分（交付质量/进度/沟通/响应/创新）+ 文字反馈
- **复盘会议记录**：什么做对了 / 什么要改进 / 行动项及负责人
- **行动项闭环**：跟踪到完成，统计闭环率
- **续单跟踪**：从一个项目到下一个项目，统计续单率
- **给驾驶舱**：续单率、满意度趋势、复盘闭环率、需求方关系热度图

### 4.10 驾驶舱（独立前端，README §4）

> 独立工程 [cockpit-screen/](cockpit-screen/)，独立 UI 风格、独立路由。
> 8 Tab 设计（v0.3）经多轮迭代后**收敛为 5 个可见 Tab + 1 隐藏**（v0.5.0 后）；客户口碑 / 项目地图等内容并入相邻 Tab。

**页面结构（5 个可见 Tab，自动轮播，自定义 SVG 主题）**：

| # | Tab | 路由 | 主要内容 |
|---|---|---|---|
| 1 | 总览视图 | `/overview` | 4 个 brag KPI（在管项目 / **C 总价值** / 团队规模 / 已交付客户）+ **数据健康面板**（隔离守门提示 + 跳动绿点 + 三层成本透视说明）+ HK 18 区项目热力图（ECharts geo，DataV CDN 拉 geoJSON，fallback SVG schematic）|
| 2 | 降本视图 | `/profit-compare` | 仅口径 C：累计降本数字滚动 + Top 5 降本项目 + Top 5 创造价值项目 + Vendor 贡献度排名（按 VSF 占比分摊降本）。**绝不展示 A/B/D 字段** |
| 3 | 项目进度视图 | `/efficiency` | 按时交付率仪表 + 返工率 + 人均变更次数 + 零失误交付 KPI + 即将到期项目 + 进行中项目数 |
| 4 | 技术沉淀视图 | `/knowledge` | 累计资产数（CountNumber 滚动）+ 近 30 天新增 + 项目覆盖率 + 跨项目复用次数 + 节省工时折算 + 7 类分布条形图 |
| 5 | 团队能力视图 | `/capability` | 团队规模（含 active）+ 证书热力图（cert_category × cert_level）+ Vendor 分布 + Top 5 认证工程师 + 季度成长曲线（SVG 折线）|
| — | 工程师视图（隐藏）| `/engineer` | 总规模 / 按 Vendor 分组 / Top 满负荷；从 nav 隐藏（数据已并入 Tab 5），URL 直访仍可用 |

**已并入相邻 Tab 的旧内容**：
- 原 Tab 2「项目地图」→ 并入 Tab 1 总览
- 原 Tab 8「客户口碑」（满意度/续单率/复盘闭环）→ 后端 `/api/cockpit/relationship-stats` 仍提供，前端 Tab 收敛后未独占 Tab

**视觉规范**：
- 暗色背景（#0A1929 / #061327），霓虹蓝/青/品红高亮
- 数字滚动动效：`CountNumber.vue`（easeOutCubic）
- brag 卡循环脉冲发光（粉/金/绿三类）
- Tab 切换 fade-in 过渡
- 默认 1920×1080，4K 自适应
- HK 地图：ECharts geo 运行时拉阿里 DataV `810000_full.json`，18 区映射 5 大宏区配色，fallback 到原 SVG schematic（带橙色警告条）

**驾驶舱后端 endpoint 清单（`/api/cockpit/*`）**：
| Endpoint | 用途 |
|---|---|
| `/overview` | 4 大 KPI + capability_by_category |
| `/savings-and-value` | C 口径核心：savings + value_created + total_c_view |
| `/data-health` | 数据健康面板（隔离守门状态）|
| `/project-board` | 项目看板 + 地区分布 |
| `/profit-compare` | C 扩展：top_savings_projects + Vendor 贡献分摊 |
| `/efficiency-stats` | 按时交付率 + 返工率 + 变更率 |
| `/engineer-stats` | 工程师统计（隐藏 Tab 用）|
| `/capability-stats` | 证书热力图 + Top 认证工程师 |
| `/knowledge-stats` | 资产统计 + 复用次数 + 节省工时 |
| `/growth-trend` | 季度成长曲线 |
| `/relationship-stats` | 满意度 + 续单胜率漏斗 + 输因分布 |

**数据源**：
- 后端 `/api/cockpit/*` 预聚合（Redis 缓存预留，当前未启用）
- 完全不接管理后台 CRUD（路由 + 鉴权独立）
- 守门：`cockpit_guard` 检查 IP 白名单 / `X-Cockpit-Token`

---

## 5. 数据模型（实际落地的 28 张表，按业务域分组）

> 详细字段定义见 [docs/VARIABLES.md §1](docs/VARIABLES.md#1-核心实体字段速查)。
> Migration 文件在 `backend/alembic/versions/`。

### 5.1 人 / 组织（8 张）
| 表 | 用途 | 关键字段 |
|---|---|---|
| `users` | 系统用户（RBAC 基础）| role ∈ {admin,lead,pm,finance,engineer,vendor} + engineer_id / vendor_id 挂接 |
| `engineers` | 外包工程师档案 | vendor_id + employment_form + id_doc_number_enc（AES 加密）+ monthly_cost_to_telecom |
| `certificates` | 工程师外部认证 | name + cert_level (L1-L3) + cert_category（6 大能力域） |
| `skill` | 技能字典 | name + category + issuer + level |
| `engineer_skills` | 工程师 × 技能（多对多）| level（旧字段已停用 default=0，待 cleanup migration drop） |
| `engineer_skill_snapshots` | 工程师能力季度快照 | snapshot_date + skill_count + cert_count |
| `vendors` | 供人公司 | name + cooperation_status + payment_terms |
| `suppliers` | 外部支出供应商（与 Vendor 区分）| name + category + payment_terms |

### 5.2 客户 / 销售（3 张）
| 表 | 用途 | 关键字段 |
|---|---|---|
| `need_parties` | 需求方/客户档案 | party_type ∈ {internal_dept, external_company} + show_in_cockpit + logo_path |
| `sales_persons` | 销售人员档案 | is_active（离职 → false） |
| `sales_transfer_logs` | 销售归属转移审计 | from / to / reason / operator |

### 5.3 项目 / 复盘 / 续单（4 张）
| 表 | 用途 | 关键字段 |
|---|---|---|
| `projects` | 项目主表 | kind + bid_outcome + status + outsource_benchmark_amount + benchmark_basis + district + rework_count + change_count + renewal_of_project_id |
| `project_comments` | 项目评论流 | author_user_id + author_role 冗余存便于审计 |
| `project_retrospectives` | 项目复盘 | satisfaction_score (1-5) + what_went_well / what_to_improve / action_items + is_closed |
| `renewal_attempts` | 续单尝试追踪 | outcome ∈ {pending,won,lost} + lost_reason 枚举 |

### 5.4 资金（3 张，是命门）
| 表 | 用途 | 关键字段 |
|---|---|---|
| `project_revenues` | 项目收入 / 资金流 4 字段 | **gross_amount** + **non_service_expense** + **amount** + **vendor_quote_amount**；仅 revenue 类项目允许 |
| `vendor_service_fees` | Vendor 服务费（成本主项）| fee_type + amount（lead/finance 可见）+ status |
| `expense_requests` | 8 类外部支出统一抽象 | expense_type（含 `outsource_engineer` 新类目）+ amount + status 审批流；vendor 角色可提交自家 |

⚠️ **没有**独立的 `ProjectMargin` / `SavingsCalc` / `ValueCreatedAggregate` / `OutsourceBenchmark` / `ProjectBudget` / `ProjectCost` 表 — 全部在 [`backend/app/services/profit.py`](backend/app/services/profit.py) 服务层按需计算（避免冗余 + 公式改动只动一处）。

### 5.5 派单 / 工时（3 张）
| 表 | 用途 | 关键字段 |
|---|---|---|
| `assignments` | 派单（工程师 × 项目 × 时段 × 角色）| status + approval_status（工程师接派单）+ planned/actual 起止 |
| `assignment_messages` | 派单双向对话留痕 | sender_kind + body |
| `timesheets` | 工时记录 | has_morning/afternoon/evening + is_workday + natural_days + **weighted_days**（晚上/非工作日 1.5×）+ approval_status |

### 5.6 知识资产 / 培训 / 发展（5 张）
| 表 | 用途 | 关键字段 |
|---|---|---|
| `knowledge_assets` | 技术沉淀归档 | category（7 类）+ confidentiality ∈ {public,internal,confidential} |
| `asset_references` | 资产被项目复用 | asset_id + project_id + estimated_hours_saved |
| `training_records` | 培训记录 | course_name + provider + hours + cost（lead/finance 可见） |
| `idps` | 个人发展计划 | target_skills + target_certs + plan_actions + status |
| `engineer_skill_snapshots` | （在 §5.1 已列）| — |

### 5.7 基础设施（2 张）
| 表 | 用途 |
|---|---|
| `data_dict` | 通用数据字典（category × code × label）— expense_type / asset_category 等都从这里 seed |
| `notification_log` | 通知历史日志 |

### 5.8 待办（PLAN 老版本列了但当前未实现）
- `Milestone` / `RiskItem` / `ComplianceEvent` / `ProjectChange` — Phase 1b-ii 待办
- `ProjectBudget` — Phase 2 标注"可选"
- `PurchaseOrder` / `ExpenseIssue` / `ExpenseApproval` 拆表 — 简化为单表 `expense_requests` + status 枚举 + approval 字段内嵌
- `AuditLog` 通用审计 — 当前只对销售转移做了 `sales_transfer_logs`，其他场景按需添加

---

## 6. 技术栈选型

| 层 | 选型 | 理由 |
|---|---|---|
| 后端 | **Python 3.12 + FastAPI** | 异步、Pydantic、OpenAPI 自动文档 |
| ORM | SQLAlchemy 2.x + Alembic | 业务实体多，严谨迁移 |
| 数据库 | **PostgreSQL 16** | 关系复杂、事务、报表、JSONB（知识资产 metadata） |
| 全文搜索 | PG 自带 `pg_trgm` + `tsvector`（Phase 4 可升 Meilisearch） | 知识资产检索够用 |
| 缓存/队列 | Redis 7 + RQ | 驾驶舱预聚合缓存 + 月结/通知/快照任务 |
| 管理后台前端 | **Vue 3 + Vite + Element Plus + Pinia** | ERP 风、中文生态 |
| 驾驶舱前端 | **Vue 3 + Vite + DataV-Vue3 + ECharts** | 大屏组件库 + 地图 |
| 鉴权 | JWT (admin) / IP白名单+token (cockpit) | 简单可控 |
| 文件存储 | 本地 → 阿里云 OSS 香港节点 (Phase 2) | 渐进 |
| 部署 | Docker Compose → K8s | 简单 |
| 日志 | Loguru + 文件轮转 | 简单 |
| 监控（Phase 3+） | Prometheus + Grafana（可选） | 长期可观测 |

---

## 7. 目录结构

```
Manpower-management-platform/
├── README.md                  ← 项目背景 + 8 大维度（每次必读）
├── PLAN.md                    ← 本文档
├── docker-compose.yml
├── .env.example
│
├── backend/                   ← FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              # 配置/鉴权/依赖注入
│   │   ├── models/            # SQLAlchemy
│   │   ├── schemas/           # Pydantic
│   │   ├── api/
│   │   │   ├── admin/         # 给管理后台用（读写）
│   │   │   └── cockpit/       # 给驾驶舱用（只读 + 预聚合）
│   │   ├── services/          # 业务逻辑（含 SavingsCalc 节省金额引擎）
│   │   ├── tasks/             # 异步任务（月结/快照/通知）
│   │   └── utils/
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
│
├── admin-web/                 ← ① 管理后台（Element Plus）
│   ├── src/
│   │   ├── api/
│   │   ├── views/             # 按 8 大维度分模块
│   │   │   ├── project/       # 4.1 项目管理（含风险/合规）
│   │   │   ├── engineer/      # 4.2 员工派单（含 Vendor/档期）
│   │   │   ├── profit/        # 4.3 利润管理（三层透视）
│   │   │   ├── expense/       # 4.4 外部支出管理
│   │   │   ├── efficiency/    # 4.5 项目完成效率
│   │   │   ├── knowledge/     # 4.7 技术沉淀 ⭐新
│   │   │   ├── capability/    # 4.8 工程师能力建设 ⭐新
│   │   │   └── relationship/  # 4.9 需求方关系/复盘 ⭐新
│   │   ├── components/
│   │   ├── stores/
│   │   └── router/
│   ├── package.json
│   └── vite.config.ts
│
├── cockpit-screen/            ← ② 驾驶舱大屏（DataV + ECharts）
│   ├── src/
│   │   ├── api/
│   │   ├── views/             # 8 个 Tab
│   │   │   ├── overview/
│   │   │   ├── project-map/
│   │   │   ├── profit-compare/
│   │   │   ├── engineer/
│   │   │   ├── efficiency/
│   │   │   ├── knowledge/     # ⭐新
│   │   │   ├── capability/    # ⭐新
│   │   │   └── relationship/  # ⭐新
│   │   ├── components/
│   │   ├── assets/
│   │   ├── stores/
│   │   └── router/
│   ├── package.json
│   └── vite.config.ts
│
└── docs/
    ├── schema.md
    ├── api.md
    └── deployment.md
```

---

## 8. 开发阶段拆分

每个阶段 = 可独立交付的版本。

### **Phase 0 — 地基** (3~5 天)
- [ ] 项目脚手架（backend + admin-web + cockpit-screen + docker-compose）
- [ ] 后端：登录、JWT、RBAC 基础
- [ ] 后端：数据字典 + 文件上传通用接口
- [ ] 管理后台：登录页 + 布局 + 菜单（8 大维度的菜单结构都摆出来）+ 用户管理
- [ ] 驾驶舱：**暗色主题壳 + 8 个 Tab 的假数据布局**
- **交付**：能登录、能传文件，驾驶舱可投屏看（假数据）

> 🎯 Phase 0 末必做：**让你/领导扫一眼驾驶舱壳子**，确认 8 个 Tab 的整体审美。

### **Phase 1 — 核心管理维度落地** (3~4 周)
聚焦"立项 → 派人 → 记工时"的最短闭环 + 能力建设字段铺底。

**1a — 人**（已完成 ✅）
- [x] **Vendor 档案** CRUD
- [x] **工程师档案** CRUD（归属 Vendor，两种签约形态）+ 技能矩阵 + 外部证书
- [x] 敏感字段加密（HKID）+ 角色脱敏 / reveal
- [x] 真实人工成本字段（lead/finance 可见）

**1b-i — 项目骨架**（已完成 ✅）
- [x] 需求方 NeedParty 档案 CRUD
- [x] **销售人员 SalesPerson** 档案 CRUD + 停用/恢复
- [x] 项目立项 + 状态机（drafting/in_progress/accepting/closing/archived）
- [x] **项目分类** `kind = revenue / no_revenue`（**仅 lead 可勾选无收入**）
- [x] **自动计算** `value_created = outsource_benchmark_amount`（R13）+ basis 枚举
- [x] 项目同时挂 SalesPerson + NeedParty 两个外键
- [x] **转移销售按钮** + SalesTransferLog 审计表（R15）

**1b-ii — 项目扩展**（待办）
- [ ] 项目里程碑 Milestone CRUD
- [ ] 风险/合规登记 RiskItem + ComplianceEvent（含 PDPO 等香港合规事件）
- [ ] 项目文档暂存
- [ ] 培训记录 CRUD（4.8 基础）

**1c — 桥**（已完成 ✅）
- [x] 派单 Assignment CRUD（工程师 × 项目 × 时段 × 角色 × 工时占比 + 状态机）
- [x] 派单"结束"按钮（一键填实际结束日）
- [x] 工时录入（单条 + bulk + Excel 导入 + 模板下载） — **单位 = 人天（0.5 步进，0.5/1.0/1.5/...，上限 3）**
- [x] 工时唯一约束 (engineer × project × work_date)
- [x] 工时审核字段铺底（approve API 已就绪，UI 在 Phase 1d 加）

**1d — 收尾**（待办）
- [ ] 档期视图（工程师月度负载占比可视化）
- [ ] 利用率指标（闲置率、满负荷预警）
- [ ] 项目看板 / 甘特图
- [ ] 工时审核 UI

**交付**：能"建一个 Vendor、登记工程师、立一个项目（带销售/客户/类型）、派人、记工时"

### **Phase 2 — 利润 + 外部支出 + 知识资产铺底**

**2a — 支出数据录入端**（已完成 ✅）
- [x] **Supplier 供应商档案**（与 Vendor 区分，含类别字段）
- [x] **6 类支出字典**自动 seed（material / subcontract / temp_labor / license / travel / other）
- [x] **ExpenseRequest** 申请审批流（pending → approved/rejected → paid）；PM 可申请，lead/finance 可审批
- [x] **VendorServiceFee** Vendor 服务费录入（按工程师月度 / 按里程碑 / 其他），可挂工程师/项目做成本归集
- [x] **项目成本归集接口** `/projects/{id}/cost-breakdown`：Vendor 服务费 + 外部支出按类型分组 + 总成本 + 外包对标
- [x] 传统外包模式对标 (`outsource_benchmark_amount`，Phase 1b 已在 Project 上铺字段，2a 已可用于对比)

**2b-i — 利润核心**（已完成 ✅）
- [x] ProjectRevenue model + CRUD（强制只允许 revenue 类项目登记收入）
- [x] **三种利润口径** API：
  - [x] 口径 A · `/api/admin/profit/overall`（lead/finance/admin）
  - [x] 口径 B · `/api/admin/profit/by-sales-person` + `/by-need-party`（含可展开的项目明细）
  - [x] 口径 C · `/api/cockpit/savings-and-value`（cockpit 守卫）
- [x] **R14 驾驶舱隔离 pytest** — 断言 `/api/cockpit/*` 任何字段名/字符串都不含 team_margin / total_revenue / vendor_fees / real_cost 等 A/B 关键字
- [x] 驾驶舱 Tab 1 总览接入真实 C 口径（"为公司创造的价值"大卡 + 节省/创造价值拆解）
- [x] `/profit` 模块 4 个 Tab：A 团队总览 / B 按销售 / B 按客户 / 项目收入登记

**2b-ii — 知识资产铺底**（已完成 ✅）
- [x] **KnowledgeAsset** model（分类 / 标签 / 摘要 / 正文 / 外链 / 附件 / 保密分级 public/internal/confidential）
- [x] `asset_category` 字典自动 seed（设计文档 / 技术方案 / 代码片段 / 问题手册 / 工艺标准 / 最佳实践 / 其他）
- [x] CRUD API + 关键词搜索（标题/摘要/标签）
- [x] **保密分级权限**：confidential 仅 admin/lead/pm/finance 可见；engineer 角色看不到机密 + 单条 GET 403
- [x] 驾驶舱 Tab 6 接入 `/api/cockpit/knowledge-stats`（累计/近 30 天/项目覆盖/分类分布）+ pytest 隔离测试

**2b-iii — 工时成本 + 项目预算**（按需，已用户决议不做"工时×单价"）
- ⏭️ ~~工时 × 工程师单价 接入成本~~ — 用户决议：成本由 VendorServiceFee 主导，不做（v0.3.7）
- [ ] 项目预算编制 ProjectBudget（可选，Phase 3 一并做）

**交付**：每个项目赚不赚钱、销售/客户层面是否欠款、节省/创造价值可算出来

### **Phase 3 — 效率 + 复盘 + 驾驶舱真数据**

**3 bulk — 6 Tab 接真数据 + 复盘域**（已完成 ✅）
- [x] ProjectRetrospective model + admin CRUD（项目复盘 + 1-5 满意度 + 做对/要改/行动项 + 闭环开关）
- [x] 5 个驾驶舱聚合接口：`project-board` / `profit-compare` / `engineer-stats` / `efficiency-stats` / `capability-stats` / `relationship-stats`
- [x] 驾驶舱 Tab 2/3/4/5/7/8 全部从 placeholder 改为真数据组件
- [x] pytest 隔离测试扩展覆盖全部 6 个新 endpoint
- [x] 管理后台 `/relationship` 模块（项目复盘 CRUD + 满意度评分 + 闭环开关）
- [x] 续单率代理指标（NeedParty 拥有 ≥2 项目 / 总客户）

**3-next-i — 知识复用 + 能力成长**（已完成 ✅）
- [x] **AssetReference** 模型：知识资产被某项目复用，可填"节省工时"折算
- [x] **EngineerSkillSnapshot** 模型 + `/api/admin/skill-snapshots/trigger` 一键拍快照接口
- [x] Cockpit Tab 6 新增 KPI：跨项目复用次数 + 节省工时
- [x] Cockpit Tab 7 新增成长曲线（季度快照 SVG 折线 + 增长 delta）
- [x] 管理后台 `/capability` 模块（KPI + 团队成长曲线 + 最新快照表 + 拍快照按钮）
- [x] 管理后台 `/knowledge` 详情抽屉新增"复用记录"区块（增/删 reference）
- [x] pytest 隔离测试扩展覆盖 `/api/cockpit/growth-trend`

**3-next-ii — 深化**（已完成 ✅）
- [x] **效率指标深化**：Project 加 `rework_count` / `change_count` 字段；驾驶舱 Tab 5 加返工率 / 人均变更次数 / 零失误交付 KPI
- [x] **IDP 个人发展计划**：IDP model + admin CRUD（/capability 下增 Tab）
- [x] **培训记录**：TrainingRecord model + admin CRUD（成本字段仅 lead/finance 可见）
- [x] **真续单率**：Project 加 `renewal_of_project_id` 自引用；驾驶舱 Tab 8 加显式续单率（与粗略代理并列展示）
- [x] **HK 简图**：Project 加 `district` 字段（HK_ISLAND/KOWLOON/NT_EAST/NT_WEST/OUTLYING）；驾驶舱 Tab 2 用 SVG 绘制港岛/九龙/新界/离岛热力图（点击区域筛选项目）
- [x] seed_demo 扩展：所有项目随机分配 district + rework/change 计数，~45% revenue 项目挂续单源；生成 76 培训 + 19 IDP

**3-next-iii — 剩余**（待办）
**3-next-iii Round 1（已完成 ✅）**
- [x] **大屏动效**：CountNumber 组件（easeOutCubic 数字滚动）+ .brag/.brag-2/.brag-growth 三类 KPI 卡循环脉冲发光 + Tab 切换淡入淡出过渡
- [x] **R6 节省金额公式打磨**：Project 加 `benchmark_basis` 枚举（vendor_quote / historical_avg / industry_benchmark / manual_estimate）+ `benchmark_basis_note` 文本；项目表单按金额可见性条件展开，详情抽屉以彩色 tag 显示可信度
- [x] 总览 Tab 用"数据健康"面板替换原占位（含数据隔离 + 三层成本透视 + 60s 刷新提示，含闪烁绿点）

**3-next-iii Round 2（已完成 ✅）**
- [x] **RenewalAttempt** 模型 + admin CRUD（outcome: pending/won/lost + 6 类输因枚举）
- [x] `/api/cockpit/relationship-stats` 扩展加 funnel（won/lost/pending）+ win_rate + lost_reason 分布
- [x] 管理后台 `/relationship` 改 2 Tab（复盘 / 续单跟踪），AttemptList 含 outcome 切换 + 条件字段
- [x] 驾驶舱 Tab 8 4 个 KPI 重做（满意度雷达 / **续单胜率** / 闭环率 / 跟踪总数）+ 右下"续单输因分布"图
- [x] CountNumber 推到 Tab 4 (engineer) / Tab 5 (efficiency) / Tab 7 (capability) / Tab 8 (relationship)
- [x] seed 自动生成 12 次续单尝试（3 赢 / 6 输 / 3 待）= 33% 胜率

**3-next-iii Round 3（已完成 ✅）**
- [x] 真 HK 地图：ECharts geo 渲染 HK 18 区，运行时从阿里 DataV CDN 拉 geoJSON
  (`https://geo.datav.aliyun.com/areas_v3/bound/810000_full.json`)；客户端把 18 区映射到我们的 5 大宏区配色；click 区域筛选项目列表；fetch 失败自动 fallback 到原 SVG schematic（带橙色警告条）

### **Phase 4 — 工程师端 + 集成 + 国际化**（按需）
- [ ] 工程师 H5/小程序：查派单、提工时、申领支出、查培训
- [ ] 企微/飞书集成（消息推送、扫码登录）
- [ ] 电子合同集成（如 DocuSign HK / e签宝）
- [ ] 报表导出 Excel/PDF
- [ ] 繁中 / 英文 i18n
- [ ] Meilisearch 升级知识资产全文检索

### **Phase 5 — 系统用户手册**（已完成 ✅ — 2026-05-24）
交付：[docs/USER_GUIDE.md](docs/USER_GUIDE.md)，含 9 大章节。

- [x] 模块功能说明（按 admin 侧栏顺序逐项） — §4 全 10 个 + 工程师端 3 个
- [x] 用户角色与权限矩阵（6 角色 × 11 模块 + 敏感字段 + 关键操作） — §2
- [x] **驾驶舱口径 C 完整计算逻辑** — §3.3（已按 v0.6 业务模型更新，
      用 bid_outcome=won 替代旧的 status=received，
      savings = benchmark − team_revenue 不再按实收封顶）
- [x] 工时加权规则（香港工作日 1.0× / 工作日晚上 + 非工作日 1.5×） — §7.3
- [x] 派单接 / 拒 / 对话留痕流程 — §7.2
- [x] 支出审批流（含 vendor 角色限制） — §7.4
- [x] 驾驶舱 5 个 Tab 各自展示什么 — §6
- [x] 常见操作 FAQ（9 个常见问题） — §8
- [x] 部署运维（本地 / 离线 / 生产 / 备份 / 升级 / 环境变量） — §9

---

## 9. 非功能性考虑

- **数据安全**：身份证号、银行卡号、薪资字段 DB 层加密（AES-GCM）
- **权限**：金额字段独立权限位；**Vendor 真实人工成本**仅负责人可见
- **审计**：所有金额变更写 AuditLog
- **知识资产保密**：按 A10 分级访问；机密资产仅团队成员可见
- **PDPO（香港隐私条例）合规**：工程师 PII 字段加密 + 数据留存策略
- **备份**：PG 每日 pg_dump，保留 30 天
- **驾驶舱性能**：预聚合 + Redis 缓存 60s
- **大屏分辨率**：默认 1920×1080，支持 4K 自适应
- **国际化**：Phase 1~3 中文，Phase 4 加 i18n
- **货币**：默认 HKD，UI `HK$`；DB numeric(18,2)

---

## 10. 风险与开放问题

| # | 问题 | 影响 | 何时必须决定 |
|---|---|---|---|
| R1 | 工程师签约形态（Vendor 直签 / Vendor 通过劳务公司） | 合同模块、字段 | Phase 1 前 |
| R2 | 内部项目结算口径（转移定价 vs 真实开票） | 利润模块 | Phase 2 前 |
| R3 | 外部支出审批流层级（单级/多级/按金额分级） | 支出模块复杂度 | Phase 2 前 |
| R4 | 驾驶舱是否需要外网访问（领导出差） | 部署架构、鉴权 | Phase 3 前 |
| R5 | 香港地图数据源（高德/百度/自有 GeoJSON） | 大屏地图 | Phase 3 前 |
| R6 | **传统外包对标公式** — "如果当年走老外包要花多少"的估算依据 | 驾驶舱核心 brag 指标 | Phase 3 前（建议 Phase 0 给出初稿）|
| R7 | PDPO（香港隐私条例）合规要求清单 | 字段设计、加密、留存 | Phase 1 前 |
| R8 | 数据初始量级（工程师/项目/月工时数） | 性能预算 | Phase 0 末 |
| R9 | **Vendor 真实人工成本能否拿到** — 协议披露 / 用户估算 / 不拿（仅做表面服务费） | 三层透视是否成立、利润模块字段 | Phase 2 前 |
| R10 | **知识资产保密分级** — 机密项是否要做加密存储？是否要做下载水印？ | 资产模块复杂度 | Phase 2 前 |
| R11 | 多 Vendor 场景下，Vendor 之间是否要做横向比较（驾驶舱 Vendor 性价比榜） | 驾驶舱 Tab 3 内容 | Phase 3 前 |
| R12 | 培训预算是否独立于项目预算（如年度培训费） | 4.8 模块与利润口径联动 | Phase 1 前 |
| ~~R13~~ ✅ | ~~无收入项目"创造价值"估算依据~~ — **已解决**：项目表勾选"无收入" → 后台自动 `value_created = outsource_benchmark_amount`；同时记 `value_created_basis` 枚举（默认 `outsource_equiv`；可选 替代审计费 / 避免罚款 / 节省工时 / 战略储备 / 其他）+ 备注。**仅 lead/admin 可勾选**。驾驶舱 Tab 3 必须拆解显示 节省 vs 创造价值。 | — | — |
| R14 | **驾驶舱接口隔离**——CI 强制断言 `/api/cockpit/*` 不返回 A/B 口径数字 | 合规风险（暴露团队真实利润）| Phase 2 前 |
| ~~R15~~ ✅ | ~~一个项目能否同时挂多个销售人员~~ — **已解决**：一个项目一个销售（单 FK `sales_person_id`）；销售离职/调岗在项目详情点"转移销售"按钮转给他人，落 `SalesTransferLog` 审计表；销售人员可设 `is_active=false` 停用。口径 B 按**当前归属**汇总。 | — | — |

---

## 11. 下一步动作（等你拍板）

1. **§0 假设表** A2–A10 哪些要改？
2. **§10 风险表** 重点：**R6 + R9** 这俩是驾驶舱"节省金额"指标的命门——
   - R6：如果让你写一句"如果走老外包，这个项目大概花 X" 的估算思路，你心里有谱吗？（同类项目均价 / 行业基准 / 一句拍脑袋？）
   - R9：Vendor 协议里能不能要求披露真实人工成本？还是只能你自己估？
3. **Phase 0 是否立刻启动**（启动 = 写脚手架、首个 commit）？
4. **git 仓库**：是否要建？要 **private**？
5. **大屏审美**：Phase 0 我会先做 8 个 Tab 的假数据壳子，你需不需要我先给 2~3 个色彩/布局原型图选审美方向？

---

*v0.3 完。*

---

## 修订历史

- **v0.3.1** (Phase 1a 完成后)：补入"三种利润口径并存"+ 项目分类（revenue/no_revenue）+ SalesPerson 实体。详见 §4.3 / §4.10 / §5 / §8 Phase 1b / R13-R15。驾驶舱新增硬约束：**永不展示口径 A**。
- **v0.3.2** (Phase 1b-i 完成后)：R13/R15 已解决。NeedParty + SalesPerson + Project + SalesTransferLog 落地；"无收入项目"勾选 + value_created 自动 = 外包估算；转移销售按钮 + 审计日志。下一步 1b-ii（里程碑 / 风险 / 合规）。
- **v0.3.3** (Phase 1c 完成后)：Assignment + Timesheet 落地，含 Excel 模板下载 + 批量导入（openpyxl）。`/engineer` 模块现有 5 个 Tab：派单（默认）/ 工时记录 / 工程师档案 / Vendor / 技能字典。工时审核 API 就绪但 UI 在 1d。
- **v0.3.4** (Phase 2a 完成后)：Supplier + ExpenseRequest（4 状态审批流）+ VendorServiceFee 三个模型落地；5 类支出字典自动 seed；项目 `/cost-breakdown` 接口归集 Vendor 服务费 + 外部支出。`/expense` 三个 Tab：外部支出 / Vendor 服务费 / 供应商。利润 A/B/C 三口径 API + 驾驶舱隔离测试留给 2b。
- **v0.3.5**：支出分类追加第 6 类 `other`（其他 — 不在前 5 类的开销），覆盖 ExpenseType 字典 seed 列表。
- **v0.3.6** (Phase 2b-i 完成后)：ProjectRevenue + 三口径 API（A/B/C）落地；pytest 强制断言驾驶舱接口不漏 A/B 字段（R14 闭环）；驾驶舱 Tab 1 接入真实 C 口径数据。`/profit` 模块 4 个 Tab。下一步 2b-ii（知识资产 + 项目预算）。
- **v0.3.7**：Timesheet 单位由「小时」改为「**人天**」(`person_days`)，0.5 自然倍数步进 (0.5/1.0/1.5/...)，单日上限 3。前后端 + Excel 模板同步；用户拍板**不**接入"人天 × 工时单价"做成本（成本仍由 VendorServiceFee 主导）。
- **v0.3.8** (Phase 2b-ii 完成后)：KnowledgeAsset 模型 + 7 类资产字典 seed + 三级保密分级（public/internal/confidential）+ 关键词搜索；engineer 角色看不到机密项；驾驶舱 Tab 6 接真数据（累计/近 30 天/项目覆盖/分类条形图 + 痛点叙事）。pytest 隔离测试覆盖到知识资产接口。下一步 Phase 3。
- **v0.3.9** (Phase 3 bulk 完成后)：ProjectRetrospective + 5 个驾驶舱聚合 endpoint + 管理后台 ⑧ 复盘模块；驾驶舱 Tab 2/3/4/5/7/8 全部从 placeholder 改为真数据组件（项目看板 / 利润对比 / 工程师视图 / 效率仪表盘 / 技能矩阵热力 / 客户满意度雷达）。pytest 隔离覆盖到 11 个 cockpit endpoint。8 Tab 真实数据全开。
- **v0.4.0** (seed_demo + Vendor 节省修复)：一次性脚本灌 30 工程师 / 28 项目 / 248 工时 / 30 资产 / 9 复盘等演示级数据；修复 Vendor 节省榜双重计数（改为按服务费比例分摊）。
- **v0.4.1** (Phase 3-next-i 完成后)：AssetReference + EngineerSkillSnapshot 两个新模型；管理后台 `/capability` 完整页（含 SVG 团队成长曲线 + 拍快照按钮）；`/knowledge` 详情抽屉加复用记录区块；驾驶舱 Tab 6 加复用 KPI、Tab 7 加成长曲线。seed_demo 生成 8 季度 × 30 工程师 = 240 快照 + 36 复用记录。
- **v0.4.2** (Phase 3-next-ii 完成后)：Project 扩展 district / rework_count / change_count / renewal_of_project_id 四个字段；新建 TrainingRecord + IDP 两域 + admin CRUD（培训成本仅 lead/finance 可见）；`/capability` 模块改为 3 Tab（成长曲线 / 培训记录 / IDP）；驾驶舱 Tab 2 改为 SVG HK schematic 5 区热力图（可点击筛选项目）；Tab 5 加返工率/人均变更/零失误 3 个 KPI；Tab 8 加显式续单率（与粗略代理并列）。seed 自动分配 5 区、~45% revenue 项目挂续单源、生成 76 培训 + 19 IDP。
- **v0.4.3** (Phase 3-next-iii Round 1 完成后)：大屏动效落地——CountNumber 组件（easeOutCubic 数字滚动）应用到 Overview/ProfitCompare/Knowledge 主 KPI；三类 brag 卡（粉/金/绿）循环脉冲发光；Tab 切换 fade-in 过渡；总览页"数据健康"面板（含跳动绿点 + 隔离守门提示）。R6 落地——Project 加 `benchmark_basis` (vendor_quote/historical/industry/manual) + note 字段；表单按金额可见性展开；详情抽屉以彩色 tag 显示可信度；seed 按 40/30/20/10 权重自动分配 basis。
- **v0.4.4** (Phase 3-next-iii Round 2 完成后)：新建 RenewalAttempt 域（outcome=pending/won/lost + 6 类输因枚举）+ admin CRUD；管理后台 `/relationship` 改 2 Tab（复盘 / 续单跟踪），AttemptList 按 outcome 条件展开字段；驾驶舱 Tab 8 重做 4 KPI（满意度 ⭐ / 续单胜率 33% / 闭环率 / 跟踪总数）+ 右下"续单输因分布"水平条形图；CountNumber 推到 Tab 4/5/7/8 主 KPI。seed 12 次尝试（3 赢/6 输/3 待）+ 6 种输因覆盖。
- **v0.4.5** (Phase 3-next-iii Round 3 完成后)：驾驶舱 Tab 2 升级为真 HK 地图——ECharts geo 运行时拉取阿里 DataV 的 HK 18 区 geoJSON 并 `registerMap('HK', geo)`；客户端把 18 区映射到原有 5 大宏区配色（港岛/九龙/新界东/新界西/离岛），项目数着色，hover tooltip 中文。fetch 失败有橙色警告条 + 自动 fallback 到原 SVG schematic 网格。echarts 让 ProjectMap chunk 涨到 ~1MB（Phase 4 再 tree-shake）。
- **v0.5.0** (2026-05-24 业务模型大改造，详见 [§20](#20-今日改动--下次开发起点))：
  全面校准业务模型——Project 加 `bid_outcome` (won/pending/lost/escaped)、ProjectRevenue 加 `non_service_expense`、删除 ProjectRevenue.status。`compute_company_margin_lift` 公式重写含非服务开销。删 4 个 value_basis 枚举只剩 2 个、删 2 个 benchmark_basis 只剩 2 个、cert_level 从 L1-L5 砍回 L1-L3。RevenueList 挪到「项目和客户管理 → 收入列表」+ benchmark/basis/gross/non_service_expense 全必填。首页大改 4 段式仪表盘。Seed 按业务比例校准（团队入账=客户付款 20%，非服务开销=客户付款 70%，team_revenue=benchmark×0.8-0.9）。

---

## 20. Changelog（关键里程碑）

> 字段、公式、枚举的"当前真相"以 [docs/VARIABLES.md](docs/VARIABLES.md) 为准。
> 本节只记录关键节点的语义变更，方便追溯"为什么会这样"。

### v0.5.0 — 业务模型定稿（2026-05-24）

**核心动作**：从"团队收入 − 成本 = 利润"的朴素模型 → "Vendor pass-through + 资金流 4 字段"模型，重写 admin 端利润公式。

| 改动 | 文件 / Migration |
|---|---|
| 加 `Project.bid_outcome` 枚举（pending/won/lost/escaped）| [models/project.py](backend/app/models/project.py) / `h8i9j0k1l2m3` |
| `value_created_basis` 6 → 2 选项 | [models/project.py](backend/app/models/project.py) / `i9j0k1l2m3n4` |
| `benchmark_basis` 4 → 2 选项 | [schemas/project.py](backend/app/schemas/project.py) / `j0k1l2m3n4o5` |
| 加 `ProjectRevenue.non_service_expense` 字段（回填 = gross × 0.70）| [models/project_revenue.py](backend/app/models/project_revenue.py) / `k1l2m3n4o5p6` |
| `cert_level` L1-L5 → L1-L3 | [models/engineer.py](backend/app/models/engineer.py) |
| `ProjectRevenue.status` UI 移除（DB column 保留）| 无 migration |
| 加 ExpenseType `outsource_engineer`（vendor 付工程师/劳务公司的钱）| [models/expense.py](backend/app/models/expense.py) |
| 团队利润公式：`team_margin = Σ VSF − Σ 全部支出`（去掉 `+ revenue`）| [services/profit.py](backend/app/services/profit.py) |
| FDE 利润率对比含 `non_service_expense` | [services/profit.py](backend/app/services/profit.py) |
| 首页改 4 段式仪表盘（KPI / 项目盘面 / 财务 / 风险预警）| [Home.vue](admin-web/src/views/dashboard/Home.vue) |
| 收入登记挪进"项目和客户管理"，5 字段必填 | [admin-web/src/views/project/](admin-web/src/views/project/) |

**业务规则确认**（已记 memory）：
- benchmark **只来自真实询价**（vendor_quote/historical_avg），没询价就空
- B 口径里 no_revenue 项目按 benchmark 算机会成本，毛利 = −benchmark

---

### v0.4.x — Phase 3-next 三轮精修（2026-05 早期）

- **Round 1**：CountNumber 数字滚动 + 三类 brag 卡循环脉冲 + Tab 切换 fade-in + 数据健康面板 + `benchmark_basis` 4 选项枚举
- **Round 2**：`RenewalAttempt` 域（outcome + 6 类输因）+ 驾驶舱 Tab 8 续单胜率漏斗 + CountNumber 推到 4/5/7/8
- **Round 3**：真 HK 地图（ECharts geo + 阿里 DataV `810000_full.json`，18 区映射 5 大宏区，fallback SVG）

### v0.4.2 — 项目深化字段

`Project` 加 `district / rework_count / change_count / renewal_of_project_id` 四字段；新建 `TrainingRecord` + `IDP` 两域；驾驶舱 Tab 5 加返工率 / 人均变更 / 零失误 3 KPI。

### v0.4.1 — 知识复用 + 能力成长

`AssetReference` + `EngineerSkillSnapshot` 两个新模型；admin `/capability` 完整页（SVG 团队成长曲线 + 拍快照按钮）；`/knowledge` 详情抽屉加复用记录区块。

### v0.4.0 — Seed Demo 灌量级数据

一次性脚本灌 30 工程师 / 28 项目 / 248 工时 / 30 资产 / 9 复盘等演示级数据；修复 Vendor 节省榜双重计数（改为按服务费比例分摊）。

### v0.3.9 — Phase 3 bulk 完成

`ProjectRetrospective` + 5 个驾驶舱聚合 endpoint + admin `/relationship` 模块；驾驶舱 Tab 2/3/4/5/7/8 全部从 placeholder 改为真数据组件；pytest 隔离覆盖到 11 个 cockpit endpoint。

### v0.3.8 — Phase 2b-ii 完成

`KnowledgeAsset` + 7 类资产字典 seed + 三级保密分级（public/internal/confidential）+ 关键词搜索；engineer 角色看不到机密项；驾驶舱 Tab 6 接真数据。

### v0.3.7 — 工时改人天

Timesheet 单位由"小时"改为"人天"(`person_days`)，0.5 自然倍数步进，单日上限 3；用户拍板**不**接入"人天 × 单价"做成本（成本仍由 VendorServiceFee 主导）。

### v0.3.6 — Phase 2b-i 完成

`ProjectRevenue` + 三口径 API（A/B/C）落地；pytest 强制断言驾驶舱接口不漏 A/B 字段（R14 闭环）；驾驶舱 Tab 1 接入真实 C 口径数据。

### v0.3.5 — 支出 6 类（v0.5 已扩到 8）

支出分类追加第 6 类 `other`，覆盖 ExpenseType 字典 seed 列表。

### v0.3.4 — Phase 2a 完成

`Supplier` + `ExpenseRequest`（4 状态审批流）+ `VendorServiceFee` 三个模型落地；项目 `/cost-breakdown` 接口归集 Vendor 服务费 + 外部支出。

### v0.3.3 — Phase 1c 完成

`Assignment` + `Timesheet` 落地，含 Excel 模板下载 + 批量导入（openpyxl）。`/engineer` 模块 5 个 Tab。

### v0.3.2 — Phase 1b-i 完成

R13/R15 已解决。`NeedParty` + `SalesPerson` + `Project` + `SalesTransferLog` 落地；"无收入项目"勾选 + value_created 自动 = 外包估算；转移销售按钮 + 审计日志。

### v0.3.1 — Phase 1a 完成后

补入"三种利润口径并存"+ 项目分类（revenue/no_revenue）+ `SalesPerson` 实体。驾驶舱硬约束：**永不展示口径 A**。

---

### Phase 5 — 系统用户手册（2026-05-24 交付）

[docs/USER_GUIDE.md](docs/USER_GUIDE.md) 9 大章节，含模块功能 / 权限矩阵 / 驾驶舱口径 C 计算逻辑 / 工时加权规则 / 派单接拒流程 / 支出审批流 / 9 个 FAQ / 部署运维。

### 2026-05-26 — 关键变量手册

[docs/VARIABLES.md](docs/VARIABLES.md) 落地：17 个表字段速查 + 4 大金额公式 + 枚举大全 + 权限矩阵 + 驾驶舱守门规则 + 8 条命门踩坑提示。改字段或公式时优先更新此文件。
