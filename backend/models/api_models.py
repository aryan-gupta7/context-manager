from pydantic import BaseModel, Field, constr
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

# --- REQUEST MODELS ---

class CreateProjectRequest(BaseModel):
    name: constr(min_length=1, max_length=200)
    description: Optional[str] = None

class UpdateProjectRequest(BaseModel):
    name: Optional[constr(min_length=1, max_length=200)] = None
    description: Optional[str] = None

class CreateNodeRequest(BaseModel):
    project_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    title: constr(min_length=1, max_length=200)
    node_type: str = "standard" # standard, exploration
    initial_message: Optional[str] = None

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

class ProjectResponse(BaseModel):
    project_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    node_count: int = 0

class NodeResponse(BaseModel):
    node_id: UUID
    project_id: Optional[UUID]
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
    knowledge_graph_updates: Dict[str, Any]
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
    summary_text: Optional[str] = None  # Brief summary text for display
    merge_parent_id: Optional[UUID] = None  # Secondary parent from merge operations
    position: Dict[str, float] = {"x": 0.0, "y": 0.0}
    children: List['TreeNodeResponse'] = []

class InheritedContextResponse(BaseModel):
    """Response model for inherited context from parent lineage"""
    node_id: UUID
    facts: List[Dict[str, Any]] = []
    decisions: List[Dict[str, Any]] = []
    open_questions: List[str] = []
    key_entities: List[str] = []
    lineage_depth: int = 0
    parent_title: Optional[str] = None
    parent_node_id: Optional[UUID] = None

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
