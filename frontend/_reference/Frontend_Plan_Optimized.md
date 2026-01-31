# Fractal Workspace - Frontend Implementation Guide

## 1. System Overview

**Core Concept:** Visual branching conversation system where each node = isolated AI context

**Tech Stack:**
- React 18 + TypeScript + Vite
- React Flow (canvas) + Zustand (state) + React Query (server state)
- Tailwind CSS + Shadcn/ui
- Framer Motion (animations)

**Key Insight:** NOT a chat app. A cognitive workspace where thoughts branch, merge, and evolve spatially.

---

## 2. Design System

### Colors
```css
/* Node States */
--active: #0EA5E9 (blue)
--frozen: #8B5CF6 (purple) 
--deleted: #EF4444 (red)
--ai: #10B981 (green)
--user: #F59E0B (orange)

/* Backgrounds */
--bg-canvas: #FAFAF9
--bg-node: #F5F5F4
--text-primary: #1C1917
```

### Typography
- Display: DM Sans (headings, node titles)
- Body: Inter (messages, UI text)
- Mono: JetBrains Mono (code, metadata)
- Sizes: 12px (labels) → 16px (body) → 18px (titles) → 24px (headers)

### Spacing
- Base unit: 8px
- Node size: 320px × 200px (collapsed), max 600px width
- Canvas grid: 24px snap

### Motion
- Fast: 150ms (hover, clicks)
- Base: 250ms (expand/collapse)
- Slow: 400ms (page transitions)
- Easing: cubic-bezier(0, 0, 0.2, 1)

---

## 3. Architecture

### File Structure
```
src/
├── components/
│   ├── nodes/CustomNode.tsx (header, body, footer)
│   ├── chat/ChatPanel.tsx (messages, input, typing)
│   ├── canvas/Canvas.tsx (React Flow wrapper)
│   ├── modals/BranchModal.tsx, MergeModal.tsx
│   └── layout/Toolbar.tsx, Sidebar.tsx, StatusBar.tsx
├── hooks/
│   ├── api/useNodes.ts, useMessages.ts, useMerge.ts
│   └── ui/useKeyboardShortcuts.ts
├── services/api/client.ts, nodesApi.ts
├── store/index.ts (Zustand)
├── types/node.types.ts, message.types.ts
└── styles/globals.css
```

### State Management

**Zustand Store:**
```typescript
{
  canvas: {
    nodes: Node<NodeData>[]  // React Flow nodes
    edges: Edge[]            // Connections
  },
  ui: {
    selectedNodeId: string | null
    expandedNodeId: string | null  // Only one open at a time
    highlightedPath: string[]      // Context lineage
    loading: { chat: Record<string, boolean> }
    toasts: Toast[]
  }
}
```

**React Query:** Handles all API calls (caching, optimistic updates, auto-refetch)

**Key Pattern:** Zustand = UI state, React Query = server state

---

## 4. Core Components

### CustomNode
```typescript
interface NodeData {
  title: string
  nodeType: 'root' | 'standard' | 'exploration'
  status: 'active' | 'frozen' | 'deleted'
  parentId: string | null
  messageCount: number
  tokenCount: number
  inheritedContext?: string  // Compressed parent summary
  lastActivity: string
}

// Structure:
<CustomNode>
  <NodeHeader title status messageCount />
  {expanded && <NodeBody nodeId inheritedContext />}
  <NodeFooter nodeId status />  // Branch, Merge, Summarize, Delete
</CustomNode>
```

**Visual States:**
- Active: Blue border
- Frozen: Purple border, faded, lock icon
- Deleted: Red border, strikethrough
- Selected: Glow shadow
- Hover: Elevated

### ChatPanel
```typescript
<ChatPanel nodeId>
  {inheritedContext && <ContextInheritance />}  // Shows parent summary
  <MessageList messages isAITyping />
  <MessageInput onSend disabled={isPending} />
</ChatPanel>
```

**Message Types:**
- user: Orange background
- assistant: Green background
- summary: Purple background (from merged branch)
- system: Gray (merge notifications)

### Canvas
```typescript
<ReactFlow
  nodes={zustandNodes}
  edges={zustandEdges}
  nodeTypes={{ custom: CustomNode }}
  onNodeClick={selectNode}
  onNodeDoubleClick={expandNode}
  fitView
>
  <Background />
  <Controls />
  <MiniMap />
  <ContextPathOverlay highlightedPath />
</ReactFlow>
```

