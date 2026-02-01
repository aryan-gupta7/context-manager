from crud.nodes import get_node_lineage, get_node
from crud.messages import get_last_n_messages, get_messages
from crud.summaries import get_latest_summary
# Imported from services.graph_service instead of crud.graph as per structure
from services.graph_service import get_node_graph, get_parent_graph
from utils.constants import (CHAT_SYSTEM_PROMPT, SUMMARIZER_SYSTEM_PROMPT,
                              GRAPH_BUILDER_SYSTEM_PROMPT, MERGE_SYSTEM_PROMPT)
from utils.helpers import format_summary, format_graph, format_messages, extract_key_points
from config import settings
import json

class ContextManager:

    async def snapshot_parent_context(self, session, parent_id: str) -> dict:
        """
        Create a frozen snapshot of parent's essential context.
        This is stored on the child node at creation time to ensure
        important details are never lost across branches.
        
        Returns a dict with:
        - facts: List of key facts from parent and ancestors
        - decisions: List of confirmed decisions
        - key_entities: Important entities from knowledge graph
        - open_questions: Unresolved questions
        - lineage_depth: How many ancestors contributed
        """
        if not parent_id:
            return None
            
        parent = await get_node(session, parent_id)
        if not parent:
            return None
            
        # Walk the full lineage to gather cumulative context
        lineage = await get_node_lineage(session, parent_id)
        
        all_facts = []
        all_decisions = []
        all_questions = []
        key_entities = set()
        
        for i, ancestor in enumerate(lineage):
            summary = await get_latest_summary(session, ancestor.node_id)
            if summary and isinstance(summary.summary, dict):
                s = summary.summary
                # Extract facts with source tracking
                if "FACTS" in s and isinstance(s["FACTS"], list):
                    for fact in s["FACTS"]:
                        if isinstance(fact, dict):
                            fact_copy = fact.copy()
                            fact_copy["lineage_depth"] = i
                            fact_copy["source_node_id"] = str(ancestor.node_id)
                            all_facts.append(fact_copy)
                        else:
                            all_facts.append({
                                "fact": str(fact),
                                "lineage_depth": i,
                                "source_node_id": str(ancestor.node_id)
                            })
                
                # Extract decisions
                if "DECISIONS" in s and isinstance(s["DECISIONS"], list):
                    for dec in s["DECISIONS"]:
                        if isinstance(dec, dict):
                            dec_copy = dec.copy()
                            dec_copy["lineage_depth"] = i
                            dec_copy["source_node_id"] = str(ancestor.node_id)
                            all_decisions.append(dec_copy)
                        else:
                            all_decisions.append({
                                "decision": str(dec),
                                "lineage_depth": i,
                                "source_node_id": str(ancestor.node_id)
                            })
                
                # Extract open questions
                if "OPEN QUESTIONS" in s and isinstance(s["OPEN QUESTIONS"], list):
                    all_questions.extend(s["OPEN QUESTIONS"])
            
            # Get key entities from knowledge graph
            graph_edges = await get_node_graph(session, ancestor.node_id)
            if graph_edges:
                for edge in graph_edges:
                    key_entities.add(edge.get("from_entity", ""))
                    key_entities.add(edge.get("to_entity", ""))
        
        # CRITICAL: If no summaries exist, extract context from raw messages
        # This ensures context transfer works even without explicit summarization
        conversation_context = []
        if not all_facts and not all_decisions:
            for i, ancestor in enumerate(lineage):
                messages = await get_messages(session, ancestor.node_id)
                if messages:
                    # Extract meaningful content from messages (limit to avoid token explosion)
                    for msg in messages[-10:]:  # Last 10 messages per node
                        if msg.role in ("user", "assistant") and msg.content:
                            # Truncate long messages
                            content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                            conversation_context.append({
                                "role": msg.role,
                                "content": content,
                                "source_node_id": str(ancestor.node_id),
                                "source_node_title": ancestor.title,
                                "lineage_depth": i
                            })
        
        # Build the frozen snapshot
        snapshot = {
            "facts": all_facts,
            "decisions": all_decisions,
            "open_questions": list(set(all_questions)),  # Dedupe
            "key_entities": list(key_entities - {""}),  # Remove empty strings
            "conversation_history": conversation_context,  # Raw messages when no summaries
            "lineage_depth": len(lineage),
            "parent_title": parent.title,
            "parent_node_id": str(parent_id)
        }
        
        return snapshot

    async def build_chat_context(self, session, node_id: str) -> dict:
        """Returns {"system_prompt": str, "user_content": str} for chat agent."""
        node = await get_node(session, node_id)
        lineage = await get_node_lineage(session, node_id)

        # PRIORITY 1: Use stored inherited_context if available (frozen snapshot)
        inherited_summary = ""
        if node and node.inherited_context:
            ctx = node.inherited_context
            # Format the frozen context
            if ctx.get("facts"):
                inherited_summary += "=== INHERITED FACTS ===\n"
                for fact in ctx["facts"]:
                    f = fact.get("fact", str(fact)) if isinstance(fact, dict) else str(fact)
                    inherited_summary += f"- {f}\n"
            
            if ctx.get("decisions"):
                inherited_summary += "\n=== CONFIRMED DECISIONS ===\n"
                for dec in ctx["decisions"]:
                    d = dec.get("decision", str(dec)) if isinstance(dec, dict) else str(dec)
                    inherited_summary += f"- [DECISION] {d}\n"
            
            if ctx.get("key_entities"):
                inherited_summary += f"\n=== KEY ENTITIES ===\n{', '.join(ctx['key_entities'][:20])}\n"
            
            if ctx.get("open_questions"):
                inherited_summary += "\n=== OPEN QUESTIONS ===\n"
                for q in ctx["open_questions"][:5]:
                    inherited_summary += f"- {q}\n"
            
            # CRITICAL: If no structured data, use conversation history
            if ctx.get("conversation_history") and not ctx.get("facts") and not ctx.get("decisions"):
                inherited_summary += "\n=== PREVIOUS CONVERSATION (from parent branch) ===\n"
                parent_title = ctx.get("parent_title", "Parent")
                inherited_summary += f"Context from: {parent_title}\n\n"
                for msg in ctx["conversation_history"]:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    inherited_summary += f"[{role}]: {content}\n\n"
        else:
            # FALLBACK: Dynamic lineage traversal (for older nodes without snapshot)
            has_any_context = False
            for ancestor in reversed(lineage[1:]):  # lineage[0] is current
                summary = await get_latest_summary(session, ancestor.node_id)
                if summary:
                    inherited_summary += extract_key_points(summary.summary) + "\n"
                    has_any_context = True
            
            # CRITICAL FALLBACK: If still no context, get raw messages from parent
            if not has_any_context and len(lineage) > 1:
                parent = lineage[1]
                parent_messages = await get_messages(session, parent.node_id)
                if parent_messages:
                    inherited_summary += f"\n=== PREVIOUS CONVERSATION (from {parent.title}) ===\n"
                    for msg in parent_messages[-10:]:  # Last 10 messages
                        if msg.role in ("user", "assistant"):
                            content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                            inherited_summary += f"[{msg.role}]: {content}\n\n"

        node_summary = await get_latest_summary(session, node_id)
        node_graph = await get_node_graph(session, node_id)
        recent = await get_last_n_messages(session, node_id, n=settings.CHAT_RECENT_MESSAGES)

        system_prompt = CHAT_SYSTEM_PROMPT.format(
            inherited_summary=inherited_summary or "(This is the root of the conversation tree - no parent context exists yet)",
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
