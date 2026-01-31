# Agent Coding Prompt — The Fractal Workspace Backend (Phase 1)

---

## WHAT YOU ARE BUILDING

A FastAPI backend for a branching, node-based AI workspace. Each node is an isolated conversation with inherited context. Nodes have summaries, knowledge graphs, and event logs. All AI inference runs locally via Ollama on two physical machines. No cloud APIs. No OpenAI. No Anthropic SDK. Only `ollama` Python client.

---

## HARD CONSTRAINTS

1. **All LLM calls go through Ollama only.** Two model names: `main-reasoner` (Device A) and `graph-builder` (Device B). No other LLM client in the codebase.
2. **Two configurable Ollama URLs.** `OLLAMA_DEVICE_A_URL` and `OLLAMA_DEVICE_B_URL` in `.env`. Both default to `http://localhost:11434`. Code must work whether they point to the same machine or different machines.
3. **Knowledge graph is active from Day 1.** The `knowledge_graph` table is created in the initial migration. Graph extraction runs after every summarization. Chat context always includes the node's graph.
4. **User names every node.** `title` is required in `POST /nodes`. No AI-generated names. No naming model.
5. **Exploration node type is a dormant stub.** The DB schema includes `exploration` in the `node_type` constraint. The routing code has a path for it. That path logs a warning and falls back to `main-reasoner`. It must never crash or return a 500.
6. **Merge uses the same model as chat.** `main-reasoner` handles chat, summarize, and merge. Each has a completely different system prompt and context payload. The model name in the Ollama call is identical. The system prompt and messages are not.
7. **Event sourcing on every mutation.** Every create, message, summarize, merge, delete, copy action inserts into `node_events`. This is the audit trail and the future replay mechanism.
8. **Summarization and graph extraction are coupled.** When the user summarizes a node, the backend first saves the summary, then calls graph-builder. If graph-builder fails (Device B down), the summary is already saved. The response flags `graph_extraction_status: "failed"`. No data is lost.
9. **Immutable messages.** Messages are never updated or deleted. `ON DELETE CASCADE` on the foreign key is for DB cleanup only — application logic never deletes messages.
10. **Async everywhere.** FastAPI routes are `async def`. SQLAlchemy is configured for async. Ollama calls are awaited.

---

## PROJECT STRUCTURE

```
backend/
├── main.py
├── config.py
├── database.py
├── models/
│   ├── db_models.py
│   └── api_models.py
├── services/
│   ├── llm_service.py
│   ├── context_manager.py
│   ├── event_processor.py
│   └── graph_service.py
├── crud/
│   ├── nodes.py
│   ├── events.py
│   ├── messages.py
│   └── summaries.py
├── utils/
│   ├── helpers.py
│   └── constants.py
├── ollama/
│   ├── Modelfile.main-reasoner
│   └── Modelfile.graph-builder
├── requirements.txt
├── .env.example
└── tests/
    ├── test_nodes.py
    ├── test_llm.py
    ├── test_merge.py
    └── test_graph.py
```

---

## FILE-BY-FILE SPECIFICATIONS

---

### `.env.example`

```
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/fractal_workspace

# Ollama — Device A hosts the FastAPI app and main-reasoner
OLLAMA_DEVICE_A_URL=http://localhost:11434

# Ollama — Device B hosts graph-builder.
# For single-machine dev: keep same as DEVICE_A_URL.
# For two machines: set to http://<device_b_ip>:11434
OLLAMA_DEVICE_B_URL=http://localhost:11434

# Logging
LOG_LEVEL=INFO
```

---

### `requirements.txt`

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
pydantic>=2.0.0
ollama>=0.1.0
python-dotenv>=1.0.0
uuid>=1.30
```

No `openai`. No `anthropic`. No other LLM SDK.

---

### `config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    ollama_device_a_url: str = "http://localhost:11434"
    ollama_device_b_url: str = "http://localhost:11434"
    log_level: str = "INFO"

    # Model role → Ollama model name mapping.
    # These are the names created via `ollama create`.
    # Change the FROM line in the Modelfiles, not these strings.
    MODEL_MAIN_REASONER: str = "main-reasoner"
    MODEL_GRAPH_BUILDER: str = "graph-builder"

    # Context window limits (must match Modelfile num_ctx)
    CTX_MAIN_REASONER: int = 8192
    CTX_GRAPH_BUILDER: int = 4096

    # How many recent messages the chat agent sees
    CHAT_RECENT_MESSAGES: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
