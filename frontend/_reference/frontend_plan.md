# Final Frontend Plan - Complete Specification

---

## 1. PROJECT SETUP

### Tech Stack (Finalized)

```
Build Tool: Vite
Framework: React 18 + TypeScript
State Management: Zustand
Canvas: React Flow
Styling: Tailwind CSS
UI Components: Shadcn/ui
Icons: Lucide React (comes with Shadcn)
HTTP Client: Axios
```

### Dependencies List

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "reactflow": "^11.10.0",
    "zustand": "^4.4.0",
    "axios": "^1.6.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-toast": "^1.1.5",
    "@radix-ui/react-tooltip": "^1.0.7",
    "lucide-react": "^0.300.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

### Initial Commands

```bash
npm create vite@latest fractal-workspace-frontend -- --template react-ts
cd fractal-workspace-frontend
npm install
npm install reactflow zustand axios lucide-react clsx tailwind-merge
npx shadcn-ui@latest init
```

### Shadcn Components to Install

```bash
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add tooltip
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add card
npx shadcn-ui@latest add badge
```

---

## 2. STATE MANAGEMENT EXPLAINED

### Why We Need Zustand

**The Problem Without State Management:**

```
Scenario: User clicks "Branch" in Node A
├─ Canvas.tsx needs to know about new node
├─ Sidebar.tsx needs to update node list
├─ StatusBar.tsx needs to update node count
└─ Toolbar.tsx needs to refresh

Without Zustand:
- Pass props through 5+ components (prop drilling)
- Or use React Context (re-renders everything)
- Or make API calls from every component (wasteful)

With Zustand:
- One global store
- Components subscribe to only what they need
- No prop drilling
- Minimal re-renders
```

### State Structure (Complete)

```typescript
{
  // ============ PROJECT STATE ============
  project: {
    id: string;
    name: string;
    rootNodeId: string;
    createdAt: string;
  } | null;

  // ============ NODES STATE ============
  nodes: [
    {
      id: string;                    // "node-1"
      type: string;                  // "custom" (for React Flow)
      position: { x: number; y: number };
      data: {
        title: string;               // "XGBoost Exploration"
        nodeType: 'root' | 'branch' | 'merged';
        parentId: string | null;     // Parent node ID
        messages: Message[];         // All chat messages
        contextSummary: string;      // AI-generated summary from parent
        status: 'active' | 'merged' | 'archived';
        tokenCount: number;          // Total tokens used
        createdAt: string;
      }
    }
  ];

  // ============ EDGES STATE ============
  edges: [
    {
      id: string;                    // "edge-node1-node2"
      source: string;                // "node-1" (parent)
      target: string;                // "node-2" (child)
      type: 'smoothstep';
      animated: boolean;             // true for active inheritance
      style: { stroke: string };     // Blue for inherit, green for merge
      data: {
        edgeType: 'inherit' | 'merge';
      }
    }
  ];

  // ============ UI STATE ============
  ui: {
    selectedNodeId: string | null;   // Currently selected node
    expandedNodeId: string | null;   // Node with chat panel open
    highlightedPath: string[];       // IDs of nodes in context path

    // Modal states
    isBranchModalOpen: boolean;
    branchModalParentId: string | null;

    isMergeModalOpen: boolean;
    mergeModalSourceId: string | null;
    mergeModalTargetId: string | null;

    // Loading states
    isLoadingChat: Record<string, boolean>;  // { "node-1": true }
    isLoadingBranch: boolean;
    isLoadingMerge: boolean;

    // Error states
    error: string | null;

    // Toast notifications
    toasts: Array<{ id: string; message: string; type: 'success' | 'error' }>;
  };

  // ============ CANVAS STATE ============
  canvas: {
    zoom: number;
    viewport: { x: number; y: number; zoom: number };
  };
}
```

### Why Each Piece of State Exists

**`project`**:

- Needed for: Project name in toolbar, project ID for API calls
- Used by: Toolbar, Sidebar, API service

**`nodes`**:

- Needed for: Rendering on canvas, displaying in sidebar
- Used by: Canvas, Sidebar, NodeComponent, ChatPanel

**`edges`**:

- Needed for: Visual connections between nodes
- Used by: Canvas, ContextPathHighlight

**`ui.selectedNodeId`**:

- Needed for: Highlighting selected node, showing node details
- Used by: Canvas, Sidebar, NodeComponent

**`ui.expandedNodeId`**:

- Needed for: Only one chat panel open at a time
- Used by: NodeComponent (to show/hide chat)

**`ui.highlightedPath`**:

- Needed for: Visual context path feature
- Used by: Canvas (to style highlighted nodes/edges)

**`ui.isLoadingChat`**:

