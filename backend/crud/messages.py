from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc
from models.db_models import Message
import uuid

async def create_message(session: AsyncSession, node_id: uuid.UUID, role: str, content: str, token_count: int = None, metadata: dict = None) -> Message:
    msg = Message(
        node_id=node_id,
        role=role,
        content=content,
        token_count=token_count,
        metadata_=metadata or {}
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg

async def get_messages(session: AsyncSession, node_id: uuid.UUID, limit: int = None) -> list[Message]:
    stmt = select(Message).where(Message.node_id == node_id).order_by(asc(Message.timestamp))
    if limit:
        stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_last_n_messages(session: AsyncSession, node_id: uuid.UUID, n: int) -> list[Message]:
    # Get last N desc, then reverse in python
    stmt = select(Message).where(Message.node_id == node_id).order_by(desc(Message.timestamp)).limit(n)
    result = await session.execute(stmt)
    msgs = result.scalars().all()
    return list(reversed(msgs))
