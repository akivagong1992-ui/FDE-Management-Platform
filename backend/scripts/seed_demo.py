"""Demo seed — wipes DB + rebuilds with ~30 projects / 30 engineers / 50 retros etc.

Run:  uv run python -m scripts.seed_demo

Designed so all 8 cockpit tabs light up convincingly for leadership demos.
Idempotent: drops + recreates SQLite db every run.
"""

import asyncio
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.crypto import encrypt_field
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.asset_reference import AssetReference
from app.models.assignment import Assignment
from app.models.data_dict import DataDict
from app.models.engineer import Certificate, Engineer
from app.models.expense import EXPENSE_TYPE_DEFAULTS, ExpenseRequest
from app.models.idp import IDP
from app.models.knowledge_asset import ASSET_CATEGORY_DEFAULTS, KnowledgeAsset
from app.models.need_party import NeedParty
from app.models.project import HK_DISTRICTS, Project, ProjectComment
from app.models.project_revenue import ProjectRevenue
from app.models.renewal_attempt import RenewalAttempt
from app.models.retrospective import ProjectRetrospective
from app.models.sales_person import SalesPerson
from app.models.skill import EngineerSkill, Skill
from app.models.skill_snapshot import EngineerSkillSnapshot
from app.models.supplier import Supplier
from app.models.timesheet import Timesheet
from app.models.training import TrainingRecord
from app.models.user import User
from app.models.vendor import Vendor
from app.models.vendor_service_fee import VendorServiceFee

random.seed(20260523)
TODAY = date(2026, 5, 23)


# ── Reference data ─────────────────────────────────────────────────────

VENDORS = [
    ("汇捷信息科技", "汇捷", "陈先生", "+852 9001 0001", "月结30天"),
    ("港兴通信工程", "港兴", "黄经理", "+852 9001 0002", "月结45天"),
    ("智联科技顾问", "智联", "刘总监", "+852 9001 0003", "月结30天"),
    ("华域 IT 服务", "华域", "梁经理", "+852 9001 0004", "月结60天"),
]

# 业务真实情况：销售面向「电信之外」的外部企业客户，无集团内部门
NEED_PARTIES = [
    ("汇丰银行（HSBC）", "银行", "李先生"),
    ("渣打银行（Standard Chartered）", "银行", "陈女士"),
    ("港铁公司（MTR）", "公用事业", "黄经理"),
    ("香港机管局（HKAA）", "政府机构", "张总监"),
    ("国泰航空（Cathay Pacific）", "物流 / 航运", "刘先生"),
    ("香港交易所（HKEX）", "证券", "周经理"),
    ("招商局港口控股", "中资企业", "钱总"),
    ("太古地产（Swire Properties）", "港资企业", "孙总监"),
    ("嘉里物流（Kerry Logistics）", "物流 / 航运", "吴经理"),
    ("友邦保险（AIA）", "保险", "郑先生"),
]

SALES_PEOPLE = [
    ("张志明", "E001", "业务一部", True),
    ("陈丽华", "E002", "业务一部", True),
    ("李建国", "E003", "业务二部", True),
    ("王晓雯", "E004", "业务二部", False),  # 已离职
    ("黄家辉", "E005", "战略客户部", True),
]

ENGINEER_NAMES = [
    "李志强", "陈伟明", "王俊杰", "张志豪", "刘思雅", "梁建华", "黄文彬", "周敏君",
    "吴俊熙", "郑家豪", "韩天宇", "宋静怡", "孙志强", "曹宇航", "钱泽宇", "杨敏",
    "卢家俊", "邓子健", "麦家俊", "罗志伟", "余佩珊", "潘文杰", "胡浩然", "马晓东",
    "唐丽琴", "范俊宇", "彭瑞祺", "苏文豪", "蒋家俊", "贾敏",
]

# 技能 / 认证目录（2026-05-25 重构）：每条 = (认证名称, 分类, 厂商, 等级 L1/L2/L3)
# 工程师挂技能即引用此目录某一条
SKILLS = [
    # 网络能力
    ("CCIE 路由交换", "网络能力", "Cisco", "L3"),
    ("华为 HCIE-数通", "网络能力", "华为", "L3"),
    ("CCNP 企业网络", "网络能力", "Cisco", "L2"),
    ("华为 HCIP-数通", "网络能力", "华为", "L2"),
    ("CCNA", "网络能力", "Cisco", "L1"),
    ("5G NR 无线", "网络能力", "中国移动", "L2"),
    # 安全能力
    ("CISSP", "安全能力", "ISC2", "L3"),
    ("CISA", "安全能力", "ISACA", "L3"),
    ("OSCP 攻防", "安全能力", "Offensive Security", "L3"),
    ("CCNP 安全", "安全能力", "Cisco", "L2"),
    ("CompTIA Security+", "安全能力", "CompTIA", "L1"),
    # 弱电能力
    ("RCDD 综合布线设计师", "弱电能力", "BICSI", "L2"),
    ("综合布线工程师初级", "弱电能力", "中国建筑学会", "L1"),
    ("机房工程认证", "弱电能力", "TIA", "L2"),
    # 云能力
    ("AWS Solutions Architect Professional", "云能力", "AWS", "L3"),
    ("Google Cloud Architect", "云能力", "Google", "L3"),
    ("AWS Solutions Architect Associate", "云能力", "AWS", "L2"),
    ("CKA Kubernetes", "云能力", "CNCF", "L2"),
    ("华为 HCIA-Cloud", "云能力", "华为", "L1"),
    ("AWS Cloud Practitioner", "云能力", "AWS", "L1"),
    # 数据能力
    ("Cloudera CCP Data Engineer", "数据能力", "Cloudera", "L3"),
    ("华为 HCIP-大数据", "数据能力", "华为", "L2"),
    ("华为 HCIA-大数据", "数据能力", "华为", "L1"),
    # AI 能力
    ("AWS Machine Learning Specialty", "AI 能力", "AWS", "L3"),
    ("TensorFlow Developer", "AI 能力", "Google", "L2"),
    ("NVIDIA DLI 入门认证", "AI 能力", "NVIDIA", "L1"),
]

