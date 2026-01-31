from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exc
from models.db_models import KnowledgeGraph, Node
from crud.nodes import get_node_lineage
import uuid
import datetime

async def store_graph_edges(session: AsyncSession, node_id: uuid.UUID, entities: list, relations: list) -> int:
    """
    Parse graph-builder output. Insert edges into knowledge_graph.
    Skip edges that already exist (unique constraint).
    Returns count of new edges inserted.
    """
    count = 0
    # relations usually contain: {from, to, relation_type, confidence}
    # entities is just a list of strings, usually implied by relations but we might process them if needed.
    # We mainly store relations as edges.
    
    for rel in relations:
        from_e = rel.get("from_entity") or rel.get("source")
        to_e = rel.get("to_entity") or rel.get("target")
        r_type = rel.get("relation_type") or rel.get("type", "RELATED")
        conf = rel.get("confidence", 1.0)
        
        if not from_e or not to_e:
            continue

        # Check existence or use ignore/on_conflict
        # SQLAlchemy asyncpg INSERT ON CONFLICT is a bit verbose, we can try/except integrity error for simple logic or check first.
        # Checking first is safer for cross-db compat, though less atomic.
        
        # We will use select check for specific edge
        existing = await session.execute(
            select(KnowledgeGraph).where(
                KnowledgeGraph.from_entity == from_e,
                KnowledgeGraph.to_entity == to_e,
                KnowledgeGraph.relation_type == r_type,
                KnowledgeGraph.source_node == node_id
            )
        )
        if existing.scalar_one_or_none():
            continue
            
        edge = KnowledgeGraph(
            from_entity=from_e,
            to_entity=to_e,
            relation_type=r_type,
            source_node=node_id,
            confidence=conf
        )
        session.add(edge)
        count += 1
    
    if count > 0:
        await session.commit()
    return count

async def get_node_graph(session: AsyncSession, node_id: uuid.UUID) -> list[dict]:
    """All non-deleted edges where source_node = node_id."""
    result = await session.execute(
        select(KnowledgeGraph).where(
            KnowledgeGraph.source_node == node_id,
            KnowledgeGraph.deleted_at.is_(None)
        )
    )
    # Convert to dicts for easy JSON serialization
    return [
        {
            "from_entity": e.from_entity,
            "to_entity": e.to_entity,
            "relation_type": e.relation_type,
            "confidence": e.confidence
        }
        for e in result.scalars().all()
    ]

async def get_lineage_graph(session: AsyncSession, node_id: uuid.UUID) -> list[dict]:
    """All non-deleted edges where source_node is in the node's lineage."""
    lineage = await get_node_lineage(session, node_id)
    node_ids = [n.node_id for n in lineage]
    
    result = await session.execute(
        select(KnowledgeGraph).where(
            KnowledgeGraph.source_node.in_(node_ids),
            KnowledgeGraph.deleted_at.is_(None)
        )
    )
    return [
        {
            "from_entity": e.from_entity,
            "to_entity": e.to_entity,
            "relation_type": e.relation_type,
            "confidence": e.confidence,
            "source_node": str(e.source_node)
        }
        for e in result.scalars().all()
    ]

async def get_parent_graph(session: AsyncSession, node_id: uuid.UUID) -> list[dict]:
    """Graph of the parent node only. Used by graph-builder context."""
    # We need to find parent ID first
    result = await session.execute(select(Node).where(Node.node_id == node_id))
    node = result.scalar_one_or_none()
    if not node or not node.parent_id:
        return []
    
    return await get_node_graph(session, node.parent_id)

async def merge_graphs(session: AsyncSession, source_id: uuid.UUID, target_id: uuid.UUID):
    """
    After a merge: mark source edges with merged_into metadata? 
    The prompt says: 'mark source edges with merged_into metadata. Do not duplicate — if an edge already exists on target, update confidence.'
    Also logic for adding edges to target.
    """
    source_edges = await session.execute(
        select(KnowledgeGraph).where(
            KnowledgeGraph.source_node == source_id,
            KnowledgeGraph.deleted_at.is_(None)
        )
    )
    source_edges = source_edges.scalars().all()
    
    for s_edge in source_edges:
        # Check if exists in target
        result = await session.execute(
            select(KnowledgeGraph).where(
                KnowledgeGraph.from_entity == s_edge.from_entity,
                KnowledgeGraph.to_entity == s_edge.to_entity,
                KnowledgeGraph.relation_type == s_edge.relation_type,
                KnowledgeGraph.source_node == target_id
            )
        )
        t_edge = result.scalar_one_or_none()
        
        if t_edge:
            # Update confidence max? or average? Prompt says "update confidence". I'll take max.
            t_edge.confidence = max(t_edge.confidence, s_edge.confidence)
            # Add metadata
            meta = t_edge.metadata_ or {}
            meta["merged_from"] = str(source_id)
            t_edge.metadata_ = meta
        else:
            # Create new edge on target
            new_edge = KnowledgeGraph(
                from_entity=s_edge.from_entity,
                to_entity=s_edge.to_entity,
                relation_type=s_edge.relation_type,
                source_node=target_id,
                confidence=s_edge.confidence,
                metadata_={"merged_from": str(source_id)}
            )
            session.add(new_edge)
    
    await session.commit()

async def soft_delete_edges(session: AsyncSession, node_id: uuid.UUID):
    """SET deleted_at = NOW() on all edges where source_node = node_id."""
    await session.execute(
        update(KnowledgeGraph)
        .where(KnowledgeGraph.source_node == node_id)
        .values(deleted_at=func.now())
    )
    await session.commit()

from sqlalchemy import func
