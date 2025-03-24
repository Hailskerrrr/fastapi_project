from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_session
from core.models import Link, User, Project
from core.schemas import LinkCreate, LinkRead, LinkUpdate, ProjectCreate, ProjectRead, ProjectUpdate
from core.users import current_active_user
from core.cache import get_cached_data, set_cached_data, delete_cached_data, clear_cache_pattern
from core.auth import get_current_user
from pydantic import BaseModel, HttpUrl
import secrets
import string

router = APIRouter()

def generate_short_code(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class LinkResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    custom_alias: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_accessed_at: Optional[datetime]
    access_count: int
    is_active: bool
    is_expired: bool
    project_id: Optional[int]

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.post("/links/shorten", response_model=LinkResponse)
async def create_short_link(
    link_data: LinkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    short_code = link_data.custom_alias or generate_short_code()
    
    existing_link = await db.execute(
        select(Link).where(
            (Link.short_code == short_code) | (Link.custom_alias == short_code)
        )
    )
    if existing_link.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Short code or custom alias already exists"
        )

    if link_data.project_id:
        project = await db.execute(
            select(Project).where(
                Project.id == link_data.project_id,
                Project.user_id == current_user.id
            )
        )
        if not project.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

    new_link = Link(
        original_url=str(link_data.original_url),
        short_code=short_code,
        custom_alias=link_data.custom_alias,
        user_id=current_user.id,
        project_id=link_data.project_id
    )
    
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    
    return new_link

@router.get("/links/{short_code}", response_model=LinkResponse)
async def get_link(
    short_code: str,
    db: AsyncSession = Depends(get_async_session)
):
    link = await db.execute(
        select(Link).where(Link.short_code == short_code)
    )
    link = link.scalar_one_or_none()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    if link.is_expired:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Link has expired"
        )
    
    link.access_count += 1
    link.last_accessed_at = datetime.utcnow()
    await db.commit()
    
    return link

@router.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    db: AsyncSession = Depends(get_async_session)
):
    link = await db.execute(
        select(Link).where(Link.short_code == short_code)
    )
    link = link.scalar_one_or_none()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    if link.is_expired:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Link has expired"
        )
    
    link.access_count += 1
    link.last_accessed_at = datetime.utcnow()
    await db.commit()
    
    return RedirectResponse(url=str(link.original_url))

@router.get("/links/", response_model=List[LinkResponse])
async def get_user_links(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(Link).where(Link.user_id == current_user.id)
    )
    return result.scalars().all()

@router.get("/links/{short_code}/stats", response_model=LinkResponse)
async def get_link_stats(
    short_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    link = await db.execute(
        select(Link).where(
            Link.short_code == short_code,
            Link.user_id == current_user.id
        )
    )
    link = link.scalar_one_or_none()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    return link

@router.get("/links/popular", response_model=List[LinkResponse])
async def get_popular_links(
    limit: int = 10,
    db: AsyncSession = Depends(get_async_session)
):
    cache_key = f"popular_links_{limit}"
    cached_data = await get_cached_data(cache_key)
    
    if cached_data:
        return cached_data
    
    result = await db.execute(
        select(Link)
        .where(Link.is_active == True)
        .order_by(Link.access_count.desc())
        .limit(limit)
    )
    links = result.scalars().all()
    
    await set_cached_data(cache_key, links)
    return links

@router.post("/projects/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        user_id=current_user.id
    )
    
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    
    return new_project

@router.get("/projects/", response_model=List[ProjectResponse])
async def get_user_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(Project).where(Project.user_id == current_user.id)
    )
    return result.scalars().all()

@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    project = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = project.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project.name = project_data.name
    project.description = project_data.description
    await db.commit()
    await db.refresh(project)
    
    return project

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    project = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = project.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted successfully"}

@router.delete("/links/{short_code}")
async def delete_link(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_active_user)
):
    link = await session.execute(
        select(Link).where(Link.short_code == short_code)
    )
    link = link.scalar_one_or_none()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if user and link.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    await session.delete(link)
    await session.commit()
    
    # Очищаем кэш
    await clear_cache_pattern("popular_links:*")
    await clear_cache_pattern("recent_links:*")
    await delete_cached_data(f"link_stats:{short_code}")
    
    return {"message": "Link deleted successfully"}

