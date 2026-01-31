# The Fractal Workspace - Complete Frontend Design & Implementation Plan

**A Visual Multi-Agent Cognitive System**

---

## Executive Summary

This document provides a complete, production-ready frontend architecture for the Fractal Workspace - a revolutionary branching conversation system that externalizes human thought processes into a visual, manipulable interface.

**What you'll find here:**
- Complete visual design system
- Technical architecture with React Flow + Zustand + React Query
- Detailed component breakdown with code examples
- Step-by-step implementation roadmap (48 hours)
- User flows and interaction patterns
- Performance optimization strategies
- Quality assurance and testing guidelines

---

## Table of Contents
1. [Vision & Design Philosophy](#1-vision--design-philosophy)
2. [Core UX Principles](#2-core-ux-principles)
3. [Visual Design System](#3-visual-design-system)
4. [Technical Architecture](#4-technical-architecture)
5. [Component Architecture](#5-component-architecture)
6. [State Management Deep Dive](#6-state-management-deep-dive)
7. [User Flows & Interactions](#7-user-flows--interactions)
8. [Advanced Features](#8-advanced-features)
9. [Performance & Optimization](#9-performance--optimization)
10. [Implementation Roadmap](#10-implementation-roadmap)
11. [Quality Assurance](#11-quality-assurance)
12. [Deployment](#12-deployment)

---

## 1. Vision & Design Philosophy

### 1.1 What We're Building

**NOT a chat app with a tree view.**  
**YES: A cognitive workspace where thoughts branch, merge, and evolve visually.**

```
Traditional Chat:
┌─────────────────┐
│ Linear timeline │
│ Mixed contexts  │
│ Lost threads    │
└─────────────────┘

Fractal Workspace:
        ┌──────────┐
        │  Root    │
        │  Idea    │
        └────┬─────┘
     ┌───────┼───────┐
     │       │       │
  ┌──▼──┐ ┌─▼──┐ ┌─▼──┐
  │ CNN │ │ XGB│ │ RNN│
  └─────┘ └────┘ └────┘
     │
  ┌──▼─────────┐
  │ ResNet vs │
  │    VGG    │
  └───────────┘
```

### 1.2 Design Pillars

**Clarity Through Hierarchy**
- Each node's status immediately visible
- Context path traceable at a glance
- Relationships spatial, not textual

**Cognitive Fidelity**
- UI mirrors how humans think (branch, explore, merge)
- Transitions feel like mental state changes
- Information density matches cognitive load

**Trust Through Transparency**
- Show where context comes from (visual lineage)
- Make AI reasoning visible (summaries, confidence)
- Reveal system state (loading, processing, errors)

**Delight in Discovery**
- Encourage exploration through intuitive interactions
- Reward organization with visual feedback
- Make complex operations feel simple

### 1.3 Aesthetic Direction

**Theme: "Thought Architecture"**

**Conceptual Inspiration:**
- Architectural blueprints (precision, structure)
- Mind maps (organic branching)
- Circuit diagrams (connections, flow)
- Notebook sketches (personal, explorative)

**Visual Language:**
- **Minimalist base** with **purposeful complexity**
- Clean canvas that reveals depth on interaction
- Geometric precision for structure, organic curves for thought flow
- Restrained color palette with semantic accents

**NOT:**
- ❌ Generic SaaS dashboard (purple gradients everywhere)
- ❌ Overwhelming neon cyberpunk
- ❌ Sterile medical interface
- ❌ Playful consumer app

**YES:**
- ✅ Sophisticated creative tool (Figma + Linear + Notion blend)
- ✅ Professional but approachable
- ✅ Calm but engaging
- ✅ Spacious but information-rich

---

## 2. Core UX Principles

### 2.1 Progressive Disclosure

**Level 1: Overview (Collapsed Nodes)**
```
Show: Title, Status badge, Connection count, Token indicator
Hide: Chat content, Messages, Detailed status
```

**Level 2: Preview (Hover)**
```
Show: First message snippet, Last activity time, Context source
Action: Tooltip with summary
```

**Level 3: Focus (Expanded Node)**
```
Show: Full chat history, Input field, Action buttons, Inherited context
Action: Chat interactions, Branch/Merge controls
```

**Level 4: Deep Context (Context Path Mode)**
```
Show: Highlighted lineage, Summary cascade, Knowledge graph connections
Action: Visual trace of information flow
```

### 2.2 Direct Manipulation

**Core Interactions:**
- **Click node** → Select (show details in sidebar)
- **Double-click node** → Expand (open chat)
- **Drag node** → Reposition on canvas
- **Drag from node edge** → Quick branch (Figma-style)
- **Right-click node** → Context menu (branch, merge, delete, freeze)
- **Shift + Click multiple nodes** → Multi-select for batch operations

**Visual Feedback:**
- Hover state: Subtle elevation, border glow
- Drag state: Semi-transparent, snap guides
- Loading state: Pulsing border, internal progress
- Error state: Red border flash, shake animation

### 2.3 Context Awareness

**The system should always answer:**
- "Where am I?" → Highlighted node, breadcrumb trail
- "What can I do here?" → Contextual actions in footer
- "What's happening?" → Status indicators, loading states
- "What came before?" → Visual lineage, inherited context panel
- "What's next?" → Suggested branches, open questions

---

## 3. Visual Design System

### 3.1 Color System

```css
:root {
  /* Neutrals - Warm Gray Base */
  --color-bg-primary: #FAFAF9;     /* Canvas background */
  --color-bg-secondary: #F5F5F4;   /* Node background */
  --color-bg-tertiary: #E7E5E4;    /* Hover states */
  
  --color-text-primary: #1C1917;   /* Headings */
  --color-text-secondary: #57534E; /* Body text */
  --color-text-tertiary: #A8A29E;  /* Subtle text */
  
  --color-border: #D6D3D1;         /* Default borders */
  --color-border-focus: #78716C;   /* Focus states */
  
  /* Semantic Colors */
  --color-active: #0EA5E9;         /* Active nodes */
  --color-active-hover: #0284C7;
  --color-active-bg: #E0F2FE;
  
  --color-frozen: #8B5CF6;         /* Merged/frozen */
  --color-frozen-bg: #EDE9FE;
  
  --color-deleted: #EF4444;        /* Deleted/error */
  --color-deleted-bg: #FEE2E2;
  
  --color-ai: #10B981;             /* AI responses */
  --color-ai-bg: #D1FAE5;
  
  --color-user: #F59E0B;           /* User messages */
  --color-user-bg: #FEF3C7;
  
  /* Accent Colors */
  --color-accent-1: #EC4899;       /* Knowledge graph */
  --color-accent-2: #6366F1;       /* Context path */
  --color-accent-3: #14B8A6;       /* Success states */
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.08);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1);
}
```

### 3.2 Typography

```css
:root {
  /* Font Families */
  --font-display: 'DM Sans', 'Inter', -apple-system, sans-serif;
  --font-body: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  /* Sizes */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  
  /* Weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
}
```

### 3.3 Spacing & Layout

```css
:root {
  /* 8px Base Unit */
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-5: 1.5rem;   /* 24px */
  --space-6: 2rem;     /* 32px */
  --space-8: 3rem;     /* 48px */
  --space-10: 4rem;    /* 64px */
}
```

**Layout Grid:**
- Canvas: Dot grid (4px dots, 24px spacing)
- Snap grid: 24px × 24px
- Node min size: 320px × 200px
- Node max width: 600px
- Sidebar width: 280px (collapsed), 360px (expanded)

### 3.4 Motion Design

```css
:root {
  /* Timing Functions */
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Durations */
  --duration-fast: 150ms;
  --duration-base: 250ms;
  --duration-slow: 400ms;
}
```

**Key Animations:**
- Node expand/collapse: 250ms ease-out
- Message reveal: Staggered 50ms delays
- Context path pulse: 1.5s infinite
- Typing indicator: Bounce animation

---

## 4. Technical Architecture

### 4.1 Tech Stack

```
Build Tool: Vite 5.0
Framework: React 18 + TypeScript 5.3
State: Zustand 4.4 (global) + React Query (server state)
Canvas: React Flow 11.10
Styling: Tailwind CSS 3.4
UI Components: Shadcn/ui
Icons: Lucide React
HTTP: Axios + React Query
Animations: Framer Motion (selective)
```

### 4.2 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   └── AppProviders.tsx
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── Toolbar/
│   │   │   ├── Sidebar/
│   │   │   └── StatusBar/
│   │   │
│   │   ├── canvas/
│   │   │   ├── Canvas.tsx
│   │   │   ├── CanvasControls.tsx
│   │   │   └── ContextPathOverlay.tsx
│   │   │
│   │   ├── nodes/
│   │   │   ├── CustomNode/
│   │   │   │   ├── CustomNode.tsx
│   │   │   │   ├── NodeHeader.tsx
│   │   │   │   ├── NodeBody.tsx
│   │   │   │   └── NodeFooter.tsx
│   │   │
│   │   ├── chat/
│   │   │   ├── ChatPanel/
│   │   │   ├── Message/
│   │   │   └── TypingIndicator.tsx
│   │   │
│   │   ├── modals/
│   │   │   ├── BranchModal/
│   │   │   ├── MergeModal/
│   │   │   └── DeleteConfirmModal.tsx
│   │   │
│   │   └── visualization/
│   │       ├── CustomEdge/
│   │       └── KnowledgeGraph/
│   │
│   ├── hooks/
│   │   ├── api/
│   │   │   ├── useNodes.ts
│   │   │   ├── useMessages.ts
│   │   │   └── useMerge.ts
│   │   │
│   │   ├── canvas/
│   │   │   └── useNodeLayout.ts
│   │   │
│   │   └── ui/
│   │       └── useKeyboardShortcuts.ts
│   │
│   ├── services/
│   │   └── api/
│   │       ├── client.ts
│   │       └── nodesApi.ts
│   │
│   ├── store/
│   │   ├── index.ts
│   │   └── types.ts
│   │
│   ├── types/
│   │   ├── node.types.ts
│   │   ├── message.types.ts
│   │   └── api.types.ts
│   │
│   └── styles/
│       ├── globals.css
│       └── animations.css
```

### 4.3 Why React Query?

**Benefits:**
- Automatic caching (fetch once, use everywhere)
- Smart refetching (on focus, mount, interval)
- Built-in loading/error states
- Optimistic updates (instant UI feedback)
- Background updates

**Example:**
```typescript
// Without React Query - Complex
const [data, setData] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

useEffect(() => {
  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await api.get('/nodes');
      setData(response.data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };
  fetchData();
}, []);

// With React Query - Simple
const { data, isLoading, error } = useQuery({
  queryKey: ['nodes'],
  queryFn: () => api.get('/nodes'),
});
```

---

## 5. Component Architecture

### 5.1 Node Component (Core)

```typescript
// CustomNode.tsx
interface NodeData {
  title: string;
  nodeType: 'root' | 'standard' | 'exploration';
  status: 'active' | 'frozen' | 'deleted';
  parentId: string | null;
  messageCount: number;
  tokenCount: number;
  inheritedContext?: string;
  lastActivity: string;
}

const CustomNode: React.FC<NodeProps<NodeData>> = ({ id, data, selected }) => {
  const isExpanded = useStore(state => state.ui.expandedNodeId === id);
  
  return (
    <div className={cn(
      "custom-node",
      selected && "node-selected",
      data.status === 'frozen' && "node-frozen"
    )}>
      <NodeHeader 
        title={data.title}
        status={data.status}
        messageCount={data.messageCount}
      />
      
      {isExpanded && (
        <NodeBody nodeId={id} />
      )}
      
      <NodeFooter nodeId={id} status={data.status} />
    </div>
  );
};
```

### 5.2 Chat Panel Component

```typescript
const ChatPanel: React.FC<{ nodeId: string }> = ({ nodeId }) => {
  const { data: messages, isLoading } = useMessages(nodeId);
  const { mutate: sendMessage, isPending } = useSendMessage(nodeId);
  const isAITyping = useStore(state => state.ui.loading.chat[nodeId]);

  return (
    <div className="chat-panel">
      <MessageList 
        messages={messages || []}
        isAITyping={isAITyping}
      />
      
      <MessageInput 
        onSend={(content) => sendMessage({ content })}
        disabled={isPending}
      />
    </div>
  );
};
```

### 5.3 Canvas Component

```typescript
const Canvas: React.FC = () => {
  const nodes = useStore(state => state.canvas.nodes);
  const edges = useStore(state => state.canvas.edges);

  const onNodeClick = useCallback((event, node) => {
    useStore.getState().setSelectedNode(node.id);
  }, []);

  const onNodeDoubleClick = useCallback((event, node) => {
    useStore.getState().toggleNodeExpanded(node.id);
  }, []);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={{ custom: CustomNode }}
      onNodeClick={onNodeClick}
      onNodeDoubleClick={onNodeDoubleClick}
      fitView
    >
      <Background />
      <Controls />
      <MiniMap />
    </ReactFlow>
  );
};
```

---

## 6. State Management Deep Dive

### 6.1 Zustand Store

```typescript
interface AppState {
  // Canvas
  canvas: {
    nodes: Node<NodeData>[];
    edges: Edge[];
  };
  
  // UI
  ui: {
    selectedNodeId: string | null;
    expandedNodeId: string | null;
    highlightedPath: string[];
    loading: {
      chat: Record<string, boolean>;
    };
    toasts: Toast[];
  };
  
  // Actions
  addNode: (node: Node<NodeData>) => void;
  updateNode: (nodeId: string, data: Partial<NodeData>) => void;
  setSelectedNode: (nodeId: string | null) => void;
  toggleNodeExpanded: (nodeId: string) => void;
  addToast: (toast: Omit<Toast, 'id'>) => void;
}

const useStore = create<AppState>((set) => ({
  canvas: { nodes: [], edges: [] },
  ui: {
    selectedNodeId: null,
    expandedNodeId: null,
    highlightedPath: [],
    loading: { chat: {} },
    toasts: [],
  },
  
  addNode: (node) => set((state) => ({
    canvas: {
      ...state.canvas,
      nodes: [...state.canvas.nodes, node],
    },
  })),
  
  toggleNodeExpanded: (nodeId) => set((state) => ({
    ui: {
      ...state.ui,
      expandedNodeId: state.ui.expandedNodeId === nodeId ? null : nodeId,
    },
  })),
  
  // More actions...
}));
```

### 6.2 React Query Hooks

```typescript
// useNodes.ts
export const useCreateNode = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateNodeRequest) => {
      const response = await nodesApi.createNode(data);
      return response;
    },
    onSuccess: (newNode) => {
      useStore.getState().addNode({
        id: newNode.node_id,
        type: 'custom',
        position: newNode.position,
        data: { /* ... */ },
      });
      
      queryClient.invalidateQueries({ queryKey: ['nodes'] });
    },
  });
};
```

---

## 7. User Flows & Interactions

### 7.1 Create Branch Flow

```
1. User clicks "Branch" button in node footer
   └─> BranchModal opens

2. User enters title: "XGBoost Exploration"
   └─> Preview shows inherited context from parent

3. User clicks "Create"
   ├─> Frontend: Optimistic update (node appears instantly)
   ├─> Backend: Creates node, generates inherited context
   └─> Frontend: Updates with real data

4. New node appears below parent
   ├─> Edge connects parent → child
   ├─> Auto-layout positions node
   └─> Success toast appears
```

### 7.2 Merge Branch Flow

```
1. User clicks "Merge" in branch node
   └─> MergeModal opens

2. User selects target (parent node)
   └─> Preview API called

3. Preview shows:
   ├─> Updated summary
   ├─> Conflicts (if any)
   └─> Warning: "Source will be frozen"

4. User confirms merge
   ├─> Backend: Merges summaries, combines graphs
   ├─> Frontend: Updates target, freezes source
   ├─> Edge changes to dashed purple
   └─> Summary message appears in target chat
```

### 7.3 Context Path Visualization

```
1. User clicks "Show Context Path" on a node
   OR presses 'C' key

2. System calculates lineage
   └─> [child, parent, grandparent, ..., root]

3. Visual updates:
   ├─> Highlighted nodes: Glow border, elevated
   ├─> Highlighted edges: Thicker, pulsing
   └─> Other elements: Faded (opacity 0.3)

4. Auto-clears after 5 seconds
   OR user clicks elsewhere
```

---

## 8. Advanced Features

### 8.1 Keyboard Shortcuts

```
Global:
  Cmd/Ctrl + N    New branch from selected
  Cmd/Ctrl + F    Focus search
  ?               Show help

Node Selected:
  Enter           Expand/collapse
  B               Branch from this
  M               Merge this
  C               Show context path
  Delete          Delete node
  Esc             Deselect

Canvas:
  Space + Drag    Pan
  Scroll          Zoom
  Cmd/Ctrl + 0    Fit view
```

### 8.2 Search Functionality

```typescript
const SearchPanel: React.FC = () => {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);

  const { data: results } = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => api.search(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  return (
    <div className="search-panel">
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search nodes and messages..."
      />
      
      <SearchResults results={results} />
    </div>
  );
};
```

### 8.3 Knowledge Graph Visualization (Phase 2)

```typescript
const KnowledgeGraphPanel: React.FC<{ nodeId: string }> = ({ nodeId }) => {
  const { data: graphData } = useKnowledgeGraph(nodeId);

  return (
    <div className="graph-panel">
      <GraphVisualization data={graphData} />
    </div>
  );
};
```

---

## 9. Performance & Optimization

### 9.1 React Optimization

```typescript
// Component memoization
const NodeHeader = React.memo<NodeHeaderProps>(({ title, status }) => {
  return <div>{/* ... */}</div>;
});

// Selector optimization
const messages = useStore(
  useCallback(
    state => state.nodes.find(n => n.id === nodeId)?.messages || [],
    [nodeId]
  ),
  shallow
);

// Virtualized lists for long message history
import { FixedSizeList } from 'react-window';

const MessageList = ({ messages }) => (
  <FixedSizeList
    height={600}
    itemCount={messages.length}
    itemSize={80}
  >
    {({ index, style }) => (
      <div style={style}>
        <MessageBubble message={messages[index]} />
      </div>
    )}
  </FixedSizeList>
);
```

### 9.2 API Optimization

```typescript
// Debounced search
const debouncedQuery = useDebounce(query, 500);

// Request batching
const useBatchedSummaries = (nodeIds: string[]) => {
  return useQuery({
    queryKey: ['summaries', nodeIds],
    queryFn: () => api.post('/summaries/batch', { nodeIds }),
  });
};

// Optimistic updates
const { mutate } = useMutation({
  mutationFn: createNode,
  onMutate: async (newNode) => {
    // Add to UI immediately
    const tempNode = { id: 'temp-' + Date.now(), ...newNode };
    addNode(tempNode);
    return { tempNode };
  },
  onError: (err, variables, context) => {
    // Rollback on error
    removeNode(context.tempNode.id);
  },
});
```

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Hours 0-16)

**Hour 0-2: Setup**
```bash
npm create vite@latest fractal-workspace -- --template react-ts
npm install reactflow zustand @tanstack/react-query axios
npx shadcn-ui@latest init
```

**Hour 2-4: Types & API**
- Define all TypeScript interfaces
- Set up Axios client
- Create API service methods

**Hour 4-8: Zustand Store**
- Create store with canvas & UI state
- Implement all actions
- Add devtools

**Hour 8-12: Basic Layout**
- AppLayout component
- Toolbar (static)
- Sidebar (static)
- Canvas (empty React Flow)

**Hour 12-16: Node Component**
- CustomNode with header/body/footer
- Node selection
- Hover states

**Deliverable:** App loads, nodes render on canvas

---

### Phase 2: Core Features (Hours 16-32)

**Hour 16-20: Chat Interface**
- ChatPanel component
- MessageList with bubbles
- MessageInput with send
- API integration

**Hour 20-24: Branch Creation**
- BranchModal UI
- Branch API integration
- Auto-layout positioning
- Edge creation

**Hour 24-28: Merge Functionality**
- MergeModal with preview
- Target selection
- Conflict display
- Source node freezing

**Hour 28-32: Context Path**
- Lineage calculation
- Path highlighting
- Visual animations

**Deliverable:** Can branch, merge, visualize context

---

### Phase 3: Polish (Hours 32-48)

**Hour 32-36: Sidebar**
- Tree view with expand/collapse
- Search panel
- Click to focus on canvas

**Hour 36-40: Status Bar & Notifications**
- Statistics display
- Toast system
- Connection status

**Hour 40-44: Animations**
- Node expand/collapse
- Message reveals
- Typing indicator
- Context path pulse

**Hour 44-48: Final Polish**
- Bug fixes
- Error handling
- Performance optimization
- Demo preparation

**Deliverable:** Production-ready demo

---

## 11. Quality Assurance

### 11.1 Critical Path Test (5 Minutes)

```
✅ Create root "Neonatal Jaundice ML"
✅ Chat: "Should we use ML?"
✅ Branch "XGBoost Exploration"
✅ Chat in branch
✅ Branch "CNN Architecture"
✅ Merge XGBoost → Root
✅ Verify summary appears
✅ Delete CNN branch
✅ Show context path
✅ Search functionality

If this works, core is solid.
```

### 11.2 Edge Cases

```
❌ Delete node with children
❌ Merge to self
❌ Network failure during chat
❌ Multiple nodes expanded
❌ Very long messages
❌ Rapid branch creation
```

### 11.3 Error Handling

```typescript
const handleApiError = (error: AxiosError) => {
  if (error.code === 'ERR_NETWORK') {
    addToast({ type: 'error', message: 'Network error' });
  } else if (error.response?.status === 404) {
    addToast({ type: 'error', message: 'Node not found' });
  } else {
    addToast({ type: 'error', message: 'Something went wrong' });
  }
};
```

---

## 12. Deployment

### 12.1 Environment Variables

```bash
# .env.example
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Fractal Workspace
VITE_MAX_MESSAGE_LENGTH=5000
```

### 12.2 Build Configuration

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

### 12.3 Deploy to Vercel

```bash
npm i -g vercel
vercel --prod
```

---

## 13. Summary

### What Makes This Special

**1. Cognitive Fidelity**
- UI mirrors human thought (branch, explore, merge)
- Visual hierarchy shows information flow

**2. Direct Manipulation**
- Drag-and-drop interactions
- Visual context tracing

**3. Trust Through Transparency**
- Shows inherited context
- Displays merge conflicts
- Reveals AI processing

**4. Performance-First**
- Optimistic updates (instant feedback)
- Smart caching
- Minimal re-renders

---

## Quick Start

```bash
# Clone and install
git clone <repo-url>
cd fractal-workspace-frontend
npm install

# Set up environment
cp .env.example .env.local

# Start development
npm run dev
```

---

## Final Checklist

**Pre-Hackathon:**
- [ ] Read this entire document
- [ ] Set up dev environment
- [ ] Test API connection
- [ ] Review React Flow docs

**Hackathon Day 1:**
- [ ] Phase 1 complete (Hours 0-16)
- [ ] Nodes render and interact

**Hackathon Day 2:**
- [ ] Phase 2 complete (Hours 16-32)
- [ ] Branch and merge work

**Hackathon Day 3:**
- [ ] Phase 3 complete (Hours 32-48)
- [ ] Demo ready to present

---

## You're Ready! 🚀

This plan gives you everything needed to build a revolutionary cognitive workspace. Focus on the demo flow, communicate with your team, and make it count.

**Good luck!** 🎯
