from crud.nodes import get_node_lineage, get_node
from crud.messages import get_last_n_messages, get_messages
from crud.summaries import get_latest_summary
# Imported from services.graph_service instead of crud.graph as per structure
from services.graph_service import get_node_graph, get_parent_graph
from utils.constants import (CHAT_SYSTEM_PROMPT, SUMMARIZER_SYSTEM_PROMPT,
                              GRAPH_BUILDER_SYSTEM_PROMPT, MERGE_SYSTEM_PROMPT)
from utils.helpers import format_summary, format_graph, format_messages, extract_key_points
from config import settings

class ContextManager:

    async def build_chat_context(self, session, node_id: str) -> dict:
        """Returns {"system_prompt": str, "user_content": str} for chat agent."""
        node = await get_node(session, node_id)
        lineage = await get_node_lineage(session, node_id)

        # Compress ancestor summaries (root → parent, progressive)
        inherited_summary = ""
        for ancestor in reversed(lineage[1:]): # lineage[0] is current
            summary = await get_latest_summary(session, ancestor.node_id)
            if summary:
                inherited_summary += extract_key_points(summary.summary) + "\n"

        node_summary = await get_latest_summary(session, node_id)
        node_graph = await get_node_graph(session, node_id)
        recent = await get_last_n_messages(session, node_id, n=settings.CHAT_RECENT_MESSAGES)

        system_prompt = CHAT_SYSTEM_PROMPT.format(
            inherited_summary=inherited_summary or "No ancestor context yet.",
            node_summary=format_summary(node_summary.summary) if node_summary else "No summary yet.",
            node_graph=format_graph(node_graph) if node_graph else "No graph yet.",
            last_n_messages=format_messages(recent),
            node_title=node.title if node else "Unknown",
            node_type=node.node_type if node else "standard"
        )
        # user_content is empty string — all context is in system prompt
        return {"system_prompt": system_prompt, "user_content": ""}

    async def build_summarize_context(self, session, node_id: str) -> dict:
        """Returns context for summarizer agent."""
        lineage = await get_node_lineage(session, node_id)
        parent_summary = ""
        if len(lineage) > 1:
            ps = await get_latest_summary(session, lineage[1].node_id)
            if ps:
                parent_summary = format_summary(ps.summary)

        all_messages = await get_messages(session, node_id)
        existing_graph = await get_node_graph(session, node_id)

        system_prompt = SUMMARIZER_SYSTEM_PROMPT.format(
            parent_summary=parent_summary or "No parent context.",
            all_messages=format_messages(all_messages),
            existing_graph=format_graph(existing_graph) if existing_graph else "No existing graph."
        )
        return {"system_prompt": system_prompt, "user_content": ""}

    async def build_graph_context(self, session, node_id: str, new_summary: dict) -> dict:
        """Returns context for graph-builder agent."""
        current_graph = await get_node_graph(session, node_id)
        parent_graph = await get_parent_graph(session, node_id)

        system_prompt = GRAPH_BUILDER_SYSTEM_PROMPT.format(
            node_summary=format_summary(new_summary),
            current_graph=format_graph(current_graph) if current_graph else "No existing graph.",
            parent_graph=format_graph(parent_graph) if parent_graph else "No parent graph."
        )
        return {"system_prompt": system_prompt, "user_content": ""}

    async def build_merge_context(self, session, source_id: str, target_id: str) -> dict:
        """Returns context for merge arbiter agent."""
        target_summary = await get_latest_summary(session, target_id)
        target_graph = await get_node_graph(session, target_id)
        source_summary = await get_latest_summary(session, source_id)
        source_graph = await get_node_graph(session, source_id)
        source_recent = await get_last_n_messages(session, source_id, n=settings.CHAT_RECENT_MESSAGES)

        system_prompt = MERGE_SYSTEM_PROMPT.format(
            target_summary=format_summary(target_summary.summary) if target_summary else "No target summary.",
            target_graph=format_graph(target_graph) if target_graph else "No target graph.",
            source_summary=format_summary(source_summary.summary) if source_summary else "No source summary.",
            source_graph=format_graph(source_graph) if source_graph else "No source graph.",
            source_recent_chats=format_messages(source_recent) if source_recent else "No recent chats."
        )
        return {"system_prompt": system_prompt, "user_content": ""}

context_manager = ContextManager()
