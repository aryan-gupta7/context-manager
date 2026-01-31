from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database import Base

class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id"), nullable=True)
    title = Column(String, nullable=False)
    node_type = Column(String, default="standard", nullable=False) # Check constraint handled by validator or DB enum if strict
    status = Column(String, default="active", nullable=False)
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, nullable=True)
    metadata_ = Column("metadata", JSON, default={})

    parent = relationship("Node", remote_side=[node_id], backref="children")
    messages = relationship("Message", back_populates="node", cascade="all, delete-orphan")
    summaries = relationship("NodeSummary", back_populates="node")
    events = relationship("NodeEvent", back_populates="node")
    # Knowledge graph relationship might be complex due to many-to-one; defining backref on KnowledgeGraph

class NodeEvent(Base):
    __tablename__ = "node_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String, nullable=True)

    node = relationship("Node", back_populates="events")

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    token_count = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSON, default={})

    node = relationship("Node", back_populates="messages")

class NodeSummary(Base):
    __tablename__ = "node_summaries"

    summary_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id"), nullable=False)
    summary = Column(JSON, nullable=False)
    generated_from_event = Column(UUID(as_uuid=True), ForeignKey("node_events.event_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_latest = Column(Boolean, default=True)

    node = relationship("Node", back_populates="summaries")
    event = relationship("NodeEvent")

class KnowledgeGraph(Base):
    __tablename__ = "knowledge_graph"

    edge_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_entity = Column(String, nullable=False)
    to_entity = Column(String, nullable=False)
    relation_type = Column(String, nullable=False)
    source_node = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id"), nullable=False)
    confidence = Column(Float, default=1.0)
    metadata_ = Column("metadata", JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    node = relationship("Node")

    __table_args__ = (
        UniqueConstraint('from_entity', 'to_entity', 'relation_type', 'source_node', name='uix_graph_edge'),
    )
