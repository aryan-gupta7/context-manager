import { useState, useEffect } from 'react';
import useStore from '../../store';
import { nodesApi } from '../../services/api/client';
import { X, GitMerge, ArrowRight } from 'lucide-react';

import type { Node } from 'reactflow';
import type { NodeData } from '../../types/node.types';

const MergeModal = () => {
  const { mergingNodeId, setMergingNodeId, nodes, addToast, currentProjectId } = useStore();
  const [description, setDescription] = useState('');
  const [selectedTargetId, setSelectedTargetId] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const node = mergingNodeId ? nodes.find(n => n.id === mergingNodeId) : null;
  const potentialTargets = nodes.filter(n => n.id !== mergingNodeId && n.data.status !== 'deleted');

  // Set default target using useEffect to avoid React state update during render
  useEffect(() => {
    if (!mergingNodeId || selectedTargetId) return;
    
    if (node?.data.parentId) {
      const parent = potentialTargets.find(n => n.id === node.data.parentId);
      if (parent) {
        setSelectedTargetId(parent.id);
        return;
      }
    }
    
    if (potentialTargets.length > 0) {
      setSelectedTargetId(potentialTargets[0].id);
    }
  }, [mergingNodeId, node?.data.parentId, potentialTargets, selectedTargetId]);

  // Reset state when modal closes
  useEffect(() => {
    if (!mergingNodeId) {
      setSelectedTargetId('');
      setDescription('');
    }
  }, [mergingNodeId]);

  if (!mergingNodeId || !node) return null;

  const handleClose = () => {
    setMergingNodeId(null);
    setDescription('');
    setSelectedTargetId('');
  };

  const handleMerge = async () => {
    if (!selectedTargetId) {
        addToast({ type: 'error', message: 'No target node selected' });
        return;
    }

    setIsSubmitting(true);
    try {
      // 1. Calculate Position for New Node (Midpoint + offset)
      const targetNode = nodes.find(n => n.id === selectedTargetId);
      if (!targetNode) throw new Error("Target node not found");

      const newX = (node.position.x + targetNode.position.x) / 2;
      const newY = Math.max(node.position.y, targetNode.position.y) + 200;

      // 2. Create the New Merged Node
      const newNodeData = {
          title: `Merge: ${node.data.title} & ${targetNode.data.title}`,
          parentId: node.id, // Primary Parent (Source)
          projectId: currentProjectId, // Associate with current project
          nodeType: 'standard' as const,
      };

      // Call API to persist (mock)
      const response = await nodesApi.createNode(newNodeData);

      // 3. Add to Store
      const newNode: Node<NodeData> = {
        id: response.node_id,
        type: 'custom',
        position: response.position || { x: newX, y: newY },
        data: {
          title: response.title,
          nodeType: response.node_type,
          status: response.status,
          parentId: response.parent_id,
          mergeParentId: targetNode.id, // Ensure this is passed
          messageCount: 0,
          tokenCount: 0,
          inheritedContext: `Merged context from ${node.data.title} and ${targetNode.data.title}`,
          lastActivity: response.created_at
        }
      };

      // Add Node
      useStore.getState().addNode(newNode);

      // 4. Create Dual Edges
      // Edge 1: Source -> New Node
      useStore.getState().onConnect({
          source: node.id,
          target: newNode.id,
          sourceHandle: null,
          targetHandle: null
      });

      // Edge 2: Target -> New Node
      useStore.getState().onConnect({
          source: targetNode.id,
          target: newNode.id,
          sourceHandle: null,
          targetHandle: null
      });

      addToast({ type: 'success', message: 'Merged successfully into new node' });
      handleClose();
    } catch (error) {
      addToast({ type: 'error', message: 'Failed to merge nodes' });
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
                <GitMerge className="text-purple-500" size={20} />
                Merge Branch
            </h3>
            <button onClick={handleClose} className="text-slate-400 hover:text-white transition-colors">
                <X size={20} />
            </button>
        </div>
        
        <div className="p-6">
            <div className="flex items-center gap-4 mb-6 p-4 bg-gray-50 dark:bg-[#111318] rounded-xl border border-gray-200 dark:border-[#282e39]">
                 <div className="flex-1 text-center">
                    <span className="text-xs text-slate-500 block mb-1">From</span>
                    <span className="text-sm font-bold text-[#111318] dark:text-white block truncate max-w-[100px] mx-auto">{node.data.title}</span>
                 </div>
                 <div className="text-slate-400">
                    <ArrowRight size={16} />
                 </div>
                 <div className="flex-1 text-center">
                    <span className="text-xs text-slate-500 block mb-1">To</span>
                    <select
                        className="w-full bg-white dark:bg-[#1a1d26] border border-gray-200 dark:border-[#282e39] rounded px-2 py-1 text-xs font-bold text-[#111318] dark:text-white truncate focus:outline-none focus:ring-1 focus:ring-primary"
                        value={selectedTargetId}
                        onChange={(e) => setSelectedTargetId(e.target.value)}
                    >
                        {potentialTargets.map(target => (
                            <option key={target.id} value={target.id}>
                                {target.data.title}
                            </option>
                        ))}
                    </select>
                 </div>
            </div>

            <div className="mb-6">
                <label className="block text-sm font-medium text-slate-400 mb-1">Merge Summary</label>
                <textarea 
                    autoFocus
                    className="w-full bg-transparent border border-gray-200 dark:border-[#282e39] rounded-lg px-4 py-2 text-[#111318] dark:text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all resize-none h-24"
                    placeholder="Describe the changes to be merged..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
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
                    onClick={handleMerge}
                    disabled={isSubmitting || !selectedTargetId}
                    className="px-4 py-2 rounded-lg text-sm font-bold bg-purple-600 hover:bg-purple-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                    {isSubmitting ? 'Merging...' : <><GitMerge size={16} /> Confirm Merge</>}
                </button>
            </div>
        </div>
      </div>
    </div>
  );
};

export default MergeModal;
