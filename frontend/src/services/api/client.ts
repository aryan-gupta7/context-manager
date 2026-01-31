import axios from 'axios';
import type { NodeData, CreateNodeRequest, Message, NodeStatus, NodeType } from '../../types/node.types';
import type { Node } from 'reactflow';



const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Mock implementations
// Backend Response Types
interface TreeNodeResponse {
    node_id: string;
    title: string;
    status: NodeStatus;
    node_type: NodeType;
    children: TreeNodeResponse[];
    position: { x: number; y: number };
    message_count?: number;
}

export const nodesApi = {
  getNodes: async (): Promise<Node<NodeData>[]> => {
    const response = await api.get<TreeNodeResponse[]>('/nodes/tree');
    const treeRoots = response.data;
    
    const flatten = (nodes: TreeNodeResponse[], parentId: string | null = null): Node<NodeData>[] => {
      let flatList: Node<NodeData>[] = [];
      for (const n of nodes) {
        flatList.push({
          id: n.node_id,
          position: n.position || { x: 0, y: 0 },
          type: 'custom',
          data: {
            title: n.title,
            status: n.status,
            nodeType: n.node_type,
            parentId: parentId,
            messageCount: n.message_count || 0,
            tokenCount: 0, // Not currently returned by tree API
            lastActivity: new Date().toISOString(), // Placeholder
            inheritedContext: "", // Placeholder
          }
        });
        
        if (n.children && n.children.length > 0) {
          flatList = flatList.concat(flatten(n.children, n.node_id));
        }
      }
      return flatList;
    };

    return flatten(treeRoots);
  },

  createNode: async (data: CreateNodeRequest): Promise<any> => {
    const payload: Record<string, any> = {
      title: data.title,
      node_type: data.nodeType || 'standard'
    };
    
    // Only include parent_id if it's a valid non-empty string
    if (data.parentId && data.parentId.trim() !== '') {
      payload.parent_id = data.parentId;
    }
    
    // Include project_id if provided
    if (data.projectId) {
      payload.project_id = data.projectId;
    }
    
    const response = await api.post('/nodes', payload);
    return response.data;
  },

  sendMessage: async (nodeId: string, content: string): Promise<Message> => {
    const response = await api.post(`/nodes/${nodeId}/messages`, { content });
    return {
      id: response.data.message_id,
      role: response.data.role,
      content: response.data.content,
      timestamp: response.data.timestamp,
      metadata: response.data.metadata
    };
  },

  mergeNode: async (data: { sourceNodeId: string; targetNodeId: string; summary: string }) => {
    const payload = {
      source_node_id: data.sourceNodeId,
      target_node_id: data.targetNodeId
    };
    const response = await api.post('/nodes/merge', payload);
    return response.data;
  },

  deleteNode: async (nodeId: string, cascade: boolean = false) => {
    const response = await api.post(`/nodes/${nodeId}/delete`, { cascade });
    return response.data;
  },

  getMessages: async (nodeId: string): Promise<Message[]> => {
    const response = await api.get(`/nodes/${nodeId}/messages`);
    return response.data.map((m: any) => ({
      id: m.message_id,
      role: m.role,
      content: m.content,
      timestamp: m.timestamp,
      metadata: m.metadata || {}
    }));
  },

  summarizeNode: async (nodeId: string) => {
    const response = await api.post(`/nodes/${nodeId}/summarize`);
    return response.data;
  },

  copyNode: async (nodeId: string, newParentId?: string) => {
    const payload: Record<string, any> = {};
    if (newParentId) {
      payload.new_parent_id = newParentId;
    }
    const response = await api.post(`/nodes/${nodeId}/copy`, payload);
    return response.data;
  },

  getGraph: async (nodeId: string) => {
    const response = await api.get(`/nodes/${nodeId}/graph`);
    return response.data;
  },
};

// Project Types
export interface Project {
  project_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string | null;
  node_count: number;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
}

export const projectsApi = {
  getProjects: async (): Promise<Project[]> => {
    const response = await api.get<Project[]>('/projects');
    return response.data;
  },

  createProject: async (data: CreateProjectRequest): Promise<Project> => {
    const response = await api.post<Project>('/projects', data);
    return response.data;
  },

  getProject: async (projectId: string): Promise<Project> => {
    const response = await api.get<Project>(`/projects/${projectId}`);
    return response.data;
  },

  updateProject: async (projectId: string, data: Partial<CreateProjectRequest>): Promise<Project> => {
    const response = await api.put<Project>(`/projects/${projectId}`, data);
    return response.data;
  },

  deleteProject: async (projectId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}`);
  },

  getProjectNodes: async (projectId: string): Promise<Node<NodeData>[]> => {
    const response = await api.get<TreeNodeResponse[]>(`/projects/${projectId}/nodes/tree`);
    const treeRoots = response.data;
    
    const flatten = (nodes: TreeNodeResponse[], parentId: string | null = null): Node<NodeData>[] => {
      let flatList: Node<NodeData>[] = [];
      for (const n of nodes) {
        flatList.push({
          id: n.node_id,
          position: n.position || { x: 0, y: 0 },
          type: 'custom',
          data: {
            title: n.title,
            status: n.status,
            nodeType: n.node_type,
            parentId: parentId,
            messageCount: n.message_count || 0,
            tokenCount: 0,
            lastActivity: new Date().toISOString(),
            inheritedContext: "",
          }
        });
        
        if (n.children && n.children.length > 0) {
          flatList = flatList.concat(flatten(n.children, n.node_id));
        }
      }
      return flatList;
    };

    return flatten(treeRoots);
  },
};

export default api;

