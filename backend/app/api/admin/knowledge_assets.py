from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.data_dict import DataDict
from app.models.knowledge_asset import (
    CONFIDENTIALITY_CONFIDENTIAL,
    CONFIDENTIALITY_INTERNAL,
    CONFIDENTIALITY_PUBLIC,
    KnowledgeAsset,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.knowledge_asset import (
    KnowledgeAssetCreate,
    KnowledgeAssetOut,
    KnowledgeAssetUpdate,
)

router = APIRouter(prefix="/knowledge-assets", tags=["knowledge-assets"])

# Roles allowed to view confidential assets (PLAN A10):
CONFIDENTIAL_VIEW_ROLES = {"admin", "lead", "pm", "finance"}


async def _label_for_category(db: AsyncSession, code: str) -> str | None:
    row = (
        await db.execute(
            select(DataDict).where(DataDict.category == "asset_category", DataDict.code == code)
        )
    ).scalar_one_or_none()
    return row.label if row else None


def _can_view_confidential(user: dict) -> bool:
    return user.get("role") in CONFIDENTIAL_VIEW_ROLES


async def _user_id_from_jwt(db: AsyncSession, user: dict) -> int | None:
    username = user.get("sub")
    if not username:
        return None
    u = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    return u.id if u else None


async def _to_out(db: AsyncSession, a: KnowledgeAsset) -> KnowledgeAssetOut:
    return KnowledgeAssetOut(
        id=a.id,
        project_id=a.project_id,
        project_name=a.project.name if a.project else None,
        category=a.category,
        category_label=await _label_for_category(db, a.category),
        title=a.title,
        summary=a.summary,
        content=a.content,
        external_url=a.external_url,
        file_path=a.file_path,
        tags=a.tags,
        confidentiality=a.confidentiality,
        created_by_user_id=a.created_by_user_id,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.get("", response_model=list[KnowledgeAssetOut])
async def list_assets(
    category: str | None = None,
    project_id: int | None = None,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list[KnowledgeAssetOut]:
    stmt = select(KnowledgeAsset).order_by(KnowledgeAsset.id.desc())
    if category:
        stmt = stmt.where(KnowledgeAsset.category == category)
    if project_id is not None:
        stmt = stmt.where(KnowledgeAsset.project_id == project_id)
    if keyword:
        kw = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                KnowledgeAsset.title.like(kw),
                KnowledgeAsset.summary.like(kw),
                KnowledgeAsset.tags.like(kw),
            )
        )
    # Confidentiality filter
    if not _can_view_confidential(user):
        stmt = stmt.where(KnowledgeAsset.confidentiality.in_([CONFIDENTIALITY_PUBLIC, CONFIDENTIALITY_INTERNAL]))
    rows = (await db.execute(stmt)).scalars().all()
    return [await _to_out(db, a) for a in rows]


@router.get("/{aid}", response_model=KnowledgeAssetOut)
async def get_asset(
    aid: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> KnowledgeAssetOut:
    a = await db.get(KnowledgeAsset, aid)
    if not a:
        raise HTTPException(status_code=404, detail="知识资产不存在")
    if a.confidentiality == CONFIDENTIALITY_CONFIDENTIAL and not _can_view_confidential(user):
        raise HTTPException(status_code=403, detail="机密资产，无访问权限")
    return await _to_out(db, a)


@router.post("", response_model=KnowledgeAssetOut, status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: KnowledgeAssetCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> KnowledgeAssetOut:
    if payload.project_id is not None and not await db.get(Project, payload.project_id):
        raise HTTPException(status_code=400, detail="项目不存在")
    if not await _label_for_category(db, payload.category):
        raise HTTPException(status_code=400, detail=f"资产分类 '{payload.category}' 不在字典中")

    a = KnowledgeAsset(**payload.model_dump())
    a.created_by_user_id = await _user_id_from_jwt(db, user)
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return await _to_out(db, a)


@router.patch("/{aid}", response_model=KnowledgeAssetOut)
async def update_asset(
    aid: int,
    payload: KnowledgeAssetUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> KnowledgeAssetOut:
    a = await db.get(KnowledgeAsset, aid)
    if not a:
        raise HTTPException(status_code=404, detail="知识资产不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    await db.commit()
    await db.refresh(a)
    return await _to_out(db, a)


@router.delete("/{aid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    aid: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    a = await db.get(KnowledgeAsset, aid)
    if not a:
        raise HTTPException(status_code=404, detail="知识资产不存在")
    await db.delete(a)
    await db.commit()
