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
from app.models.project import HK_DISTRICTS, Project
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

NEED_PARTIES = [
    ("集团香港 IT 部", "internal_dept", "王主管"),
    ("香港数据中心", "internal_dept", "陈总监"),
    ("网络运营部", "internal_dept", "李经理"),
    ("客户服务中心", "internal_dept", "张主任"),
    ("集团合规部", "internal_dept", "孙总监"),
    ("海事卫星业务部", "internal_dept", "周经理"),
    ("国际批发业务", "internal_dept", "吴总监"),
    ("5G 创新实验室", "internal_dept", "郑博士"),
    ("跨境光纤项目组", "internal_dept", "韩工"),
    ("中海集团", "external_company", "钱总"),
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

SKILLS = [
    ("Python", "编程语言"), ("Java", "编程语言"), ("Go", "编程语言"),
    ("JavaScript", "编程语言"), ("C++", "编程语言"),
    ("BGP/MPLS", "网络"), ("SDN", "网络"), ("5G NR", "通信"),
    ("光纤施工", "通信"), ("CCIE 路由交换", "网络"),
    ("渗透测试", "安全"), ("零信任架构", "安全"), ("CISSP 域", "安全"),
    ("Kubernetes", "云"), ("AWS / Azure", "云"),
    ("PostgreSQL", "数据"), ("BigQuery", "数据"),
    ("PMP 项目管理", "其他"),
]

# 厂商认证：(name, issuer, cert_category, cert_level)
# cert_level: L1 初级 / L2 中级 / L3 高级
CERTS = [
    # L3 高级
    ("CCIE 路由交换", "Cisco", "网络", "L3"),
    ("CISSP", "ISC2", "安全", "L3"),
    ("华为 HCIE", "华为", "网络", "L3"),
    ("CISA", "ISACA", "安全", "L3"),
    ("AWS Solutions Architect Professional", "AWS", "云", "L3"),
    # L2 中级
    ("PMP", "PMI", "其他", "L2"),
    ("AWS Solutions Architect Associate", "AWS", "云", "L2"),
    ("CKA", "CNCF", "云", "L2"),
    ("CCNP 安全", "Cisco", "安全", "L2"),
    ("OCP Java", "Oracle", "编程语言", "L2"),
    ("Python PCAP", "Python Institute", "编程语言", "L2"),
    ("华为 HCIP-数通", "华为", "通信", "L2"),
    # L1 初级
    ("CCNA", "Cisco", "网络", "L1"),
    ("华为 HCIA-Cloud", "华为", "云", "L1"),
    ("华为 HCIA-大数据", "华为", "数据", "L1"),
    ("AWS Cloud Practitioner", "AWS", "云", "L1"),
    ("CompTIA Security+", "CompTIA", "安全", "L1"),
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
        engineer_user = User(username="eng1", full_name="基层工程师", role="engineer",
                             hashed_password=hash_password("eng123"))
        db.add_all([admin, finance, pm, engineer_user])
        await db.flush()
        print(f"  ✓ users x{4}")

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
        for name, cat in SKILLS:
            s = Skill(name=name, category=cat, is_active=True)
            db.add(s); skill_objs.append(s)
        await db.flush()
        print(f"  ✓ skills x{len(skill_objs)}")

        # ── Engineers ─────────────────────────────────────────────────
        # 个人评级（engineers.level）已废除，仅靠厂商认证体现工程师水平
        eng_objs = []
        for name in ENGINEER_NAMES:
            vendor = random.choice(vendor_objs)
            monthly_cost = Decimal(random.randint(18, 65)) * 1000  # 18K-65K
            real_cost = monthly_cost * Decimal("0.65")  # Vendor takes ~35% margin
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
                status=random.choices(["active", "active", "active", "reserved", "departed"],
                                       weights=[60, 20, 10, 5, 5])[0],
                entry_date=random_date_within(540, 30),
                monthly_cost_to_telecom=monthly_cost,
                monthly_real_cost=real_cost,
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
        proj_objs = []
        for i, tmpl in enumerate(PROJECT_TEMPLATES_REVENUE):
            name = tmpl.format(n=random.randint(1, 5), client=random.choice(np_objs).name.split("（")[0])
            need = random.choice(np_objs)
            sales = random.choice([s for s in sp_objs if s.is_active])
            benchmark = Decimal(random.randint(40, 350)) * 10000  # 400K - 3.5M
            status = random.choices(
                ["in_progress", "in_progress", "accepting", "closing", "archived", "drafting"],
                weights=[35, 20, 10, 15, 15, 5],
            )[0]
            planned_start = random_date_within(540, 60)
            planned_end = planned_start + timedelta(days=random.randint(60, 180))
            actual_end = (planned_end + timedelta(days=random.randint(-15, 30))
                          if status in {"closing", "archived"} else None)
            p = Project(
                code=f"P-2026-{i+1:03d}", name=name,
                need_party_id=need.id, sales_person_id=sales.id,
                kind="revenue", outsource_benchmark_amount=benchmark,
                status=status,
                planned_start_date=planned_start, planned_end_date=planned_end,
                actual_start_date=planned_start + timedelta(days=random.randint(-3, 7)),
                actual_end_date=actual_end,
                description=f"项目 {name} — 自动 seed 生成",
                district=random.choices(
                    [c for c, _ in HK_DISTRICTS],
                    weights=[30, 30, 15, 15, 10])[0],
                rework_count=random.choices([0, 0, 0, 1, 2], weights=[55, 20, 10, 10, 5])[0],
                change_count=random.choices([0, 1, 2, 3, 4], weights=[30, 30, 20, 15, 5])[0],
                benchmark_basis=random.choices(
                    ["vendor_quote", "historical_avg", "industry_benchmark", "manual_estimate"],
                    weights=[40, 30, 20, 10])[0],
                benchmark_basis_note=random.choice([
                    "参考 2024 同类项目 P-2024-005 报价",
                    "Gartner 2025 IT 服务行业基准",
                    "外包供应商 A/B 实际报价单 + 10%",
                    "PM 经验估算",
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
                value_created_basis=random.choice(["outsource_equiv", "replace_audit_fee",
                                                    "avoid_penalty", "strategic_reserve"]),
                value_created_note="自动 seed",
                status=random.choices(["in_progress", "closing", "archived"], weights=[40, 20, 40])[0],
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

        revenue_projects = [p for p in proj_objs if p.kind == "revenue"]

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

        # ── Vendor Service Fees ───────────────────────────────────────
        # Each in-progress engineer ~ 4-6 months of fees on a random project
        active_engineers = [e for e in eng_objs if e.status == "active"]
        vsf_count = 0
        for e in active_engineers:
            project = random.choice(revenue_projects + proj_objs[-5:])  # mix
            months = random.randint(2, 6)
            for m in range(months):
                period_start = date(2025, 12 - m % 12, 1) if m < 12 else date(2025, 1, 1)
                # use a simpler month walker
                base_month = TODAY.month - m
                base_year = TODAY.year
                while base_month <= 0:
                    base_month += 12
                    base_year -= 1
                period_start = date(base_year, base_month, 1)
                # period_end ≈ last day
                if base_month == 12:
                    period_end = date(base_year, 12, 31)
                else:
                    period_end = date(base_year, base_month + 1, 1) - timedelta(days=1)
                amount = e.monthly_cost_to_telecom * Decimal(random.uniform(0.9, 1.1))
                db.add(VendorServiceFee(
                    vendor_id=e.vendor_id, engineer_id=e.id, project_id=project.id,
                    fee_type="monthly_per_engineer",
                    period_start=period_start, period_end=period_end,
                    amount=amount.quantize(Decimal("0.01")),
                    invoice_no=f"INV-{base_year}{base_month:02d}-{e.id:03d}",
                    status=random.choices(["paid", "billed", "draft"], weights=[70, 20, 10])[0],
                ))
                vsf_count += 1
        await db.flush()
        print(f"  ✓ vendor service fees x{vsf_count}")

        # ── External Expenses ─────────────────────────────────────────
        exp_count = 0
        for _ in range(60):
            project = random.choice(proj_objs)
            etype = random.choice(list(EXPENSE_TITLES.keys()))
            title = random.choice(EXPENSE_TITLES[etype])
            amount = Decimal(random.randint(1, 80)) * 1000
            status = random.choices(["paid", "approved", "pending", "rejected"],
                                     weights=[55, 25, 15, 5])[0]
            db.add(ExpenseRequest(
                project_id=project.id, supplier_id=random.choice(sup_objs).id,
                expense_type=etype, title=title, amount=amount,
                expense_date=random_date_within(180), status=status,
                requested_by_user_id=pm.id,
                approved_by_user_id=admin.id if status != "pending" else None,
                approved_at=datetime.utcnow() if status != "pending" else None,
                paid_at=datetime.utcnow() if status == "paid" else None,
            ))
            exp_count += 1
        await db.flush()
        print(f"  ✓ expenses x{exp_count}")

        # ── Project Revenues ──────────────────────────────────────────
        rev_count = 0
        for p in revenue_projects:
            bench = float(p.outsource_benchmark_amount or 0)
            # Total revenue ~ 70% of benchmark on average (some over, some under)
            total = Decimal(bench) * Decimal(random.uniform(0.55, 0.95))
            installments = random.randint(1, 3)
            installment_amount = (total / installments).quantize(Decimal("0.01"))
            for i in range(installments):
                db.add(ProjectRevenue(
                    project_id=p.id, amount=installment_amount,
                    recognized_date=random_date_within(360, 0),
                    invoice_no=f"INV-R-{p.id}-{i+1}",
                    status="received" if random.random() < 0.7 else "pending",
                ))
                rev_count += 1
        await db.flush()
        print(f"  ✓ project revenues x{rev_count}")

        # ── Assignments ───────────────────────────────────────────────
        assn_count = 0
        for p in proj_objs:
            for e in random.sample(active_engineers, k=random.randint(1, 4)):
                start = p.planned_start_date or random_date_within(120, 30)
                end = p.planned_end_date or (start + timedelta(days=random.randint(30, 120)))
                a_status = "ended" if p.status == "archived" else random.choice(
                    ["in_progress", "planned", "in_progress"])
                db.add(Assignment(
                    engineer_id=e.id, project_id=p.id,
                    role=random.choice(["现场工程师", "技术负责人", "测试", "PM", "架构师"]),
                    allocation_ratio=random.choice([20, 40, 50, 60, 80, 100]),
                    planned_start_date=start, planned_end_date=end,
                    actual_start_date=start,
                    actual_end_date=end if a_status == "ended" else None,
                    status=a_status,
                ))
                assn_count += 1
        await db.flush()
        print(f"  ✓ assignments x{assn_count}")

        # ── Timesheets ────────────────────────────────────────────────
        ts_count = 0
        # Last 30 days, ~5 engineers per day, 1-3 entries each
        for d in range(30):
            wd = days_ago(d)
            if wd.weekday() >= 5:  # skip weekends mostly
                continue
            for e in random.sample(active_engineers, k=min(8, len(active_engineers))):
                projects_for_eng = random.sample(proj_objs, k=random.randint(1, 2))
                seen = set()
                for p in projects_for_eng:
                    key = (e.id, p.id, wd)
                    if key in seen:
                        continue
                    seen.add(key)
                    db.add(Timesheet(
                        engineer_id=e.id, project_id=p.id, work_date=wd,
                        person_days=random.choice([Decimal("0.5"), Decimal("1.0")]),
                        is_approved=random.random() < 0.6,
                    ))
                    ts_count += 1
        await db.flush()
        print(f"  ✓ timesheets x{ts_count} (近 30 天)")

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
            base_level = round(random.uniform(2.0, 3.5), 2)
            base_certs = random.randint(0, 1)
            # 8 snapshots: 720d ago to 0d ago, every 90d
            for q in range(8):
                snap_date = days_ago(720 - q * 90)
                # Simulate growth: each quarter +0.3 skill on avg, +0.05 level, +0.1 cert
                growth_factor = q / 8.0
                skills_now = base_skills + int(growth_factor * random.uniform(2, 5))
                level_now = round(min(5.0, base_level + growth_factor * random.uniform(0.5, 1.2)), 2)
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
                target_level = min(5, (e.level or 3) + 1)
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
