from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from models.db_models import Node
from fastapi import HTTPException
import uuid

async def create_node(session: AsyncSession, node_data: dict) -> Node:
    node = Node(**node_data)
    session.add(node)
    await session.commit()
    await session.refresh(node)
    return node

async def get_node(session: AsyncSession, node_id: uuid.UUID) -> Node | None:
    result = await session.execute(select(Node).where(Node.node_id == node_id))
    return result.scalar_one_or_none()

async def get_node_by_id_or_404(session: AsyncSession, node_id: uuid.UUID) -> Node:
    node = await get_node(session, node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    return node

async def update_node_status(session: AsyncSession, node_id: uuid.UUID, status: str):
    await session.execute(update(Node).where(Node.node_id == node_id).values(status=status))
    await session.commit()

async def get_node_lineage(session: AsyncSession, node_id: uuid.UUID) -> list[Node]:
    """Returns [current, parent, grandparent, ..., root]"""
    lineage = []
    current_id = node_id
    while current_id:
        node = await get_node(session, current_id)
        if not node:
            break
        lineage.append(node)
        current_id = node.parent_id
    return lineage

async def get_all_descendants(session: AsyncSession, node_id: uuid.UUID) -> list[Node]:
    """
    Naive recursive implementation. 
    For production with deep trees, CTEs are better, but keeping it simple for Phase 1.
    """
    descendants = []
    # Get direct children
    result = await session.execute(select(Node).where(Node.parent_id == node_id))
    children = result.scalars().all()
    for child in children:
        descendants.append(child)
        descendants.extend(await get_all_descendants(session, child.node_id))
    return descendants

async def get_tree(session: AsyncSession) -> list[Node]:
    """Returns all non-deleted nodes."""
    result = await session.execute(select(Node).where(Node.status != 'deleted'))
    return result.scalars().all()

async def calculate_position(session: AsyncSession, parent_id: uuid.UUID | None) -> tuple[float, float]:
    """Simple grid layout: parent.x, parent.y + 100. If multiple children, shift x."""
    if not parent_id:
        return 0.0, 0.0
    
    parent = await get_node(session, parent_id)
    if not parent:
        return 0.0, 0.0

    # Count siblings to determine X offset
    result = await session.execute(
        select(func.count()).select_from(Node).where(Node.parent_id == parent_id)
    )
    sibling_count = result.scalar_one()
    
    # 200px spacing per sibling
    return parent.position_x + (sibling_count * 200), parent.position_y + 200.0

from sqlalchemy import func
