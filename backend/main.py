from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, init_db
from models.api_models import (
    CreateNodeRequest, NodeResponse,
    SendMessageRequest, MessageResponse,
    SummarizeResponse,
    MergeRequest, MergeResponse,
    DeleteRequest, DeleteResponse,
    CopyRequest,
    TreeNodeResponse, GraphResponse, GraphEdge,
    CreateProjectRequest, UpdateProjectRequest, ProjectResponse
)
from crud.nodes import create_node as crud_create_node, get_node_by_id_or_404, get_tree as crud_get_tree, update_node_status, calculate_position, get_node_lineage
from crud.messages import create_message, get_messages as crud_get_messages
from crud.summaries import create_summary, get_latest_summary
from services.context_manager import context_manager
from services.llm_service import llm_service
from services.event_processor import record_event
from services.graph_service import store_graph_edges, get_lineage_graph, soft_delete_edges, merge_graphs
from utils.helpers import estimate_token_count
import json
import logging
import uuid

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fractal Workspace Backend", version="0.1.0")

# Add CORS middleware for frontend-backend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.post("/api/v1/nodes", response_model=NodeResponse)
async def create_node(request: CreateNodeRequest, session: AsyncSession = Depends(get_db)):
    # If parent provided, check existence
    if request.parent_id:
        await get_node_by_id_or_404(session, request.parent_id)

    # Position calculation
    pos_x, pos_y = await calculate_position(session, request.parent_id)

    node_data = {
        "title": request.title,
        "project_id": request.project_id,
        "parent_id": request.parent_id,
        "node_type": request.node_type,
        "position_x": pos_x,
        "position_y": pos_y,
        "status": "active"
    }
    
    node = await crud_create_node(session, node_data)
    await record_event(session, node.node_id, "NODE_CREATED", {
        "title": node.title,
        "parent_id": str(node.parent_id) if node.parent_id else None,
        "project_id": str(node.project_id) if node.project_id else None
    })
    
    return NodeResponse(
        node_id=node.node_id,
        project_id=node.project_id,
        parent_id=node.parent_id,
        title=node.title,
        node_type=node.node_type,
        status=node.status,
        position={"x": node.position_x, "y": node.position_y},
        created_at=node.created_at,
        created_by=node.created_by,
        metadata=node.metadata_ or {}
    )

@app.post("/api/v1/nodes/{node_id}/messages", response_model=MessageResponse)
async def send_message(node_id: uuid.UUID, request: SendMessageRequest, session: AsyncSession = Depends(get_db)):
    node = await get_node_by_id_or_404(session, node_id)
    if node.status != "active":
        raise HTTPException(status_code=400, detail="Node is not active")

    # 1. User Message
    user_msg_token_count = estimate_token_count(request.content)
    user_msg = await create_message(session, node_id, "user", request.content, user_msg_token_count)
    await record_event(session, node_id, "MESSAGE_ADDED", {"role": "user", "message_id": str(user_msg.message_id)})

    # 2. Build Context
    chat_ctx = await context_manager.build_chat_context(session, node_id)

    # 3. Call LLM
    fallback_from = None
    agent_used = "main-reasoner"
    
    if node.node_type == "exploration":
        response_text, fallback = await llm_service.exploration_chat(chat_ctx["system_prompt"], request.content)
        fallback_from = fallback
        if fallback:
            agent_used = "main-reasoner (fallback)"
        else:
            agent_used = "exploration-model"
    else:
        response_text = await llm_service.chat(chat_ctx["system_prompt"], request.content)

    # 4. Assistant Message
    asst_token_count = estimate_token_count(response_text)
    asst_msg = await create_message(session, node_id, "assistant", response_text, asst_token_count)
    await record_event(session, node_id, "MESSAGE_ADDED", {"role": "assistant", "message_id": str(asst_msg.message_id)})

    return MessageResponse(
        message_id=asst_msg.message_id,
        node_id=asst_msg.node_id,
        role=asst_msg.role,
        content=asst_msg.content,
        timestamp=asst_msg.timestamp,
        token_count=asst_msg.token_count,
        metadata=asst_msg.metadata_,
        agent_used=agent_used,
        fallback_from=fallback_from
    )

