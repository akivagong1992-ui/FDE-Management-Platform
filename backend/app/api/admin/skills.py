from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillOut, SkillUpdate

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillOut])
async def list_skills(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[SkillOut]:
    result = await db.execute(select(Skill).order_by(Skill.category, Skill.name))
    return [SkillOut.model_validate(s) for s in result.scalars().all()]


@router.post("", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: SkillCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> SkillOut:
    if (await db.execute(select(Skill).where(Skill.name == payload.name))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="技能已存在")
    s = Skill(**payload.model_dump())
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return SkillOut.model_validate(s)


@router.patch("/{skill_id}", response_model=SkillOut)
async def update_skill(
    skill_id: int,
    payload: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> SkillOut:
    s = await db.get(Skill, skill_id)
    if not s:
        raise HTTPException(status_code=404, detail="技能不存在")
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, val)
    await db.commit()
    await db.refresh(s)
    return SkillOut.model_validate(s)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    s = await db.get(Skill, skill_id)
    if not s:
        raise HTTPException(status_code=404, detail="技能不存在")
    await db.delete(s)
    await db.commit()
