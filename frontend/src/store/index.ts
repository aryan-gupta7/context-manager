import { create } from 'zustand';
import { type Node, type Edge, type Connection, addEdge, applyNodeChanges, applyEdgeChanges, type NodeChange, type EdgeChange } from 'reactflow';
import type { NodeData, Message } from '../types/node.types';
import { nodesApi, projectsApi, type Project } from '../services/api/client';

interface AppState {
  // Canvas State
  nodes: Node<NodeData>[];
  edges: Edge[];
  isInitialized: boolean;
  
  // Project State
  projects: Project[];
  currentProjectId: string | null;
  createProjectModalOpen: boolean;
  
  // UI State
  selectedNodeId: string | null;
  expandedNodeId: string | null;
  creatingBranchNodeId: string | null; // ID of the node being branched from
  mergingNodeId: string | null; // ID of the node being merged
  highlightedPath: string[]; // Node IDs in the context path
  messages: Record<string, Message[]>; // Chat messages per node
  loading: Record<string, boolean>; // generic loading states by key
  toasts: Array<{ id: string; type: 'success' | 'error' | 'info'; message: string }>;

  // Project Actions
  fetchProjects: () => Promise<void>;
  setCurrentProject: (id: string | null) => Promise<void>;
  createProject: (name: string, description?: string) => Promise<Project | null>;
  setCreateProjectModalOpen: (open: boolean) => void;

  // Node Actions
  fetchNodes: () => Promise<void>;
  setNodes: (nodes: Node<NodeData>[]) => void;
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

// Helper to build edges from nodes based on parent-child relationships
const buildEdgesFromNodes = (nodes: Node<NodeData>[]): Edge[] => {
  const edges: Edge[] = [];
  for (const node of nodes) {
    // Primary parent edge
    if (node.data.parentId) {
      edges.push({
        id: `e-${node.data.parentId}-${node.id}`,
        source: node.data.parentId,
        target: node.id,
        type: 'context',
        animated: false,
        style: { strokeWidth: 1.5 }
      });
    }
    // Secondary parent edge (from merge)
    if (node.data.mergeParentId) {
      edges.push({
        id: `e-merge-${node.data.mergeParentId}-${node.id}`,
        source: node.data.mergeParentId,
        target: node.id,
        type: 'context',
        animated: false,
        style: { strokeWidth: 1.5, strokeDasharray: '5,5' } // Dashed for merge edges
      });
    }
  }
  return edges;
};

const useStore = create<AppState>((set, get) => ({
  nodes: [],
  edges: [],
  isInitialized: false,
  
  // Project State
  projects: [],
  currentProjectId: null,
  createProjectModalOpen: false,
  
  // UI State
  selectedNodeId: null,
  expandedNodeId: null,
  creatingBranchNodeId: null,
  mergingNodeId: null,
  highlightedPath: [],
  messages: {},
  loading: {},
  toasts: [],

  // Project Actions
  fetchProjects: async () => {
    try {
      set({ loading: { ...get().loading, projects: true } });
      const projects = await projectsApi.getProjects();
      set({ projects, loading: { ...get().loading, projects: false } });
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      get().addToast({ type: 'error', message: 'Failed to load projects' });
      set({ loading: { ...get().loading, projects: false } });
    }
  },

  setCurrentProject: async (id: string | null) => {
    set({ currentProjectId: id, nodes: [], edges: [], isInitialized: false });
    
    if (id) {
      try {
        set({ loading: { ...get().loading, nodes: true } });
        const nodes = await projectsApi.getProjectNodes(id);
        const edges = buildEdgesFromNodes(nodes);
        set({ nodes, edges, isInitialized: true, loading: { ...get().loading, nodes: false } });
      } catch (error) {
        console.error('Failed to fetch project nodes:', error);
        get().addToast({ type: 'error', message: 'Failed to load project nodes' });
        set({ isInitialized: true, loading: { ...get().loading, nodes: false } });
      }
    } else {
      set({ isInitialized: true });
    }
  },

  createProject: async (name: string, description?: string) => {
    try {
      const project = await projectsApi.createProject({ name, description });
      set({ projects: [project, ...get().projects] });
      get().addToast({ type: 'success', message: `Created project: ${name}` });
      return project;
    } catch (error) {
      console.error('Failed to create project:', error);
      get().addToast({ type: 'error', message: 'Failed to create project' });
      return null;
    }
  },

  setCreateProjectModalOpen: (open: boolean) => {
    set({ createProjectModalOpen: open });
  },

  // Node Actions
  fetchNodes: async () => {
    try {
      set({ loading: { ...get().loading, nodes: true } });
      const nodes = await nodesApi.getNodes();
      const edges = buildEdgesFromNodes(nodes);
      set({ nodes, edges, isInitialized: true, loading: { ...get().loading, nodes: false } });
    } catch (error) {
      console.error('Failed to fetch nodes:', error);
      get().addToast({ type: 'error', message: 'Failed to load nodes from server' });
      set({ isInitialized: true, loading: { ...get().loading, nodes: false } });
    }
  },

  setNodes: (nodes) => {
    const edges = buildEdgesFromNodes(nodes);
    set({ nodes, edges });
  },

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
    set((state) => {
      const newNodes = [...state.nodes, node];
      // Also add the edge if it has a parent
      let newEdges = state.edges;
      if (node.data.parentId) {
        newEdges = [...state.edges, {
          id: `e-${node.data.parentId}-${node.id}`,
          source: node.data.parentId,
          target: node.id,
          type: 'context',
          animated: false,
          style: { strokeWidth: 1.5 }
        }];
      }
      return { nodes: newNodes, edges: newEdges };
    });
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
            id: `e-${parentId}-${child.id}`,
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

