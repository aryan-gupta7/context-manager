import { useState } from 'react';
import useStore from '../../store';
import { nodesApi } from '../../services/api/client';
import { X, GitMerge, ArrowRight } from 'lucide-react';

const MergeModal = () => {
  const { mergingNodeId, setMergingNodeId, nodes, addToast } = useStore();
  const [description, setDescription] = useState('');
  const [selectedTargetId, setSelectedTargetId] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!mergingNodeId) return null;

  const node = nodes.find(n => n.id === mergingNodeId);
  const potentialTargets = nodes.filter(n => n.id !== mergingNodeId && n.data.status !== 'deleted');

  // Set default target to parent if not set
  if (!selectedTargetId && node?.data.parentId) {
      // Find parent if it exists in potential targets
      const parent = potentialTargets.find(n => n.id === node.data.parentId);
      if (parent) setSelectedTargetId(parent.id);
      else if (potentialTargets.length > 0) setSelectedTargetId(potentialTargets[0].id);
  }

  if (!node) return null;

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
      await nodesApi.mergeNode({
        sourceNodeId: node.id,
        targetNodeId: selectedTargetId,
        summary: description
      });

      // Visual update: maybe add a specific edge type or update status
      // For now, simpler: just toast
      
      addToast({ type: 'success', message: 'Merge request created successfully' });
      handleClose();
    } catch (error) {
      addToast({ type: 'error', message: 'Failed to create merge request' });
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
