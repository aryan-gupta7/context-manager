import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Lock, Sparkles, Lightbulb, ChevronDown } from 'lucide-react';
import clsx from 'clsx';
import type { NodeData } from '../../types/node.types';
import useStore from '../../store';

const CustomNode = ({ id, data, selected }: NodeProps<NodeData> & { id: string }) => {
  const isRoot = data.nodeType === 'root';
  const isActive = data.status === 'active';
  const isFrozen = data.status === 'frozen';
  const setExpandedNode = useStore(state => state.setExpandedNode);
  const setCreatingBranchNodeId = useStore(state => state.setCreatingBranchNodeId);
  const setMergingNodeId = useStore(state => state.setMergingNodeId);
  const removeNode = useStore(state => state.removeNode);
  const highlightedPath = useStore(state => state.highlightedPath);
  const selectedNodeId = useStore(state => state.selectedNodeId);

  const isHighlighted = highlightedPath.includes(id);
  const isDimmed = selectedNodeId && !isHighlighted;

  const handleExpand = (e: React.MouseEvent) => {
     e.stopPropagation();
     setExpandedNode(id);
  };
  
  const handleBranch = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCreatingBranchNodeId(id);
  };

  const handleMerge = (e: React.MouseEvent) => {
    e.stopPropagation();
    setMergingNodeId(id);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this node? Children will be re-parented.')) {
        removeNode(id);
    }
  };

  return (
    <div 
      className={clsx(
        "relative rounded-2xl overflow-hidden transition-all duration-300 group min-w-[300px]",
        isFrozen && "glass-card-frozen grayscale hover:grayscale-0",
        isActive && !isRoot && "glass-card-active ring-1 ring-primary/50",
        isRoot && "glass-panel shadow-2xl hover:shadow-primary/20",
        selected && "ring-2 ring-primary shadow-lg shadow-primary/20",
        isHighlighted && !selected && "ring-1 ring-primary/50 shadow-md shadow-primary/10",
        isDimmed && "opacity-40 hover:opacity-100"
      )}
    >
      {/* Handles */}
      <Handle type="target" position={Position.Top} className="!bg-transparent !border-none" />
      <Handle type="source" position={Position.Bottom} className="!bg-transparent !border-none" />

      {/* Header / Banner */}
      {isRoot ? (
        <div 
          className="h-32 bg-cover bg-center relative" 
          style={{
            backgroundImage: 'linear-gradient(180deg, rgba(0,0,0,0) 0%, #111318 100%), url("https://lh3.googleusercontent.com/aida-public/AB6AXuCrAGlIUa1xQYiLqSpW1o-Nsxo2ewPU5SBoKTqERaroJpLK3Ez3MrwDBdc2Vv6UJEFAK8OsIT1ZKulbwP2UePyxJsa8FADvaaGF24jypFMvqXd-i3eqkouAmlzBwLrTNzPe89ekPedye6qpmHWj1SXjrLj8VZB2p8oMoph84W9tE1D5h4IlQq0Ql5Ai604-PKf0SaVgGH8fYOJonMXDQRYuAO90PTwZqAJLfkUP_U6R6hiLemZN8nfwg3ETSAX3IwRo3sgD_R0aTjys")'
          }}
        >
          <div className="absolute top-3 right-3 bg-black/50 backdrop-blur-sm rounded-full px-2 py-1 text-[10px] text-white font-mono border border-white/10">ROOT</div>
        </div>
      ) : (
         // Standard Node Header 
         <div className="flex items-center justify-between p-4 pb-2">
            <div className={clsx(
                "text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider flex items-center gap-1",
                isActive ? "bg-primary/20 text-primary" : "bg-slate-700 text-slate-400"
            )}>
                {isFrozen && <Lock size={10} />}
                {data.status}
            </div>
            {isActive && <Sparkles size={18} className="text-primary" />}
         </div>
      )}

      {/* Body */}
      <div className={clsx("p-5", isRoot && "pt-2")}>
        <h3 className={clsx("text-2xl font-bold text-white mb-1 transition-colors", !isRoot && "text-lg leading-tight")}>
            {data.title}
        </h3>
        
        {/* Description / Summary - using inherited context for demo or a fixed string */}
        <p className="text-slate-400 text-sm mb-4 line-clamp-2">
            {data.inheritedContext || "No context summary available."}
        </p>

        {/* Insight Block (Active Node specific) */}
        {isActive && !isRoot && (
            <div className="bg-primary/10 rounded p-2 border border-primary/20 mb-3">
                <div className="flex gap-2 items-center text-xs text-primary mb-1">
                    <Lightbulb size={14} />
                    <span className="font-bold">Insight</span>
                </div>
                <p className="text-xs text-white/80 italic">"Recursive depth improves coherence."</p>
            </div>
        )}

        {/* Footer */}
        {isRoot && (
            <div className="flex items-center justify-between">
                <div className="flex -space-x-2">
                    <div className="w-6 h-6 rounded-full bg-slate-700 border border-background-dark flex items-center justify-center text-xs text-white">A</div>
                    <div className="w-6 h-6 rounded-full bg-primary border border-background-dark flex items-center justify-center text-xs text-white">B</div>
                </div>
                <button 
                    onClick={handleExpand}
                    className="text-primary text-sm font-bold hover:underline flex items-center gap-1"
                >
                    Expand <ChevronDown size={16} />
                </button>
            </div>
        )}
        {isActive && (
            <div className="flex gap-2 mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="flex-1 bg-primary hover:bg-blue-600 text-white text-xs font-bold py-1.5 rounded transition-colors" onClick={handleExpand}>
                    Expand
                </button>
                <button className="flex-1 bg-surface-border hover:bg-gray-700 text-white text-xs font-bold py-1.5 rounded transition-colors" onClick={handleBranch}>
                    Branch
                </button>
                <button className="flex-1 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 border border-purple-500/20 text-xs font-bold py-1.5 rounded transition-colors" onClick={handleMerge}>
                    Merge
                </button>
                <button className="flex-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 text-xs font-bold py-1.5 rounded transition-colors" onClick={handleDelete}>
                    Delete
                </button>
            </div>
        )}
      </div>
    </div>
  );
};

export default memo(CustomNode);
