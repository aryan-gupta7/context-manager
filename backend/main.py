from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, init_db
from models.api_models import (
    CreateNodeRequest, NodeResponse,
    SendMessageRequest, MessageResponse,
    SummarizeResponse,
    MergeRequest, MergeResponse,
    DeleteRequest, DeleteResponse,
    CopyRequest,
    TreeNodeResponse, GraphResponse, GraphEdge
)
from crud.nodes import create_node as crud_create_node, get_node_by_id_or_404, get_tree as crud_get_tree, update_node_status, calculate_position, get_node_lineage
from crud.messages import create_message, get_messages as crud_get_messages
from crud.summaries import create_summary
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
        "parent_id": request.parent_id,
        "node_type": request.node_type,
        "position_x": pos_x,
        "position_y": pos_y,
        "status": "active"
    }
    
    node = await crud_create_node(session, node_data)
    await record_event(session, node.node_id, "NODE_CREATED", {
        "title": node.title,
        "parent_id": str(node.parent_id) if node.parent_id else None
    })
    
    return NodeResponse(
        node_id=node.node_id,
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
    
    # Build tree in memory
    node_map = {}
    roots = []
    
    # Create responses first
    for n in nodes:
        node_map[n.node_id] = TreeNodeResponse(
            node_id=n.node_id,
            title=n.title,
            status=n.status,
            node_type=n.node_type,
            has_summary=False, # Optimisation needed
            children=[]
        )
        
    # Link
    for n in nodes:
        if n.parent_id and n.parent_id in node_map:
            node_map[n.parent_id].children.append(node_map[n.node_id])
        elif not n.parent_id:
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
