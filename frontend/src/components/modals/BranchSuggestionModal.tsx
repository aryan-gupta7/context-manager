import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GitBranch, X, Sparkles, Loader2 } from 'lucide-react';
import useStore from '../../store';
import { nodesApi } from '../../services/api/client';
import type { Node } from 'reactflow';
import type { NodeData } from '../../types/node.types';

const BranchSuggestionModal = () => {
  const { 
    branchSuggestion, 
    branchSuggestionNodeId, 
    setBranchSuggestion, 
    addNode, 
    addToast,
    nodes
  } = useStore();
  const [isCreating, setIsCreating] = useState(false);

  if (!branchSuggestion || !branchSuggestionNodeId) return null;

  const parentNode = nodes.find(n => n.id === branchSuggestionNodeId);

  const handleAccept = async () => {
    setIsCreating(true);
    try {
      const response = await nodesApi.autoBranch(
        branchSuggestionNodeId, 
        branchSuggestion.suggested_branches
      );
      
      // Add created nodes to store
      response.created_nodes.forEach((nodeData: any, index: number) => {
        const newNode: Node<NodeData> = {
          id: nodeData.node_id,
          type: 'custom',
          position: nodeData.position || { 
            x: (parentNode?.position.x || 0) + (index * 350), 
            y: (parentNode?.position.y || 0) + 400 
          },
          data: {
            title: nodeData.title,
            nodeType: nodeData.node_type,
            status: nodeData.status,
            parentId: nodeData.parent_id,
            messageCount: 1,
            tokenCount: 0,
            inheritedContext: '',
            lastActivity: nodeData.created_at
          }
        };
        addNode(newNode);
      });
      
      addToast({ 
        type: 'success', 
        message: `Created ${response.created_nodes.length} branch${response.created_nodes.length > 1 ? 'es' : ''}` 
      });
      setBranchSuggestion(null);
    } catch (error) {
      console.error('Failed to create branches:', error);
      addToast({ type: 'error', message: 'Failed to create branches' });
    } finally {
      setIsCreating(false);
    }
  };

  const handleDismiss = () => {
    setBranchSuggestion(null);
  };

  return (
    <AnimatePresence>
      <motion.div 
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50"
      >
        <div className="bg-gradient-to-r from-purple-500/10 via-blue-500/10 to-purple-500/10
                        backdrop-blur-xl rounded-2xl border border-purple-500/30 
                        p-5 shadow-2xl shadow-purple-500/10 max-w-lg
                        animate-in slide-in-from-bottom-4 duration-300">
          
          {/* Header */}
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-xl 
                            border border-purple-400/20 shadow-inner">
              <Sparkles className="text-purple-400" size={22} />
            </div>
            
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-white font-bold text-base">
                  Split into branches?
                </h4>
                <button 
                  onClick={handleDismiss}
                  className="text-slate-500 hover:text-slate-300 transition-colors p-1 -mr-1"
                >
                  <X size={18} />
                </button>
              </div>
              
              <p className="text-slate-400 text-sm mb-4 leading-relaxed">
                {branchSuggestion.reason}
              </p>
              
              {/* Suggested Branches */}
              <div className="space-y-2.5 mb-5">
                {branchSuggestion.suggested_branches.map((branch, i) => (
                  <div 
                    key={i} 
                    className="flex items-start gap-3 p-3 rounded-xl 
                               bg-white/5 border border-white/10
                               hover:bg-white/8 transition-colors"
                  >
                    <div className="p-1.5 bg-purple-500/20 rounded-lg mt-0.5">
                      <GitBranch size={14} className="text-purple-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-white font-medium text-sm block truncate">
                        {branch.title}
                      </span>
                      <span className="text-slate-400 text-xs block mt-0.5 line-clamp-2">
                        {branch.focus}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Actions */}
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDismiss}
                  className="px-4 py-2 text-sm text-slate-400 hover:text-white 
                             transition-colors font-medium"
                >
                  Not now
                </button>
                <button
                  onClick={handleAccept}
                  disabled={isCreating}
                  className="flex-1 px-5 py-2.5 
                             bg-gradient-to-r from-purple-500 to-blue-500 
                             hover:from-purple-600 hover:to-blue-600 
                             text-white text-sm font-bold rounded-xl 
                             shadow-lg shadow-purple-500/25
                             transition-all duration-200
                             disabled:opacity-50 disabled:cursor-not-allowed
                             flex items-center justify-center gap-2"
                >
                  {isCreating ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <GitBranch size={16} />
                      Create {branchSuggestion.suggested_branches.length} Branch{branchSuggestion.suggested_branches.length > 1 ? 'es' : ''}
                    </>
                  )}
                </button>
              </div>
              
              {/* Confidence indicator */}
              <div className="mt-3 pt-3 border-t border-white/10">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">AI Confidence</span>
                  <span className="text-purple-400 font-medium">
                    {Math.round(branchSuggestion.confidence * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default BranchSuggestionModal;