- Needed for: Show typing indicator per node
- Used by: ChatPanel (specific node's loading state)

**`ui.toasts`**:

- Needed for: Show success/error messages
- Used by: Toast component

### How Components Use State

**Example 1: ChatPanel component**

```
ChatPanel needs:
1. Messages for this node → useStore(state => state.nodes.find(...).data.messages)
2. Is AI responding? → useStore(state => state.ui.isLoadingChat[nodeId])
3. Send message action → useStore(state => state.sendMessage)

ChatPanel subscribes only to:
- This specific node's messages
- This specific node's loading state
- NOT the entire store

Result: ChatPanel only re-renders when ITS data changes
```

**Example 2: Canvas component**

```
Canvas needs:
1. All nodes → useStore(state => state.nodes)
2. All edges → useStore(state => state.edges)
3. Highlighted path → useStore(state => state.ui.highlightedPath)

Canvas subscribes to:
- All nodes (needs to render all)
- All edges (needs to render all)
- Highlighted path (for styling)

Result: Canvas re-renders when nodes/edges change (expected)
```

### Store Organization (File Split)

**Why split the store:**

- One giant file = 1000+ lines, hard to maintain
- Logical separation = easier to find code

**File structure:**

```
store/
├── index.ts           // Combine all slices
├── projectSlice.ts    // Project-level state & actions
├── nodesSlice.ts      // Nodes & edges state & actions
├── uiSlice.ts         // UI state & actions
└── types.ts           // TypeScript interfaces
```

**How slices work:**

```typescript
// Each slice is a function that returns state + actions
const createProjectSlice = (set, get) => ({
  project: null,
  initProject: (name) => {
    /* ... */
  },
  loadProject: (id) => {
    /* ... */
  },
});

// Combined in index.ts
const useStore = create((...a) => ({
  ...createProjectSlice(...a),
  ...createNodesSlice(...a),
  ...createUiSlice(...a),
}));
```

---

## 3. FOLDER STRUCTURE (Final)

```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx          // Main wrapper with Toolbar + Sidebar + Canvas
│   │   │   ├── Toolbar.tsx            // Top bar (project name, create root, export)
│   │   │   ├── Sidebar.tsx            // Left panel (node list, search)
│   │   │   └── StatusBar.tsx          // Bottom bar (token count, status)
│   │   │
│   │   ├── canvas/
│   │   │   ├── Canvas.tsx             // React Flow wrapper
│   │   │   └── CustomBackground.tsx   // Custom grid pattern
│   │   │
│   │   ├── nodes/
│   │   │   ├── CustomNode.tsx         // Main node component (handles all types)
│   │   │   ├── NodeHeader.tsx         // Title, icon, collapse button
│   │   │   ├── NodeBody.tsx           // Chat panel container
│   │   │   ├── NodeFooter.tsx         // Action buttons
│   │   │   └── NodeBadge.tsx          // Status badge (active/merged/etc)
│   │   │
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx          // Main chat container
│   │   │   ├── MessageList.tsx        // Scrollable messages
│   │   │   ├── MessageBubble.tsx      // Single message (user/ai/merged)
│   │   │   ├── MessageInput.tsx       // Input + send button
│   │   │   ├── TypingIndicator.tsx    // Animated "AI is typing..."
│   │   │   └── ContextInfo.tsx        // Shows inherited context
│   │   │
│   │   ├── modals/
│   │   │   ├── BranchModal.tsx        // Dialog to create branch
│   │   │   ├── MergePreviewModal.tsx  // Preview merge before confirming
│   │   │   └── ConfirmDialog.tsx      // Generic confirmation
│   │   │
│   │   ├── visualization/
│   │   │   ├── CustomEdge.tsx         // Styled edge component
│   │   │   └── ContextPathOverlay.tsx // Highlights context path
│   │   │
│   │   └── ui/                        // Shadcn components
│   │       ├── button.tsx
│   │       ├── dialog.tsx
│   │       ├── toast.tsx
│   │       ├── tooltip.tsx
│   │       ├── input.tsx
│   │       └── ...
│   │
│   ├── hooks/
│   │   ├── useProject.ts              // Project operations
│   │   ├── useNodes.ts                // Node CRUD operations
│   │   ├── useChat.ts                 // Chat functionality
│   │   ├── useBranch.ts               // Branch creation
│   │   ├── useMerge.ts                // Merge operations
│   │   └── useReactFlow.ts            // Canvas helpers (zoom, fit view)
│   │
│   ├── services/
│   │   └── api.ts                     // All backend API calls
│   │
│   ├── store/
│   │   ├── index.ts                   // Combined store
│   │   ├── projectSlice.ts            // Project state
│   │   ├── nodesSlice.ts              // Nodes & edges
│   │   ├── uiSlice.ts                 // UI state
│   │   └── types.ts                   // Store types
│   │
│   ├── types/
│   │   ├── project.ts                 // Project interfaces
│   │   ├── node.ts                    // Node interfaces
│   │   ├── message.ts                 // Message interfaces
│   │   └── api.ts                     // API request/response types
│   │
│   ├── utils/
│   │   ├── formatters.ts              // Format dates, text, etc.
│   │   ├── validators.ts              // Input validation
│   │   ├── canvas.ts                  // Node positioning logic
│   │   └── constants.ts               // Constants & enums
│   │
│   ├── lib/
│   │   └── utils.ts                   // Tailwind merge utility (from Shadcn)
│   │
│   ├── App.tsx                        // Root component
│   ├── main.tsx                       // Entry point
│   └── index.css                      // Global styles + Tailwind imports
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── components.json                    // Shadcn config
```

---

## 4. TAILWIND CSS CONFIGURATION

### Design System

**Colors:**

```javascript
// tailwind.config.js
colors: {
  // Node types
  'node-root': '#3b82f6',      // Blue
  'node-branch': '#8b5cf6',    // Purple
  'node-merged': '#6b7280',    // Gray

  // Message types
  'msg-user': '#3b82f6',       // Blue
  'msg-ai': '#f3f4f6',         // Light gray
  'msg-merged': '#fef3c7',     // Yellow tint

  // Edge types
  'edge-inherit': '#3b82f6',   // Blue
  'edge-merge': '#10b981',     // Green

  // Status
  'status-active': '#10b981',  // Green
  'status-loading': '#f59e0b', // Amber
  'status-error': '#ef4444',   // Red
}
```

**Spacing:**

```javascript
spacing: {
  'node-padding': '16px',
  'chat-height': '500px',
  'chat-width': '400px',
  'sidebar-width': '280px',
  'toolbar-height': '64px',
}
```

**Typography:**

```javascript
fontFamily: {
  sans: ['Inter', 'system-ui', 'sans-serif'],
  mono: ['Fira Code', 'monospace'],
}
fontSize: {
  'node-title': '16px',
  'message': '14px',
  'timestamp': '12px',
}
```

**Custom Utilities:**

```javascript
// Add to Tailwind config
extend: {
  animation: {
    'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
    'slide-up': 'slideUp 0.3s ease-out',
  },
  keyframes: {
    slideUp: {
      '0%': { transform: 'translateY(10px)', opacity: 0 },
      '100%': { transform: 'translateY(0)', opacity: 1 },
    }
  }
}
```

### Component Styling Standards

**Node Components:**

- Border radius: `rounded-lg` (8px)
- Shadow: `shadow-lg` for expanded, `shadow-md` for collapsed
- Hover: `hover:shadow-xl transition-shadow`
- Border: `border-2` with type-specific color

**Chat Messages:**

- User: `bg-blue-500 text-white rounded-2xl rounded-tr-sm`
- AI: `bg-gray-100 text-gray-900 rounded-2xl rounded-tl-sm`
- Padding: `px-4 py-2`
- Max width: `max-w-[80%]`

**Buttons:**

- Primary: `bg-blue-500 hover:bg-blue-600 text-white`
- Secondary: `bg-gray-200 hover:bg-gray-300 text-gray-900`
- Danger: `bg-red-500 hover:bg-red-600 text-white`
- Size: `px-4 py-2 rounded-md`

**Input Fields:**

- Border: `border-2 border-gray-300 focus:border-blue-500`
- Padding: `px-3 py-2`
- Rounded: `rounded-md`

---

## 5. SHADCN/UI INTEGRATION

### Which Components We Use

**Dialog (for modals):**

- BranchModal
- MergePreviewModal
- ConfirmDialog

**Toast (for notifications):**

- Success messages
- Error messages
- Info messages

**Tooltip (for help text):**

- Button explanations
- Icon meanings
- Feature hints

**Button (for all buttons):**

- Consistent styling
- Variants: default, destructive, outline, ghost

**Input (for text inputs):**

- Branch name input
- Search input in sidebar

**Card (for layouts):**

- Node containers
- Sidebar sections

**Badge (for status indicators):**

- Node status (active/merged)
- Token count display

### Customization

**Override Shadcn defaults in `globals.css`:**

```css
@layer base {
  :root {
    --radius: 0.5rem; /* Consistent border radius */
  }
}

@layer components {
  /* Make dialogs wider for merge preview */
  [data-dialog-content] {
    @apply max-w-2xl;
  }

  /* Custom toast positioning */
  [data-toast-viewport] {
    @apply bottom-20; /* Above status bar */
  }
}
```

---

## 6. REACT FLOW CONFIGURATION

### Canvas Settings

```typescript
const defaultViewport = { x: 0, y: 0, zoom: 1 };
const minZoom = 0.5;
const maxZoom = 2;

const proOptions = { hideAttribution: true }; // Remove React Flow watermark

const nodeTypes = {
  custom: CustomNode, // Our custom node component
};

const edgeTypes = {
  custom: CustomEdge, // Our custom edge component
};
```

### Node Positioning Strategy

**Auto-layout algorithm:**

```
Root Node: Center of canvas (x: 400, y: 100)

First child:
  x: parent.x
  y: parent.y + 350

Subsequent children:
  x: parent.x + (childIndex * 300) - (totalChildren * 150)
  y: parent.y + 350

Example with 3 children:
Parent (400, 100)
├─ Child 1 (250, 450)  // 400 + (0 * 300) - (3 * 150)
├─ Child 2 (550, 450)  // 400 + (1 * 300) - (3 * 150)
└─ Child 3 (850, 450)  // 400 + (2 * 300) - (3 * 150)
```

### Node Sizes

```typescript
const NODE_SIZES = {
  collapsed: { width: 250, height: 80 },
  expanded: { width: 450, height: 600 },
};
```

### Edge Styling

```typescript
// Inheritance edge (parent → child)
{
  type: 'smoothstep',
  animated: true,
  style: {
    stroke: '#3b82f6',  // Blue
    strokeWidth: 2
  },
  markerEnd: {
    type: MarkerType.ArrowClosed,
    color: '#3b82f6',
  }
}

// Merge edge (merged node → parent, dashed)
{
  type: 'smoothstep',
  animated: false,
  style: {
    stroke: '#10b981',  // Green
    strokeWidth: 2,
    strokeDasharray: '5,5'  // Dashed line
  }
}
```

### Controls Configuration

```typescript
<Controls
  showInteractive={false}  // Hide interactive mode toggle
  position="bottom-right"
/>

<MiniMap
  nodeColor={(node) => {
    switch(node.data.nodeType) {
      case 'root': return '#3b82f6';
      case 'branch': return '#8b5cf6';
      case 'merged': return '#6b7280';
    }
  }}
  position="bottom-left"
  style={{
    backgroundColor: '#f9fafb',
    border: '1px solid #e5e7eb'
  }}
/>

<Background
  variant="dots"
  gap={16}
  size={1}
  color="#e5e7eb"
/>
```

---

## 7. COMPONENT RESPONSIBILITIES (Detailed)

### Layout Components

**AppLayout.tsx:**

- Purpose: Overall app structure
- Structure:
  ```
  ┌──────────────────────────────┐
  │        Toolbar               │ <- Fixed height (64px)
  ├────────┬─────────────────────┤
  │Sidebar │                     │
  │        │      Canvas         │ <- Flex-1 (fills remaining)
  │        │                     │
  └────────┴─────────────────────┘
  ```
- Responsibilities:
  - Render Toolbar
  - Render Sidebar
  - Render Canvas
  - Handle layout responsiveness

**Toolbar.tsx:**

- Purpose: Top navigation and actions
- Contains:
  - Project name (editable on click)
  - "New Root Node" button
  - "Export Project" button
  - Settings icon (future)
- State needed:
  - Project name (from store)
- Actions:
  - Create root node
  - Export project as JSON

**Sidebar.tsx:**

- Purpose: Show all nodes in tree structure
- Contains:
  - Search input (filter nodes)
  - Node tree (nested list)
  - Click node → select it on canvas
- Structure:
  ```
  ┌─────────────────┐
  │ [Search....]    │
  ├─────────────────┤
  │ ▼ Root          │ <- Expandable
  │   ├─ Branch 1   │
  │   ├─ Branch 2   │
  │   └─ Branch 3   │
  │       └─ Sub 1  │
  └─────────────────┘
  ```
- State needed:
  - All nodes (from store)
  - Selected node (from store)
- Actions:
  - Select node
  - Filter nodes by search

**StatusBar.tsx:**

- Purpose: Show global stats
- Contains:
  - Total nodes count
  - Total messages count
  - Total tokens used
  - Connection status (online/offline)
- State needed:
  - Nodes (to calculate stats)
- Display:
  ```
  📊 5 nodes | 💬 23 messages | 🔢 12,450 tokens | 🟢 Online
  ```

---

### Canvas Components

**Canvas.tsx:**

- Purpose: React Flow wrapper
- Responsibilities:
  - Initialize React Flow
  - Handle node drag
  - Handle zoom/pan
  - Render nodes and edges
  - Apply highlighting to context path
- State needed:
  - Nodes (from store)
  - Edges (from store)
  - Highlighted path (from store)
- Event handlers:
  - `onNodesChange` → Update node positions
  - `onNodeClick` → Select node, show context path
  - `onPaneClick` → Deselect all

**CustomBackground.tsx:**

- Purpose: Custom grid pattern (optional enhancement)
- Could add:
  - Gradient background
  - Animated particles
  - Zone indicators (root zone, branch zone)

---

### Node Components

**CustomNode.tsx:**

- Purpose: Main node component (used for all node types)
- Displays differently based on `data.nodeType`:
  - Root: Blue border, crown icon
  - Branch: Purple border, branch icon
  - Merged: Gray border, faded, checkmark icon
- Structure:
  ```
  ┌─────────────────────────────┐
  │ NodeHeader                  │
  ├─────────────────────────────┤
  │ NodeBody (if expanded)      │
  ├─────────────────────────────┤
  │ NodeFooter                  │
  └─────────────────────────────┘
  ```
- State needed:
  - Is this node expanded? (from store: `ui.expandedNodeId`)
  - Is this node selected? (from store: `ui.selectedNodeId`)
  - Is this node highlighted? (from store: `ui.highlightedPath`)
- Actions:
  - Toggle expand/collapse
  - Select node

**NodeHeader.tsx:**

- Purpose: Title and metadata
- Contains:
  - Icon (based on type)
  - Title (editable on double-click)
  - Message count badge
  - Token count badge
  - Expand/collapse button
- Layout:
  ```
  ┌─────────────────────────────┐
  │ 👑 Root Discussion      [▼] │
  │ 💬 5 | 🔢 1.2k             │
  └─────────────────────────────┘
  ```

**NodeBody.tsx:**

- Purpose: Container for chat panel
- Shows only when `ui.expandedNodeId === this.id`
- Contains:
  - ChatPanel component
- Animation:
  - Fade in/out when toggling
  - Height: 0 → 500px transition

**NodeFooter.tsx:**

- Purpose: Action buttons
- Contains different buttons based on node type:

  ```
  Root node:
  [🌿 Branch] [🗑️ Delete]

  Branch node (not merged):
  [🌿 Branch] [🔀 Merge] [🗑️ Delete]

  Merged node:
  [👁️ View] (grayed out, read-only)
  ```

- State needed:
  - Node data (to determine which buttons)
- Actions:
  - Create branch
  - Merge
  - Delete

**NodeBadge.tsx:**

- Purpose: Small status indicator
- Shows:
  - "Active" (green)
  - "Merged" (gray)
  - "Has AI suggestions" (yellow with notification dot)
- Position: Top-right corner of node

---

### Chat Components

**ChatPanel.tsx:**

- Purpose: Complete chat interface
- Structure:
  ```
  ┌─────────────────────────┐
  │ ContextInfo             │ <- Shows inherited context
  ├─────────────────────────┤
  │                         │
  │ MessageList             │ <- Scrollable area
  │                         │
  ├─────────────────────────┤
  │ MessageInput            │ <- Fixed at bottom
  └─────────────────────────┘
  ```
- Props:
  - `nodeId: string`
- State needed (via hooks):
  - `const { messages, sendMessage, isLoading } = useChat(nodeId)`
- Behavior:
  - Auto-scroll to bottom on new message
  - Show TypingIndicator when `isLoading`

**MessageList.tsx:**

- Purpose: Scrollable message container
- Responsibilities:
  - Render all messages
  - Auto-scroll to bottom
  - Virtualization for performance (if >100 messages)
- Props:
  - `messages: Message[]`
  - `isLoading: boolean`

**MessageBubble.tsx:**

- Purpose: Single message display
- Types of messages:
  1. User message (right-aligned, blue)
  2. AI message (left-aligned, gray)
  3. Merged summary (full-width, yellow background)
  4. System message (centered, small, gray)
- Props:
  - `message: Message`
- Display format:

  ```
  User message:
                    ┌──────────────┐
                    │ Hello!       │
                    │ 2:30 PM      │
                    └──────────────┘

  AI message:
  ┌──────────────┐
  │ Hi there!    │
  │ 2:30 PM      │
  └──────────────┘

  Merged summary:
  ┌────────────────────────────┐
  │ 📊 MERGED FROM "XGBoost"  │
  │                            │
  │ Summary: After testing...  │
  │                            │
  │ 2:35 PM                    │
  └────────────────────────────┘
  ```

**MessageInput.tsx:**

- Purpose: Text input for messages
- Contains:
  - Textarea (auto-resize up to 5 lines)
  - Send button
  - Character counter (optional)
- Keyboard shortcuts:
  - Enter → Send message
  - Shift+Enter → New line
- Props:
  - `onSend: (message: string) => void`
  - `disabled: boolean` (when loading)

**TypingIndicator.tsx:**

- Purpose: Show AI is responding
- Display: Animated dots
  ```
  AI is thinking ●●●
  ```
- Animation: Pulse effect on dots

**ContextInfo.tsx:**

- Purpose: Show inherited context from parent
- Collapsible section at top of chat
- Display:
  ```
  ▼ Inherited Context
    From: "Root Discussion"
    Summary: "Exploring ML models for jaundice detection..."
  ```
- Props:
  - `contextSummary: string`
  - `parentTitle: string`

---

### Modal Components

**BranchModal.tsx:**

- Purpose: Create new branch
- Opens when: User clicks "Branch" button
- Contains:
  - Input for branch title
  - Preview of inherited context
  - Cancel/Create buttons
- Layout:
  ```
  ┌──────────────────────────────┐
  │ Create Branch           [×]  │
  ├──────────────────────────────┤
  │                              │
  │ Branch Name:                 │
  │ [_____________________]      │
  │                              │
  │ Inherited Context:           │
  │ "Exploring ML models..."     │
  │                              │
  │        [Cancel] [Create]     │
  └──────────────────────────────┘
  ```
- State needed:
  - `ui.isBranchModalOpen`
  - `ui.branchModalParentId`
- Actions:
  - `createBranch(parentId, title)`

**MergePreviewModal.tsx:**

- Purpose: Preview merge before confirming
- Opens when: User clicks "Merge" button
- Contains:
  - Source node title
  - Target node title
  - AI-generated merge summary (fetched on open)
  - Cancel/Confirm buttons
- Layout:
  ```
  ┌──────────────────────────────┐
  │ Merge Preview           [×]  │
  ├──────────────────────────────┤
  │                              │
  │ From: "XGBoost Exploration"  │
  │ To: "Root Discussion"        │
  │                              │
  │ Summary:                     │
  │ ┌──────────────────────────┐ │
  │ │ After testing XGBoost... │ │
  │ │ (AI-generated summary)   │ │
  │ └──────────────────────────┘ │
  │                              │
  │   [Cancel] [Confirm Merge]   │
  └──────────────────────────────┘
  ```
- Behavior:
  - On open → API call to get merge preview
  - Show loading spinner while fetching
- State needed:
  - `ui.isMergeModalOpen`
  - `ui.mergeModalSourceId`
  - `ui.mergeModalTargetId`
- Actions:
  - `mergeBranch(sourceId, targetId)`

**ConfirmDialog.tsx:**

- Purpose: Generic confirmation for destructive actions
- Used for:
  - Delete node
  - Clear chat
  - Reset project
- Props:
  - `title: string`
  - `message: string`
  - `onConfirm: () => void`
  - `onCancel: () => void`
  - `variant: 'danger' | 'warning'`

---

### Visualization Components

**CustomEdge.tsx:**

- Purpose: Styled edge component for React Flow
- Types:
  1. Inheritance edge (parent → child)
     - Blue, animated, solid
  2. Merge edge (merged node → parent)
     - Green, not animated, dashed
- Props (from React Flow):
  - `id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data`
- Styling based on `data.edgeType`

**ContextPathOverlay.tsx:**

- Purpose: Highlight context inheritance path
- How it works:
  1. User selects a node
  2. Calculate path: [root → grandparent → parent → current]
  3. Highlight these nodes and edges
- Visual effect:
  - Highlighted nodes: Gold border glow
  - Highlighted edges: Thicker, gold color
  - Non-highlighted: Faded opacity
- Implementation:
  - Not a separate overlay
  - Modify node/edge styles in Canvas based on `ui.highlightedPath`

---

## 8. HOOKS SPECIFICATION

### useProject

**Purpose:** Project-level operations

**Returns:**

```typescript
{
  project: Project | null,
  isLoading: boolean,
  error: string | null,

  // Actions
  initProject: (name: string) => Promise<void>,
  loadProject: (id: string) => Promise<void>,
  updateProjectName: (name: string) => Promise<void>,
  exportProject: () => void,  // Download as JSON
}
```

**Usage:**

```typescript
// In Toolbar.tsx
const { project, updateProjectName } = useProject();
```

---

### useNodes

**Purpose:** Node CRUD operations

**Returns:**

```typescript
{
  nodes: Node[],

  // Actions
  createNode: (data: NodeCreate) => Promise<Node>,
  updateNode: (id: string, updates: Partial<Node>) => Promise<void>,
  deleteNode: (id: string) => Promise<void>,
  selectNode: (id: string | null) => void,
  expandNode: (id: string | null) => void,
}
```

**Usage:**

```typescript
// In CustomNode.tsx
const { selectNode, expandNode } = useNodes();

const handleHeaderClick = () => {
  selectNode(nodeId);
  expandNode(isExpanded ? null : nodeId);
};
```

---

### useChat

**Purpose:** Chat functionality for a specific node

**Parameters:**

```typescript
nodeId: string;
```

**Returns:**

```typescript
{
  messages: Message[],
  isLoading: boolean,
  error: string | null,

  // Actions
  sendMessage: (content: string) => Promise<void>,
  clearMessages: () => Promise<void>,
}
```

**Internal logic:**

```typescript
1. User calls sendMessage("Hello")
2. Optimistically add user message to store
3. Set isLoading = true
4. API call: POST /nodes/{nodeId}/chat
5. Add AI response to store
6. Set isLoading = false
```

**Usage:**

```typescript
// In ChatPanel.tsx
const { messages, sendMessage, isLoading } = useChat(nodeId);
```

---

### useBranch

**Purpose:** Branch creation logic

**Returns:**

```typescript
{
  isCreating: boolean,
  error: string | null,

  // Actions
  openBranchModal: (parentId: string) => void,
  closeBranchModal: () => void,
  createBranch: (parentId: string, title: string) => Promise<void>,
}
```

**Internal logic:**

```typescript
1. User clicks "Branch" → openBranchModal(parentId)
2. Modal opens with input
3. User submits title → createBranch(parentId, title)
4. API call: POST /nodes/{parentId}/branch
5. Add new node to store
6. Add edge to store
7. Calculate and set position
8. Close modal
9. Auto-select and expand new node
```

**Usage:**

```typescript
// In NodeFooter.tsx
const { openBranchModal } = useBranch();

<button onClick={() => openBranchModal(nodeId)}>
  Branch
</button>

// In BranchModal.tsx
const { createBranch, closeBranchModal } = useBranch();
```

---

### useMerge

**Purpose:** Merge operations

**Returns:**

```typescript
{
  isMerging: boolean,
  mergePreview: string | null,
  error: string | null,

  // Actions
  openMergeModal: (sourceId: string, targetId: string) => void,
  closeMergeModal: () => void,
  fetchMergePreview: () => Promise<void>,
  confirmMerge: () => Promise<void>,
}
```

**Internal logic:**

```typescript
1. User clicks "Merge" → openMergeModal(sourceId, targetId)
2. Modal opens, calls fetchMergePreview()
3. API call: GET /nodes/{sourceId}/merge-preview
4. Display preview in modal
5. User confirms → confirmMerge()
6. API call: POST /merge
7. Add merge summary to target node messages
8. Mark source node as merged
9. Update edge style (change to merge type)
10. Close modal
```

**Usage:**

```typescript
// In NodeFooter.tsx
const { openMergeModal } = useMerge();

<button onClick={() => openMergeModal(nodeId, parentId)}>
  Merge
</button>

// In MergePreviewModal.tsx
const { mergePreview, confirmMerge } = useMerge();
```

---

### useReactFlow (from React Flow library)

**Purpose:** Canvas operations

**Returns:**

```typescript
{
  // React Flow methods
  fitView: () => void,
  zoomIn: () => void,
  zoomOut: () => void,
  setCenter: (x: number, y: number, zoom?: number) => void,
}
```

**Usage:**

```typescript
// In Toolbar.tsx
const { fitView } = useReactFlow();

<button onClick={fitView}>
  Fit View
</button>
```

---

## 9. API SERVICE SPECIFICATION

### Base Configuration

```typescript
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds (AI calls can be slow)
  headers: {
    "Content-Type": "application/json",
  },
});
```

### API Functions

**Project APIs:**

```typescript
initProject(name: string): Promise<ProjectResponse>
  → POST /projects
  → Body: { name }

getProject(id: string): Promise<ProjectResponse>
  → GET /projects/{id}

updateProject(id: string, updates: Partial<Project>): Promise<ProjectResponse>
  → PATCH /projects/{id}
  → Body: updates
```

**Node APIs:**

```typescript
createNode(data: NodeCreate): Promise<NodeResponse>
  → POST /nodes
  → Body: { project_id, title, parent_id?, position }

getNode(id: string): Promise<NodeResponse>
  → GET /nodes/{id}

updateNode(id: string, updates: Partial<Node>): Promise<NodeResponse>
  → PATCH /nodes/{id}
  → Body: updates

deleteNode(id: string): Promise<void>
  → DELETE /nodes/{id}
```

**Chat APIs:**

```typescript
sendMessage(nodeId: string, content: string): Promise<ChatResponse>
  → POST /nodes/{nodeId}/messages
  → Body: { content }
  → Response: { id, role: 'assistant', content, timestamp }

getMessages(nodeId: string): Promise<Message[]>
  → GET /nodes/{nodeId}/messages
```

**Branch APIs:**

```typescript
createBranch(parentId: string, title: string): Promise<BranchResponse>
  → POST /nodes/{parentId}/branch
  → Body: { title }
  → Response: { id, title, inherited_context, parent_id, position }
```

**Merge APIs:**

```typescript
getMergePreview(sourceId: string, targetId: string): Promise<MergePreviewResponse>
  → GET /nodes/{sourceId}/merge-preview?target={targetId}
  → Response: { summary }

mergeBranch(sourceId: string, targetId: string): Promise<MergeResponse>
  → POST /merge
  → Body: { source_id, target_id }
  → Response: { success, summary }
```

### Error Handling

```typescript
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || "An error occurred";

    // Add to toast
    useStore.getState().addToast({
      type: "error",
      message,
    });

    return Promise.reject(error);
  },
);
```

---

## 10. TYPES & INTERFACES

### Core Types

```typescript
// types/project.ts
interface Project {
  id: string;
  name: string;
  rootNodeId: string;
  createdAt: string;
}

// types/node.ts
interface Node {
  id: string;
  type: string; // For React Flow ('custom')
  position: { x: number; y: number };
  data: NodeData;
}

interface NodeData {
  title: string;
  nodeType: "root" | "branch" | "merged";
  parentId: string | null;
  messages: Message[];
  contextSummary: string;
  status: "active" | "merged" | "archived";
  tokenCount: number;
  createdAt: string;
}

// types/message.ts
interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "merged";
  content: string;
  timestamp: string;
  tokenCount?: number;
}

// types/edge.ts
interface Edge {
  id: string;
  source: string;
  target: string;
  type: "smoothstep" | "custom";
  animated?: boolean;
  style?: CSSProperties;
  data?: {
    edgeType: "inherit" | "merge";
  };
}
```

### API Types

```typescript
// types/api.ts
interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

interface ChatRequest {
  content: string;
}

interface ChatResponse {
  id: string;
  role: "assistant";
  content: string;
  timestamp: string;
  tokenCount: number;
}

interface BranchRequest {
  title: string;
}

interface BranchResponse {
  id: string;
  title: string;
  parentId: string;
  inheritedContext: string;
  position: { x: number; y: number };
}

interface MergeRequest {
  sourceId: string;
  targetId: string;
}

interface MergeResponse {
  success: boolean;
  summary: string;
}
```

---

## 11. CONSTANTS & ENUMS

```typescript
// utils/constants.ts

export const NODE_TYPES = {
  ROOT: "root",
  BRANCH: "branch",
  MERGED: "merged",
} as const;

export const NODE_STATUS = {
  ACTIVE: "active",
  MERGED: "merged",
  ARCHIVED: "archived",
} as const;

export const MESSAGE_ROLES = {
  USER: "user",
  ASSISTANT: "assistant",
  SYSTEM: "system",
  MERGED: "merged",
} as const;

export const EDGE_TYPES = {
  INHERIT: "inherit",
  MERGE: "merge",
} as const;

export const COLORS = {
  NODE_ROOT: "#3b82f6",
  NODE_BRANCH: "#8b5cf6",
  NODE_MERGED: "#6b7280",
  EDGE_INHERIT: "#3b82f6",
  EDGE_MERGE: "#10b981",
  MSG_USER: "#3b82f6",
  MSG_AI: "#f3f4f6",
  MSG_MERGED: "#fef3c7",
} as const;

export const CANVAS_CONFIG = {
  MIN_ZOOM: 0.5,
  MAX_ZOOM: 2,
  DEFAULT_ZOOM: 1,
  NODE_SPACING_X: 300,
  NODE_SPACING_Y: 350,
} as const;

export const SIZES = {
  NODE_COLLAPSED: { width: 250, height: 80 },
  NODE_EXPANDED: { width: 450, height: 600 },
  CHAT_HEIGHT: 500,
  SIDEBAR_WIDTH: 280,
  TOOLBAR_HEIGHT: 64,
} as const;

export const API_ENDPOINTS = {
  PROJECTS: "/projects",
  NODES: "/nodes",
  MESSAGES: "/messages",
  BRANCH: "/branch",
  MERGE: "/merge",
} as const;
```

---

## 12. BUILD PHASES (Detailed Timeline)

### Phase 1: Setup & Foundation (Hours 0-4)

**Hour 0-1: Project initialization**

- Create Vite project
- Install dependencies
- Configure Tailwind
- Initialize Shadcn
- Set up folder structure

**Hour 1-2: Type definitions**

- Create all interfaces
- Create constants
- Set up API service skeleton

**Hour 2-3: Store setup**

- Create Zustand slices
- Wire up actions
- Test state updates

**Hour 3-4: Basic layout**

- AppLayout component
- Toolbar (static)
- Sidebar (static)
- Canvas (empty React Flow)

**Deliverable:** App loads with empty canvas

---

### Phase 2: Core Canvas (Hours 4-10)

**Hour 4-6: Node components**

- CustomNode structure
- NodeHeader
- NodeFooter
- Basic styling

**Hour 6-8: Node interaction**

- Click to select
- Expand/collapse
- Position on canvas

**Hour 8-10: Store integration**

- Connect nodes to Zustand
- Add/update/delete actions
- Test CRUD operations

**Deliverable:** Can create and interact with nodes

---

### Phase 3: Chat Interface (Hours 10-18)

**Hour 10-12: Chat UI**

- ChatPanel layout
- MessageList
- MessageBubble (user/AI)

**Hour 12-14: Message input**

- MessageInput component
- Send functionality
- Keyboard shortcuts

**Hour 14-16: API integration**

- Wire up chat API
- Optimistic updates
- Loading states

**Hour 16-18: Polish chat**

- Auto-scroll
- Typing indicator
- Error handling

**Deliverable:** Fully functional chat

---

### Phase 4: Branching (Hours 18-24)

**Hour 18-20: Branch modal**

- BranchModal component
- Input validation
- API integration

**Hour 20-22: Branch logic**

- useBranch hook
- Create branch flow
- Position new nodes

**Hour 22-24: Visual connections**

- Edges appear
- Context path highlight
- Test branching

**Deliverable:** Can create branches

---

### Phase 5: Merging (Hours 24-32)

**Hour 24-26: Merge modal**

- MergePreviewModal
- Fetch preview API
- Display summary

**Hour 26-28: Merge logic**

- useMerge hook
- Confirm merge flow
- Update parent

**Hour 28-30: Merge visuals**

- Merged node styling
- Merge summary in chat
- Edge updates

**Hour 30-32: Test merging**

- Full merge flow
- Edge cases
- Error handling

**Deliverable:** Can merge branches

---

### Phase 6: Enhancements (Hours 32-40)

**Hour 32-34: Context path**

- Implement highlighting
- Click to show path
- Visual effects

**Hour 34-36: Sidebar**

- Node tree display
- Search functionality
- Click to select

**Hour 36-38: Status bar**

- Calculate stats
- Display token count
- Connection indicator

**Hour 38-40: Animations**

- Smooth transitions
- Toast notifications
- Loading spinners

**Deliverable:** Polished UI

---

### Phase 7: Final Polish (Hours 40-48)

**Hour 40-42: Bug fixes**

- Test all flows
- Fix edge cases
- Improve error handling

**Hour 42-44: Demo prep**

- Create demo project
- Pre-fill sample data
- Test demo script

**Hour 44-46: Performance**

- Optimize re-renders
- Lazy load components
- Test with many nodes

**Hour 46-48: Documentation**

- README
- Comments in code
- Demo video (optional)

**Deliverable:** Production-ready demo

---

## 13. DEMO SCENARIO (For Judges)

### Pre-loaded Demo Project

**Setup:**

- Project name: "Neonatal Jaundice ML Project"
- Already has nodes created
- Shows the power of branching

**Structure:**

```
Root: "Model Selection"
├─ Branch A: "XGBoost Exploration" (merged)
│   └─ Merge summary in root
├─ Branch B: "CNN Architecture" (active)
│   ├─ Sub-branch: "ResNet vs VGG"
│   └─ Sub-branch: "Data Augmentation"
└─ Branch C: "Feature Engineering" (active)
```

### Demo Script (5 minutes)

**Minute 1: The Problem**

- Show traditional chat: context pollution issue
- "When you explore two ideas, they get mixed up"

**Minute 2: The Solution**

- Show fractal workspace canvas
- "Each node is a separate context"
- Click Root → show chat
- Click Branch → show it doesn't see other branch

**Minute 3: Context Inheritance**

- Click "XGBoost Exploration"
- Show inherited context at top
- "It knows about the parent, but isolated from siblings"
- Select node → highlight context path

**Minute 4: Branching & Merging**

- Create new branch live
- Show chat in new branch
- Merge "XGBoost" branch
- Show summary appears in root

**Minute 5: The Win**

- Show sidebar with tree
- Show token count savings
- "This is how you explore without losing context"
- Questions

---

## 14. GOTCHAS & TIPS

### React Flow Gotchas

**Issue:** Nodes re-render too often
**Solution:** Memoize node data

```typescript
const nodeData = useMemo(() => ({...}), [dependencies]);
```

**Issue:** Edges don't update when nodes move
**Solution:** Use `onNodesChange` to update state

**Issue:** Canvas zoom/pan breaks
**Solution:** Use `<ReactFlowProvider>` wrapper

### Zustand Gotchas

**Issue:** Components re-render when unrelated state changes
**Solution:** Use selectors

```typescript
// Bad
const store = useStore(); // Subscribes to everything

// Good
const nodes = useStore((state) => state.nodes); // Only nodes
```

**Issue:** Actions not updating UI
**Solution:** Always use `set()` to update state

```typescript
// Bad
state.nodes.push(newNode); // Mutates directly

// Good
set({ nodes: [...state.nodes, newNode] }); // Creates new reference
```

### Tailwind Gotchas

**Issue:** Dynamic classes don't work

```typescript
// Bad
className={`bg-${color}-500`}  // Won't compile

// Good
className={color === 'blue' ? 'bg-blue-500' : 'bg-red-500'}
```

**Issue:** Styles not applying
**Solution:** Check Tailwind config `content` includes all files

### TypeScript Gotchas

**Issue:** React Flow types are complex
**Solution:** Use `Node<NodeData>` instead of plain `Node`

**Issue:** Store types are hard to infer
**Solution:** Explicitly type store slices

---

## FINAL CHECKLIST

**Before starting:**

- [ ] Understand state management concept
- [ ] Know which components need which data
- [ ] Reviewed React Flow docs
- [ ] Tailwind config ready
- [ ] Shadcn installed

**Phase completeness:**

- [ ] Can create nodes
- [ ] Can chat in nodes
- [ ] Can branch
- [ ] Can merge
- [ ] Context path highlights
- [ ] Sidebar works
- [ ] Demo data loaded

**Polish:**

- [ ] All loading states
- [ ] All error states
- [ ] Toast notifications
- [ ] Smooth animations
- [ ] Mobile responsive (optional)

---

Ready to start coding? Which part should we build first?