---

## 5. User Flows

### Create Branch
```
1. Click "Branch" button → BranchModal opens
2. Enter title → Shows inherited context preview
3. Confirm → POST /nodes { parent_id, title, node_type }
4. Optimistic: Add temp node instantly
5. Backend responds → Replace with real node + edge
6. Auto-layout: Position below parent (offset by sibling count)
```

### Merge Branch
```
1. Click "Merge" → MergeModal opens
2. Select target (ancestor only, prevent cycles)
3. Preview → POST /nodes/merge/preview { source_id, target_id }
4. Show: Updated summary, conflicts, warning
5. Confirm → POST /nodes/merge
6. Update target node, freeze source, change edge to dashed purple
7. Add summary message in target chat
```

### Context Path
```
1. Click "Show Path" or press 'C'
2. Calculate lineage: getNodeLineage(nodeId) → [child, parent, ..., root]
3. Highlight: Nodes glow, edges pulse, others fade (opacity 0.3)
4. Auto-clear after 5s or click elsewhere
```

### Chat
```
1. Double-click node → Expand
2. Type message → Optimistic add to chat
3. POST /nodes/{id}/messages { content }
4. Show typing indicator (animated dots)
5. Backend returns AI response (2-10s)
6. Add assistant message, auto-scroll
```

---

## 6. Key Features

### Keyboard Shortcuts
```
Cmd+N: New branch from selected
Enter: Expand/collapse node
B: Branch, M: Merge, C: Context path, Delete: Delete node
Esc: Deselect, clear highlights
Space+Drag: Pan canvas
```

### Auto-Layout Algorithm
```typescript
calculateNodePosition(parentId) {
  if (!parentId) return { x: 400, y: 200 }  // Root center
  
  const parent = findNode(parentId)
  const siblings = findChildren(parentId)
  
  return {
    x: parent.x + (siblings.length * 350) - 175,  // Horizontal offset
    y: parent.y + 300  // Below parent
  }
}
```

### Context Assembly (Backend Logic, Frontend Needs to Understand)
```
Node chat context = 
  Inherited summary (from parent chain, compressed)
  + Current node summary (compressed state)
  + Last 10 messages
  + Optional: Knowledge graph facts
  
Frontend shows inherited context in collapsed panel at top of chat
```

### Search
```typescript
// Debounced search (300ms delay)
const { data: results } = useQuery({
  queryKey: ['search', debouncedQuery],
  queryFn: () => api.get('/search?q=' + query),
  enabled: query.length >= 2
})

// Results: nodes (title match) + messages (content match)
// Click result → Focus canvas on node + expand
```

---

## 7. Performance Optimizations

### React
```typescript
// Memoize expensive components
const NodeHeader = React.memo(({ title, status }) => ...)

// Selector optimization (only subscribe to needed data)
const messages = useStore(
  state => state.nodes.find(n => n.id === nodeId)?.messages,
  shallow
)

// Virtualize long lists
import { FixedSizeList } from 'react-window'
<FixedSizeList height={600} itemCount={messages.length} itemSize={80}>
  {MessageBubble}
</FixedSizeList>
```

### API
```typescript
// Optimistic updates
useMutation({
  mutationFn: createNode,
  onMutate: (newNode) => {
    addNode({ id: 'temp-' + Date.now(), ...newNode })  // Instant UI
    return { tempNode }
  },
  onError: (err, vars, context) => {
    removeNode(context.tempNode.id)  // Rollback
  },
  onSuccess: (realNode, vars, context) => {
    updateNode(context.tempNode.id, realNode)  // Replace
  }
})

// Batch requests
useBatchedSummaries = (nodeIds) => 
  useQuery(['summaries', nodeIds], () => 
    api.post('/summaries/batch', { nodeIds })
  )
```

---

## 8. Implementation Roadmap (48 Hours)

### Phase 1: Foundation (0-16h)
**H0-2:** Setup (Vite, deps, Tailwind, Shadcn)
**H2-4:** Types, API client, service methods
**H4-8:** Zustand store (all actions)
**H8-12:** Layout (Toolbar, Sidebar, Canvas skeleton)
**H12-16:** CustomNode (header, footer, collapsed state)

