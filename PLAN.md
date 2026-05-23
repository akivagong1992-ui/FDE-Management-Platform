# Manpower Management Platform — 项目规划 (PLAN)

> 版本: **v0.3** (按"项目服务费供人链路"+ 8 大管理维度重写)
> 编写日期: 2026-05-23
> v0.1 已废弃（错误视角："劳务派遣公司自用"）
> v0.2 已废弃（未含 Vendor 链路、未含知识资产/能力建设/复盘三维度）
>
> **阅读顺序**：先读 [README.md](README.md)（背景 + 8 大维度 + Vendor 链路），再读本文档（实施方案）

---

## 0. 待你评审的关键假设

下列假设直接影响系统结构，请先评审，**不对的地方点出来，我改完 PLAN 再开始编码**。

| # | 假设项 | 当前默认 | 备选 |
|---|---|---|---|
| A1 | **业务视角** | 甲方用工方（电信HK 自用） | （已锁定） |
| A2 | **供人结构** | 「电信 → Vendor → 劳务公司 → 工程师」三层链路（项目服务费形式） | （已锁定，但 Vendor 数量未定，见 R9）|
| A3 | **项目来源** | 主要是电信集团内部工程订单；少量对外项目 | 全部对外 / 全部内部 |
| A4 | **利润口径（关键！见 README §1.5）** | **三种口径并存**：A 团队整体利润（内部正数）/ B 销售-项目维度（可正负，按销售人/客户汇总）/ C 驾驶舱对外（节省金额+无收入项目创造价值）。**驾驶舱绝不展示口径 A**。 | — |
| A4b | **项目分类** | `kind=revenue` 有收入项目 / `kind=no_revenue` 无收入项目（必填"估算创造价值"金额）| — |
| A4c | **销售维度** | 项目同时挂 SalesPerson（销售人员）+ NeedParty（客户/需求方）两个外键，两个维度都可汇总利润 | 单维度 |
| A5 | **货币** | 港币 HKD 为主 | 多币种 |
| A6 | **语言** | 简体中文，Phase 4 加繁中/英文 i18n | 一开始就多语 |
| A7 | **驾驶舱观看者认证** | 内网 IP 白名单 + 单次 token；不要求领导登录 | 必须登录 |
| A8 | **部署** | 内网/云 Docker Compose 自部署 | 全托管 |
| A9 | **规模** | 50~200 工程师，10~50 并行项目，2~5 个 Vendor | 更大需另设计 |
| A10 | **知识资产保密** | 默认按项目敏感度分级（公开/内部/机密），仅团队成员可见机密项 | 全部公开 / 全部机密 |

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

### 4.3 利润管理（README §3 维度 2）— **三种口径并存**（详见 README §1.5）

> ⚠️ 三个口径的数据**完全独立**展示，互不混淆，因为受众不同。

#### 口径 A · 团队整体利润（内部对账，**必为正数**）
公式：
```
A = Σ 所有项目收入  −  Σ Vendor 服务费  −  Σ 外部支出
```
- 仅管理后台 lead / finance 可见
- 显示位置：管理后台 → 利润管理 → "团队总览"卡片
- 用于内部对账、税务、汇报母公司财务

#### 口径 B · 销售-项目维度（可正可负）
- 每个项目实时计算 `project_margin = 收入 − 成本`（成本 = 服务费 + 外部支出 + 杂费分摊）
  - 有收入项目：可正可负
  - 无收入项目：margin = -成本（始终负数），不进入口径 B 视图
- **两个聚合按钮**（管理后台 → 利润管理 → "销售维度")：
  - 「按销售人员汇总」按 `sales_person_id` 分组 → 该销售名下所有项目累计 margin
  - 「按客户汇总」按 `need_party_id` 分组 → 该客户名下所有项目累计 margin
- 红/绿/灰标记：盈利绿、亏损红、未完成灰
- 用途：催回款、判断哪个销售/客户净亏、决定是否继续合作