```

The routing map (role → URL) is derived here:

```python
# Device routing: which URL serves which model
DEVICE_URLS = {
    settings.MODEL_MAIN_REASONER: settings.ollama_device_a_url,
    settings.MODEL_GRAPH_BUILDER: settings.ollama_device_b_url,
}
```

---

### `database.py`

Standard async SQLAlchemy setup. Use `create_async_engine` with the `DATABASE_URL` from settings. Define `AsyncSessionLocal`. Provide an `async_session` dependency for FastAPI route injection. Include an `init_db()` function that runs `Base.metadata.create_all()` on startup.

---

### `models/db_models.py`

Five SQLAlchemy models mapping to the five tables. Use `uuid.uuid4` as default for primary keys. All timestamps default to `func.now()`.

**Node:**
- `node_id` (UUID, PK)
- `parent_id` (UUID, FK → nodes.node_id, nullable)
- `title` (String, NOT NULL)
- `node_type` (String, default `"standard"`, check constraint: `root`, `standard`, `exploration`)
- `status` (String, default `"active"`, check constraint: `active`, `frozen`, `deleted`)
- `position_x` (Float, default 0)
- `position_y` (Float, default 0)
- `created_at` (DateTime)
- `created_by` (String, nullable)
- `metadata` (JSON, default `{}`)

**NodeEvent:**
- `event_id` (UUID, PK)
- `node_id` (UUID, FK → nodes)
- `event_type` (String, NOT NULL, check constraint on valid event types)
- `payload` (JSON, NOT NULL)
- `timestamp` (DateTime)
- `user_id` (String, nullable)

Valid event types: `NODE_CREATED`, `MESSAGE_ADDED`, `NODE_MERGED`, `NODE_SPLIT`, `NODE_DELETED`, `NODE_COPIED`, `SUMMARY_UPDATED`, `GRAPH_UPDATED`

**Message:**
- `message_id` (UUID, PK)
- `node_id` (UUID, FK → nodes, cascade delete)
- `role` (String, check: `user`, `assistant`, `system`, `summary`)
- `content` (Text, NOT NULL)
- `timestamp` (DateTime)
- `token_count` (Integer, nullable)
- `metadata` (JSON, default `{}`)

**NodeSummary:**
- `summary_id` (UUID, PK)
- `node_id` (UUID, FK → nodes)
- `summary` (JSON, NOT NULL)
- `generated_from_event` (UUID, FK → node_events, nullable)
- `created_at` (DateTime)
- `is_latest` (Boolean, default True)

**KnowledgeGraph:**
- `edge_id` (UUID, PK)
- `from_entity` (String, NOT NULL)
- `to_entity` (String, NOT NULL)
- `relation_type` (String, NOT NULL)
- `source_node` (UUID, FK → nodes)
- `confidence` (Float, default 1.0)
- `metadata` (JSON, default `{}`)
- `created_at` (DateTime)
- `deleted_at` (DateTime, nullable)
- Unique constraint on `(from_entity, to_entity, relation_type, source_node)`

Add appropriate indexes as specified in the schema.

---

### `models/api_models.py`

Pydantic models for every request and response.

**Requests:**
- `CreateNodeRequest`: `parent_id` (optional UUID), `title` (str, required, min 1 char, max 200), `node_type` (str, default `"standard"`, enum `standard`/`exploration` — root is system-only)
- `SendMessageRequest`: `content` (str, required)
- `MergeRequest`: `source_node_id` (UUID), `target_node_id` (UUID)
- `DeleteRequest`: `cascade` (bool, default False)
- `CopyRequest`: `new_parent_id` (optional UUID)

**Responses:**
- `NodeResponse`: all node fields + `position` as `{"x": float, "y": float}`
- `MessageResponse`: message fields + `agent_used` (str) + `fallback_from` (optional str)
- `SummarizeResponse`: `summary_id`, `node_id`, `summary` (dict), `graph_extraction_status` (str: `"success"` or `"failed"`), `knowledge_graph` (optional dict with counts), `graph_extraction_error` (optional str)
- `MergeResponse`: `target_node_id`, `source_node_id`, `updated_summary`, `conflicts` (list), `knowledge_graph_updates` (dict), `source_node_status`
- `DeleteResponse`: `node_id`, `status`, `affected_descendants` (list), `recomputed` (bool), `graph_edges_removed` (int)
- `TreeNodeResponse`: recursive structure with `node_id`, `title`, `status`, `node_type`, `message_count`, `has_summary`, `children` (list of same type)
- `GraphResponse`: `node_id`, `entities` (list), `relations` (list)

---

### `utils/constants.py`

All system prompts live here as string constants. Do not inline prompts in service files.

```python
CHAT_SYSTEM_PROMPT = """You are an AI assistant helping with project exploration in a branching conversation system.

CONTEXT HIERARCHY:
1. Inherited Context (compressed ancestor summaries): {inherited_summary}
2. Current Node Summary: {node_summary}
3. Current Node Knowledge Graph: {node_graph}
4. Recent Conversation: {last_n_messages}

GUIDELINES:
- Build on established decisions and facts
- Flag conflicts with inherited context if found
- Suggest creating a new branch when exploring alternatives
- Reference knowledge graph entities when relevant
- Maintain awareness of open questions

CURRENT NODE: {node_title}
NODE TYPE: {node_type}"""