@app.post("/api/v1/nodes/{node_id}/summarize", response_model=SummarizeResponse)
async def summarize_node(node_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    node = await get_node_by_id_or_404(session, node_id)
    if node.status != "active":
        raise HTTPException(status_code=400, detail="Node is not active")

    # Build Context
    ctx = await context_manager.build_summarize_context(session, node_id)
    
    # Call Summarizer
    try:
        summary_text = await llm_service.summarize(ctx["system_prompt"], "")
        summary_dict = json.loads(summary_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse summary JSON from LLM")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Store Summary
    summary_obj = await create_summary(session, node_id, summary_dict)
    await record_event(session, node_id, "SUMMARY_UPDATED", {"summary_id": str(summary_obj.summary_id)})

    # Graph Extraction
    graph_status = "success"
    graph_error = None
    graph_counts = None
    
    try:
        graph_ctx = await context_manager.build_graph_context(session, node_id, summary_dict)
        graph_response = await llm_service.extract_graph(graph_ctx["system_prompt"], "")
        graph_data = json.loads(graph_response)
        
        entities = graph_data.get("entities", [])
        relations = graph_data.get("relations", [])
        
        count = await store_graph_edges(session, node_id, entities, relations)
        
        await record_event(session, node_id, "GRAPH_UPDATED", {"relations_added": count})
        graph_counts = {"entities_count": len(entities), "relations_added": count}
        
    except Exception as e:
        graph_status = "failed"
        graph_error = f"Graph extraction failed: {str(e)}. Re-run summarize to retry."
        logger.error(f"Graph extraction failed for node {node_id}: {e}")

    return SummarizeResponse(
        summary_id=summary_obj.summary_id,
        node_id=node_id,
        summary=summary_obj.summary,
        graph_extraction_status=graph_status,
        knowledge_graph=graph_counts,
        graph_extraction_error=graph_error
    )

@app.post("/api/v1/nodes/merge", response_model=MergeResponse)
async def merge_nodes(request: MergeRequest, session: AsyncSession = Depends(get_db)):
    source = await get_node_by_id_or_404(session, request.source_node_id)
    target = await get_node_by_id_or_404(session, request.target_node_id)

    # Validate lineage: Source must be descendant of Target? 
    # Prompt: "Validate source is a descendant of target (walk lineage from source, check if target is in it)"
    lineage = await get_node_lineage(session, source.node_id)
    is_descendant = any(n.node_id == target.node_id for n in lineage)
    if not is_descendant:
        raise HTTPException(status_code=400, detail="Source node is not a descendant of target node")

    await record_event(session, target.node_id, "NODE_MERGED", {"source_node": str(source.node_id)})

    # Merge Logic
    ctx = await context_manager.build_merge_context(session, source.node_id, target.node_id)
    merge_resp_text = await llm_service.merge(ctx["system_prompt"], "")
    
    try:
        merge_data = json.loads(merge_resp_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse merge JSON")

    updated_summary = merge_data.get("updated_target_summary", {})
    conflicts = merge_data.get("conflicts", [])

    # Store new summary for target
    await create_summary(session, target.node_id, updated_summary)
    await record_event(session, target.node_id, "SUMMARY_UPDATED", {"reason": "merge", "source": str(source.node_id)})

    # Merge Graphs
    await merge_graphs(session, source.node_id, target.node_id)
    
    # Freeze Source
    await update_node_status(session, source.node_id, "frozen")

    # Insert Summary Message
    summary_msg_content = f"Merged from {source.title}: {json.dumps(updated_summary.get('FACTS', 'See summary'))}"
    await create_message(session, target.node_id, "summary", summary_msg_content)

    return MergeResponse(
        target_node_id=target.node_id,
        source_node_id=source.node_id,
        updated_summary=updated_summary,
        conflicts=conflicts,
        knowledge_graph_updates={"status": "merged"}, # Simplified
        source_node_status="frozen"
    )

@app.post("/api/v1/nodes/{node_id}/delete", response_model=DeleteResponse)
async def delete_node(node_id: uuid.UUID, request: DeleteRequest, session: AsyncSession = Depends(get_db)):
    node = await get_node_by_id_or_404(session, node_id)
    
    await record_event(session, node_id, "NODE_DELETED", {})
    await update_node_status(session, node_id, "deleted")
    
    # Soft delete edges
    await soft_delete_edges(session, node_id)
    
    # In a full implementation, we'd count edges. Here we assume success.
    # Also would handle cascading status updates if requested.
    
    return DeleteResponse(
        node_id=node_id,
        status="deleted",
        affected_descendants=[], # Placeholder for Phase 1
        recomputed=False,
        graph_edges_removed=0 # Placeholder
    )

@app.post("/api/v1/nodes/{node_id}/copy", response_model=NodeResponse)
async def copy_node(node_id: uuid.UUID, request: CopyRequest, session: AsyncSession = Depends(get_db)):
    original = await get_node_by_id_or_404(session, node_id)
    
    new_parent_id = request.new_parent_id or original.parent_id
    if new_parent_id:
        await get_node_by_id_or_404(session, new_parent_id)
        
    pos_x, pos_y = await calculate_position(session, new_parent_id)
    
    new_node = await crud_create_node(session, {
        "title": f"{original.title} (Copy)",
        "parent_id": new_parent_id,
        "node_type": original.node_type,
        "position_x": pos_x,
        "position_y": pos_y,
        "status": "active"
    })
    
    # Copy latest summary if any
    # (Leaving simplistic for now: just record event)
    await record_event(session, new_node.node_id, "NODE_COPIED", {"original_node_id": str(original.node_id)})
    
    return NodeResponse(
        node_id=new_node.node_id,
        parent_id=new_node.parent_id,
        title=new_node.title,
        node_type=new_node.node_type,
        status=new_node.status,
        position={"x": new_node.position_x, "y": new_node.position_y},
        created_at=new_node.created_at,
        created_by=new_node.created_by,
        metadata=new_node.metadata_ or {}
    )

@app.get("/api/v1/nodes/tree", response_model=list[TreeNodeResponse])
async def get_tree(session: AsyncSession = Depends(get_db)):
    nodes = await crud_get_tree(session)
    
    # Fetch summaries for all nodes
    node_summaries = {}
    for n in nodes:
        summary = await get_latest_summary(session, n.node_id)
        if summary:
            # Extract summary text from the summary JSON
            summary_json = summary.summary
            if isinstance(summary_json, dict):
                # Try to get a meaningful text from the summary
                facts = summary_json.get("FACTS", [])
                if isinstance(facts, list) and facts:
                    node_summaries[n.node_id] = "; ".join(str(f) for f in facts[:3])  # First 3 facts
                else:
                    node_summaries[n.node_id] = str(summary_json.get("summary", ""))[:200]
    
    # Build tree in memory
    node_map = {}
    roots = []
    
    # Create responses first
    for n in nodes:
        summary_text = node_summaries.get(n.node_id)
        node_map[n.node_id] = TreeNodeResponse(
            node_id=n.node_id,
            title=n.title,
            status=n.status,
            node_type=n.node_type,
            has_summary=n.node_id in node_summaries,
            summary_text=summary_text,
            position={"x": n.position_x, "y": n.position_y},
            children=[]
        )
        
    # Link
    for n in nodes:
        if n.parent_id and n.parent_id in node_map:
            node_map[n.parent_id].children.append(node_map[n.node_id])
        else:
            # Parent is None OR Parent is deleted/missing
            roots.append(node_map[n.node_id])
            
    return roots

@app.get("/api/v1/nodes/{node_id}/messages", response_model=list[MessageResponse])
async def get_messages_endpoint(node_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    await get_node_by_id_or_404(session, node_id)
    msgs = await crud_get_messages(session, node_id)
    return [
        MessageResponse(
            message_id=m.message_id,
            node_id=m.node_id,
            role=m.role,
            content=m.content,
            timestamp=m.timestamp,
            token_count=m.token_count,
            metadata=m.metadata_
        )
        for m in msgs
    ]

@app.get("/api/v1/nodes/{node_id}/graph", response_model=GraphResponse)
async def get_graph_endpoint(node_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    await get_node_by_id_or_404(session, node_id)
    edges = await get_lineage_graph(session, node_id)
    
    entities = set()
    graph_edges = []
    
    for e in edges:
        entities.add(e["from_entity"])
        entities.add(e["to_entity"])
        graph_edges.append(GraphEdge(
            from_entity=e["from_entity"],
            to_entity=e["to_entity"],
            relation_type=e["relation_type"],
            confidence=e["confidence"],
            source_node=uuid.UUID(e["source_node"])
        ))
        
    return GraphResponse(
        node_id=node_id,
        entities=list(entities),
        relations=graph_edges
    )

# ========================
# PROJECT ENDPOINTS
# ========================

from models.db_models import Project
from sqlalchemy import select, func as sql_func

@app.post("/api/v1/projects", response_model=ProjectResponse)
async def create_project(request: CreateProjectRequest, session: AsyncSession = Depends(get_db)):
    project = Project(
        name=request.name,
        description=request.description
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    
    # Create root node for the project
    root_node_data = {
        "title": f"{project.name} Root",
        "project_id": project.project_id,
        "parent_id": None,
        "node_type": "standard",
        "position_x": 0.0,
        "position_y": 0.0,
        "status": "active"
    }
    root_node = await crud_create_node(session, root_node_data)
    await record_event(session, root_node.node_id, "NODE_CREATED", {
        "title": root_node.title,
        "parent_id": None,
        "project_id": str(project.project_id),
        "is_root": True
    })
    
    logger.info(f"Created project: {project.project_id} - {project.name} with root node: {root_node.node_id}")
    
    return ProjectResponse(
        project_id=project.project_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        node_count=1
    )

@app.get("/api/v1/projects", response_model=list[ProjectResponse])
async def list_projects(session: AsyncSession = Depends(get_db)):
    from models.db_models import Node
    
    # Get projects with node count
    result = await session.execute(
        select(
            Project,
            sql_func.count(Node.node_id).label("node_count")
        )
        .outerjoin(Node, Project.project_id == Node.project_id)
        .group_by(Project.project_id)
        .order_by(Project.created_at.desc())
    )
    
    projects = []
    for row in result:
        project = row[0]
        node_count = row[1]
        projects.append(ProjectResponse(
            project_id=project.project_id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            node_count=node_count
        ))
    
    return projects

@app.get("/api/v1/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    from models.db_models import Node
    
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Count nodes
    count_result = await session.execute(
        select(sql_func.count(Node.node_id)).where(Node.project_id == project_id)
    )
    node_count = count_result.scalar() or 0
    
    return ProjectResponse(
        project_id=project.project_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        node_count=node_count
    )

@app.put("/api/v1/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: uuid.UUID, request: UpdateProjectRequest, session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description
    
    await session.commit()
    await session.refresh(project)
    
    return ProjectResponse(
        project_id=project.project_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        node_count=len(project.nodes) if project.nodes else 0
    )

@app.delete("/api/v1/projects/{project_id}")
async def delete_project(project_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await session.delete(project)
    await session.commit()
    
    logger.info(f"Deleted project: {project_id}")
    
    return {"status": "deleted", "project_id": str(project_id)}

@app.get("/api/v1/projects/{project_id}/nodes/tree", response_model=list[TreeNodeResponse])
async def get_project_tree(project_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get nodes for this project
    nodes = await crud_get_tree(session, project_id=project_id)
    
    # Fetch summaries for all nodes
    node_summaries = {}
    for n in nodes:
        summary = await get_latest_summary(session, n.node_id)
        if summary:
            summary_json = summary.summary
            if isinstance(summary_json, dict):
                facts = summary_json.get("FACTS", [])
                if isinstance(facts, list) and facts:
                    node_summaries[n.node_id] = "; ".join(str(f) for f in facts[:3])
                else:
                    node_summaries[n.node_id] = str(summary_json.get("summary", ""))[:200]
    
    # Build tree in memory
    node_map = {}
    roots = []
    
    # Create responses first
    for n in nodes:
        summary_text = node_summaries.get(n.node_id)
        node_map[n.node_id] = TreeNodeResponse(
            node_id=n.node_id,
            title=n.title,
            status=n.status,
            node_type=n.node_type,
            has_summary=n.node_id in node_summaries,
            summary_text=summary_text,
            position={"x": n.position_x, "y": n.position_y},
            children=[]
        )
        
    # Link children to parents
    for n in nodes:
        if n.parent_id and n.parent_id in node_map:
            node_map[n.parent_id].children.append(node_map[n.node_id])
        else:
            roots.append(node_map[n.node_id])
            
    return roots