**Checkpoint:** Nodes render on canvas, selection works

### Phase 2: Core Features (16-32h)
**H16-20:** ChatPanel (messages, input, send API)
**H20-24:** Branch (modal, API, auto-layout, edges)
**H24-28:** Merge (preview, conflicts, freeze source)
**H28-32:** Context path (lineage calc, highlighting)

**Checkpoint:** Branch/merge/chat all working

### Phase 3: Polish (32-48h)
**H32-36:** Sidebar (tree view, search, click-to-focus)
**H36-40:** StatusBar, Toasts, keyboard shortcuts
**H40-44:** Animations (expand, messages, typing, path pulse)
**H44-48:** Bug fixes, error handling, demo prep

**Checkpoint:** Production-ready demo

---

## 9. Critical Path Test (5-Minute Demo)

```
✓ Create root "Neonatal Jaundice ML"
✓ Chat: "Should we use ML?"
✓ Branch "XGBoost Exploration"
✓ Chat in branch (different context)
✓ Branch "CNN Architecture"
✓ Merge XGBoost → Root
  → Summary message appears in root
  → Source frozen (purple, faded)
✓ Delete CNN branch
✓ Show context path (root → branch)
✓ Search for "XGBoost" → Finds node
```

If this works end-to-end, MVP is solid.

---

## 10. API Integration Patterns

### Create Node
```typescript
const { mutate: createNode } = useMutation({
  mutationFn: (data) => api.post('/nodes', data),
  onSuccess: (response) => {
    useStore.getState().addNode({
      id: response.node_id,
      type: 'custom',
      position: response.position,
      data: {
        title: response.title,
        status: response.status,
        parentId: response.parent_id,
        messageCount: 0,
        tokenCount: 0,
        inheritedContext: response.inherited_context,
        lastActivity: response.created_at
      }
    })
    
    // Add edge if has parent
    if (response.parent_id) {
      useStore.getState().addEdge({
        id: `${response.parent_id}-${response.node_id}`,
        source: response.parent_id,
        target: response.node_id,
        type: 'smoothstep',
        animated: true
      })
    }
  }
})
```

### Send Message
```typescript
const { mutate: sendMessage } = useMutation({
  mutationFn: ({ nodeId, content }) => 
    api.post(`/nodes/${nodeId}/messages`, { content }),
  onMutate: ({ nodeId, content }) => {
    // Optimistic: Add user message instantly
    const tempMsg = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    }
    useStore.getState().addMessage(nodeId, tempMsg)
    useStore.getState().setLoading('chat', nodeId, true)
  },
  onSuccess: (response, { nodeId }) => {
    // Add AI response
    useStore.getState().addMessage(nodeId, response)
    useStore.getState().setLoading('chat', nodeId, false)
  }
})
```

### Merge Nodes
```typescript
const { mutate: merge } = useMutation({
  mutationFn: ({ source_id, target_id }) => 
    api.post('/nodes/merge', { source_id, target_id }),
  onSuccess: (result) => {
    // Update target node
    useStore.getState().updateNode(result.target_node_id, {
      /* updated summary data */
    })
    
    // Freeze source
    useStore.getState().updateNode(result.source_node_id, {
      status: 'frozen'
    })
    
    // Update edge style
    useStore.getState().updateEdge(
      `${result.source_node_id}-${result.target_node_id}`,
      {
        type: 'merge',
        animated: false,
        style: { stroke: '#8B5CF6', strokeDasharray: '5,5' }
      }
    )
  }
})
```

---

## 11. Error Handling

```typescript
// Global error handler
apiClient.interceptors.response.use(
  response => response,
  error => {
    const message = 
      error.code === 'ERR_NETWORK' ? 'Network error. Check connection.' :
      error.response?.status === 404 ? 'Node not found.' :
      error.response?.status === 500 ? 'Server error. Try again.' :
      'Something went wrong.'
    
    useStore.getState().addToast({ type: 'error', message })
    return Promise.reject(error)
  }
)
```

**Empty States:**
- No nodes: "Create your first project node"
- No messages: "Start a conversation"
- No search results: "No matches for '{query}'"

**Edge Cases:**
- Prevent merge to self
- Prevent merge to descendant (creates cycle)
- Disable actions on frozen/deleted nodes
- Handle rapid API calls (debounce/throttle)