#### 口径 C · 驾驶舱对外口径（节省 + 创造价值）
公式：
```
C = Σ (传统外包模式估算 − 实际成本)  +  Σ 无收入项目的 value_created
       └─── 节省 ────────────────────┘     └── 创造价值 ──┘
```
- 传统外包模式估算：基于历史项目均价 / 行业基准 / 同类外包报价单（R6）
- 实际成本 = Vendor 服务费 + 外部支出
- value_created = 无收入项目 PM 填写的"估算创造价值"
- **驾驶舱里所有'金额类'指标只能来自这里**
- 输出位置：驾驶舱 Tab 1 总览的 "累计创造的价值" 大卡 + Tab 3 利润对比页

#### 共用基础数据
- **项目预算**：人工服务费预算 + 外部支出预算 + 杂费 + 含税
- **收入登记**：内部转移定价 / 外部合同金额 / 分期到账（仅 revenue 类项目）
- **Vendor 真实人工成本**（README §1.4 链路第二层）：用于 Vendor 性价比分析（仅 lead 可见）
- **Vendor 性价比分析**：服务费 / 真实成本 比、议价记录

#### 关键约束
- 任何驾驶舱接口（`/api/cockpit/*`）**禁止返回 A 或 B 口径的数字**——CI 测试需断言这一点
- 利润 API 按 `Accept-Profile: admin|cockpit` 头分流，避免误用

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
> 不是 4.1~4.9 的报表汇总，是独立工程、独立 UI 风格、独立路由。

**页面结构（多 Tab 自动轮播）**：

| Tab | 内容 |
|---|---|
| 1 · 总览 | 4 个核心 KPI（在管项目数、**累计创造价值**、团队规模、**累计节省金额**）+ 香港项目地图 + 月度创造价值曲线。⚠️ **不展示团队真实毛利** |
| 2 · 项目地图 | 香港地图标点，点击/轮播显示项目卡片（项目名、PM、状态、**节省金额或创造价值**——不展示真实毛利） |
| 3 · 利润对比 ⭐核心 brag | 仅口径 C：①传统外包模式 vs 自办 — 累计节省 ②有收入项目的节省 vs 无收入项目的创造价值（堆叠柱）③Vendor 性价比榜（服务费/真实成本比）。**绝不展示口径 A/B 数字** |
| 4 · 工程师视图 | 团队规模增长、技能矩阵雷达、Top 5 满负荷、Vendor 分布 |
| 5 · 效率榜 | 当月 Top 项目、Top 工程师、按时交付率仪表盘 |
| 6 · **技术沉淀** ⭐新 | 累计资产数（按类别条形图）、复用次数热力、节省工时金额 |
| 7 · **团队能力** ⭐新 | 技能矩阵热力图、季度能力成长曲线、累计证书墙 |
| 8 · **客户口碑** ⭐新 | 满意度雷达、续单率仪表盘、复盘闭环率、需求方关系热度 |

**视觉**：
- 暗色背景（#0A1929 或 #061327），霓虹蓝/青/品红高亮
- 数字滚动动效（vue3-count-to）
- 流光线、发光边框（DataV-Vue3）
- 香港地图（ECharts geoJSON）
- 默认 1920×1080，4K 自适应

**数据源**：
- 后端 `/api/cockpit/*` 预聚合（Redis 缓存 60s）
- 不接管理后台 CRUD（隔离性能/权限）

---

## 5. 数据模型（核心实体，简版）