SUMMARIZER_SYSTEM_PROMPT = """You are a semantic compression engine. Extract ONLY essential information.

INPUT:
- Parent Context: {parent_summary}
- Conversation Messages: {all_messages}
- Existing Knowledge Graph: {existing_graph}

Extract and structure into valid JSON:
1. FACTS: [ { "fact", "source_node", "confidence", "timestamp" } ]
2. DECISIONS: [ { "decision", "source_node", "rationale", "confidence" } ]
3. OPEN QUESTIONS: [ "..." ]
4. METADATA: { "total_messages", "token_count", "generated_by": "main-reasoner", "key_topics" }

EXCLUDE: chitchat, abandoned ideas, redundant statements, off-topic.
OUTPUT: Valid JSON only. No explanation. No markdown."""

GRAPH_BUILDER_SYSTEM_PROMPT = """You are a knowledge graph extraction engine.

INPUT:
- Current Node Summary: {node_summary}
- Current Node Existing Graph: {current_graph}
- Parent Graph: {parent_graph}

ENTITY TYPES: concept, decision, person, technology, dataset
RELATION TYPES: USES, ALTERNATIVE_TO, REQUIRES, INFLUENCES, PART_OF, FINALIZED_AS

RULES:
- Extract 3-10 entities
- Meaningful relations only
- Do NOT duplicate edges already in current_graph
- Include confidence scores

OUTPUT: Valid JSON only. No explanation. No markdown.
{ "entities": [...], "relations": [...] }"""

