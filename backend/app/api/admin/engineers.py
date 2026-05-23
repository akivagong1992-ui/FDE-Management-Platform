from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_field, encrypt_field, mask_id_number
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.engineer import Certificate, Engineer
from app.models.skill import EngineerSkill, Skill
from app.models.vendor import Vendor
from app.schemas.engineer import (
    CertificateIn,
    CertificateOut,
    EngineerCreate,
    EngineerOut,
    EngineerSensitiveOut,
    EngineerUpdate,
)
from app.schemas.skill import EngineerSkillItem, EngineerSkillOut

router = APIRouter(prefix="/engineers", tags=["engineers"])

# Roles that can see real-cost (Vendor 真实人工成本) and Vendor service fee.
COST_VIEW_ROLES = {"admin", "lead", "finance"}


def _can_view_cost(user: dict) -> bool:
    return user.get("role") in COST_VIEW_ROLES


def _to_out(e: Engineer, *, include_cost: bool) -> EngineerOut:
    skills = [
        EngineerSkillOut(
            id=es.id,
            skill_id=es.skill_id,
            skill_name=es.skill.name if es.skill else "",
            skill_category=es.skill.category if es.skill else "",
            level=es.level,
            notes=es.notes,
        )
        for es in (e.skills or [])
    ]
    certs = [CertificateOut.model_validate(c) for c in (e.certificates or [])]
    return EngineerOut(
        id=e.id,
        vendor_id=e.vendor_id,
        vendor_name=e.vendor.name if e.vendor else None,
        employment_form=e.employment_form,
        labor_company=e.labor_company,
        full_name=e.full_name,
        english_name=e.english_name,
        gender=e.gender,
        birth_date=e.birth_date,
        mobile=e.mobile,
        email=e.email,
        id_doc_type=e.id_doc_type,
        id_doc_number_masked=mask_id_number(decrypt_field(e.id_doc_number_enc)),
        level=e.level,
        status=e.status,
        entry_date=e.entry_date,
        exit_date=e.exit_date,
        notes=e.notes,
        monthly_cost_to_telecom=e.monthly_cost_to_telecom if include_cost else None,
        monthly_real_cost=e.monthly_real_cost if include_cost else None,
        skills=skills,
        certificates=certs,
        created_at=e.created_at,
    )


