import { create } from 'zustand';
import { type Node, type Edge, type Connection, addEdge, applyNodeChanges, applyEdgeChanges, type NodeChange, type EdgeChange } from 'reactflow';
import type { NodeData, Message } from '../types/node.types';

interface AppState {
  // Canvas State
  nodes: Node<NodeData>[];
  edges: Edge[];
  
  // UI State
  selectedNodeId: string | null;
  expandedNodeId: string | null;
  creatingBranchNodeId: string | null; // ID of the node being branched from
  mergingNodeId: string | null; // ID of the node being merged
  highlightedPath: string[]; // Node IDs in the context path
  messages: Record<string, Message[]>; // Chat messages per node
  loading: Record<string, boolean>; // generic loading states by key
  toasts: Array<{ id: string; type: 'success' | 'error' | 'info'; message: string }>;

  // Actions
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  
  addNode: (node: Node<NodeData>) => void;
  updateNode: (id: string, data: Partial<NodeData>) => void;
  removeNode: (id: string) => void;
  
  setSelectedNode: (id: string | null) => void;
  setExpandedNode: (id: string | null) => void;
  setCreatingBranchNodeId: (id: string | null) => void;
  setMergingNodeId: (id: string | null) => void;
  setHighlightedPath: (path: string[]) => void;
  
  addMessage: (nodeId: string, message: Message) => void;
  
  addToast: (toast: { type: 'success' | 'error' | 'info'; message: string }) => void;
  removeToast: (id: string) => void;
}

const useStore = create<AppState>((set, get) => ({
  nodes: [
    {
      id: 'root',
      type: 'custom',
      position: { x: 0, y: 0 },
      data: {
        title: 'AI Cognition',
        nodeType: 'root',
        status: 'active',
        parentId: null,
        messageCount: 5,
        tokenCount: 1200,
        lastActivity: new Date().toISOString(),
        inheritedContext: "Foundation models and ethical constraints for the next generation."
      },
    },
     {
      id: 'node-2',
      type: 'custom',
      position: { x: 400, y: 300 },
      data: {
        title: 'Neural Pathways',
        nodeType: 'standard',
        status: 'active',
        parentId: 'root',
        messageCount: 2,
        tokenCount: 400,
        lastActivity: new Date().toISOString(),
        inheritedContext: "Mapping synaptic weights to logical operators."
      },
    },
  ],
  edges: [
      { id: 'e1-2', source: 'root', target: 'node-2', type: 'context', animated: false, style: { strokeWidth: 1.5 } }
  ],
  
  selectedNodeId: null,
  expandedNodeId: null,
  creatingBranchNodeId: null,
  mergingNodeId: null,
  highlightedPath: [],
  messages: {},
  loading: {},
  toasts: [],

  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },
  
  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },
  
  onConnect: (connection) => {
    set({
      edges: addEdge({ ...connection, type: 'context' }, get().edges),
    });
  },

  addNode: (node) => {
    set((state) => ({ nodes: [...state.nodes, node] }));
  },

  updateNode: (id, data) => {
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === id ? { ...node, data: { ...node.data, ...data } } : node
      ),
    }));
  },

  removeNode: (id) => {
    const { nodes, edges } = get();
    const nodeToRemove = nodes.find(n => n.id === id);
    
    // Prevent deleting root
    if (nodeToRemove?.data.nodeType === 'root') {
        set((state) => ({ 
             toasts: [...state.toasts, { id: 'root-delete-err', type: 'error', message: 'Cannot delete root node' }] 
        }));
        return;
    }

    // Find parent of the deleted node (Grandparent to children)
    const parentId = nodeToRemove?.data.parentId;

    // Find children of the deleted node
    const children = nodes.filter(n => n.data.parentId === id);

    // Re-parent children
    const updatedNodes = nodes
        .filter(n => n.id !== id) // Remove target node
        .map(n => {
            if (n.data.parentId === id) {
                return { 
                    ...n, 
                    data: { ...n.data, parentId: parentId || null } // Set to grandparent or null if no grandparent
                };
            }
            return n;
        });

    // Update Edges
    // 1. Remove edges connected to deleted node
    // 2. Add edges from Parent -> Children (if Parent exists)
    let updatedEdges = edges.filter(e => e.source !== id && e.target !== id);

    if (parentId) {
        const newEdges = children.map(child => ({
            id: `e${parentId}-${child.id}`,
            source: parentId,
            target: child.id,
            type: 'context',
            animated: false,
            style: { strokeWidth: 1.5 }
        }));
        updatedEdges = [...updatedEdges, ...newEdges];
    }

    set({
      nodes: updatedNodes,
      edges: updatedEdges,
      selectedNodeId: get().selectedNodeId === id ? null : get().selectedNodeId,
      expandedNodeId: get().expandedNodeId === id ? null : get().expandedNodeId,
    });
  },

  setSelectedNode: (id) => {
    set({ selectedNodeId: id });
    
    // Calculate context path (trace back to root)
    if (!id) {
        set({ highlightedPath: [] });
        return;
    }

    const { nodes } = get();
    const path: string[] = [];
    let currentId: string | null = id;

    while (currentId) {
        path.unshift(currentId);
        const node = nodes.find(n => n.id === currentId);
        currentId = node?.data.parentId || null;
    }

    set({ highlightedPath: path });
  },
  setExpandedNode: (id) => set({ expandedNodeId: id }),
  setCreatingBranchNodeId: (id) => set({ creatingBranchNodeId: id }),
  setMergingNodeId: (id) => set({ mergingNodeId: id }),
  setHighlightedPath: (path) => set({ highlightedPath: path }),

  addMessage: (nodeId, message) => {
    set((state) => ({
        messages: {
            ...state.messages,
            [nodeId]: [...(state.messages[nodeId] || []), message]
        }
    }));
  },

  addToast: ({ type, message }) => {
    const id = Math.random().toString(36).substring(7);
    set((state) => ({ toasts: [...state.toasts, { id, type, message }] }));
    setTimeout(() => get().removeToast(id), 3000);
  },

  removeToast: (id) => {
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
  },
}));

export default useStore;