MERGE_SYSTEM_PROMPT = """You are merging a branch's findings into the main thread.

STRICT RULES:
1. NEVER delete confirmed decisions from target
2. Prefer specific over vague
3. Flag conflicts — do NOT auto-resolve
4. Maintain all source_node IDs
5. Combine compatible facts. Flag contradictions.

INPUT:
- Target Summary: {target_summary}
- Target Graph: {target_graph}
- Source Summary: {source_summary}
- Source Graph: {source_graph}
- Source Recent Chats: {source_recent_chats}

CONFLICT TYPES: decision conflicts, contradicting facts, incompatible assumptions.

OUTPUT: Valid JSON only.
{ "updated_target_summary": {...}, "conflicts": [...] }"""
```

---

### `utils/helpers.py`

Utility functions:
- `estimate_token_count(text: str) -> int` — approximate token count (split on whitespace, multiply by 1.3 is a reasonable heuristic for non-BPE estimation)
- `format_summary(summary: dict) -> str` — convert summary JSON to a readable string for prompt injection
- `format_graph(edges: list) -> str` — convert graph edges to a readable string like `"Entity A --[USES]--> Entity B (conf: 0.9)"`
- `format_messages(messages: list) -> str` — convert message list to `"[user]: ...\n[assistant]: ...\n"` format
- `extract_key_points(summary: dict) -> str` — from a summary dict, extract only facts and decisions as a short compressed string (for lineage compression)

---

### `crud/nodes.py`

Async CRUD functions using SQLAlchemy:
- `create_node(session, node_data) -> Node`
- `get_node(session, node_id) -> Node | None`
- `get_node_by_id_or_404(session, node_id) -> Node` — raises HTTPException 404
- `update_node_status(session, node_id, status)`
- `get_node_lineage(session, node_id) -> list[Node]` — returns `[current, parent, grandparent, ..., root]` by walking `parent_id` chain
- `get_all_descendants(session, node_id) -> list[Node]` — recursive query for all children
- `get_tree(session) -> list[Node]` — all non-deleted nodes, structured for tree response
- `calculate_position(session, parent_id) -> tuple[float, float]` — simple grid layout below parent

---

### `crud/events.py`

- `insert_event(session, node_id, event_type, payload, user_id=None) -> NodeEvent`

That is the only function needed. Every service calls this after every mutation.

---

### `crud/messages.py`

- `create_message(session, node_id, role, content, token_count=None, metadata=None) -> Message`
- `get_messages(session, node_id, limit=None) -> list[Message]` — ordered by timestamp ASC
- `get_last_n_messages(session, node_id, n: int) -> list[Message]` — ordered by timestamp DESC, limit n, then reverse for chronological order

---

### `crud/summaries.py`

- `create_summary(session, node_id, summary_json, generated_from_event=None) -> NodeSummary`
  - Before inserting, set `is_latest = False` on all existing summaries for this node
- `get_latest_summary(session, node_id) -> NodeSummary | None`

---

### `services/llm_service.py`

This is the single entry point for all Ollama calls. It knows about two models and two device URLs. It does not know about prompts (those come from `constants.py` via `context_manager.py`).

```python
import ollama
from config import settings, DEVICE_URLS

class LLMService:
    def _get_client(self, model_name: str) -> ollama.Client:
        """Return an Ollama client pointed at the correct device URL for this model."""
        url = DEVICE_URLS.get(model_name, settings.ollama_device_a_url)
        return ollama.Client(host=url)

    async def call(self, model_name: str, system_prompt: str, user_content: str) -> str:
        """
        Generic Ollama call. All agents go through here.
        model_name: "main-reasoner" or "graph-builder"
        Returns the text content of the response.
        """
        client = self._get_client(model_name)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        # ollama.Client.chat is synchronous — run in executor for async compatibility
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat(model=model_name, messages=messages)
        )
        return response["message"]["content"]

    async def chat(self, system_prompt: str, user_content: str) -> str:
        return await self.call(settings.MODEL_MAIN_REASONER, system_prompt, user_content)

    async def summarize(self, system_prompt: str, user_content: str) -> str:
        return await self.call(settings.MODEL_MAIN_REASONER, system_prompt, user_content)

    async def merge(self, system_prompt: str, user_content: str) -> str:
        return await self.call(settings.MODEL_MAIN_REASONER, system_prompt, user_content)

    async def extract_graph(self, system_prompt: str, user_content: str) -> str:
        """Calls graph-builder on Device B. Caller must catch exceptions."""
        return await self.call(settings.MODEL_GRAPH_BUILDER, system_prompt, user_content)

    async def exploration_chat(self, system_prompt: str, user_content: str) -> tuple[str, str | None]:
        """
        Exploration stub. Attempts exploration model. Falls back to main-reasoner.
        Returns (response_text, fallback_from).
        fallback_from is None if exploration worked, "exploration" if it fell back.
        """
        try:
            # Future: call a 3B exploration model on Device B
            # For now, this always falls back.
            raise NotImplementedError("Exploration model not yet configured")
        except Exception:
            import logging
            logging.warning("Exploration model not configured or unreachable. Falling back to main-reasoner.")
            response = await self.chat(system_prompt, user_content)
            return response, "exploration"

