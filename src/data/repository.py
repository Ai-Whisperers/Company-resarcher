"""
Repository pattern implementation for database operations.

Provides a clean abstraction layer for CRUD operations on the
database models, supporting both sync and async operations.

Usage:
    from src.data.repository import CompanyRepository
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(engine) as session:
        repo = CompanyRepository(session)
        company = await repo.create(name="Acme Corp", website="https://acme.com")
"""

import uuid
from datetime import datetime
from typing import Optional, List, TypeVar, Generic, Type
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    Base,
    Company,
    ResearchRun,
    Source,
    Insight,
    ResearchRunStatus,
    InsightCategory,
    SourceType,
)

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic repository base class.

    Provides common CRUD operations for all models.
    """

    model: Type[T]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: uuid.UUID) -> Optional[T]:
        """Get entity by ID."""
        return await self.session.get(self.model, id)

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[T]:
        """Get all entities with pagination."""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        """Create a new entity."""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, id: uuid.UUID, **kwargs) -> Optional[T]:
        """Update an entity by ID."""
        entity = await self.get(id)
        if entity:
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            await self.session.flush()
            await self.session.refresh(entity)
        return entity

    async def delete(self, id: uuid.UUID) -> bool:
        """Delete an entity by ID."""
        entity = await self.get(id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
            return True
        return False

    async def count(self) -> int:
        """Count total entities."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0


