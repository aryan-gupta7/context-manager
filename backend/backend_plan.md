# Backend Template Planning - AI-Ready Architecture

Good call! Let's plan everything first before writing code.

---

## Core Decisions to Make

### 1. **Database Choice**: SQLite + SQLAlchemy ORM\*\*

---

### 2. **Database Schema Design**

**Tables we need:**

```
projects
├── id (PRIMARY KEY)
├── name
├── root_node_id (FOREIGN KEY -> nodes.id)
├── created_at

nodes
├── id (PRIMARY KEY)
├── project_id (FOREIGN KEY -> projects.id)
├── parent_id (FOREIGN KEY -> nodes.id, NULLABLE)
├── title
├── node_type (root/branch/merged)
├── position_x (for canvas)
├── position_y (for canvas)
├── context_summary (TEXT - AI-generated summary)
├── status (active/merged/archived)
├── created_at
├── updated_at

messages
├── id (PRIMARY KEY)
├── node_id (FOREIGN KEY -> nodes.id)
├── role (user/assistant/system)
├── content (TEXT)
├── timestamp
├── token_count (for tracking)

edges (optional - can derive from parent_id)
├── id (PRIMARY KEY)
├── source_node_id (FOREIGN KEY -> nodes.id)
├── target_node_id (FOREIGN KEY -> nodes.id)
├── edge_type (inherit/merge)
```

**Questions:**

- Do we need `edges` table or just use `parent_id` in nodes?
- Should we store `token_count` per message or calculate on-the-fly?

---

### 3. **API Design Strategy**

**RESTful Design:**

```
Base URL: http://localhost:8000/api/v1

Resources:
├── /projects
├── /nodes
├── /messages
└── /operations (branch, merge, etc.)
```

**Endpoint Structure Options:**

**Option A: Nested Routes (RESTful)**

```
POST   /api/v1/projects
GET    /api/v1/projects/{project_id}
POST   /api/v1/projects/{project_id}/nodes
GET    /api/v1/nodes/{node_id}
POST   /api/v1/nodes/{node_id}/messages
POST   /api/v1/nodes/{node_id}/branch
POST   /api/v1/nodes/{source_id}/merge/{target_id}
```

**Option B: Flat Routes (Simpler)**

```
POST   /api/v1/projects
GET    /api/v1/projects/{project_id}
POST   /api/v1/nodes
GET    /api/v1/nodes/{node_id}
POST   /api/v1/messages
POST   /api/v1/branch
POST   /api/v1/merge
```

**My Recommendation: Option A (Nested)**

- More intuitive
- Clearer relationships
- Standard REST practice

---

### 4. **AI Integration Points**

```python
# llm_service.py

def chat_with_ai(node_id: str, user_message: str) -> str:
    """
    🤖 AI PLUG POINT #1: Chat in a node

    1. Get node context from database
    2. Build prompt with context
    3. Call Claude API
    4. Return AI response
    """
    # TODO
    return "AI response placeholder"


def summarize_for_branch(parent_node_id: str) -> str:
    """
    🤖 AI PLUG POINT #2: Summarize parent when branching

    1. Get parent messages
    2. Prompt Claude to summarize
    3. Return summary
    """
    # TODO
    return "Summary placeholder"


def generate_merge_summary(source_node_id: str) -> str:
    """
    🤖 AI PLUG POINT #3: Create merge summary

    1. Get all branch messages
    2. Prompt Claude to extract key findings
    3. Return merge summary
    """
    # TODO
    return "Merge summary placeholder"


def detect_should_branch(node_id: str) -> bool:
    """
    🤖 AI PLUG POINT #4: Suggest branching (optional)

    1. Get recent messages
    2. Ask Claude if topic is diverging
    3. Return true/false
    """
    # TODO
    return False
```

---

### 5. **Response Format Standardization**

**Consistent API responses:**

```python
# Success response
{
    "success": true,
    "data": { ... },
    "message": "Operation successful"
}

# Error response
{
    "success": false,
    "error": {
        "code": "NODE_NOT_FOUND",
        "message": "Node with id xyz not found"
    }
}
```

**Or just return data directly?**

```python
# Simple approach (recommended for hackathon)
return {"id": "123", "title": "My Node"}

# Let FastAPI handle errors automatically
```

**My Recommendation: Simple approach**

- FastAPI has built-in error handling
- Less boilerplate
- Faster to implement

---

### 6. **Error Handling Strategy**

**Custom exceptions:**

```python
# exceptions.py

class NodeNotFoundError(Exception):
    pass

class InvalidMergeError(Exception):
    pass

class ContextTooLargeError(Exception):
    pass

# In routes:
@app.get("/nodes/{node_id}")
def get_node(node_id: str):
    node = db.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node
```