# 厂商认证：(name, issuer, cert_category, cert_level)
# cert_level: L1 初级 / L2 中级 / L3 高级
# 类别与 SKILLS 同枚举（6 类）
CERTS = [
    # L3 高级
    ("CCIE 路由交换", "Cisco", "网络能力", "L3"),
    ("华为 HCIE-数通", "华为", "网络能力", "L3"),
    ("CISSP", "ISC2", "安全能力", "L3"),
    ("CISA", "ISACA", "安全能力", "L3"),
    ("AWS Solutions Architect Professional", "AWS", "云能力", "L3"),
    ("AWS Machine Learning Specialty", "AWS", "AI 能力", "L3"),
    # L2 中级
    ("AWS Solutions Architect Associate", "AWS", "云能力", "L2"),
    ("CKA", "CNCF", "云能力", "L2"),
    ("CCNP 安全", "Cisco", "安全能力", "L2"),
    ("华为 HCIP-数通", "华为", "网络能力", "L2"),
    ("华为 HCIP-大数据", "华为", "数据能力", "L2"),
    ("RCDD 综合布线设计师", "BICSI", "弱电能力", "L2"),
    ("TensorFlow Developer", "Google", "AI 能力", "L2"),
    # L1 初级
    ("CCNA", "Cisco", "网络能力", "L1"),
    ("华为 HCIA-Cloud", "华为", "云能力", "L1"),
    ("华为 HCIA-大数据", "华为", "数据能力", "L1"),
    ("AWS Cloud Practitioner", "AWS", "云能力", "L1"),
    ("CompTIA Security+", "CompTIA", "安全能力", "L1"),
    ("综合布线工程师初级", "中国建筑学会", "弱电能力", "L1"),
    ("NVIDIA DLI 入门认证", "NVIDIA", "AI 能力", "L1"),
]

PROJECT_TEMPLATES_REVENUE = [
    "九龙湾基站 5G 扩容", "中环网络升级", "数据中心机房改造", "海底光缆维护-第{n}期",
    "客户 BSS 系统升级", "OSS 监控平台优化", "IDC 安全加固", "客户专线开通-{client}",
    "云迁移服务-{client}", "网络设备替换", "VPN 端点扩容", "API 网关重构",
    "新界基站巡检", "数据备份系统迁移", "智能客服平台搭建", "邮件系统迁移",
    "Wi-Fi 6 部署 - 写字楼 {n}", "IPv6 改造-第{n}期", "客户数据中台",
    "实时风控引擎",
]

PROJECT_TEMPLATES_NO_REVENUE = [
    "内部合规扫描 2026", "PDPO 隐私审计准备", "员工安全意识培训平台",
    "内部知识库重构", "团队 DevOps 工具链统一", "故障演练自动化",
    "运维监控告警优化", "灾备演练-{n}",
]

EXPENSE_TITLES = {
    "material": ["光纤跳线 30 条", "万兆 SFP 模块 20 个", "工业级交换机 2 台",
                 "工具箱 + 测试仪", "标签机 + 标签纸", "千兆 PoE 注入器 10 个"],
    "subcontract": ["渗透测试外包", "UI/UX 专项设计", "第三方代码审计",
                    "合规咨询服务", "光纤布放分包 - 新界"],
    "temp_labor": ["短期实施工程师 - 周末", "应急运维顶班", "数据迁移 24h 值班"],
    "license": ["Atlassian 年费", "GitHub Copilot 团队版", "Splunk Enterprise",
                "Datadog APM", "Microsoft 365 E5"],
    "travel": ["新加坡 5G 峰会", "深圳客户拜访", "九龙基站现场出差", "东京 ICT 培训"],
    "other": ["团队建设活动", "新工程师入职装备", "应急加班餐补", "电子合同年费"],
}

ASSET_TITLES = {
    "design_doc": ["5G 核心网架构设计 v2", "光纤拓扑标准图集", "IDC 机柜布线规范",
                   "客户 BSS 总体设计", "OSS 监控架构图"],
    "tech_solution": ["统一鉴权方案", "API 网关高可用方案", "数据中台分层方案",
                      "灰度发布方案", "应急切换方案"],
    "code_snippet": ["OAuth2 client 通用片段", "K8s Operator 脚手架",
                     "Prometheus 通用 alert 规则", "FastAPI 工程模板", "ECharts 大屏组件库"],
    "troubleshoot": ["BGP 收敛慢排查手册", "K8s 网络丢包速查", "DB 慢查询案例集",
                     "光路 OTDR 故障定位 SOP"],
    "standard": ["代码评审规范", "运维变更管控规范", "应急响应 SOP",
                 "供应商接入安全规范"],
    "best_practice": ["跨项目复用经验", "微服务拆分指南",
                       "CI/CD 工程实践", "技术债治理"],
    "other": ["年度技术雷达", "工具采购建议", "团队学习路径图"],
}


# ── Helpers ────────────────────────────────────────────────────────────

def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def random_date_within(start_days_ago: int, end_days_ago: int = 0) -> date:
    return days_ago(random.randint(end_days_ago, start_days_ago))


def fmt_int(n: int) -> str:
    return f"{n:,}"


# ── Main seed ──────────────────────────────────────────────────────────