llm_service = LLMService()
```

---

### `services/context_manager.py`

Builds the prompt payload for each agent type. Does not call Ollama — just assembles strings.

```python
from crud.nodes import get_node_lineage, get_node
from crud.messages import get_last_n_messages, get_messages
from crud.summaries import get_latest_summary
from crud.graph import get_node_graph, get_parent_graph
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
        for ancestor in reversed(lineage[1:]):
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
            node_title=node.title,
            node_type=node.node_type
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
```

---

### `services/graph_service.py`

Handles knowledge graph storage and retrieval. Called by the summarize endpoint after graph-builder returns.

```python
# Functions:
async def store_graph_edges(session, node_id, entities, relations) -> int:
    """
    Parse graph-builder output. Insert edges into knowledge_graph.
    Skip edges that already exist (unique constraint).
    Returns count of new edges inserted.
    """

async def get_node_graph(session, node_id) -> list[dict]:
    """All non-deleted edges where source_node = node_id."""

async def get_lineage_graph(session, node_id) -> list[dict]:
    """All non-deleted edges where source_node is in the node's lineage.
    This is what the chat agent sees."""

async def get_parent_graph(session, node_id) -> list[dict]:
    """Graph of the parent node only. Used by graph-builder context."""

async def merge_graphs(session, source_id, target_id):
    """
    After a merge: mark source edges with merged_into metadata.
    Do not duplicate — if an edge already exists on target, update confidence.
    """

async def soft_delete_edges(session, node_id):
    """SET deleted_at = NOW() on all edges where source_node = node_id."""
```

---

### `services/event_processor.py`

Thin wrapper. Every route calls this after a mutation:

```python
async def record_event(session, node_id: str, event_type: str, payload: dict, user_id: str = None):
    await insert_event(session, node_id, event_type, payload, user_id)
```

This exists as a single place to add future logic (e.g., trigger async jobs in Phase 3).

---

### `main.py`

FastAPI app. Register routes. Run `init_db()` on startup.

Routes to implement:

```
POST   /api/v1/nodes                        → create_node
POST   /api/v1/nodes/{node_id}/messages     → send_message
POST   /api/v1/nodes/{node_id}/summarize    → summarize_node
POST   /api/v1/nodes/merge                  → merge_nodes
POST   /api/v1/nodes/{node_id}/delete       → delete_node
POST   /api/v1/nodes/{node_id}/copy         → copy_node
GET    /api/v1/nodes/tree                   → get_tree
GET    /api/v1/nodes/{node_id}/messages     → get_messages
GET    /api/v1/nodes/{node_id}/graph        → get_graph
```

Each route handler:
1. Gets a DB session via dependency injection
2. Validates input (Pydantic handles this automatically from request body)
3. Performs business logic (calls CRUD + services)
4. Records event
5. Returns response model

---

### Route Implementation Details

#### `create_node`
- Validate `title` is present
- If `parent_id` is provided, verify parent exists and is not deleted
- Create node row
- Record `NODE_CREATED` event
- Return `NodeResponse`

#### `send_message`
- Verify node exists and is `active`
- Create user message row
- Record `MESSAGE_ADDED` event
- Build chat context via `context_manager.build_chat_context()`
- Route based on `node_type`:
  - If `exploration`: call `llm_service.exploration_chat()` — get `(response, fallback_from)`
  - Else: call `llm_service.chat()` — `fallback_from = None`
- Create assistant message row
- Record `MESSAGE_ADDED` event
- Return `MessageResponse` with `agent_used` and `fallback_from`

#### `summarize_node`
- Verify node exists and is `active`
- Build summarize context via `context_manager.build_summarize_context()`
- Call `llm_service.summarize()`
- Parse JSON response into summary dict. If JSON parsing fails, return 500 with error detail.
- Store summary via `crud.summaries.create_summary()`
- Record `SUMMARY_UPDATED` event
- **Graph extraction (always runs, catches failure):**
  ```python
  graph_status = "success"
  graph_error = None
  graph_counts = None
  try:
      graph_ctx = await context_manager.build_graph_context(session, node_id, summary_dict)
      graph_response = await llm_service.extract_graph(graph_ctx["system_prompt"], graph_ctx["user_content"])
      graph_data = json.loads(graph_response)
      count = await graph_service.store_graph_edges(session, node_id, graph_data["entities"], graph_data["relations"])
      await record_event(session, node_id, "GRAPH_UPDATED", {"entities_added": ..., "relations_added": count})
      graph_counts = {"entities_added": len(graph_data["entities"]), "relations_added": count}
  except Exception as e:
      graph_status = "failed"
      graph_error = f"Graph extraction failed: {str(e)}. Re-run summarize to retry."
      logging.error(f"Graph extraction failed for node {node_id}: {e}")
  ```
- Return `SummarizeResponse`

#### `merge_nodes`
- Validate both nodes exist
- Validate source is a descendant of target (walk lineage from source, check if target is in it)
- Record `NODE_MERGED` event
- Build merge context via `context_manager.build_merge_context()`
- Call `llm_service.merge()`
- Parse JSON response: `updated_target_summary` and `conflicts`
- Store new summary for target
- Record `SUMMARY_UPDATED` event on target
- Call `graph_service.merge_graphs(source_id, target_id)`
- Update source node status to `frozen`
- Insert a message into target with `role = "summary"`:
  - Content: `"Merged from [source_title]: [brief summary of key points from the merge]"`
- Return `MergeResponse`

#### `delete_node`
- Validate node exists
- Record `NODE_DELETED` event
- Update status to `deleted`
- Call `graph_service.soft_delete_edges(node_id)`
- Count removed edges
- Return `DeleteResponse` with `recomputed: false`

#### `copy_node`
- Validate original exists
- If `new_parent_id`, validate it exists
- Create new node with title = `"{original_title} (Copy)"`
- Copy latest summary reference
- Record `NODE_COPIED` event
- Return `NodeResponse`

#### `get_tree`
- Query all non-deleted nodes
- Build recursive tree structure in Python
- Return root(s) as `TreeNodeResponse`

#### `get_messages`
- Verify node exists
- Return all messages ordered by timestamp ASC

#### `get_graph`
- Verify node exists
- Call `graph_service.get_lineage_graph()` (includes ancestor edges)
- Format into entities and relations lists
- Return `GraphResponse`

---

### `ollama/Modelfile.main-reasoner`

```
FROM llama3:8b

