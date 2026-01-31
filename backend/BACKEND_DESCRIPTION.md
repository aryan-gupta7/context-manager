# The Fractal Workspace - Complete Backend Description
## Enhanced Architecture with Knowledge Graph & Multi-Agent AI System

---

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Core Philosophy](#2-core-philosophy)
3. [AI Architecture - Multi-Agent System](#3-ai-architecture)
4. [Database Design](#4-database-design)
5. [API Endpoints](#5-api-endpoints)
6. [LLM Pipeline & Prompts](#6-llm-pipeline)
7. [Knowledge Graph Integration](#7-knowledge-graph)
8. [Event-Sourcing & Deletion](#8-event-sourcing)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Team Responsibilities](#10-team-responsibilities)

---

## 1. System Overview

### What You're Actually Building

```
Traditional Chat App:
┌────────────┐
│  Messages  │ → LLM → Response
└────────────┘

The Fractal Workspace:
┌─────────────────────────────────────────────────────┐
│  Multi-Agent Cognitive Pipeline                     │
│                                                     │
│  Event Stream → Context Assembly → AI Routing →    │
│  → Knowledge Graph Update → Summary Generation →   │
│  → State Propagation                               │
└─────────────────────────────────────────────────────┘
```

**You're not building a chat API. You're building:**
- A DAG (Directed Acyclic Graph) of semantic states
- An event-sourced cognitive state manager
- A multi-agent AI orchestration system
- A persistent knowledge graph with temporal versioning

---

## 2. Core Philosophy

### 2.1 Events Are Truth, State Is Derived

```
❌ Traditional: Store current state, lose history
✅ Event-Sourced: Store all events, compute state

When user deletes Node A:
Traditional: UPDATE nodes SET deleted=true → Lost forever
Event-Sourced: INSERT event('NODE_DELETED') → Can replay, recompute
```

### 2.2 Bounded Cognitive Universes

```
Each Node = Isolated thought space with:
- Inherited context (from ancestors)
- Local conversation (messages)
- Derived summary (compressed semantics)
- Knowledge graph delta (structured insights)

Parent context ≠ Copied into child
Parent context = Compressed and referenced
```

### 2.3 Multiple AI Agents, Not One Model

```
❌ One LLM doing everything:
   "You are a helpful assistant. Also compress this. Also extract graph. Also..."
   Result: Role confusion, poor quality

✅ Specialized agents:
   Agent 1: Deep conversation (Claude Sonnet)
   Agent 2: Quick exploration (Llama 3.2)
   Agent 3: Summarization (GPT-4o-mini)
   Agent 4: Graph extraction (GPT-4o with JSON mode)
   Result: Each does one thing well
```

---

## 3. AI Architecture - Multi-Agent System

### 3.1 AI Agent Roles

| Agent | Purpose | When Triggered | Input | Output | Model Choice |
|-------|---------|---------------|-------|--------|--------------|
| **Main Chat** | Deep reasoning, long discussions | User sends message in node | System prompt + Inherited summary + Node summary + Last 10 messages | AI response text | Claude Sonnet 3.5 / GPT-4 |
| **Lightweight Node** | Quick idea exploration, disposable reasoning | User creates "exploration" node | Local node context only | AI response text | Llama 3.2 3B (local) |
| **Summarizer** | Compress conversation into semantic state | Manual trigger / After merge / Auto (future) | Parent summary + All node messages | Summary JSON with source tracking | GPT-4o-mini |
| **Knowledge Graph Builder** | Extract structured knowledge | After summarization | Node summary JSON | Graph entities + relations | GPT-4 with JSON mode |
| **Merge Arbiter** | Intelligently merge branches | User merges nodes | Target summary + Source summary | Updated target summary + conflicts | Claude Sonnet 3.5 |

### 3.2 Why This Architecture?

**Problem:** Using one model for everything causes:
- **Role contamination:** Summarizer starts chatting, chat model starts compressing
- **Context pollution:** Model doesn't know what "mode" it's in
- **Quality degradation:** Jack of all trades, master of none

**Solution:** Dedicated agents with:
- Separate system prompts (different "personalities")
- Different context windows (summarizer sees full history, chat sees compressed)
- Different models (expensive for quality, cheap for speed)

### 3.3 Context Flow

```
┌─────────────────────────────────────────────────┐
│  CONTEXT ASSEMBLY (Before any LLM call)        │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. Get Node Lineage (child → parent → root)   │
│  2. Collect Ancestor Summaries (compress)      │
│  3. Get Current Node Summary                   │
│  4. Get Knowledge Graph Context (optional)     │
│  5. Get Last N Messages                        │
│  6. Assemble into final context                │
│                                                 │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  AGENT ROUTING (Which agent should respond?)   │
├─────────────────────────────────────────────────┤
│                                                 │
│  IF node.type == "exploration" → Lightweight   │
│  IF action == "chat" → Main Chat              │
│  IF action == "summarize" → Summarizer        │
│  IF action == "merge" → Merge Arbiter         │
│  IF action == "extract_graph" → Graph Builder │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 4. Database Design

### 4.1 Core Principle: Event-Sourced

Every action = An immutable event in the database.  
Current state = Derived by replaying events.

### 4.2 Schema

#### Table 1: `nodes` (Existence)

```sql
CREATE TABLE nodes (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID REFERENCES nodes(node_id),
    title TEXT NOT NULL,
    node_type TEXT DEFAULT 'standard' CHECK (node_type IN ('root', 'standard', 'exploration')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'frozen', 'deleted')),
    position_x FLOAT DEFAULT 0,
    position_y FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_nodes_parent ON nodes(parent_id);
CREATE INDEX idx_nodes_status ON nodes(status);
```

**Key Points:**
- No `summary` column → Summaries are derived state
- `node_type` distinguishes heavyweight (standard) vs lightweight (exploration) nodes
- `metadata` for future extensibility

#### Table 2: `node_events` (SOURCE OF TRUTH)

```sql
CREATE TABLE node_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id UUID REFERENCES nodes(node_id),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'NODE_CREATED',
        'MESSAGE_ADDED',
        'NODE_MERGED',
        'NODE_SPLIT',
        'NODE_DELETED',
        'NODE_COPIED',
        'SUMMARY_UPDATED',
        'GRAPH_UPDATED'
    )),
    payload JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    user_id TEXT
);

CREATE INDEX idx_events_node ON node_events(node_id);
CREATE INDEX idx_events_type ON node_events(event_type);
CREATE INDEX idx_events_timestamp ON node_events(timestamp DESC);
```

**Example Events:**

```json
// NODE_CREATED
{
  "event_type": "NODE_CREATED",
  "payload": {
    "parent_id": "uuid-or-null",
    "title": "XGBoost Exploration",
    "node_type": "standard",
    "inherited_context": "Summary from parent..."
  }
}

// MESSAGE_ADDED
{
  "event_type": "MESSAGE_ADDED",
  "payload": {
    "role": "user",
    "content": "Should we use CNN or XGBoost?",
    "token_count": 8
  }
}

// NODE_MERGED
{
  "event_type": "NODE_MERGED",
  "payload": {
    "source_node_id": "uuid-branch",
    "target_node_id": "uuid-parent",
    "merge_strategy": "append",
    "conflicts": []
  }
}

// GRAPH_UPDATED
{
  "event_type": "GRAPH_UPDATED",
  "payload": {
    "entities_added": [...],
    "relations_added": [...],
    "source_summary_id": "uuid"
  }
}
```

#### Table 3: `messages` (Immutable Chat Logs)

```sql
CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id UUID REFERENCES nodes(node_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'summary')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    token_count INTEGER,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_messages_node ON messages(node_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
```

**Special `role` values:**
- `user`: User message
- `assistant`: AI response
- `system`: System message (e.g., "Branch merged from...")
- `summary`: Merged branch summary (appears as special message bubble)

#### Table 4: `node_summaries` (Derived, Versioned)

```sql
CREATE TABLE node_summaries (
    summary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id UUID REFERENCES nodes(node_id),
    summary JSONB NOT NULL,
    generated_from_event UUID REFERENCES node_events(event_id),
    created_at TIMESTAMP DEFAULT NOW(),
    is_latest BOOLEAN DEFAULT true
);

CREATE INDEX idx_summaries_node ON node_summaries(node_id);
CREATE INDEX idx_summaries_latest ON node_summaries(node_id, is_latest) WHERE is_latest = true;
```

**Summary JSONB Structure:**

```json
{
  "facts": [
    {
      "fact": "Finalized CNN architecture with 3 conv layers",
      "source_node": "node_21",
      "confidence": 0.9,
      "timestamp": "2026-01-31T10:00:00Z"
    }
  ],
  "decisions": [
    {
      "decision": "Use healthcare domain for model testing",
      "source_node": "node_14",
      "rationale": "Better data quality than synthetic datasets",
      "confidence": 0.85
    }
  ],
  "open_questions": [
    "Should we use transfer learning?",
    "What batch size is optimal?"
  ],
  "metadata": {
    "total_messages": 12,
    "token_count": 3500,
    "generated_by": "gpt-4o-mini",
    "generation_timestamp": "2026-01-31T10:05:00Z"
  }
}
```

**Why Source Node IDs?**
- ✅ Enables deletion propagation (remove facts from deleted nodes)
- ✅ Provides explainability ("This decision came from node X")
- ✅ Supports audit trail

#### Table 5: `knowledge_graph` (Structured Insights)

```sql
CREATE TABLE knowledge_graph (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity TEXT NOT NULL,
    to_entity TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    source_node UUID REFERENCES nodes(node_id),
    confidence FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    
    UNIQUE(from_entity, to_entity, relation_type, source_node)
);

CREATE INDEX idx_graph_from ON knowledge_graph(from_entity);
CREATE INDEX idx_graph_to ON knowledge_graph(to_entity);
CREATE INDEX idx_graph_source ON knowledge_graph(source_node);
CREATE INDEX idx_graph_active ON knowledge_graph(deleted_at) WHERE deleted_at IS NULL;
```

**Example Knowledge Graph Entries:**

```json
[
  {
    "from_entity": "Healthcare Project",
    "to_entity": "CNN Architecture",
    "relation_type": "USES",
    "source_node": "node_12",
    "confidence": 0.9,
    "metadata": {
      "context": "Decided in discussion about model selection"
    }
  },
  {
    "from_entity": "CNN Architecture",
    "to_entity": "XGBoost",
    "relation_type": "ALTERNATIVE_TO",
    "source_node": "node_15",
    "confidence": 0.7
  }
]
```

**Graph Lifecycle:**
```
Node Created → Summary Generated → Graph Extracted → Edges Stored
Node Deleted → Find edges with source_node → Soft delete (set deleted_at)
Node Merged → Combine graphs → Mark duplicates → Update confidences
```

---

## 5. API Endpoints

### 5.1 Request Flow

```
Frontend Action → API Route → Event Validator → Event Store → 
→ Event Processor → AI Pipeline (conditional) → 
→ Derived State Update → Response
```

### 5.2 Endpoints

#### 1. POST /api/v1/nodes (Create Node)

**Request:**
```json
{
  "parent_id": "uuid-or-null",
  "title": "Model Architecture Exploration",
  "node_type": "standard"  // or "exploration" for lightweight
}
```

**Backend Flow:**
1. Create `nodes` row
2. Insert `NODE_CREATED` event
3. If `parent_id` exists:
   - Fetch parent's latest summary
   - Call **Summarizer** to compress parent summary into inherited context
   - Store new summary
   - Insert `SUMMARY_UPDATED` event
4. Calculate position on canvas (grid layout below parent)
5. Return node metadata

**Response:**
```json
{
  "node_id": "uuid",
  "parent_id": "uuid-or-null",
  "title": "Model Architecture Exploration",
  "node_type": "standard",
  "inherited_context": "Parent project focuses on neonatal jaundice diagnosis using ML...",
  "status": "active",
  "position": {"x": 400, "y": 450},
  "created_at": "2026-01-31T12:00:00Z"
}
```

---

#### 2. POST /api/v1/nodes/{node_id}/messages (Send Message)

**Request:**
```json
{
  "content": "Should we use CNN or XGBoost for this?"
}
```

**Backend Flow:**
1. Validate node exists and status = 'active'
2. Store user message in `messages`
3. Insert `MESSAGE_ADDED` event
4. **Route to appropriate AI agent:**
   - If `node.type == "exploration"` → Lightweight Node Agent
   - Else → Main Chat Agent
5. **Build context:**
   ```
   System Prompt
   + Inherited Summary (from parent)
   + Node Summary (current node compressed)
   + Knowledge Graph Context (optional, top 5 relevant facts)
   + Last 10 messages
   ```
6. Call LLM
7. Store assistant reply in `messages`
8. Insert `MESSAGE_ADDED` event
9. Return response

**Response:**
```json
{
  "message_id": "uuid",
  "role": "assistant",
  "content": "Based on your healthcare domain focus, CNNs would be more suitable because...",
  "timestamp": "2026-01-31T12:01:00Z",
  "token_count": 250,
  "agent_used": "main_chat"
}
```

---

#### 3. POST /api/v1/nodes/{node_id}/summarize (Summarize Node)

**Request:**
```json
{}  // No body needed
```

**Backend Flow:**
1. Fetch parent summary
2. Fetch all messages in node
3. Fetch current knowledge graph (if exists)
4. Call **Summarizer Agent** with prompt:
   ```
   Given parent context and conversation, extract:
   - Facts (with source node IDs and confidence)
   - Decisions made (with rationale)
   - Open questions remaining
   
   Exclude:
   - Exploratory chit-chat
   - Abandoned ideas
   - Redundant statements
   
   Output: JSON following schema
   ```
5. Store summary in `node_summaries` (mark old as `is_latest = false`)
6. Insert `SUMMARY_UPDATED` event
7. **Trigger Graph Builder Agent:**
   - Extract entities and relations from summary
   - Store in `knowledge_graph`
   - Insert `GRAPH_UPDATED` event
8. Return new summary

**Response:**
```json
{
  "summary_id": "uuid",
  "node_id": "uuid",
  "summary": {
    "facts": [...],
    "decisions": [...],
    "open_questions": [...]
  },
  "knowledge_graph": {
    "entities_added": 5,
    "relations_added": 3
  },
  "created_at": "2026-01-31T12:05:00Z"
}
```

---

#### 4. POST /api/v1/nodes/merge (Merge Branches)

**Request:**
```json
{
  "source_node_id": "uuid-branch",
  "target_node_id": "uuid-parent"
}
```

**Backend Flow:**
1. Validate both nodes exist
2. Validate source is descendant of target (prevent cycles)
3. Insert `NODE_MERGED` event
4. Fetch summaries:
   - Target node summary
   - Source node summary
5. Call **Merge Arbiter Agent** with prompt:
   ```
   You are merging branch findings into main context.
   
   RULES:
   - Never delete confirmed decisions from target
   - Prefer more specific over vague
   - If conflict exists, flag it (don't auto-resolve)
   - Maintain source node IDs
   
   Target: {...}
   Source: {...}
   
   Output: Updated target summary + conflicts list
   ```
6. Store new summary for target
7. Insert `SUMMARY_UPDATED` event
8. **Merge knowledge graphs:**
   - Find common entities
   - Combine relations
   - Update confidence scores
   - Mark source edges with `merged_into = target_node_id`
9. Mark source node as `frozen`
10. **Create summary message in target:**
    - Insert special message with `role = "summary"`
    - Content = "Merged findings from XGBoost Exploration: [key points]"
11. Return updated target

**Response:**
```json
{
  "target_node_id": "uuid",
  "source_node_id": "uuid",
  "updated_summary": {...},
  "conflicts": [
    {
      "type": "decision_conflict",
      "target_decision": "Use CNN",
      "source_decision": "Use XGBoost",
      "resolution": "manual_required"
    }
  ],
  "knowledge_graph_updates": {
    "entities_merged": 3,
    "relations_added": 2
  },
  "source_node_status": "frozen"
}
```

---

#### 5. POST /api/v1/nodes/{node_id}/delete (Delete Node)

**Request:**
```json
{
  "cascade": false  // If true, delete children too
}
```

**Backend Flow (MVP - Soft Delete):**
1. Validate node exists
2. Insert `NODE_DELETED` event
3. Mark `nodes.status = 'deleted'`
4. Soft delete knowledge graph edges: `UPDATE knowledge_graph SET deleted_at = NOW() WHERE source_node = node_id`
5. **DO NOT** delete messages (immutable)
6. Return success

**Backend Flow (Phase 3 - With Recomputation):**
1-5. Same as above
6. Find all descendant nodes
7. For each descendant:
   - Extract facts/decisions with `source_node = deleted_node_id`
   - Remove those from summary
   - Regenerate summary
   - Update knowledge graph
   - Insert `SUMMARY_UPDATED` event
8. This is **event replay** - enables true deletion

**Response:**
```json
{
  "node_id": "uuid",
  "status": "deleted",
  "affected_descendants": ["uuid1", "uuid2"],
  "recomputed": false,  // true in Phase 3
  "graph_edges_removed": 5
}
```

---

#### 6. POST /api/v1/nodes/{node_id}/copy (Copy/Branch Node)

**Request:**
```json
{
  "new_parent_id": "uuid-or-null"
}
```

**Backend Flow:**
1. Create new node
2. Insert `NODE_COPIED` event
3. **Copy summary reference** (not messages!)
4. Generate new inherited context from new parent
5. Copy relevant knowledge graph edges
6. Return new node

**Response:**
```json
{
  "new_node_id": "uuid",
  "original_node_id": "uuid",
  "parent_id": "uuid",
  "title": "Model Architecture Exploration (Copy)",
  "copied_at": "2026-01-31T12:10:00Z"
}
```

---

#### 7. GET /api/v1/nodes/tree (Get Full Tree)

**Response:**
```json
{
  "root": {
    "node_id": "uuid",
    "title": "Neonatal Jaundice Project",
    "status": "active",
    "message_count": 5,
    "has_summary": true,
    "children": [
      {
        "node_id": "uuid",
        "title": "XGBoost Exploration",
        "status": "frozen",
        "message_count": 12,
        "children": []
      },
      {
        "node_id": "uuid",
        "title": "CNN Architecture",
        "status": "active",
        "message_count": 8,
        "children": [...]
      }
    ]
  }
}
```

---

#### 8. GET /api/v1/nodes/{node_id}/messages

**Response:**
```json
{
  "node_id": "uuid",
  "messages": [
    {
      "message_id": "uuid",
      "role": "user",
      "content": "Should we use CNN?",
      "timestamp": "2026-01-31T10:00:00Z"
    },
    {
      "message_id": "uuid",
      "role": "assistant",
      "content": "Yes, because...",
      "timestamp": "2026-01-31T10:01:00Z"
    }
  ],
  "total_count": 15,
  "has_more": false
}
```

---

#### 9. GET /api/v1/nodes/{node_id}/graph (Get Knowledge Graph)

**Response:**
```json
{
  "node_id": "uuid",
  "entities": [
    {
      "name": "CNN Architecture",
      "type": "concept",
      "mentioned_count": 5
    }
  ],
  "relations": [
    {
      "from": "Healthcare Project",
      "to": "CNN Architecture",
      "type": "USES",
      "confidence": 0.9
    }
  ],
  "visualization_data": {
    "nodes": [...],
    "edges": [...]
  }
}
```

---

## 6. LLM Pipeline & Prompts

### 6.1 Main Chat Agent

**System Prompt:**
```
You are an AI assistant helping with project exploration in a branching conversation system.

CONTEXT HIERARCHY:
1. Inherited Context (from ancestor nodes): {inherited_summary}
2. Current Node Summary (this branch's compressed state): {node_summary}
3. Knowledge Graph (structured insights): {graph_context}
4. Recent Conversation: {last_10_messages}

GUIDELINES:
- Build on established decisions and facts
- Flag conflicts with inherited context if found
- Suggest creating a new branch when exploring alternatives
- Reference knowledge graph entities when relevant
- Maintain awareness of open questions

CURRENT NODE: {node_title}
NODE TYPE: {node_type}
```

**Context Assembly Code:**
```python
def build_main_chat_context(node_id: str) -> str:
    # 1. Get lineage
    lineage = get_node_lineage(node_id)  # [child, parent, grandparent, ..., root]
    
    # 2. Collect ancestor summaries (compress progressively)
    inherited_context = ""
    for ancestor in reversed(lineage[1:]):
        summary = get_latest_summary(ancestor.node_id)
        # Compress to key facts/decisions only
        inherited_context += extract_key_points(summary)
    
    # 3. Get current node summary
    node_summary = get_latest_summary(node_id)
    
    # 4. Get relevant knowledge graph context
    graph_context = get_relevant_graph_facts(node_id, limit=5)
    
    # 5. Get recent messages
    recent_messages = get_last_n_messages(node_id, n=10)
    
    # 6. Assemble
    return MAIN_CHAT_PROMPT.format(
        inherited_summary=inherited_context,
        node_summary=json.dumps(node_summary, indent=2),
        graph_context=format_graph_context(graph_context),
        last_10_messages=format_messages(recent_messages),
        node_title=get_node_title(node_id),
        node_type=get_node_type(node_id)
    )
```

---

### 6.2 Summarizer Agent

**System Prompt:**
```
You are a semantic compression engine. Extract ONLY essential information.

INPUT:
- Parent Context: {parent_summary}
- Conversation Messages: {all_messages}
- Existing Knowledge Graph: {existing_graph}

TASK: Extract and structure:

1. FACTS (concrete, established information):
   - fact: "..."
   - source_node: "node_id"
   - confidence: 0.0-1.0
   - timestamp: "..."

2. DECISIONS (choices made with rationale):
   - decision: "..."
   - source_node: "node_id"
   - rationale: "..."
   - confidence: 0.0-1.0

3. OPEN QUESTIONS (unresolved):
   - "..."

4. METADATA:
   - total_messages: N
   - token_count: N
   - key_topics: [...]

EXCLUDE:
- Exploratory chitchat
- Abandoned ideas
- Redundant statements
- Off-topic discussions

OUTPUT FORMAT: Valid JSON matching schema
```

**Example Output:**
```json
{
  "facts": [
    {
      "fact": "Healthcare domain selected for testing",
      "source_node": "node_12",
      "confidence": 0.95,
      "timestamp": "2026-01-31T10:00:00Z"
    }
  ],
  "decisions": [
    {
      "decision": "Use CNN architecture over XGBoost",
      "source_node": "node_15",
      "rationale": "Better feature extraction from medical images",
      "confidence": 0.85
    }
  ],
  "open_questions": [
    "Should we use transfer learning?",
    "What data augmentation techniques?"
  ],
  "metadata": {
    "total_messages": 12,
    "token_count": 3500,
    "key_topics": ["model selection", "architecture", "healthcare"]
  }
}
```

---

### 6.3 Knowledge Graph Builder Agent

**System Prompt:**
```
You are a knowledge graph extraction engine. Convert summaries into structured entities and relations.

INPUT: Node summary (JSON)

OUTPUT: Knowledge graph (JSON)

ENTITY TYPES:
- concept (e.g., "CNN Architecture")
- decision (e.g., "Use Healthcare Domain")
- person (e.g., "Dr. Smith")
- technology (e.g., "TensorFlow")
- dataset (e.g., "MIMIC-III")

RELATION TYPES:
- USES (entity uses another)
- ALTERNATIVE_TO (two options)
- REQUIRES (dependency)
- INFLUENCES (affects)
- PART_OF (containment)
- FINALIZED_AS (exploration → decision)

RULES:
- Extract 3-10 entities per summary
- Create meaningful relations (not trivial)
- Include confidence scores
- Reference source nodes

OUTPUT FORMAT: Valid JSON
```

**Example Output:**
```json
{
  "entities": [
    {
      "id": "cnn_arch_1",
      "name": "CNN Architecture",
      "type": "concept",
      "confidence": 0.9
    },
    {
      "id": "xgboost_1",
      "name": "XGBoost",
      "type": "concept",
      "confidence": 0.8
    },
    {
      "id": "healthcare_domain_1",
      "name": "Healthcare Domain",
      "type": "concept",
      "confidence": 0.95
    }
  ],
  "relations": [
    {
      "from": "cnn_arch_1",
      "to": "xgboost_1",
      "type": "ALTERNATIVE_TO",
      "confidence": 0.85,
      "context": "Both considered for model selection"
    },
    {
      "from": "healthcare_domain_1",
      "to": "cnn_arch_1",
      "type": "USES",
      "confidence": 0.9,
      "context": "Healthcare project will use CNN architecture"
    }
  ]
}
```

---

### 6.4 Merge Arbiter Agent

**System Prompt:**
```
You are merging a branch's findings back into the main thread.

STRICT RULES:
1. NEVER delete confirmed decisions from target
2. Prefer more specific information over vague
3. If conflict exists, flag it (DO NOT auto-resolve)
4. Maintain all source_node IDs for traceability
5. Combine facts if compatible, flag if conflicting

INPUT:
- Target Summary (main thread): {target_summary}
- Source Summary (branch): {source_summary}

CONFLICT TYPES TO FLAG:
- Different decisions on same question
- Contradicting facts
- Incompatible assumptions

OUTPUT:
- updated_target_summary (merged JSON)
- conflicts (list of flagged issues)
```

**Example Output:**
```json
{
  "updated_target_summary": {
    "facts": [
      {
        "fact": "Healthcare domain selected",
        "source_node": "node_12",
        "confidence": 0.95
      },
      {
        "fact": "XGBoost achieves 85% accuracy",
        "source_node": "node_15",
        "confidence": 0.8
      }
    ],
    "decisions": [
      {
        "decision": "Use CNN architecture",
        "source_node": "node_18",
        "rationale": "Better for image data",
        "confidence": 0.9,
        "supersedes": ["node_15"]
      }
    ]
  },
  "conflicts": [
    {
      "type": "decision_conflict",
      "description": "Target chose CNN (node_18), source explored XGBoost (node_15)",
      "target_value": "CNN Architecture",
      "source_value": "XGBoost",
      "resolution": "Keep both as alternatives explored",
      "action_required": false
    }
  ]
}
```

---

## 7. Knowledge Graph Integration

### 7.1 Why Knowledge Graph?

```
Problem: Summaries are text blobs
"We decided to use CNN for healthcare."

Better: Structured knowledge
ENTITY: CNN Architecture
ENTITY: Healthcare Domain
RELATION: Healthcare USES CNN (confidence: 0.9, source: node_12)

Benefits:
✅ Queryable ("What technologies are we using?")
✅ Visualizable (show graph in sidebar)
✅ Deletion-aware (remove node → remove its contributions)
✅ Conflict detection (two branches claim different things)
```

### 7.2 Graph Lifecycle

```
1. Node Created
   └─> No graph yet (empty)

2. User Chats in Node
   └─> Messages accumulate

3. User Clicks "Summarize"
   ├─> Summarizer extracts facts/decisions
   ├─> Graph Builder extracts entities/relations
   └─> Both stored in DB

4. User Merges Branch → Parent
   ├─> Combine graphs
   ├─> Detect conflicts
   └─> Update parent graph

5. User Deletes Node
   ├─> Soft delete graph edges (set deleted_at)
   └─> (Phase 3) Propagate to descendants
```

### 7.3 Graph Queries (Examples)

```sql
-- Get all technologies used in project
SELECT DISTINCT to_entity
FROM knowledge_graph
WHERE relation_type = 'USES'
  AND deleted_at IS NULL;

-- Find conflicts (same entities with different relations)
SELECT from_entity, to_entity, relation_type, source_node
FROM knowledge_graph
WHERE (from_entity, to_entity) IN (
  SELECT from_entity, to_entity
  FROM knowledge_graph
  GROUP BY from_entity, to_entity
  HAVING COUNT(DISTINCT relation_type) > 1
);

-- Get graph for visualization (node + ancestors)
WITH RECURSIVE lineage AS (
  SELECT node_id FROM nodes WHERE node_id = $1
  UNION
  SELECT n.parent_id FROM nodes n
  INNER JOIN lineage l ON n.node_id = l.node_id
  WHERE n.parent_id IS NOT NULL
)
SELECT * FROM knowledge_graph
WHERE source_node IN (SELECT node_id FROM lineage)
  AND deleted_at IS NULL;
```

### 7.4 Graph Visualization Data

**API Endpoint:** `GET /api/v1/nodes/{node_id}/graph/viz`

**Response:**
```json
{
  "nodes": [
    {
      "id": "cnn_arch",
      "label": "CNN Architecture",
      "type": "concept",
      "color": "#3b82f6",
      "size": 30
    },
    {
      "id": "healthcare",
      "label": "Healthcare Domain",
      "type": "concept",
      "color": "#10b981",
      "size": 25
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "source": "healthcare",
      "target": "cnn_arch",
      "label": "USES",
      "confidence": 0.9,
      "animated": true
    }
  ]
}
```

---

## 8. Event-Sourcing & Deletion

### 8.1 Why Event-Sourcing?

```
Traditional Database:
User deletes Node A → UPDATE nodes SET deleted=true
Result: Lost forever, can't undo, descendants broken

Event-Sourced Database:
User deletes Node A → INSERT INTO node_events (type='NODE_DELETED')
Result: Can replay, can undo, can recompute descendants
```

### 8.2 Deletion Algorithm (Phase 3)

```python
def delete_node_with_propagation(node_id: str):
    """
    True deletion with downstream recomputation.
    This is the killer feature that makes the system work.
    """
    
    # Step 1: Record deletion event
    insert_event('NODE_DELETED', node_id, {
        'deleted_by': current_user,
        'cascade': False
    })
    
    # Step 2: Mark node as deleted
    update_node_status(node_id, 'deleted')
    
    # Step 3: Soft delete knowledge graph edges
    soft_delete_graph_edges(source_node=node_id)
    
    # Step 4: Find all descendants
    descendants = get_all_descendants(node_id)
    
    # Step 5: For each descendant, recompute summary
    for desc in descendants:
        # Get current summary
        current_summary = get_latest_summary(desc.node_id)
        
        # Remove facts/decisions sourced from deleted node
        cleaned_summary = {
            'facts': [f for f in current_summary['facts'] 
                     if f['source_node'] != node_id],
            'decisions': [d for d in current_summary['decisions']
                         if d['source_node'] != node_id],
            'open_questions': current_summary['open_questions']
        }
        
        # Store new summary
        create_summary(desc.node_id, cleaned_summary, 
                      generated_from='NODE_DELETION_PROPAGATION')
        
        # Regenerate knowledge graph
        rebuild_graph_for_node(desc.node_id)
        
        # Insert event
        insert_event('SUMMARY_UPDATED', desc.node_id, {
            'reason': 'ancestor_deleted',
            'deleted_ancestor': node_id
        })
    
    return {
        'deleted_node': node_id,
        'affected_descendants': len(descendants),
        'recomputed': True
    }
```

### 8.3 Event Replay (Future: Undo/Redo)

```python
def replay_events_from(start_event_id: str):
    """
    Rebuild system state by replaying events.
    Enables time-travel, undo, debugging.
    """
    
    # Get all events after start_event
    events = get_events_after(start_event_id, order='ASC')
    
    # Clear derived state (summaries, graph)
    clear_summaries()
    clear_knowledge_graph()
    
    # Replay each event
    for event in events:
        if event.type == 'NODE_CREATED':
            create_node(**event.payload)
        
        elif event.type == 'MESSAGE_ADDED':
            store_message(**event.payload)
        
        elif event.type == 'SUMMARY_UPDATED':
            store_summary(**event.payload)
        
        elif event.type == 'NODE_MERGED':
            replay_merge(**event.payload)
        
        elif event.type == 'NODE_DELETED':
            replay_deletion(**event.payload)
        
        # ... etc
    
    return {'events_replayed': len(events)}
```

---

## 9. Implementation Roadmap

### Phase 1: Survival MVP (Hackathon - 48 Hours)

**Goal:** Prove the UX works

**Backend Checklist:**
- [x] Database setup
  - [x] `nodes`, `node_events`, `messages`, `node_summaries` tables
  - [x] Basic indexes
- [x] API Endpoints
  - [x] POST /nodes (create)
  - [x] POST /nodes/{id}/messages (chat)
  - [x] POST /nodes/{id}/summarize (manual summarize)
  - [x] POST /nodes/merge (merge branches)
  - [x] POST /nodes/{id}/delete (soft delete only)
  - [x] GET /nodes/tree
  - [x] GET /nodes/{id}/messages
- [x] LLM Integration
  - [x] Main Chat Agent (Claude/GPT-4)
  - [x] Summarizer Agent (GPT-4o-mini)
  - [x] Context assembly logic
- [x] Event Logging
  - [x] All actions insert into `node_events`
- [ ] NOT INCLUDED
  - [ ] Knowledge graph (Phase 2)
  - [ ] Cascading deletion (Phase 3)
  - [ ] Embeddings (Phase 4)
  - [ ] RAG (Phase 4)

**Deliverable:**
- User can create nodes
- User can chat in nodes with context inheritance
- User can manually summarize nodes
- User can merge branches (basic)
- User can soft-delete nodes
- Backend logs all events for future replay

---

### Phase 2: Structured Memory (Post-Hackathon, Week 1-2)

**Goal:** Add knowledge graph + source tracking

**Backend Checklist:**
- [x] Database
  - [x] Add `knowledge_graph` table
  - [x] Modify summary JSONB to include source_node IDs
- [x] API Endpoints
  - [x] GET /nodes/{id}/graph
  - [x] GET /nodes/{id}/graph/viz (visualization data)
- [x] LLM Integration
  - [x] Graph Builder Agent
  - [x] Graph-aware prompts
- [x] Logic
  - [x] Graph extraction after summarization
  - [x] Graph merging during node merge
  - [x] Graph soft-delete on node delete

**Deliverable:**
- Knowledge graph extracted from summaries
- Graph visualization in sidebar
- Source tracking for all facts/decisions
- Graph-aware merging

---

### Phase 3: Deletion & Recomputation (Week 3-4)

**Goal:** True node deletion with propagation

**Backend Checklist:**
- [x] Event Replay System
  - [x] `replay_events_from()` function
  - [x] State reconstruction from events
- [x] Cascading Deletion
  - [x] `delete_node_with_propagation()` function
  - [x] Remove sourced facts from descendants
  - [x] Regenerate summaries
  - [x] Rebuild graphs
- [x] Undo/Redo (bonus)
  - [x] Checkpoint system
  - [x] Rollback to event ID

**Deliverable:**
- True deletion (not just soft delete)
- Descendants updated correctly
- No "ghost" references to deleted nodes
- Audit trail maintained

---

### Phase 4: Embeddings + RAG (Week 5-6)

**Goal:** Semantic search + external knowledge

**Backend Checklist:**
- [x] Vector Database
  - [x] Qdrant or FAISS integration
  - [x] `embeddings` table
- [x] Embedding Generation
  - [x] Embed node summaries
  - [x] Embed graph entities
  - [x] Embed RAG chunks
- [x] RAG Pipeline
  - [x] Document chunking
  - [x] Chunk embedding
  - [x] Semantic retrieval
  - [x] RAG-aware summarization
- [x] API Endpoints
  - [x] POST /rag/upload (upload document)
  - [x] GET /nodes/{id}/search (semantic search)

**Deliverable:**
- Semantic search across project history
- Book/document ingestion
- RAG-enhanced context (without pollution)
- "Find where we discussed X" feature

---

## 10. Team Responsibilities

### 10.1 Backend Developer (You)

**Week 1 (Pre-Hackathon):**
1. Set up PostgreSQL database (local + Railway)
2. Create all tables (`nodes`, `node_events`, `messages`, `node_summaries`)
3. Set up FastAPI project structure
4. Write database CRUD functions (SQLAlchemy)
5. Define LLM service interface (`llm_service.py` with method stubs)
6. Create API route skeletons
7. Share API contract (OpenAPI YAML) with team

**Week 2 (Hackathon):**
1. Implement all Phase 1 API endpoints
2. Connect routes to database
3. Integrate LLM service calls (from AI teammate)
4. Test end-to-end flows
5. Handle errors gracefully
6. Deploy backend (Railway/Render)
7. Monitor logs and fix bugs

**Your Mindset:**
- Think 3 phases ahead (design for future even if not building now)
- Log ALL events (enables future replay)
- Keep LLM logic abstracted (easy to swap models)
- Document API clearly (frontend depends on it)

---

### 10.2 AI/LLM Developer (Your Friend)

**Week 1 (Pre-Hackathon):**
1. Set up LLM API accounts (OpenAI, Anthropic)
2. Install Ollama + download Llama 3.2 3B
3. Test local model inference (Llama, embeddings)
4. Write first drafts of prompts:
   - Main Chat system prompt
   - Summarizer prompt
   - Merge Arbiter prompt
5. Implement `llm_service.py` interface:
   ```python
   class LLMService:
       async def chat_with_ai(node_id, user_message) -> str
       async def summarize_node(node_id, parent_summary, messages) -> dict
       async def merge_summaries(target, source) -> dict
       async def generate_inherited_context(parent_id) -> str
   ```
6. Test context assembly logic
7. Handle token counting

**Week 2 (Hackathon):**
1. Refine prompts based on testing
2. Implement context assembly (get lineage, compress summaries)
3. Add error handling (API timeouts, rate limits)
4. Optimize inference speed (cache where possible)
5. Test with real conversation flows
6. Iterate on summary quality

**Phase 2 Addition:**
1. Write Graph Builder Agent prompt
2. Implement `build_knowledge_graph(summary) -> dict`
3. Test graph extraction quality

**Your Mindset:**
- Prompt engineering is 80% of quality
- Test prompts extensively before hackathon
- Handle LLM failures gracefully (retries, fallbacks)
- Keep token budgets in check (compress aggressively)

---

### 10.3 Frontend Developer

**Week 1 (Pre-Hackathon):**
1. Set up React + React Flow
2. Create node component (collapsed/expanded states)
3. Implement drag-and-drop (for merge)
4. Build chat panel UI
5. Create API service layer (fetch wrappers)
6. Study API contract from backend

**Week 2 (Hackathon):**
1. Connect all API endpoints
2. Handle loading states (spinners, skeletons)
3. Implement visual feedback (frozen, deleted, active states)
4. Test merge/delete flows
5. Polish animations (smooth transitions)
6. Add error toasts
7. Deploy frontend (Vercel/Netlify)

**Phase 2 Addition:**
1. Build knowledge graph visualization (sidebar)
2. Use D3.js or React Flow for graph rendering
3. Show entity details on hover

**Your Mindset:**
- API might fail → show graceful errors
- LLM calls are slow → show loading states
- Users will drag wrong nodes → validate on frontend too
- Canvas state ≠ backend truth (always sync)

---

### 10.4 Shared Contract (Critical)

**Create `api-contract.yaml` (OpenAPI Spec):**

```yaml
openapi: 3.0.0
info:
  title: Fractal Workspace API
  version: 1.0.0
  description: Event-sourced multi-agent AI conversation system

servers:
  - url: http://localhost:8000/api/v1
    description: Local development
  - url: https://fractal-backend.railway.app/api/v1
    description: Production

paths:
  /nodes:
    post:
      summary: Create a new node
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [title]
              properties:
                parent_id:
                  type: string
                  format: uuid
                  nullable: true
                title:
                  type: string
                  minLength: 1
                  maxLength: 200
                node_type:
                  type: string
                  enum: [standard, exploration]
                  default: standard
      responses:
        201:
          description: Node created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Node'
        400:
          description: Invalid request
        404:
          description: Parent node not found

  # ... (all other endpoints)

components:
  schemas:
    Node:
      type: object
      properties:
        node_id:
          type: string
          format: uuid
        parent_id:
          type: string
          format: uuid
          nullable: true
        title:
          type: string
        node_type:
          type: string
          enum: [root, standard, exploration]
        status:
          type: string
          enum: [active, frozen, deleted]
        position:
          type: object
          properties:
            x:
              type: number
            y:
              type: number
        created_at:
          type: string
          format: date-time
```

**Why This Matters:**
- Frontend knows exact request/response shapes
- Backend knows exact validation rules
- Both teams stay in sync
- Auto-generate TypeScript types (frontend) and Pydantic models (backend)

---

## 11. Tech Stack Summary

### Backend
```
- Language: Python 3.11+
- Framework: FastAPI (async, auto docs, Pydantic validation)
- Database: PostgreSQL 15+ (JSONB support)
- ORM: SQLAlchemy 2.0 (async)
- LLM SDKs: 
  - openai-python (GPT models)
  - anthropic-python (Claude models)
  - ollama-python (local Llama)
- Background Jobs: Celery + Redis (Phase 3+)
- Deployment: Railway / Render
```

### AI/LLM
```
- Main Chat: Claude Sonnet 3.5 / GPT-4 (via API)
- Lightweight Node: Llama 3.2 3B (local via Ollama)
- Summarizer: GPT-4o-mini (fast + cheap)
- Graph Builder: GPT-4 with JSON mode
- Embeddings (Phase 4): bge-m3 (local)
- Vector DB (Phase 4): Qdrant / FAISS
```

### Frontend
```
- Framework: React 18 + TypeScript
- Canvas: React Flow
- State: Zustand
- Styling: Tailwind CSS
- UI Components: Shadcn/ui
- Deployment: Vercel / Netlify
```

---

## 12. Critical Success Factors

### 12.1 Must Work on Demo Day

**The 5-Minute Flow:**
```
1. CREATE root node: "Neonatal Jaundice Project"
2. CHAT: "Should we use ML for diagnosis?"
3. CREATE branch: "XGBoost Exploration"
4. CHAT in branch: "What features should we use?"
5. SUMMARIZE branch
6. CREATE another branch: "CNN Exploration"
7. CHAT in CNN branch: "What architecture?"
8. SUMMARIZE CNN branch
9. MERGE XGBoost back to root
   → Root chat shows summary message
   → Root node updated
10. DELETE CNN branch
   → Disappears from tree
11. VIEW root node chat
   → Should see XGBoost summary as special message

If this works, your MVP works. ✅
```

### 12.2 Quality Checklist

**Summaries:**
- [ ] Capture key decisions (not everything)
- [ ] Include source node IDs
- [ ] Exclude chitchat
- [ ] Maintain traceability

**Merging:**
- [ ] No data loss (all decisions preserved)
- [ ] Conflicts flagged (not auto-resolved)
- [ ] Summary appears in parent chat
- [ ] Source node frozen (not deleted)

**Knowledge Graph (Phase 2):**
- [ ] Entities correctly extracted
- [ ] Relations make sense
- [ ] Visualization is readable
- [ ] Graph updates on merge/delete

**Context Inheritance:**
- [ ] Child sees parent's compressed summary
- [ ] Grandchild sees grandparent's summary (compressed further)
- [ ] Token budget stays under limit
- [ ] Compression doesn't lose critical info

---

## 13. What Makes This Backend Special

### 13.1 It's Not a Chat API

```
Normal Chat API:
User sends message → Store → Call LLM → Store response → Done

The Fractal Workspace Backend:
User sends message → 
→ Store event → 
→ Rebuild context from lineage → 
→ Route to correct AI agent → 
→ Call LLM with assembled context → 
→ Store response → 
→ Store event → 
→ (Future) Update knowledge graph → 
→ (Future) Update embeddings → 
→ Return to user
```

### 13.2 It's Built for Evolution

```
Phase 1: Works without graph ✅
Phase 2: Graph added seamlessly ✅
Phase 3: Deletion replay added seamlessly ✅
Phase 4: Embeddings added seamlessly ✅

Why? Event-sourcing + Clean abstractions
```

### 13.3 It Respects Cognitive Science

```
Traditional AI: Monolithic context (everything smooshed together)

The Fractal Workspace:
- Each node = Bounded cognitive universe
- Inheritance = Deliberate information flow
- Merge = Conscious integration
- Deletion = Controlled forgetting

You're externalizing human working memory into a manipulable structure.
```

---

## 14. File Structure

```
backend/
├── main.py                     # FastAPI app, routes
├── config.py                   # Settings, API keys, env vars
├── database.py                 # SQLAlchemy setup, session management
│
├── models/
│   ├── db_models.py           # SQLAlchemy models (Node, Event, Message, etc.)
│   └── api_models.py          # Pydantic request/response models
│
├── services/
│   ├── llm_service.py         # 🔌 AI PLUG POINT - Your friend implements
│   ├── context_manager.py     # Context assembly logic
│   ├── event_processor.py     # Event handling
│   └── graph_service.py       # Knowledge graph operations (Phase 2)
│
├── crud/
│   ├── nodes.py               # Node CRUD operations
│   ├── events.py              # Event operations
│   ├── messages.py            # Message operations
│   └── summaries.py           # Summary operations
│
├── utils/
│   ├── helpers.py             # Utility functions
│   └── constants.py           # Constants, enums
│
├── requirements.txt
├── .env.example
└── tests/
    ├── test_nodes.py
    ├── test_llm.py
    └── test_merge.py
```

---

## 15. Next Steps

### This Week (Pre-Hackathon):

**Backend Developer:**
1. ✅ Set up PostgreSQL (local + Railway)
2. ✅ Create database tables
3. ✅ Set up FastAPI project
4. ✅ Write CRUD functions
5. ✅ Define LLM service interface
6. ✅ Create API contract YAML
7. ✅ Share with team

**AI Developer:**
1. ✅ Set up LLM API accounts
2. ✅ Install Ollama
3. ✅ Write initial prompts
4. ✅ Implement `llm_service.py` interface
5. ✅ Test context assembly
6. ✅ Test local model inference

**Frontend Developer:**
1. ✅ Set up React project
2. ✅ Create node component
3. ✅ Build chat panel UI
4. ✅ Study API contract
5. ✅ Create API service layer

### Next Week (Hackathon):

**All Team:**
1. ✅ Connect all pieces
2. ✅ Test end-to-end flow
3. ✅ Fix bugs
4. ✅ Refine prompts
5. ✅ Polish UI
6. ✅ Prepare demo script
7. ✅ Present and win 🏆

---

## Conclusion

This backend is **not a prototype** — it's a **foundation**.

By designing with:
- ✅ Event-sourcing (enables deletion, undo, replay)
- ✅ Clean abstractions (LLM service interface)
- ✅ Multi-agent AI (specialized, high-quality)
- ✅ Knowledge graph (structured, queryable)
- ✅ Source tracking (explainable, deletable)

You're building a system that:
- Works today (Phase 1 MVP)
- Scales tomorrow (Phases 2-4)
- Maintains quality (prompt engineering)
- Enables debugging (event audit trail)
- Supports collaboration (team independence)

**Most importantly:**  
You're building something **truly novel** — a visual, branching, context-managing AI workspace that respects how humans actually think.

Good luck! 🚀

---

**Want to Go Deeper?**

Ask me for:
1. "Show me exact LLM prompts with examples"
2. "How do I handle token limits and context compression?"
3. "Show me the Phase 1 task list with hour-by-hour breakdown"
4. "Simulate a full merge/delete flow with example data"
5. "How do I deploy this to production?"

Let me know what you need next!