---

## 12. Animations

### Node Expand/Collapse
```typescript
<motion.div
  initial={{ height: 0, opacity: 0 }}
  animate={{ height: 'auto', opacity: 1 }}
  exit={{ height: 0, opacity: 0 }}
  transition={{ duration: 0.25 }}
>
  <ChatPanel />
</motion.div>
```

### Message Reveal (Staggered)
```typescript
<motion.div
  initial={{ opacity: 0, y: 10 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ delay: index * 0.05 }}
>
  <MessageBubble />
</motion.div>
```

### Typing Indicator
```css
.typing-dot {
  animation: bounce 0.6s infinite;
  animation-delay: calc(var(--i) * 0.15s);
}

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}
```

### Context Path Pulse
```css
.path-highlight {
  stroke: #6366F1;
  stroke-width: 4px;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; stroke-width: 3px; }
  50% { opacity: 1; stroke-width: 5px; }
}
```

---

## 13. Deployment

### Environment
```bash
# .env.local
VITE_API_URL=http://localhost:8000/api/v1
VITE_MAX_MESSAGE_LENGTH=5000
```

### Build
```bash
npm run build  # → dist/
```

### Deploy (Vercel)
```bash
vercel --prod
```

**vercel.json:**
```json
{
  "rewrites": [
    { "source": "/api/:path*", 
      "destination": "https://backend.railway.app/api/:path*" }
  ]
}
```

---

## 14. Quick Reference

### Must-Have Features (MVP)
- ✅ Create root node
- ✅ Chat with AI (context inheritance)
- ✅ Create branches
- ✅ Merge branches (with preview)
- ✅ Delete nodes (soft delete)
- ✅ Context path visualization
- ✅ Node tree sidebar
- ✅ Search nodes/messages

### Nice-to-Have (If Time)
- Knowledge graph visualization (Phase 2)
- Export project (JSON/Markdown)
- Undo/redo (Phase 3)
- Dark mode toggle
- Mobile responsive

### Dependencies
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "reactflow": "^11.10.0",
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0",
    "framer-motion": "^10.16.0",
    "lucide-react": "^0.300.0",
    "tailwindcss": "^3.3.0"
  }
}
```

### Zustand Actions Cheat Sheet
```typescript
addNode(node)
updateNode(id, data)
removeNode(id)
addEdge(edge)
updateEdge(id, data)
setSelectedNode(id)
toggleNodeExpanded(id)
setHighlightedPath(ids[])
addMessage(nodeId, message)
setLoading(type, nodeId, bool)
addToast({ type, message })
```

### React Query Hooks Pattern
```typescript
// Query (GET)
useQuery({ 
  queryKey: ['nodes'], 
  queryFn: () => api.get('/nodes/tree') 
})

// Mutation (POST/PUT/DELETE)
useMutation({
  mutationFn: (data) => api.post('/nodes', data),
  onMutate: () => { /* optimistic update */ },
  onSuccess: () => { /* update store */ },
  onError: () => { /* rollback */ }
})
```

---

## 15. Troubleshooting

**Nodes not appearing?**
→ Check API returns position {x, y}, Zustand has nodes array, React Flow nodeTypes registered

**Messages not sending?**
→ Check node status is 'active', API endpoint correct, network tab shows request

**Merge failing?**
→ Ensure target is ancestor, source is active, backend returns proper response

**Performance slow?**
→ Check for unnecessary re-renders (React DevTools), implement viewport rendering, memoize components

---

## 16. Summary

**What You're Building:**
A visual cognitive workspace where AI conversations branch like thoughts, maintain isolated contexts, and merge back intelligently.

**Core Technical Decisions:**
- React Flow: Best canvas library
- Zustand: Simple, fast state management
- React Query: Server state + caching + optimistic updates
- Tailwind: Rapid styling with design system

**Success Metrics:**
- 5-minute demo works flawlessly
- Smooth with 20+ nodes
- No crashes during presentation
- Visually polished and professional

**Remember:**
1. Start with Phase 1 foundation
2. Test each feature before moving on
3. Use optimistic updates for instant feedback
4. Handle errors gracefully
5. Focus on demo flow first

You're building something revolutionary. Make every pixel count. 🚀
