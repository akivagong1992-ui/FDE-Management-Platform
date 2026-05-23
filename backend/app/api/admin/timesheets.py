"""Timesheet API: single CRUD + bulk + Excel import + template download."""

import io
from datetime import date as date_cls
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import (
    APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status,
)
from openpyxl import Workbook, load_workbook
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.engineer import Engineer
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.schemas.timesheet import (
    ImportResult,
    ImportRowError,
    TimesheetBulkCreate,
    TimesheetCreate,
    TimesheetOut,
    TimesheetUpdate,
)

router = APIRouter(prefix="/timesheets", tags=["timesheets"])


def _to_out(t: Timesheet) -> TimesheetOut:
    return TimesheetOut(
        id=t.id,
        engineer_id=t.engineer_id,
        engineer_name=t.engineer.full_name if t.engineer else None,
        project_id=t.project_id,
        project_name=t.project.name if t.project else None,
        assignment_id=t.assignment_id,
        work_date=t.work_date,
        hours=t.hours,
        description=t.description,
        is_approved=t.is_approved,
        created_at=t.created_at,
    )


@router.get("", response_model=list[TimesheetOut])
async def list_timesheets(
    engineer_id: int | None = None,
    project_id: int | None = None,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[TimesheetOut]:
    stmt = select(Timesheet).order_by(Timesheet.work_date.desc(), Timesheet.id.desc())
    if engineer_id is not None:
        stmt = stmt.where(Timesheet.engineer_id == engineer_id)
    if project_id is not None:
        stmt = stmt.where(Timesheet.project_id == project_id)
    if date_from:
        stmt = stmt.where(Timesheet.work_date >= date_cls.fromisoformat(date_from))
    if date_to:
        stmt = stmt.where(Timesheet.work_date <= date_cls.fromisoformat(date_to))
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(t) for t in rows]


async def _create_one(db: AsyncSession, payload: TimesheetCreate) -> Timesheet:
    if not await db.get(Engineer, payload.engineer_id):
        raise HTTPException(status_code=400, detail=f"工程师 #{payload.engineer_id} 不存在")
    if not await db.get(Project, payload.project_id):
        raise HTTPException(status_code=400, detail=f"项目 #{payload.project_id} 不存在")
    t = Timesheet(**payload.model_dump())
    db.add(t)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="同一工程师在同一项目同一天的工时已存在（如需修改请用编辑）",
        ) from e
    await db.refresh(t)
    return t


