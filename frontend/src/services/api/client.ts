import axios from 'axios';
import type { NodeData, CreateNodeRequest, Message } from '../../types/node.types';
import type { Node } from 'reactflow';

// Mock data for initial development since backend might not be ready
const MOCK_DELAY = 500;

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Mock implementations
export const nodesApi = {
  getNodes: async (): Promise<Node<NodeData>[]> => {
    // In real app, this would fetch from backend
    return []; 
  },

  createNode: async (data: CreateNodeRequest): Promise<any> => {
    await new Promise(resolve => setTimeout(resolve, MOCK_DELAY));
    return {
      node_id: `node-${Date.now()}`,
      position: { x: 0, y: 0 }, // Backend should ideally calculate or frontend does it
      ...data,
      status: 'active',
      created_at: new Date().toISOString(),
      inherited_context: "Mock inherited context...",
    };
  },

  sendMessage: async (nodeId: string, content: string): Promise<Message> => {
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate AI delay
    return {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: `Echo: ${content}\n\nThis is a mock response from the AI for node ${nodeId}.`,
      timestamp: new Date().toISOString(),
    };
  },

  mergeNode: async (data: { sourceNodeId: string; targetNodeId: string; summary: string }) => {
    await new Promise(resolve => setTimeout(resolve, MOCK_DELAY));
    console.log('Mock merging nodes:', data);
    return { success: true };
  },
};

export default api;
