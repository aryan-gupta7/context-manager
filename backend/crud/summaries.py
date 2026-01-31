from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from models.db_models import NodeSummary
import uuid

async def create_summary(session: AsyncSession, node_id: uuid.UUID, summary_json: dict, generated_from_event: uuid.UUID = None) -> NodeSummary:
    # Set is_latest=False on existing
    await session.execute(
        update(NodeSummary)
        .where(NodeSummary.node_id == node_id)
        .where(NodeSummary.is_latest == True)
        .values(is_latest=False)
    )
    
    summary = NodeSummary(
        node_id=node_id,
        summary=summary_json,
        generated_from_event=generated_from_event,
        is_latest=True
    )
    session.add(summary)
    await session.commit()
    await session.refresh(summary)
    return summary

async def get_latest_summary(session: AsyncSession, node_id: uuid.UUID) -> NodeSummary | None:
    result = await session.execute(
        select(NodeSummary)
        .where(NodeSummary.node_id == node_id)
        .where(NodeSummary.is_latest == True)
        .order_by(desc(NodeSummary.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()