async def main() -> None:
    print("⏳ Dropping & recreating tables…")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # ── Users ─────────────────────────────────────────────────────
        admin = User(username="admin", full_name="Team Lead", role="lead",
                     hashed_password=hash_password("admin123"))
        finance = User(username="finance", full_name="财务王", role="finance",
                       hashed_password=hash_password("fin123"))
        pm = User(username="pm1", full_name="项目经理", role="pm",
                  hashed_password=hash_password("pm123"))
        # 通用 engineer 测试账号（未关联具体 engineer_id，仅用于早期联调）
        engineer_user = User(username="eng1", full_name="基层工程师", role="engineer",
                             hashed_password=hash_password("eng123"))
        db.add_all([admin, finance, pm, engineer_user])
        await db.flush()
        print(f"  ✓ users x{4} (engineer 个人账号见下方派单环节后追加)")

        # ── Dictionaries ──────────────────────────────────────────────
        for idx, (code, label) in enumerate(EXPENSE_TYPE_DEFAULTS):
            db.add(DataDict(category="expense_type", code=code, label=label, sort_order=idx))
        for idx, (code, label) in enumerate(ASSET_CATEGORY_DEFAULTS):
            db.add(DataDict(category="asset_category", code=code, label=label, sort_order=idx))
        await db.flush()
        print(f"  ✓ data dicts (expense_type x{len(EXPENSE_TYPE_DEFAULTS)}, "
              f"asset_category x{len(ASSET_CATEGORY_DEFAULTS)})")

        # ── Vendors ───────────────────────────────────────────────────
        vendor_objs = []
        for name, short, contact, phone, terms in VENDORS:
            v = Vendor(name=name, short_name=short, contact_person=contact,
                       contact_phone=phone, payment_terms=terms, cooperation_status="active")
            db.add(v); vendor_objs.append(v)
        await db.flush()
        print(f"  ✓ vendors x{len(vendor_objs)}")

        # ── Vendor users ──────────────────────────────────────────────
        # 每个 vendor 公司预装一个登录账号 (用户名 v1..vN / 密码 demo123)
        # role=vendor，只能看 / 提交自己 vendor 名下的 ExpenseRequest
        vendor_users = []
        for idx, v in enumerate(vendor_objs, start=1):
            vu = User(
                username=f"v{idx}", full_name=f"{v.short_name} 联系人",
                role="vendor", vendor_id=v.id,
                hashed_password=hash_password("demo123"),
            )
            db.add(vu); vendor_users.append(vu)
        await db.flush()
        print(f"  ✓ vendor 登录账号 x{len(vendor_users)} (v1..v{len(vendor_users)} / demo123)")

        # ── NeedParties ───────────────────────────────────────────────
        np_objs = []
        for name, ptype, contact in NEED_PARTIES:
            np = NeedParty(name=name, party_type=ptype, contact_person=contact,
                           contact_phone=f"+852 8{random.randint(100,999)} {random.randint(1000,9999)}")
            db.add(np); np_objs.append(np)
        await db.flush()
        print(f"  ✓ need parties x{len(np_objs)}")

        # ── SalesPeople ───────────────────────────────────────────────
        sp_objs = []
        for name, eid, dept, active in SALES_PEOPLE:
            sp = SalesPerson(name=name, employee_id=eid, department=dept, is_active=active,
                             email=f"{eid.lower()}@telecom-hk.com")
            db.add(sp); sp_objs.append(sp)
        await db.flush()
        print(f"  ✓ sales people x{len(sp_objs)} (1 已停用)")

        # ── Skills ────────────────────────────────────────────────────
        skill_objs = []
        for name, cat, issuer, level in SKILLS:
            s = Skill(name=name, category=cat, issuer=issuer, level=level, is_active=True)
            db.add(s); skill_objs.append(s)
        await db.flush()
        print(f"  ✓ skills x{len(skill_objs)}")

        # ── Engineers ─────────────────────────────────────────────────
        # 个人评级（engineers.level）已废除，仅靠厂商认证体现工程师水平
        eng_objs = []
        for name in ENGINEER_NAMES:
            vendor = random.choice(vendor_objs)
            monthly_cost = Decimal(random.randint(18, 65)) * 1000  # 18K-65K
            e = Engineer(
                vendor_id=vendor.id,
                employment_form=random.choice(["vendor_direct", "vendor_via_labor"]),
                labor_company=random.choice(["香港人力中介", "粤港劳务", "联众派遣", None]),
                full_name=name,
                gender=random.choice(["M", "F"]),
                mobile=f"+852 9{random.randint(100,999)} {random.randint(1000,9999)}",
                id_doc_type="HKID",
                id_doc_number_enc=encrypt_field(f"A{random.randint(1000000, 9999999)}({random.randint(1, 9)})"),
                level=None,
                status=random.choices(["active", "departed"], weights=[90, 10])[0],
                entry_date=random_date_within(540, 30),
                monthly_cost_to_telecom=monthly_cost,
            )
            db.add(e); eng_objs.append(e)
        await db.flush()
        print(f"  ✓ engineers x{len(eng_objs)}")

        # ── Skills × Engineers ────────────────────────────────────────
        # EngineerSkill.level 已停用，仅保留「会/不会」标记（level=0 当占位）
        for e in eng_objs:
            for s in random.sample(skill_objs, k=random.randint(2, 5)):
                db.add(EngineerSkill(engineer_id=e.id, skill_id=s.id, level=0))
        await db.flush()

        # ── Certificates ──────────────────────────────────────────────
        # 厂商认证带 cert_level (L1/L2/L3) + cert_category，是工程师水平的唯一客观依据
        cert_count = 0
        for e in eng_objs:
            if random.random() < 0.7:  # 70% 工程师至少有一张
                for cert_name, issuer, category, level in random.sample(CERTS, k=random.randint(1, 3)):
                    db.add(Certificate(
                        engineer_id=e.id, name=cert_name, issuer=issuer,
                        cert_category=category, cert_level=level,
                        issue_date=random_date_within(900, 200),
                        expiry_date=random_date_within(-180, -720) if random.random() < 0.7 else None,
                    ))
                    cert_count += 1
        await db.flush()
        print(f"  ✓ engineer skills + {cert_count} certificates (含 cert_level/category)")

        # ── Projects ──────────────────────────────────────────────────
        # 真实业务模型驱动的生成：
        #   bid_outcome ∈ {won 70%, pending 12%, lost 12%, escaped 6%}
        #   status 与 bid_outcome 协调（pending → drafting；lost → drafting/cancelled）
        #   benchmark 来自真实询价（每个项目都有），savings 假设 FDE 比外包便宜 30-50%
        proj_objs = []
        # 显式控制 bid_outcome 分布，确保每种都有合理数量
        N_REV = len(PROJECT_TEMPLATES_REVENUE)  # 20
        bid_pool = (["won"] * 14 + ["pending"] * 3 + ["lost"] * 2 + ["escaped"] * 1)[:N_REV]
        random.shuffle(bid_pool)

        for i, tmpl in enumerate(PROJECT_TEMPLATES_REVENUE):
            name = tmpl.format(n=random.randint(1, 5), client=random.choice(np_objs).name.split("（")[0])
            need = random.choice(np_objs)
            sales = random.choice([s for s in sp_objs if s.is_active])
            benchmark = Decimal(random.randint(40, 350)) * 10000  # 400K - 3.5M
            bid_outcome = bid_pool[i]

            # status 与 bid_outcome 协调
            if bid_outcome == "pending":
                status = "drafting"
            elif bid_outcome == "lost":
                status = random.choice(["drafting", "cancelled"])
            elif bid_outcome == "escaped":
                # 中标后跑单 → 多半已开始执行
                status = random.choice(["in_progress", "cancelled"])
            else:  # won
                status = random.choices(
                    ["in_progress", "accepting", "closing", "archived"],
                    weights=[40, 15, 20, 25],
                )[0]

            planned_start = random_date_within(540, 60)
            planned_end = planned_start + timedelta(days=random.randint(60, 180))
            actual_start = (planned_start + timedelta(days=random.randint(-3, 7))
                            if bid_outcome in {"won", "escaped"} else None)
            actual_end = (planned_end + timedelta(days=random.randint(-15, 30))
                          if status in {"closing", "archived"} else None)
            # 70% 的项目随机派一个对接工程师
            contact_eng = random.choice(eng_objs) if random.random() < 0.7 else None
            summary_text = random.choice([
                "现场实施进入收尾阶段，本周完成验收",
                "客户提了一个变更，需评估工期影响",
                "硬件已到货，等待网络割接窗口",
                "Vendor 报价已审，等 PM 确认 SOW",
                None,
            ])
            p = Project(
                code=f"P-2026-{i+1:03d}", name=name,
                need_party_id=need.id, sales_person_id=sales.id,
                contact_engineer_id=contact_eng.id if contact_eng else None,
                kind="revenue", outsource_benchmark_amount=benchmark,
                status=status, bid_outcome=bid_outcome,
                planned_start_date=planned_start, planned_end_date=planned_end,
                actual_start_date=actual_start,
                actual_end_date=actual_end,
                summary=summary_text,
                description=f"项目 {name} — 自动 seed 生成",
                district=random.choices(
                    [c for c, _ in HK_DISTRICTS],
                    weights=[30, 30, 15, 15, 10])[0],
                rework_count=random.choices([0, 0, 0, 1, 2], weights=[55, 20, 10, 10, 5])[0],
                change_count=random.choices([0, 1, 2, 3, 4], weights=[30, 30, 20, 15, 5])[0],
                benchmark_basis=random.choices(
                    ["vendor_quote", "historical_avg"],
                    weights=[70, 30])[0],
                benchmark_basis_note=random.choice([
                    "参考 2024 同类项目 P-2024-005 报价",
                    "Gartner 2025 IT 服务行业基准",
                    "外包供应商 A/B 实际报价单 + 10%",
                    None, None,
                ]),
            )
            db.add(p); proj_objs.append(p)
        for i, tmpl in enumerate(PROJECT_TEMPLATES_NO_REVENUE):
            name = tmpl.format(n=random.randint(1, 4))
            need = random.choice(np_objs)
            sales = random.choice([s for s in sp_objs if s.is_active])
            benchmark = Decimal(random.randint(15, 80)) * 10000  # 150K - 800K
            p = Project(
                code=f"N-2026-{i+1:03d}", name=name,
                need_party_id=need.id, sales_person_id=sales.id,
                kind="no_revenue",
                outsource_benchmark_amount=benchmark,
                value_created_basis="outsource_equiv",
                value_created_note="自动 seed",
                status=random.choices(["in_progress", "closing", "archived"], weights=[40, 20, 40])[0],
                # no_revenue 项目一般是公司内部审批立项，默认视为已"中标" 进入交付
                bid_outcome="won",
                planned_start_date=random_date_within(360, 30),
                planned_end_date=random_date_within(120, -180),
                district=random.choices(
                    [c for c, _ in HK_DISTRICTS],
                    weights=[30, 30, 15, 15, 10])[0],
                rework_count=0,
                change_count=random.choice([0, 1, 2]),
            )
            db.add(p); proj_objs.append(p)
        await db.flush()

        # Mark ~25% of revenue projects as renewals of an earlier project from the same need_party
        renewal_marked = 0
        for p in proj_objs:
            if p.kind != "revenue":
                continue
            if random.random() > 0.45:
                continue
            # find an earlier-created project for the same need_party
            candidates = [
                q for q in proj_objs
                if q.id != p.id and q.id < p.id and q.need_party_id == p.need_party_id
            ]
            if candidates:
                p.renewal_of_project_id = random.choice(candidates).id
                renewal_marked += 1
        await db.flush()
        print(f"  ✓ projects x{len(proj_objs)} "
              f"({sum(1 for p in proj_objs if p.kind=='revenue')} revenue / "
              f"{sum(1 for p in proj_objs if p.kind=='no_revenue')} no_revenue, "
              f"{renewal_marked} 续单)")

        # 给约 40% 在管项目添加 1-3 条 demo 评论（admin ↔ engineer 互动）
        in_progress_projs = [
            p for p in proj_objs
            if p.status in {"drafting", "in_progress", "accepting"}
        ]
        cmt_pool = [
            ("lead", admin.id, "请本周内同步一下现场进度"),
            ("pm", pm.id, "客户已确认变更，请评估工期"),
            ("engineer", engineer_user.id, "本周五前可完成核心配置"),
            ("engineer", engineer_user.id, "需协调甲方机房进场时间"),
            ("lead", admin.id, "记得发周报"),
        ]
        n_cmts = 0
        for p in in_progress_projs:
            if random.random() > 0.4:
                continue
            for role, uid, body in random.sample(cmt_pool, random.randint(1, 3)):
                db.add(ProjectComment(
                    project_id=p.id, author_user_id=uid,
                    author_role=role, body=body,
                ))
                n_cmts += 1
        await db.flush()
        print(f"  ✓ project_comments x{n_cmts}")

        revenue_projects = [p for p in proj_objs if p.kind == "revenue"]

        # ── Project finance plan ──────────────────────────────────────
        # 业务模型（用户 2026-05-24 校准）：
        #   team_revenue = benchmark × random(0.7, 0.9)  — FDE 比外包便宜 10-30%
        #   VSF = team_revenue × random(0.99, 1.01)      — 100% pass-through ±1%
        # 不按 status completion 缩放 — 让 won 项目数据满额，方便 FDE 利润率对比展示
        def vsf_noise() -> float:
            return random.uniform(0.99, 1.01)

        project_finance: dict[int, dict[str, float]] = {}
        for p in proj_objs:
            if p.kind != "revenue":
                # no_revenue：B 口径用 benchmark 当机会成本，不需要 VSF / Revenue
                project_finance[p.id] = {"team_revenue": 0.0, "vsf": 0.0}
                continue
            bench = float(p.outsource_benchmark_amount or 0)
            if p.bid_outcome == "won":
                ratio = random.uniform(0.80, 0.90)  # FDE 比外包便宜 10-20%
                team_rev = bench * ratio
                vsf = team_rev * vsf_noise()
            elif p.bid_outcome == "escaped":
                # 中标后跑单 — 部分完成（20-50%），钱已付给 vendor
                partial = random.uniform(0.20, 0.50)
                ratio = random.uniform(0.80, 0.90)
                team_rev = bench * ratio * partial
                vsf = team_rev * vsf_noise()
            elif p.bid_outcome == "lost":
                # 丢标 — pre-sales 投入小成本（3-8% benchmark），无 revenue
                team_rev = 0.0
                vsf = bench * random.uniform(0.03, 0.08)
            else:  # pending
                team_rev = 0.0
                vsf = 0.0
            project_finance[p.id] = {"team_revenue": team_rev, "vsf": vsf}

        # ── Suppliers ─────────────────────────────────────────────────
        sup_objs = []
        for name, cat in [
            ("星辉线缆", "耗材"), ("锐能设备", "耗材"), ("世昌测试服务", "分包"),
            ("智库咨询", "分包"), ("速达人力派遣", "临时人力"),
            ("Microsoft HK", "许可"), ("AWS HK", "许可"), ("惠通商旅", "差旅"),
        ]:
            s = Supplier(name=name, category=cat, contact_person="对接人", is_active=True,
                         payment_terms=random.choice(["月结30天", "月结45天", "票到付"]))
            db.add(s); sup_objs.append(s)
        await db.flush()
        print(f"  ✓ suppliers x{len(sup_objs)}")

        # ── Engineer login accounts ───────────────────────────────────
        # 前 5 个 active 工程师拥有个人登录账号（用户名 = e1..e5，默认密码 demo123）
        # 用于演示派单接 / 拒 / 留言双向流转
        active_engineers = [e for e in eng_objs if e.status == "active"]
        engineer_user_accounts = []
        for idx, eng in enumerate(active_engineers[:5], start=1):
            u = User(
                username=f"e{idx}", full_name=eng.full_name,
                role="engineer", engineer_id=eng.id,
                hashed_password=hash_password("demo123"),
            )
            db.add(u); engineer_user_accounts.append(u)
        await db.flush()
        print(f"  ✓ engineer 登录账号 x{len(engineer_user_accounts)} "
              f"(e1..e{len(engineer_user_accounts)} / demo123)")

        # ── Vendor Service Fees ───────────────────────────────────────
        # 按 project_finance 计划生成：每个项目的 VSF 总额 ≈ 该项目 team_revenue
        # 业务模型：100% pass-through，团队入账 → 月结发 VSF 给 vendor
        vsf_count = 0
        for p in proj_objs:
            target_vsf = project_finance.get(p.id, {}).get("vsf", 0)
            if target_vsf <= 0:
                continue
            # 拆成 1-4 个月度账单，反映真实月结发票节奏
            months = random.randint(1, 4)
            monthly = target_vsf / months
            vendor = random.choice(vendor_objs)
            engineer = random.choice(active_engineers)
            for m in range(months):
                base_month = TODAY.month - m
                base_year = TODAY.year
                while base_month <= 0:
                    base_month += 12
                    base_year -= 1
                period_start = date(base_year, base_month, 1)
                if base_month == 12:
                    period_end = date(base_year, 12, 31)
                else:
                    period_end = date(base_year, base_month + 1, 1) - timedelta(days=1)
                db.add(VendorServiceFee(
                    vendor_id=vendor.id, engineer_id=engineer.id, project_id=p.id,
                    fee_type="monthly_per_engineer",
                    period_start=period_start, period_end=period_end,
                    amount=Decimal(str(round(monthly, 2))),
                    invoice_no=f"INV-{base_year}{base_month:02d}-P{p.id:03d}-{m+1}",
                    status=random.choices(["paid", "billed", "draft"], weights=[70, 20, 10])[0],
                ))
                vsf_count += 1
        await db.flush()
        print(f"  ✓ vendor service fees x{vsf_count} (项目驱动，合计 ≈ Σ team_revenue)")

        # ── External Expenses ─────────────────────────────────────────
        # 用户 2026-05-25 新模型：vendor 提交申请；vendor_id 是哪家 vendor 提交的
        exp_count = 0
        for _ in range(60):
            project = random.choice(proj_objs)
            etype = random.choice(list(EXPENSE_TITLES.keys()))
            title = random.choice(EXPENSE_TITLES[etype])
            amount = Decimal(random.randint(1, 80)) * 1000
            status = random.choices(["paid", "approved", "pending", "rejected"],
                                     weights=[55, 25, 15, 5])[0]
            vendor = random.choice(vendor_objs)
            vendor_user = vendor_users[vendor_objs.index(vendor)]
            db.add(ExpenseRequest(
                project_id=project.id, supplier_id=random.choice(sup_objs).id,
                vendor_id=vendor.id,
                expense_type=etype, title=title, amount=amount,
                expense_date=random_date_within(180), status=status,
                requested_by_user_id=vendor_user.id,
                approved_by_user_id=admin.id if status != "pending" else None,
                approved_at=datetime.utcnow() if status != "pending" else None,
                paid_at=datetime.utcnow() if status == "paid" else None,
            ))
            exp_count += 1
        await db.flush()
        print(f"  ✓ expenses x{exp_count}")

        # ── Project Revenues ──────────────────────────────────────────
        # 只为 won / escaped 项目生成；pending / lost / no_revenue 无收入记录
        # 业务模型（用户 2026-05-24 校准）：
        #   team_revenue 约占 gross 的 20%（销售切除 80%）→ gross = team × random(4.5, 5.5)
        #   non_service_expense 约占 gross 的 65-75%（硬件 / 第三方 / 物料）
        #   → 公司毛利 = gross − team − non_service ≈ gross × 5-15%
        rev_count = 0
        for p in revenue_projects:
            target_team_rev = project_finance.get(p.id, {}).get("team_revenue", 0)
            if target_team_rev <= 0:
                continue
            installments = (random.randint(1, 3) if p.bid_outcome == "won"
                            else random.randint(1, 2))
            installment_amount = Decimal(str(round(target_team_rev / installments, 2)))
            for i in range(installments):
                gross_mult = random.uniform(4.5, 5.5)
                gross = (installment_amount * Decimal(str(round(gross_mult, 3)))).quantize(Decimal("0.01"))
                nse_ratio = random.uniform(0.65, 0.75)
                nse = (gross * Decimal(str(round(nse_ratio, 3)))).quantize(Decimal("0.01"))
                db.add(ProjectRevenue(
                    project_id=p.id, amount=installment_amount,
                    gross_amount=gross,
                    non_service_expense=nse,
                    recognized_date=random_date_within(360, 0),
                    invoice_no=f"INV-R-{p.id}-{i+1}",
                ))
                rev_count += 1
        await db.flush()
        print(f"  ✓ project revenues x{rev_count} (含 gross + non_service_expense)")

        # ── Assignments + 对话消息 ────────────────────────────────────
        # 历史派单默认 accepted（已经在跑），少量给出 pending / rejected 演示流转
        from app.models.assignment import AssignmentMessage as _AM  # noqa: PLC0415
        pending_eng_ids = {u.engineer_id for u in engineer_user_accounts}
        REJECT_REASONS = [
            "本周已在进行 5G 扩容现场，时间排满，建议下周再派",
            "当前技能栈和该项目要求差距较大，建议派给云组同事",
            "家中临时有事，下周才能恢复全力",
            "已和另一项目 PM 口头确认承担更多，避免分散精力",
        ]
        assn_count = 0
        new_assignments: list[tuple[Assignment, str, str]] = []  # (a, status, project_name)

        non_archived_projects = [p for p in proj_objs if p.status != "archived"]

        # 1) 给 5 位测试工程师每人强制塞 1 条 pending 派单（保证登录后能看到接 / 拒 UI）
        for u in engineer_user_accounts:
            eng = next(e for e in active_engineers if e.id == u.engineer_id)
            p = random.choice(non_archived_projects)
            start = p.planned_start_date or random_date_within(120, 30)
            end = p.planned_end_date or (start + timedelta(days=random.randint(30, 120)))
            a = Assignment(
                engineer_id=eng.id, project_id=p.id,
                role=random.choice(["现场工程师", "技术负责人", "架构师"]),
                planned_start_date=start, planned_end_date=end,
                status=random.choice(["planned", "in_progress"]),
                approval_status="pending",
                created_by_user_id=pm.id,
            )
            db.add(a)
            new_assignments.append((a, "pending", p.name))
            assn_count += 1

        # 2) 正常随机派单（默认 accepted，少量 rejected）
        for p in proj_objs:
            for e in random.sample(active_engineers, k=random.randint(1, 4)):
                start = p.planned_start_date or random_date_within(120, 30)
                end = p.planned_end_date or (start + timedelta(days=random.randint(30, 120)))
                a_status = "ended" if p.status == "archived" else random.choice(
                    ["in_progress", "planned", "in_progress"])
                roll = random.random()
                appr = "rejected" if roll < 0.07 else "accepted"
                a = Assignment(
                    engineer_id=e.id, project_id=p.id,
                    role=random.choice(["现场工程师", "技术负责人", "测试", "PM", "架构师"]),
                    planned_start_date=start, planned_end_date=end,
                    actual_start_date=start if appr == "accepted" else None,
                    actual_end_date=end if a_status == "ended" else None,
                    status=a_status,
                    approval_status=appr,
                    created_by_user_id=pm.id,
                )
                db.add(a)
                new_assignments.append((a, appr, p.name))
                assn_count += 1
        await db.flush()

        msg_count = 0
        for a, appr, proj_name in new_assignments:
            # 系统消息：每条派单都有
            db.add(_AM(
                assignment_id=a.id, sender_user_id=pm.id, sender_kind="system",
                body=f"项目经理向你派单：{proj_name} · 角色 {a.role}。请确认接单或拒单。",
            ))
            msg_count += 1
            if appr == "accepted":
                db.add(_AM(
                    assignment_id=a.id, sender_user_id=None, sender_kind="engineer",
                    body="✓ 接单：已收到，按时进场",
                )); msg_count += 1
            elif appr == "rejected":
                db.add(_AM(
                    assignment_id=a.id, sender_user_id=None, sender_kind="engineer",
                    body=f"✗ 拒单理由：{random.choice(REJECT_REASONS)}",
                )); msg_count += 1
        await db.flush()
        print(f"  ✓ assignments x{assn_count} + 对话消息 x{msg_count}")

        # ── Timesheets ────────────────────────────────────────────────
        ts_count = 0
        # 近 30 天，每天若干工程师 × 1-2 项目，每天选 slot 组合并自动算加权
        from app.models.timesheet import compute_weighted_days, is_hk_workday  # noqa: PLC0415
        for d in range(30):
            wd = days_ago(d)
            is_wd = is_hk_workday(wd)
            # 工作日：大多数人填上下午整天；周末/节假日：少数人加班
            engs_today = random.sample(active_engineers,
                                       k=min(8 if is_wd else 3, len(active_engineers)))
            for e in engs_today:
                projects_for_eng = random.sample(proj_objs, k=random.randint(1, 2))
                seen = set()
                for p in projects_for_eng:
                    key = (e.id, p.id, wd)
                    if key in seen:
                        continue
                    seen.add(key)
                    # 时段组合：工作日 70% 上下午、20% 全天、10% 仅上午；非工作日 = 晚上加班
                    if is_wd:
                        roll = random.random()
                        if roll < 0.7:
                            has_m, has_a, has_e = True, True, False
                        elif roll < 0.9:
                            has_m, has_a, has_e = True, True, True  # 加班晚上
                        else:
                            has_m, has_a, has_e = True, False, False
                    else:
                        has_m, has_a, has_e = False, False, True  # 周末晚上加班
                    natural, weighted = compute_weighted_days(wd, has_m, has_a, has_e, is_workday=is_wd)
                    # 60% 已审，20% 待审，20% 已拒（含示例理由）
                    roll = random.random()
                    if roll < 0.6:
                        appr, reason = "approved", None
                    elif roll < 0.8:
                        appr, reason = "pending", None
                    else:
                        appr, reason = "rejected", random.choice([
                            "项目不在该时段排期内，请核对项目编号",
                            "已超出本月预算上限，下月再提",
                            "描述过于简略，请补充具体工作内容",
                        ])
                    db.add(Timesheet(
                        engineer_id=e.id, project_id=p.id, work_date=wd,
                        has_morning=has_m, has_afternoon=has_a, has_evening=has_e,
                        is_workday=is_wd,
                        natural_days=natural, weighted_days=weighted,
                        approval_status=appr, reject_reason=reason,
                        is_approved=(appr == "approved"),
                        submitted_by_user_id=engineer_user_accounts[0].id if engineer_user_accounts else None,
                    ))
                    ts_count += 1
        await db.flush()
        print(f"  ✓ timesheets x{ts_count} (近 30 天，含晚上 / 周末加权)")

        # ── Knowledge Assets ──────────────────────────────────────────
        ka_count = 0
        for cat_code, titles in ASSET_TITLES.items():
            for title in titles:
                db.add(KnowledgeAsset(
                    project_id=random.choice(proj_objs).id,
                    category=cat_code, title=title,
                    summary=f"{title} 摘要 — 自动 seed 生成",
                    tags=",".join(random.sample(
                        ["5G", "拓扑", "K8s", "安全", "网络", "云", "数据", "OAuth", "Python", "BGP"],
                        k=random.randint(2, 4))),
                    confidentiality=random.choices(
                        ["public", "internal", "confidential"],
                        weights=[20, 60, 20])[0],
                    created_by_user_id=admin.id,
                ))
                ka_count += 1
        await db.flush()
        print(f"  ✓ knowledge assets x{ka_count}")

        # ── Retrospectives ────────────────────────────────────────────
        retro_count = 0
        finished_projects = [p for p in proj_objs if p.status in {"accepting", "closing", "archived"}]
        for p in finished_projects:
            if random.random() < 0.85:  # 85% of finished projects have retros
                score = random.choices([3, 4, 4, 5, 5, 5], weights=[5, 20, 30, 20, 15, 10])[0]
                db.add(ProjectRetrospective(
                    project_id=p.id,
                    satisfaction_score=score,
                    what_went_well=random.choice([
                        "按时交付，质量稳定", "团队协作高效",
                        "客户反馈积极", "无重大事故",
                    ]),
                    what_to_improve=random.choice([
                        "需求变更频繁", "测试环节可前移",
                        "文档归档不够及时", "沟通频次可优化",
                    ]),
                    action_items="1) 立项锁需求 2) 验收前提前演练 3) 文档随交付即归档",
                    is_closed=random.random() < 0.6,
                    created_by_user_id=admin.id,
                ))
                retro_count += 1
        await db.flush()
        print(f"  ✓ retrospectives x{retro_count}")

        # ── Asset References (knowledge reuse) ────────────────────────
        ref_count = 0
        all_assets = (await db.execute(select(KnowledgeAsset))).scalars().all()
        # ~50% of assets get referenced 1-3 times
        for a in all_assets:
            if random.random() < 0.5:
                continue
            for _ in range(random.randint(1, 3)):
                target_project = random.choice(proj_objs)
                hours_saved = Decimal(random.choice([4, 8, 16, 24, 40, 60])) + random.choice([Decimal("0"), Decimal("0.5")])
                db.add(AssetReference(
                    asset_id=a.id, project_id=target_project.id,
                    estimated_hours_saved=hours_saved,
                    notes=f"复用 {a.title[:20]}",
                    referenced_by_user_id=admin.id,
                ))
                ref_count += 1
        await db.flush()
        print(f"  ✓ asset references x{ref_count}")

        # ── EngineerSkillSnapshots (8 quarters of growth) ─────────────
        # For each active engineer, create snapshots every ~90 days for 2 years
        # with simulated growth: skill_count and avg_level slightly higher
        # in later snapshots.
        snap_count = 0
        for e in active_engineers:
            base_skills = random.randint(2, 4)  # starting skill count
            base_level = round(random.uniform(1.2, 2.0), 2)  # 3 级系统：起点 L1.2-L2.0
            base_certs = random.randint(0, 1)
            # 8 snapshots: 720d ago to 0d ago, every 90d
            for q in range(8):
                snap_date = days_ago(720 - q * 90)
                # Simulate growth: each quarter +0.3 skill on avg, +~0.1 level, +0.1 cert
                growth_factor = q / 8.0
                skills_now = base_skills + int(growth_factor * random.uniform(2, 5))
                # 3 级封顶 L3.0：从 base + 最多 +1.0 涨幅
                level_now = round(min(3.0, base_level + growth_factor * random.uniform(0.3, 0.8)), 2)
                certs_now = base_certs + int(growth_factor * random.uniform(0, 3))
                db.add(EngineerSkillSnapshot(
                    engineer_id=e.id, snapshot_date=snap_date,
                    skill_count=skills_now,
                    avg_level=Decimal(str(level_now)),
                    cert_count=certs_now,
                    level=e.level,
                ))
                snap_count += 1
        await db.flush()
        print(f"  ✓ skill snapshots x{snap_count} (8 季度 × {len(active_engineers)} 工程师)")

        # ── Training records ──────────────────────────────────────────
        TRAINING_COURSES = [
            ("5G NR 进阶", "智联学院", "外训"),
            ("Kubernetes 实战", "CNCF 中国", "在线"),
            ("CISSP 备考冲刺", "ISC2", "外训"),
            ("内部 BGP 故障复盘", "网络团队", "内训"),
            ("Datadog APM 应用", "Datadog HK", "在线"),
            ("PMP 续证课程", "PMI 香港", "外训"),
            ("FastAPI 进阶", "团队负责人", "内训"),
            ("AWS Solutions Architect", "AWS HK", "外训"),
            ("ICT 安全意识", "合规部", "在线"),
            ("DevOps 工具链统一", "团队负责人", "内训"),
        ]
        train_count = 0
        for e in active_engineers:
            for _ in range(random.randint(1, 4)):
                course, provider, cat = random.choice(TRAINING_COURSES)
                db.add(TrainingRecord(
                    engineer_id=e.id,
                    course_name=course, provider=provider, category=cat,
                    training_date=random_date_within(540, 0),
                    hours=Decimal(random.choice(["8", "16", "24", "40"])),
                    cost=Decimal(random.randint(500, 8000)) if cat in ("外训", "在线") else None,
                    passed=random.random() < 0.9,
                ))
                train_count += 1
        await db.flush()
        print(f"  ✓ trainings x{train_count}")

        # ── IDPs ──────────────────────────────────────────────────────
        idp_count = 0
        for e in active_engineers:
            if random.random() < 0.6:  # 60% have an IDP
                target_level = min(3, (e.level or 2) + 1)
                db.add(IDP(
                    engineer_id=e.id,
                    title=f"L{e.level} → L{target_level} 成长路径",
                    target_skills=",".join(random.sample(
                        ["K8s", "5G", "BGP", "Python", "Java", "CISSP", "AWS"],
                        k=random.randint(2, 4))),
                    target_certs=random.choice(["CCIE / CISSP", "AWS SA", "PMP", "CKA"]),
                    plan_actions="1) 完成内训 2) 报考外部证书 3) 担任项目技术负责人一次",
                    due_date=random_date_within(-90, -360),
                    status=random.choices(
                        ["in_progress", "completed", "draft"],
                        weights=[60, 25, 15])[0],
                ))
                idp_count += 1
        await db.flush()
        print(f"  ✓ IDPs x{idp_count}")

        # ── Renewal attempts (Phase 3-next-iii Round 2) ───────────────
        # Projects with renewal_of_project_id are the "won" ones — log them.
        # Plus generate a few "lost" + "pending" attempts for funnel realism.
        renewal_attempt_count = 0
        won_projects = [p for p in proj_objs if p.renewal_of_project_id]
        for p in won_projects:
            db.add(RenewalAttempt(
                previous_project_id=p.renewal_of_project_id,
                attempt_date=random_date_within(540, 90),
                outcome="won",
                won_project_id=p.id,
                notes="按时续单成功",
                created_by_user_id=admin.id,
            ))
            renewal_attempt_count += 1

        # Lost attempts — pick random archived/closing projects that DON'T already
        # have a successor; mark a "lost renewal attempt" with diverse reasons.
        successor_sources = {p.renewal_of_project_id for p in won_projects}
        finished_no_successor = [
            p for p in proj_objs
            if p.status in {"closing", "archived"}
            and p.kind == "revenue"
            and p.id not in successor_sources
        ]
        LOST_REASONS = [
            ("lost_to_outsource", "客户最终选了传统外包供应商"),
            ("price", "竞品报价低 15%"),
            ("quality", "上次验收时有小瑕疵被记账"),
            ("no_budget", "客户预算冻结"),
            ("internal_hire", "客户决定自建团队"),
            ("other", "需求范围未敲定"),
        ]
        for p in random.sample(finished_no_successor, min(7, len(finished_no_successor))):
            reason_code, reason_note = random.choice(LOST_REASONS)
            db.add(RenewalAttempt(
                previous_project_id=p.id,
                attempt_date=random_date_within(360, 30),
                outcome="lost",
                lost_reason=reason_code,
                lost_reason_note=reason_note,
                created_by_user_id=admin.id,
            ))
            renewal_attempt_count += 1

        # Pending — a few in-flight pitches
        pending_pool = [p for p in proj_objs if p.status == "archived" and p.kind == "revenue"]
        for p in random.sample(pending_pool, min(3, len(pending_pool))):
            db.add(RenewalAttempt(
                previous_project_id=p.id,
                attempt_date=random_date_within(60, 0),
                outcome="pending",
                notes="商务洽谈中",
                created_by_user_id=admin.id,
            ))
            renewal_attempt_count += 1

        await db.flush()
        print(f"  ✓ renewal attempts x{renewal_attempt_count}")

        await db.commit()

    print()
    print("✅ DONE — login as admin / admin123")
    print("   驾驶舱 token: cockpit-dev-token（IP 白名单 localhost 也可）")


if __name__ == "__main__":
    asyncio.run(main())
