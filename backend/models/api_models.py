from pydantic import BaseModel, Field, constr
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

# --- REQUEST MODELS ---

class CreateNodeRequest(BaseModel):
    parent_id: Optional[UUID] = None
    title: constr(min_length=1, max_length=200)
    node_type: str = "standard" # standard, exploration

class SendMessageRequest(BaseModel):
    content: str

class MergeRequest(BaseModel):
    source_node_id: UUID
    target_node_id: UUID

class DeleteRequest(BaseModel):
    cascade: bool = False

class CopyRequest(BaseModel):
    new_parent_id: Optional[UUID] = None

# --- RESPONSE MODELS ---

class NodeResponse(BaseModel):
    node_id: UUID
    parent_id: Optional[UUID]
    title: str
    node_type: str
    status: str
    position: Dict[str, float]
    created_at: datetime
    created_by: Optional[str]
    metadata: Dict[str, Any]

class MessageResponse(BaseModel):
    message_id: UUID
    node_id: UUID
    role: str
    content: str
    timestamp: datetime
    token_count: Optional[int]
    metadata: Dict[str, Any]
    agent_used: Optional[str] = None
    fallback_from: Optional[str] = None

class SummarizeResponse(BaseModel):
    summary_id: UUID
    node_id: UUID
    summary: Dict[str, Any]
    graph_extraction_status: str # "success", "failed"
    knowledge_graph: Optional[Dict[str, int]] # counts of entities/relations added
    graph_extraction_error: Optional[str] = None

class MergeResponse(BaseModel):
    target_node_id: UUID
    source_node_id: UUID
    updated_summary: Dict[str, Any]
    conflicts: List[str]
    knowledge_graph_updates: Dict[str, int]
    source_node_status: str

class DeleteResponse(BaseModel):
    node_id: UUID
    status: str
    affected_descendants: List[UUID]
    recomputed: bool
    graph_edges_removed: int

class TreeNodeResponse(BaseModel):
    node_id: UUID
    title: str
    status: str
    node_type: str
    message_count: Optional[int] = 0
    has_summary: bool
    children: List['TreeNodeResponse'] = []

class GraphEdge(BaseModel):
    from_entity: str
    to_entity: str
    relation_type: str
    confidence: float
    source_node: UUID

class GraphResponse(BaseModel):
    node_id: UUID
    entities: List[str]
    relations: List[GraphEdge]

# Recursive model update
TreeNodeResponse.model_rebuild()
