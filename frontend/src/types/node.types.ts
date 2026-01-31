export type NodeType = 'root' | 'standard' | 'exploration';
export type NodeStatus = 'active' | 'frozen' | 'deleted';

export interface NodeData {
  title: string;
  nodeType: NodeType;
  status: NodeStatus;
  parentId: string | null;
  messageCount: number;
  tokenCount: number;
  inheritedContext?: string; // Compressed parent summary
  lastActivity: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'summary';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface CreateNodeRequest {
  title: string;
  parentId: string | null;
  nodeType: NodeType;
}

export interface MergeNodeRequest {
  sourceId: string;
  targetId: string;
}