@router.put("/links/{short_code}", response_model=LinkRead)
async def update_link(
    short_code: str,
    link_update: LinkUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_active_user)
):
    link = await session.execute(
        select(Link).where(Link.short_code == short_code)
    )
    link = link.scalar_one_or_none()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if user and link.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if link_update.original_url:
        link.original_url = str(link_update.original_url)
    if link_update.expires_at:
        link.expires_at = link_update.expires_at
    
    await session.commit()
    await session.refresh(link)
    
    # Очищаем кэш
    await clear_cache_pattern("popular_links:*")
    await clear_cache_pattern("recent_links:*")
    await delete_cached_data(f"link_stats:{short_code}")
    
    return link

@router.get("/links/search")
async def search_link(
    original_url: str = Query(..., description="Original URL to search for"),
    session: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_active_user)
):
    link = await session.execute(
        select(Link).where(Link.original_url == original_url)
    )
    link = link.scalar_one_or_none()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if user and link.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return link

@router.get("/links/my", response_model=List[LinkRead])
async def get_my_links(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
    skip: int = 0,
    limit: int = 10
):
    """Получение всех ссылок текущего пользователя"""
    result = await session.execute(
        select(Link)
        .where(Link.user_id == user.id)
        .order_by(Link.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/links/recent", response_model=List[LinkRead])
async def get_recent_links(
    session: AsyncSession = Depends(get_async_session),
    limit: int = 10
):
    """Получение недавно созданных ссылок"""
    # Пробуем получить из кэша
    cache_key = f"recent_links:{limit}"
    cached_data = await get_cached_data(cache_key)
    if cached_data:
        return [LinkRead(**link) for link in cached_data]

    # Если нет в кэше, получаем из БД
    result = await session.execute(
        select(Link)
        .order_by(Link.created_at.desc())
        .limit(limit)
    )
    links = result.scalars().all()
    
    # Сохраняем в кэш только необходимые данные
    cache_data = [
        {
            "id": link.id,
            "original_url": link.original_url,
            "short_code": link.short_code,
            "custom_alias": link.custom_alias,
            "created_at": link.created_at.isoformat(),
            "last_accessed_at": link.last_accessed_at.isoformat() if link.last_accessed_at else None,
            "access_count": link.access_count,
            "is_active": link.is_active,
            "is_expired": link.is_expired,
            "user_id": link.user_id,
            "project_id": link.project_id
        }
        for link in links
    ]
    await set_cached_data(cache_key, cache_data, expire=300)  # Кэшируем на 5 минут
    return links

@router.get("/stats/overview")
async def get_stats_overview(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Получение общей статистики пользователя"""
    # Общее количество ссылок
    total_links = await session.execute(
        select(func.count()).select_from(Link).where(Link.user_id == user.id)
    )
    total_links = total_links.scalar()

    # Общее количество переходов
    total_clicks = await session.execute(
        select(func.sum(Link.access_count)).select_from(Link).where(Link.user_id == user.id)
    )
    total_clicks = total_clicks.scalar() or 0

    # Количество активных ссылок
    active_links = await session.execute(
        select(func.count()).select_from(Link)
        .where(Link.user_id == user.id)
        .where(Link.is_active == True)
    )
    active_links = active_links.scalar()

    return {
        "total_links": total_links,
        "total_clicks": total_clicks,
        "active_links": active_links
    }

@router.get("/projects/{project_id}/links", response_model=List[LinkRead])
async def get_project_links(
    project_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Получение ссылок проекта"""
    # Проверяем права доступа
    project = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project.scalar_one_or_none()
    
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = await session.execute(
        select(Link)
        .where(Link.project_id == project_id)
        .order_by(Link.created_at.desc())
    )
    return result.scalars().all()

@router.get("/links/expired", response_model=List[LinkRead])
async def get_expired_links(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Получение истории истекших ссылок"""
    result = await session.execute(
        select(Link)
        .where(Link.user_id == user.id)
        .where(Link.is_expired == True)
        .order_by(Link.expires_at.desc())
    )
    return result.scalars().all()

@router.get("/links/inactive", response_model=List[LinkRead])
async def get_inactive_links(
    days: int = Query(30, description="Количество дней неактивности"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Получение неактивных ссылок"""
    inactive_date = datetime.utcnow() - timedelta(days=days)
    result = await session.execute(
        select(Link)
        .where(Link.user_id == user.id)
        .where(Link.is_active == False)
        .where(Link.last_accessed_at <= inactive_date)
        .order_by(Link.last_accessed_at.desc())
    )
    return result.scalars().all() 