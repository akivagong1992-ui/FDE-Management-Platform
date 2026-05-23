from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.asset_reference import AssetReference
from app.models.knowledge_asset import (
    CONFIDENTIALITY_CONFIDENTIAL, KnowledgeAsset,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.asset_reference import AssetReferenceCreate, AssetReferenceOut

router = APIRouter(prefix="/knowledge-assets/{asset_id}/references", tags=["asset-references"])

CONFIDENTIAL_VIEW_ROLES = {"admin", "lead", "pm", "finance"}


async def _user_id_from_jwt(db: AsyncSession, user: dict) -> int | None:
    username = user.get("sub")
    if not username:
        return None
    u = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    return u.id if u else None


def _to_out(r: AssetReference) -> AssetReferenceOut:
    return AssetReferenceOut(
        id=r.id,
        asset_id=r.asset_id,
        project_id=r.project_id,
        project_name=r.project.name if r.project else None,
        estimated_hours_saved=r.estimated_hours_saved,
        notes=r.notes,
        referenced_by_user_id=r.referenced_by_user_id,
        referenced_at=r.referenced_at,
    )


@router.get("", response_model=list[AssetReferenceOut])
async def list_refs(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list[AssetReferenceOut]:
    asset = await db.get(KnowledgeAsset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="知识资产不存在")
    if asset.confidentiality == CONFIDENTIALITY_CONFIDENTIAL and user.get("role") not in CONFIDENTIAL_VIEW_ROLES:
        raise HTTPException(status_code=403, detail="无权访问")
    rows = (await db.execute(
        select(AssetReference)
        .where(AssetReference.asset_id == asset_id)
        .order_by(AssetReference.referenced_at.desc())
    )).scalars().all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=AssetReferenceOut, status_code=status.HTTP_201_CREATED)
async def create_ref(
    asset_id: int,
    payload: AssetReferenceCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> AssetReferenceOut:
    if not await db.get(KnowledgeAsset, asset_id):
        raise HTTPException(status_code=404, detail="知识资产不存在")
    if not await db.get(Project, payload.project_id):
        raise HTTPException(status_code=400, detail="项目不存在")
    r = AssetReference(asset_id=asset_id, **payload.model_dump())
    r.referenced_by_user_id = await _user_id_from_jwt(db, user)
    db.add(r)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="引用记录已存在") from e
    await db.refresh(r)
    return _to_out(r)


@router.delete("/{ref_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ref(
    asset_id: int,
    ref_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> None:
    r = await db.get(AssetReference, ref_id)
    if not r or r.asset_id != asset_id:
        raise HTTPException(status_code=404, detail="引用记录不存在")
    await db.delete(r)
    await db.commit()