PARAMETER num_ctx 8192
PARAMETER num_gpu 999
PARAMETER temperature 0.7
```

### `ollama/Modelfile.graph-builder`

```
FROM llama3:8b

PARAMETER num_ctx 4096
PARAMETER num_gpu 999
PARAMETER temperature 0.2
```

---

### Tests

Write tests for:
- `test_nodes.py`: create, get, tree, delete, copy. Verify event insertion on each.
- `test_llm.py`: Mock `ollama.Client`. Verify routing goes to correct URL per model. Verify exploration fallback logs warning and returns response.
- `test_merge.py`: Verify merge context assembly. Verify source is frozen after merge. Verify summary message is inserted.
- `test_graph.py`: Verify graph edges are stored after summarize. Verify soft delete works. Verify lineage graph query returns ancestor edges.

Use `pytest` with `pytest-asyncio`. Mock the database session and Ollama client. Do not hit real Ollama or a real database in unit tests.

---

## WHAT TO DO IF SOMETHING IS AMBIGUOUS

If you are unsure about a detail not covered above, follow these priorities in order:
1. The hard constraints at the top of this prompt
2. The context construction rules (Main Chat sees X, Graph Builder sees Y)
3. The principle: summary is always saved before graph extraction is attempted
4. The principle: exploration never crashes, always falls back
5. Keep it simple — Phase 1 only. Do not build Phase 2/3/4 features.

---

## COMPLETION CRITERIA

The agent is done when every file in the project structure exists, compiles without errors, and the following flow works end-to-end (assuming Ollama is running with the correct models):

```
1. POST /nodes         → node created, event logged
2. POST /nodes/{id}/messages → message stored, Ollama called, response stored, event logged
3. POST /nodes/{id}/summarize → summary stored, graph extraction attempted, events logged
4. POST /nodes/merge   → merge called, summary updated, graphs merged, source frozen, summary message inserted
5. POST /nodes/{id}/delete → node marked deleted, edges soft-deleted, event logged
6. GET /nodes/tree     → returns correct tree excluding deleted nodes
7. GET /nodes/{id}/graph → returns lineage graph edges
```
