import { useState } from 'react';
import { LayoutDashboard, Clock, Bookmark, Share2, Archive, Search, ChevronRight, FileText, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import useStore from '../../store';
import clsx from 'clsx';

const Sidebar = () => {
  const { nodes, selectedNodeId, setSelectedNode } = useStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [isTreeExpanded, setIsTreeExpanded] = useState(true);

  const filteredNodes = nodes.filter(node => 
    node.data.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (node.data.inheritedContext && node.data.inheritedContext.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <aside className="w-72 bg-background-dark border-r border-surface-border flex flex-col h-full z-40 shrink-0 transition-all duration-300">
      {/* Project Header */}
      <div className="p-4 border-b border-surface-border/50">
        <div className="flex gap-3 items-center mb-4">
          <div 
            className="bg-center bg-no-repeat aspect-square bg-cover rounded-xl size-12 shadow-inner" 
            style={{backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuAtQeCC8zYrrZQaiERkn75YGM4e_ojYkrKd9Anq_O7N91u-PZREynOZmHYfMQ1FMEffvNDkccDepKL8sNKZIw7eNY3BG5tEwS680tuEkNStvzRpJe5gkJaE3k7zMoLXrVrtd1BAaXLkXSc0yvXmsQd8hXNoOsixDODs2rDJgPT6jFA2h6Fq5fnoNfTHydqOAlnXuNthecIUeRo6WRsRDQoZD5Ak69ES4ucKVFomQ6qkfMfRepIz8N-syDp27HGj9CLMxuQ3QsToGz1G")'}}
          ></div>
          <div className="flex flex-col">
            <h1 className="text-white text-base font-bold leading-tight">Project Alpha</h1>
            <p className="text-slate-400 text-xs font-normal">Last edited 5m ago</p>
          </div>
        </div>
        
        {/* Search Bar */}
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search size={20} />
          </div>
          <input 
            className="block w-full rounded-lg border-none bg-surface-border py-2 pl-10 pr-3 text-sm text-white placeholder:text-slate-500 focus:ring-1 focus:ring-primary focus:bg-[#1f242e] transition-all" 
            placeholder="Search nodes..." 
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
        {/* Tree View Section */}
        <div className="mb-2">
            <button 
                onClick={() => setIsTreeExpanded(!isTreeExpanded)}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-border text-slate-300 hover:text-white transition-colors text-left"
            >
                <LayoutDashboard size={20} className="text-primary" />
                <span className="text-sm font-medium flex-1">Tree View</span>
                {isTreeExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            
            <AnimatePresence>
            {isTreeExpanded && (
                <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="mt-1 ml-4 space-y-0.5 border-l border-surface-border/50 pl-2 overflow-hidden"
                >
                    {filteredNodes.length > 0 ? (
                        filteredNodes.map(node => (
                            <button
                                key={node.id}
                                onClick={() => setSelectedNode(node.id)}
                                className={clsx(
                                    "w-full flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors text-left group",
                                    selectedNodeId === node.id 
                                        ? "bg-primary/20 text-white" 
                                        : "text-slate-400 hover:bg-surface-border hover:text-slate-200"
                                )}
                            >
                                <FileText size={14} className={clsx(selectedNodeId === node.id ? "text-primary" : "text-slate-500 group-hover:text-slate-300")} />
                                <span className="text-xs font-medium truncate">{node.data.title}</span>
                                {node.data.status === 'frozen' && <span className="w-1.5 h-1.5 rounded-full bg-slate-500 ml-auto" />}
                                {node.data.status === 'active' && <span className="w-1.5 h-1.5 rounded-full bg-green-500 ml-auto" />}
                            </button>
                        ))
                    ) : (
                         <div className="px-3 py-2 text-xs text-slate-500 italic">No nodes found</div>
                    )}
                </motion.div>
            )}
            </AnimatePresence>
        </div>

        <a className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-border text-slate-300 hover:text-white transition-colors" href="#">
          <Clock size={20} />
          <span className="text-sm font-medium">Recent Thoughts</span>
        </a>
        <a className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-border text-slate-300 hover:text-white transition-colors" href="#">
          <Bookmark size={20} />
          <span className="text-sm font-medium">Bookmarks</span>
        </a>
        
        <div className="my-4 border-t border-surface-border/50 mx-3"></div>
        <div className="px-3 pb-2 text-xs font-bold text-slate-500 uppercase tracking-wider">Shared Spaces</div>
        
        <a className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-border text-slate-300 hover:text-white transition-colors" href="#">
          <Share2 size={20} />
          <span className="text-sm font-medium">Team Brain</span>
        </a>
        <a className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-border text-slate-300 hover:text-white transition-colors" href="#">
          <Archive size={20} />
          <span className="text-sm font-medium">Archive</span>
        </a>
      </nav>
      
      {/* Sidebar Footer */}
      <div className="p-4 border-t border-surface-border/50">
        <div className="flex items-center justify-between text-slate-400 text-xs">
          <span>v2.4.0</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500"></span> Online</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
