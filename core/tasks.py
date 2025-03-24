from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_session
from core.models import Link
from core.cache import clear_cache_pattern

async def mark_expired_links():
    """Помечает истекшие ссылки"""
    async with get_async_session() as session:
        # Помечаем ссылки с истекшим сроком действия
        await session.execute(
            update(Link)
            .where(Link.expires_at <= datetime.utcnow())
            .where(Link.is_expired == False)
            .values(is_expired=True, is_active=False)
        )
        await session.commit()

async def mark_inactive_links(days: int = 30):
    """Помечает неиспользуемые ссылки как неактивные"""
    async with get_async_session() as session:
        # Помечаем ссылки, не использовавшиеся более N дней
        inactive_date = datetime.utcnow() - timedelta(days=days)
        await session.execute(
            update(Link)
            .where(Link.last_accessed_at <= inactive_date)
            .where(Link.is_active == True)
            .values(is_active=False)
        )
        await session.commit()

async def cleanup_expired_links():
    """Удаляет истекшие ссылки"""
    async with get_async_session() as session:
        # Удаляем ссылки, помеченные как истекшие
        expired_links = await session.execute(
            select(Link).where(Link.is_expired == True)
        )
        expired_links = expired_links.scalars().all()
        
        for link in expired_links:
            await session.delete(link)
        
        await session.commit()
        
        # Очищаем кэш
        await clear_cache_pattern("popular_links:*")
        await clear_cache_pattern("recent_links:*")
        for link in expired_links:
            await clear_cache_pattern(f"link_stats:{link.short_code}") 