```
User                       系统操作员
Role / Permission          RBAC

Vendor                     供人公司（项目服务费链路的中间方）
  ├─ VendorContract        与电信的项目服务合同
  └─ VendorServiceFee      实际支付服务费（月度/里程碑结算单）

Engineer                   外包工程师档案（归属 Vendor）
  ├─ EngineerSkill         技能项（多对多）
  ├─ EngineerCertificate   外部认证（CCIE/CISSP/...）
  ├─ EngineerTraining      培训记录（4.8）
  ├─ EngineerSkillSnapshot 技能矩阵季度快照（4.8）
  ├─ EngineerIDP           个人发展计划（4.8）
  └─ VendorEngineerCost    Vendor 真实人工成本（估算/披露，三层透视第二层）

NeedParty                  需求方/客户档案（电信内部部门 / 外部合同方）
SalesPerson                销售人员/业务员（B 口径汇总维度之一）

Project                    项目
  ├─ kind                  revenue / no_revenue
  ├─ value_created         仅 no_revenue 项目用，估算创造价值 (HKD)
  ├─ sales_person_id       FK → SalesPerson（B 口径按销售汇总）
  ├─ need_party_id         FK → NeedParty（B 口径按客户汇总）
  ├─ Milestone             里程碑
  ├─ RiskItem              风险登记（含合规/安全事件，子维度 D）
  ├─ ComplianceEvent       合规/安全事件
  ├─ ProjectChange         变更记录
  ├─ ProjectBudget         预算（人工/外部支出/杂费）
  └─ OutsourceBenchmark    传统外包模式估算（C 口径用）

Assignment                 派单（Engineer × Project × 时段 × 角色 × 工时占比）

Timesheet                  工时（日报/周报粒度）

ExternalExpense            外部支出项（统一抽象，含类型字段）
  ├─ ExpenseType           支出分类字典（耗材/分包/临时人力/许可/差旅/其他）
  ├─ ExpenseRequest        申请单
  ├─ ExpenseApproval       审批流
  ├─ PurchaseOrder         采购单（耗材类需要）
  └─ ExpenseIssue          领用/分摊（必关联 Project）

Supplier                   外部支出供应商（与 Vendor 区分）

ProjectRevenue             项目收入（内部计价/外部合同；仅 revenue 类项目）
ProjectCost                项目成本（Timesheet→服务费 + ExternalExpense 自动汇总）
ProjectMargin              项目毛利（视图/物化，仅 B 口径用，可正可负）
SavingsCalc                节省金额计算（C 口径：OutsourceBenchmark − 实际成本）
ValueCreatedAggregate      创造价值汇总（C 口径：Σ revenue项目节省 + Σ no_revenue项目value_created）

EfficiencyMetric           效率指标快照（月度滚动）

KnowledgeAsset             知识资产（4.7）
  ├─ AssetCategory         分类字典
  ├─ AssetAttachment       附件
  ├─ AssetReference        资产引用记录（哪个项目复用了哪个资产）
  └─ AssetUsageSaving      复用节省工时折算

ProjectRetrospective       项目复盘（4.9）
  ├─ SatisfactionScore     需求方满意度评分
  ├─ RetroNote             复盘记录（做对的/要改的）
  ├─ ActionItem            行动项（含闭环状态）
  └─ RenewalTracking       续单跟踪

Notification               通知
AuditLog                   审计日志
DataDict                   数据字典
```

详细 schema（字段、外键、索引）在 Phase 0 输出 `docs/schema.md`。

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

**3 next — 深化**（待办）
- [ ] **效率指标深化**：人均交付、返工率、变更次数
- [ ] **能力成长曲线**：EngineerSkillSnapshot 季度快照 + IDP 个人发展计划
- [ ] **知识资产复用追踪**：AssetReference + 节省工时折算
- [ ] 完整 RenewalTracking model（替代当前粗略代理）
- [ ] 大屏动效打磨、自动轮播、4K 适配
- [ ] **节省金额** brag 指标公式打磨（R6）
- [ ] HK 地图组件（替代项目看板，需 geoJSON）

### **Phase 4 — 工程师端 + 集成 + 国际化**（按需）
- [ ] 工程师 H5/小程序：查派单、提工时、申领支出、查培训
- [ ] 企微/飞书集成（消息推送、扫码登录）
- [ ] 电子合同集成（如 DocuSign HK / e签宝）
- [ ] 报表导出 Excel/PDF
- [ ] 繁中 / 英文 i18n
- [ ] Meilisearch 升级知识资产全文检索

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
