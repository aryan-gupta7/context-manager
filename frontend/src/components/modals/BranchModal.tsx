import { useState } from 'react';
import useStore from '../../store';
import { nodesApi } from '../../services/api/client';
import { X, GitBranch, Plus } from 'lucide-react';
import type { NodeData } from '../../types/node.types';
import type { Node } from 'reactflow';

const BranchModal = () => {
  const { creatingBranchNodeId, setCreatingBranchNodeId, nodes, addNode, addToast, currentProjectId } = useStore();
  const [title, setTitle] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!creatingBranchNodeId) return null;

  const parentNode = nodes.find(n => n.id === creatingBranchNodeId);
  if (!parentNode) return null;

  const handleClose = () => {
    setCreatingBranchNodeId(null);
    setTitle('');
  };

  const calculatePosition = (parentId: string) => {
    const parent = nodes.find(n => n.id === parentId)!;
    
    // Find siblings (nodes that have this parent)
    const siblings = nodes.filter(n => n.data.parentId === parentId);
    
    // Simple layout strategy: 
    // Place below parent, offset horizontally by sibling index
    // Assuming node width ~350px + gap
    const xOffset = (siblings.length * 350) - (siblings.length > 0 ? 100 : 0); 
    const yOffset = 400;

    return {
      x: parent.position.x + xOffset,
      y: parent.position.y + yOffset
    };
  };

  const handleCreate = async () => {
    if (!title.trim()) return;

    setIsSubmitting(true);
    try {
      const position = calculatePosition(parentNode.id);
      
      const newNodeData = {
        title,
        parentId: parentNode.id,
        projectId: currentProjectId,
        nodeType: 'standard' as const,
      };

      const response = await nodesApi.createNode(newNodeData);
      
      const newNode: Node<NodeData> = {
        id: response.node_id,
        type: 'custom',
        position: response.position || position,
        data: {
          title: response.title,
          nodeType: response.node_type,
          status: response.status,
          parentId: response.parent_id,
          messageCount: 0,
          tokenCount: 0,
          inheritedContext: '',
          lastActivity: response.created_at
        }
      };

      addNode(newNode);
      
      // Edge is added automatically by ReactFlow if we had an 'onAddEdge' but we are using custom logic
      // We need to add the edge manually in the store
      useStore.getState().onConnect({
        source: parentNode.id,
        target: newNode.id,
        sourceHandle: null,
        targetHandle: null
      });

      addToast({ type: 'success', message: 'Branch created successfully' });
      handleClose();
    } catch (error) {
      addToast({ type: 'error', message: 'Failed to create branch' });
      console.error(error);
    } finally {
        setIsSubmitting(false);
    }
  };

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-50">
      <div className="bg-white dark:bg-[#1a1d26] w-full max-w-md rounded-2xl shadow-2xl border border-gray-200 dark:border-[#282e39] overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-[#282e39]">
            <h3 className="text-lg font-bold text-[#111318] dark:text-white flex items-center gap-2">
                <GitBranch className="text-primary" size={20} />
                New Branch
            </h3>
            <button onClick={handleClose} className="text-slate-400 hover:text-white transition-colors">
                <X size={20} />
            </button>
        </div>
        
        <div className="p-6">
            <div className="mb-4">
                <label className="block text-sm font-medium text-slate-400 mb-1">Parent Context</label>
                <div className="p-3 bg-gray-100 dark:bg-[#111318] rounded-lg text-sm text-[#111318] dark:text-gray-300 border border-gray-200 dark:border-[#282e39]">
                    {parentNode.data.title}
                </div>
            </div>

            <div className="mb-6">
                <label className="block text-sm font-medium text-slate-400 mb-1">Branch Title</label>
                <input 
                    autoFocus
                    type="text" 
                    className="w-full bg-transparent border border-gray-200 dark:border-[#282e39] rounded-lg px-4 py-2 text-[#111318] dark:text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                    placeholder="e.g., Alternative Algorithm..."
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                />
            </div>

            <div className="flex justify-end gap-3">
                <button 
                    onClick={handleClose}
                    className="px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                >
                    Cancel
                </button>
                <button 
                    onClick={handleCreate}
                    disabled={isSubmitting || !title.trim()}
                    className="px-4 py-2 rounded-lg text-sm font-bold bg-primary hover:bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                    {isSubmitting ? 'Creating...' : <><Plus size={16} /> Create Branch</>}
                </button>
            </div>
        </div>
      </div>
    </div>
  );
};

export default BranchModal;
