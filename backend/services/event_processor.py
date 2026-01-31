from crud.events import insert_event
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

async def record_event(session: AsyncSession, node_id: uuid.UUID, event_type: str, payload: dict, user_id: str = None):
    await insert_event(session, node_id, event_type, payload, user_id)