@router.get("", response_model=list[EngineerOut])
async def list_engineers(
    vendor_id: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list[EngineerOut]:
    stmt = select(Engineer).order_by(Engineer.id.desc())
    if vendor_id is not None:
        stmt = stmt.where(Engineer.vendor_id == vendor_id)
    if status_filter:
        stmt = stmt.where(Engineer.status == status_filter)
    result = await db.execute(stmt)
    include_cost = _can_view_cost(user)
    return [_to_out(e, include_cost=include_cost) for e in result.scalars().all()]


@router.get("/{engineer_id}", response_model=EngineerOut)
async def get_engineer(
    engineer_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> EngineerOut:
    e = await db.get(Engineer, engineer_id)
    if not e:
        raise HTTPException(status_code=404, detail="工程师不存在")
    return _to_out(e, include_cost=_can_view_cost(user))


@router.get("/{engineer_id}/sensitive", response_model=EngineerSensitiveOut)
async def reveal_engineer_id(
    engineer_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> EngineerSensitiveOut:
    e = await db.get(Engineer, engineer_id)
    if not e:
        raise HTTPException(status_code=404, detail="工程师不存在")
    return EngineerSensitiveOut(
        id=e.id, id_doc_type=e.id_doc_type, id_doc_number=decrypt_field(e.id_doc_number_enc)
    )


@router.post("", response_model=EngineerOut, status_code=status.HTTP_201_CREATED)
async def create_engineer(
    payload: EngineerCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> EngineerOut:
    if not await db.get(Vendor, payload.vendor_id):
        raise HTTPException(status_code=400, detail="Vendor 不存在")
    if payload.employment_form == "vendor_via_labor" and not payload.labor_company:
        raise HTTPException(status_code=400, detail="vendor_via_labor 需填写劳务公司")

    data = payload.model_dump(exclude={"id_doc_number", "monthly_real_cost"})
    e = Engineer(**data)
    e.id_doc_number_enc = encrypt_field(payload.id_doc_number)
    if _can_view_cost(user):
        e.monthly_real_cost = payload.monthly_real_cost
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return _to_out(e, include_cost=_can_view_cost(user))


@router.patch("/{engineer_id}", response_model=EngineerOut)
async def update_engineer(
    engineer_id: int,
    payload: EngineerUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> EngineerOut:
    e = await db.get(Engineer, engineer_id)
    if not e:
        raise HTTPException(status_code=404, detail="工程师不存在")
    data = payload.model_dump(exclude_unset=True)
    new_id = data.pop("id_doc_number", None)
    if new_id is not None:
        e.id_doc_number_enc = encrypt_field(new_id)
    if "monthly_real_cost" in data and not _can_view_cost(user):
        data.pop("monthly_real_cost")
    for k, v in data.items():
        setattr(e, k, v)
    await db.commit()
    await db.refresh(e)
    return _to_out(e, include_cost=_can_view_cost(user))


@router.delete("/{engineer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_engineer(
    engineer_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    e = await db.get(Engineer, engineer_id)
    if not e:
        raise HTTPException(status_code=404, detail="工程师不存在")
    await db.delete(e)
    await db.commit()


# ─── Skill matrix ──────────────────────────────────────────────────────

@router.post("/{engineer_id}/skills", response_model=EngineerSkillOut)
async def attach_skill(
    engineer_id: int,
    payload: EngineerSkillItem,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> EngineerSkillOut:
    e = await db.get(Engineer, engineer_id)
    if not e:
        raise HTTPException(status_code=404, detail="工程师不存在")
    skill = await db.get(Skill, payload.skill_id)
    if not skill:
        raise HTTPException(status_code=400, detail="技能不存在")
    existing = (
        await db.execute(
            select(EngineerSkill).where(
                EngineerSkill.engineer_id == engineer_id,
                EngineerSkill.skill_id == payload.skill_id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.level = payload.level
        existing.notes = payload.notes
        await db.commit()
        await db.refresh(existing)
        es = existing
    else:
        es = EngineerSkill(engineer_id=engineer_id, **payload.model_dump())
        db.add(es)
        await db.commit()
        await db.refresh(es)
    return EngineerSkillOut(
        id=es.id,
        skill_id=es.skill_id,
        skill_name=skill.name,
        skill_category=skill.category,
        level=es.level,
        notes=es.notes,
    )


@router.delete("/{engineer_id}/skills/{es_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_skill(
    engineer_id: int,
    es_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> None:
    es = await db.get(EngineerSkill, es_id)
    if not es or es.engineer_id != engineer_id:
        raise HTTPException(status_code=404, detail="技能记录不存在")
    await db.delete(es)
    await db.commit()


# ─── Certificates ──────────────────────────────────────────────────────

@router.post("/{engineer_id}/certificates", response_model=CertificateOut)
async def add_certificate(
    engineer_id: int,
    payload: CertificateIn,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> CertificateOut:
    e = await db.get(Engineer, engineer_id)
    if not e:
        raise HTTPException(status_code=404, detail="工程师不存在")
    c = Certificate(engineer_id=engineer_id, **payload.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return CertificateOut.model_validate(c)


@router.delete("/{engineer_id}/certificates/{cert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(
    engineer_id: int,
    cert_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> None:
    c = await db.get(Certificate, cert_id)
    if not c or c.engineer_id != engineer_id:
        raise HTTPException(status_code=404, detail="证书不存在")
    await db.delete(c)
    await db.commit()