@router.post("", response_model=TimesheetOut, status_code=status.HTTP_201_CREATED)
async def create_timesheet(
    payload: TimesheetCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> TimesheetOut:
    t = await _create_one(db, payload)
    return _to_out(t)


@router.post("/bulk", response_model=ImportResult)
async def bulk_create(
    payload: TimesheetBulkCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> ImportResult:
    created, skipped, errors = 0, 0, []
    for idx, item in enumerate(payload.items, start=1):
        try:
            await _create_one(db, item)
            created += 1
        except HTTPException as e:
            skipped += 1
            errors.append(ImportRowError(row=idx, message=str(e.detail)))
    return ImportResult(created=created, skipped=skipped, errors=errors)


@router.patch("/{ts_id}", response_model=TimesheetOut)
async def update_timesheet(
    ts_id: int,
    payload: TimesheetUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> TimesheetOut:
    t = await db.get(Timesheet, ts_id)
    if not t:
        raise HTTPException(status_code=404, detail="工时记录不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    await db.commit()
    await db.refresh(t)
    return _to_out(t)


@router.delete("/{ts_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timesheet(
    ts_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> None:
    t = await db.get(Timesheet, ts_id)
    if not t:
        raise HTTPException(status_code=404, detail="工时记录不存在")
    await db.delete(t)
    await db.commit()


@router.patch("/{ts_id}/approve", response_model=TimesheetOut)
async def approve_timesheet(
    ts_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> TimesheetOut:
    t = await db.get(Timesheet, ts_id)
    if not t:
        raise HTTPException(status_code=404, detail="工时记录不存在")
    t.is_approved = True
    t.approved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(t)
    return _to_out(t)


# ─── Excel template + import ─────────────────────────────────────────

EXCEL_HEADERS = ["工程师姓名", "项目编号或名称", "工作日期(YYYY-MM-DD)", "工时", "描述(可选)"]


@router.get("/template")
async def download_template(
    _: dict = Depends(get_current_user),
) -> Response:
    """返回一个空白 Excel 模板，含正确表头 + 1 行示例。"""
    wb = Workbook()
    ws = wb.active
    ws.title = "工时导入"
    ws.append(EXCEL_HEADERS)
    ws.append(["李志强", "PROJ-001", "2026-05-23", 8, "基站现场调试"])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="timesheet-template.xlsx"'},
    )


@router.post("/import-excel", response_model=ImportResult)
async def import_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> ImportResult:
    """读 Excel → 按行解析 → 逐行创建工时记录，最后返回 created/skipped/errors。"""
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx / .xls 文件")
    content = await file.read()
    try:
        wb = load_workbook(io.BytesIO(content), data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel 解析失败：{e}") from e
    ws = wb.active

    rows_iter = ws.iter_rows(min_row=2, values_only=True)  # skip header
    created, skipped, errors = 0, 0, []

    # Cache lookups
    eng_by_name: dict[str, Engineer] = {}
    proj_by_key: dict[str, Project] = {}

    for idx, row in enumerate(rows_iter, start=2):
        try:
            if not row or all(c is None for c in row):
                continue
            eng_name_raw, proj_key_raw, date_raw, hours_raw, desc_raw = (list(row) + [None] * 5)[:5]
            if eng_name_raw is None or proj_key_raw is None or date_raw is None or hours_raw is None:
                errors.append(ImportRowError(row=idx, message="缺少必填字段"))
                skipped += 1
                continue

            eng_name = str(eng_name_raw).strip()
            proj_key = str(proj_key_raw).strip()

            # Lookup engineer by full_name
            if eng_name not in eng_by_name:
                e = (await db.execute(
                    select(Engineer).where(Engineer.full_name == eng_name)
                )).scalar_one_or_none()
                if not e:
                    errors.append(ImportRowError(row=idx, message=f"工程师 '{eng_name}' 不存在"))
                    skipped += 1
                    continue
                eng_by_name[eng_name] = e
            engineer = eng_by_name[eng_name]

            # Lookup project: prefer code, fallback to name
            if proj_key not in proj_by_key:
                p = (await db.execute(
                    select(Project).where(Project.code == proj_key)
                )).scalar_one_or_none()
                if not p:
                    p = (await db.execute(
                        select(Project).where(Project.name == proj_key)
                    )).scalar_one_or_none()
                if not p:
                    errors.append(ImportRowError(row=idx, message=f"项目 '{proj_key}' 不存在"))
                    skipped += 1
                    continue
                proj_by_key[proj_key] = p
            project = proj_by_key[proj_key]

            # Date
            if isinstance(date_raw, datetime):
                work_date = date_raw.date()
            elif isinstance(date_raw, date_cls):
                work_date = date_raw
            else:
                work_date = date_cls.fromisoformat(str(date_raw).strip())

            # Hours
            try:
                hours = Decimal(str(hours_raw))
            except (InvalidOperation, ValueError) as e:
                raise ValueError(f"工时格式不对: {hours_raw}") from e
            if hours <= 0 or hours > 24:
                raise ValueError(f"工时超出范围: {hours}")

            payload = TimesheetCreate(
                engineer_id=engineer.id,
                project_id=project.id,
                work_date=work_date,
                hours=hours,
                description=str(desc_raw).strip() if desc_raw else None,
            )
            try:
                await _create_one(db, payload)
                created += 1
            except HTTPException as he:
                errors.append(ImportRowError(row=idx, message=str(he.detail)))
                skipped += 1
        except Exception as e:
            errors.append(ImportRowError(row=idx, message=str(e)))
            skipped += 1

    return ImportResult(created=created, skipped=skipped, errors=errors)