class CompanyRepository(BaseRepository[Company]):
    """Repository for Company entities."""

    model = Company

    async def get_by_name(self, name: str) -> Optional[Company]:
        """Get company by exact name match."""
        result = await self.session.execute(
            select(Company).where(Company.name == name)
        )
        return result.scalar_one_or_none()

    async def search_by_name(
        self,
        name_pattern: str,
        limit: int = 10,
    ) -> List[Company]:
        """Search companies by name pattern (case-insensitive)."""
        result = await self.session.execute(
            select(Company)
            .where(Company.name.ilike(f"%{name_pattern}%"))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_industry(
        self,
        industry: str,
        limit: int = 100,
    ) -> List[Company]:
        """Get companies by industry."""
        result = await self.session.execute(
            select(Company)
            .where(Company.industry == industry)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_research_runs(
        self,
        id: uuid.UUID,
    ) -> Optional[Company]:
        """Get company with all research runs loaded."""
        result = await self.session.execute(
            select(Company)
            .where(Company.id == id)
            .options(selectinload(Company.research_runs))
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        name: str,
        **kwargs,
    ) -> tuple[Company, bool]:
        """
        Get existing company or create new one.

        Returns:
            Tuple of (company, created) where created is True if new.
        """
        company = await self.get_by_name(name)
        if company:
            return company, False
        company = await self.create(name=name, **kwargs)
        return company, True


class ResearchRunRepository(BaseRepository[ResearchRun]):
    """Repository for ResearchRun entities."""

    model = ResearchRun

    async def get_by_company(
        self,
        company_id: uuid.UUID,
        limit: int = 100,
    ) -> List[ResearchRun]:
        """Get all research runs for a company."""
        result = await self.session.execute(
            select(ResearchRun)
            .where(ResearchRun.company_id == company_id)
            .order_by(ResearchRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: ResearchRunStatus,
        limit: int = 100,
    ) -> List[ResearchRun]:
        """Get research runs by status."""
        result = await self.session.execute(
            select(ResearchRun)
            .where(ResearchRun.status == status)
            .order_by(ResearchRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_running(self) -> List[ResearchRun]:
        """Get all currently running research runs."""
        return await self.get_by_status(ResearchRunStatus.RUNNING)

    async def get_recent(
        self,
        days: int = 7,
        limit: int = 100,
    ) -> List[ResearchRun]:
        """Get recent research runs within specified days."""
        cutoff = datetime.utcnow() - datetime.timedelta(days=days)
        result = await self.session.execute(
            select(ResearchRun)
            .where(ResearchRun.created_at >= cutoff)
            .order_by(ResearchRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_sources(
        self,
        id: uuid.UUID,
    ) -> Optional[ResearchRun]:
        """Get research run with all sources loaded."""
        result = await self.session.execute(
            select(ResearchRun)
            .where(ResearchRun.id == id)
            .options(selectinload(ResearchRun.sources))
        )
        return result.scalar_one_or_none()

    async def get_with_insights(
        self,
        id: uuid.UUID,
    ) -> Optional[ResearchRun]:
        """Get research run with all insights loaded."""
        result = await self.session.execute(
            select(ResearchRun)
            .where(ResearchRun.id == id)
            .options(selectinload(ResearchRun.insights))
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        id: uuid.UUID,
        status: ResearchRunStatus,
        error_message: Optional[str] = None,
    ) -> Optional[ResearchRun]:
        """Update research run status."""
        updates = {"status": status}
        if status == ResearchRunStatus.RUNNING:
            updates["started_at"] = datetime.utcnow()
        elif status in (ResearchRunStatus.COMPLETED, ResearchRunStatus.FAILED):
            updates["completed_at"] = datetime.utcnow()
            run = await self.get(id)
            if run and run.started_at:
                updates["duration_seconds"] = (
                    datetime.utcnow() - run.started_at
                ).total_seconds()
        if error_message:
            updates["error_message"] = error_message
        return await self.update(id, **updates)

    async def update_progress(
        self,
        id: uuid.UUID,
        progress_percent: int,
        current_phase: Optional[str] = None,
    ) -> Optional[ResearchRun]:
        """Update research run progress."""
        updates = {"progress_percent": min(100, max(0, progress_percent))}
        if current_phase:
            updates["current_phase"] = current_phase
        return await self.update(id, **updates)


class SourceRepository(BaseRepository[Source]):
    """Repository for Source entities."""

    model = Source

    async def get_by_research_run(
        self,
        research_run_id: uuid.UUID,
        limit: int = 1000,
    ) -> List[Source]:
        """Get all sources for a research run."""
        result = await self.session.execute(
            select(Source)
            .where(Source.research_run_id == research_run_id)
            .order_by(Source.quality_score.desc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_domain(
        self,
        domain: str,
        limit: int = 100,
    ) -> List[Source]:
        """Get sources by domain."""
        result = await self.session.execute(
            select(Source)
            .where(Source.domain == domain)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_type(
        self,
        source_type: SourceType,
        research_run_id: Optional[uuid.UUID] = None,
        limit: int = 100,
    ) -> List[Source]:
        """Get sources by type, optionally filtered by research run."""
        query = select(Source).where(Source.source_type == source_type)
        if research_run_id:
            query = query.where(Source.research_run_id == research_run_id)
        result = await self.session.execute(query.limit(limit))
        return list(result.scalars().all())

    async def get_high_quality(
        self,
        research_run_id: uuid.UUID,
        min_quality: float = 0.7,
        limit: int = 50,
    ) -> List[Source]:
        """Get high-quality sources for a research run."""
        result = await self.session.execute(
            select(Source)
            .where(Source.research_run_id == research_run_id)
            .where(Source.quality_score >= min_quality)
            .order_by(Source.quality_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def exists_by_url(
        self,
        url: str,
        research_run_id: uuid.UUID,
    ) -> bool:
        """Check if a source with this URL already exists in the run."""
        result = await self.session.execute(
            select(func.count())
            .select_from(Source)
            .where(Source.url == url)
            .where(Source.research_run_id == research_run_id)
        )
        return (result.scalar() or 0) > 0


class InsightRepository(BaseRepository[Insight]):
    """Repository for Insight entities."""

    model = Insight

    async def get_by_research_run(
        self,
        research_run_id: uuid.UUID,
        limit: int = 500,
    ) -> List[Insight]:
        """Get all insights for a research run."""
        result = await self.session.execute(
            select(Insight)
            .where(Insight.research_run_id == research_run_id)
            .order_by(Insight.importance_score.desc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_category(
        self,
        category: InsightCategory,
        research_run_id: Optional[uuid.UUID] = None,
        limit: int = 100,
    ) -> List[Insight]:
        """Get insights by category, optionally filtered by research run."""
        query = select(Insight).where(Insight.category == category)
        if research_run_id:
            query = query.where(Insight.research_run_id == research_run_id)
        result = await self.session.execute(
            query.order_by(Insight.importance_score.desc().nullslast()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_verified(
        self,
        research_run_id: uuid.UUID,
        limit: int = 100,
    ) -> List[Insight]:
        """Get verified insights for a research run."""
        result = await self.session.execute(
            select(Insight)
            .where(Insight.research_run_id == research_run_id)
            .where(Insight.verified == True)
            .order_by(Insight.importance_score.desc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_sentiment(
        self,
        sentiment: str,
        research_run_id: uuid.UUID,
        limit: int = 100,
    ) -> List[Insight]:
        """Get insights by sentiment (positive, negative, neutral)."""
        result = await self.session.execute(
            select(Insight)
            .where(Insight.research_run_id == research_run_id)
            .where(Insight.sentiment == sentiment)
            .order_by(Insight.importance_score.desc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_top_insights(
        self,
        research_run_id: uuid.UUID,
        limit: int = 10,
    ) -> List[Insight]:
        """Get top insights by importance score."""
        result = await self.session.execute(
            select(Insight)
            .where(Insight.research_run_id == research_run_id)
            .where(Insight.importance_score.isnot(None))
            .order_by(Insight.importance_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def verify(
        self,
        id: uuid.UUID,
        verified_by: str,
    ) -> Optional[Insight]:
        """Mark an insight as verified."""
        return await self.update(
            id,
            verified=True,
            verified_by=verified_by,
            verified_at=datetime.utcnow(),
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "BaseRepository",
    "CompanyRepository",
    "ResearchRunRepository",
    "SourceRepository",
    "InsightRepository",
]