**Or use FastAPI's built-in HTTPException everywhere?**

**My Recommendation: Just use HTTPException**

- Simpler
- Built-in
- Good enough for hackathon

---

### 7. **File Structure**

**Option A: Flat (Simple)**

```
backend/
├── main.py              (all routes here)
├── database.py          (all DB logic)
├── models.py            (Pydantic models)
├── llm_service.py       (AI plug point)
├── config.py
└── utils.py
```

**Option B: Organized (Scalable)**

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── projects.py
│   │   │   ├── nodes.py
│   │   │   └── messages.py
│   │   └── dependencies.py
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py      (SQLAlchemy models)
│   │   └── crud.py        (CRUD operations)
│   ├── schemas/
│   │   └── models.py      (Pydantic models)
│   ├── services/
│   │   ├── llm_service.py
│   │   └── context_manager.py
│   └── core/
│       └── config.py
└── requirements.txt
```

**My Recommendation: Option A for hackathon**

- Easier to navigate
- Less context switching
- Can refactor later if needed

---

### 8. **Data Storage Location**

**Where to store things:**

```
backend/
├── fractal_workspace.db     (SQLite database)
├── data/                    (if we need file storage)
│   └── exports/             (exported projects)
└── logs/                    (error logs)
```

**Or keep it simple:**

```
backend/
└── fractal_workspace.db     (just the database)
```

**My Recommendation: Just the database**

- Keep it minimal
- Everything in SQLite

---

### 9. **CORS Configuration**

**What origins to allow:**

```python
# During development:
allow_origins=["http://localhost:5173", "http://localhost:3000"]

# For demo:
allow_origins=["*"]  # Allow all (only for demo!)
```

**My Recommendation: Allow specific origins**

- More secure
- Easy to add more

---

### 10. **Testing Strategy**

**Do we build tests?**

**For Hackathon:**

- ❌ Skip unit tests (time crunch)
- ✅ Manual testing with Postman/Thunder Client
- ✅ Create a `test_requests.md` with example API calls

**Example test_requests.md:**

```markdown
# Test API Endpoints

## Create Project

POST http://localhost:8000/api/v1/projects
{
"name": "Neonatal Jaundice Project"
}

## Create Node

POST http://localhost:8000/api/v1/nodes
{
"project_id": "xxx",
"title": "Root Discussion"
}
```

---

## My Proposed Architecture

Based on all the above, here's what I recommend:

### **Stack:**

- FastAPI (routes)
- SQLite (database)
- SQLAlchemy (ORM)
- Pydantic (validation)

### **File Structure:**

```
backend/
├── main.py              # FastAPI app + all routes
├── database.py          # SQLAlchemy setup + CRUD operations
├── models.py            # Pydantic models (request/response)
├── db_models.py         # SQLAlchemy models (database tables)
├── config.py            # Settings
├── utils.py             # Helper functions
├── llm_service.py       # AI PLUG POINT (placeholder functions)
├── context_manager.py   # AI PLUG POINT (placeholder functions)
├── requirements.txt
├── .env.example
└── test_requests.md     # API testing examples
```

### **API Routes:**

```
POST   /api/v1/projects              # Create project
GET    /api/v1/projects/{id}         # Get project with all nodes

POST   /api/v1/nodes                 # Create node
GET    /api/v1/nodes/{id}            # Get node details
PATCH  /api/v1/nodes/{id}            # Update node
DELETE /api/v1/nodes/{id}            # Delete node

POST   /api/v1/nodes/{id}/messages   # Add message (triggers AI)
GET    /api/v1/nodes/{id}/messages   # Get all messages

POST   /api/v1/nodes/{id}/branch     # Create branch
POST   /api/v1/merge                 # Merge nodes
```

### **Database Tables:**

- `projects` (id, name, root_node_id, created_at)
- `nodes` (id, project_id, parent_id, title, node_type, position_x, position_y, context_summary, status, created_at)
- `messages` (id, node_id, role, content, timestamp)

### **AI Placeholders:**

```python
# llm_service.py
def chat_with_ai(node_id, message):
    return "Placeholder AI response"

def summarize_for_branch(parent_node_id):
    return "Placeholder summary"

def generate_merge_summary(source_node_id):
    return "Placeholder merge summary"
```

---

## Questions for You:

1. **Database**: SQLite OK? Or do you want Postgres?
2. **File structure**: Flat (simple) or organized (folders)?
3. **Testing**: Skip tests or create basic ones?
4. **Should we add WebSockets** for real-time chat streaming? (Or just HTTP polling?)
5. **Do we need user authentication?** (I assume no for hackathon)
