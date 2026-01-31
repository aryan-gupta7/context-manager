import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, CheckSquare, Minimize2, Send, Mic, 
  History, Bot, CornerUpLeft
} from 'lucide-react';
import useStore from '../../store';
import type { Message } from '../../types/node.types';
import { nodesApi } from '../../services/api/client';

const ChatPanel = () => {
  const { expandedNodeId, nodes, messages, setExpandedNode, addMessage: addStoreMessage } = useStore();
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [_isLoadingMessages, setIsLoadingMessages] = useState(false);

  const node = nodes.find(n => n.id === expandedNodeId);

  // Load messages from backend when node is expanded
  useEffect(() => {
    if (!expandedNodeId) return;
    
    // Skip if we already have messages for this node
    if (messages[expandedNodeId]?.length > 0) return;
    
    const loadMessages = async () => {
      setIsLoadingMessages(true);
      try {
        const fetchedMessages = await nodesApi.getMessages(expandedNodeId);
        // Add each message to the store
        fetchedMessages.forEach(msg => addStoreMessage(expandedNodeId, msg));
      } catch (error) {
        console.error('Failed to load messages:', error);
      } finally {
        setIsLoadingMessages(false);
      }
    };
    
    loadMessages();
  }, [expandedNodeId, messages, addStoreMessage]);

  if (!expandedNodeId || !node) return null;

  const nodeMessages = messages[expandedNodeId] || [];

  const handleClose = () => setExpandedNode(null);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;
    
    const userMsg: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: inputText,
        timestamp: new Date().toISOString()
    };
    
    addStoreMessage(node.id, userMsg);
    
    setInputText('');
    setIsTyping(true);

    try {
        const response = await nodesApi.sendMessage(node.id, userMsg.content);
        addStoreMessage(node.id, response);
    } finally {
        setIsTyping(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="absolute inset-0 flex items-center justify-center p-4 sm:p-8 backdrop-blur-[2px] z-50"
      >
      <div className="flex flex-col w-full max-w-[1000px] h-full max-h-[85vh] bg-white dark:bg-[#151a23] rounded-2xl shadow-2xl border border-gray-200 dark:border-[#282e39] overflow-hidden relative">
        
        {/* Header */}
        <div className="flex flex-col border-b border-gray-200 dark:border-[#282e39] bg-gray-50/80 dark:bg-[#1a202a]/80 backdrop-blur-md z-10">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-[#282e39]/50">
                <div className="flex flex-wrap items-center gap-2">
                    <CornerUpLeft size={16} className="text-slate-400" />
                    <span className="text-slate-400 text-sm font-medium">Root</span>
                    <span className="text-slate-400 text-sm">/</span>
                    <span className="text-slate-400 text-sm font-medium">Project Alpha</span>
                    <span className="text-slate-400 text-sm">/</span>
                    <span className="text-[#111318] dark:text-white text-sm font-bold bg-primary/10 px-2 py-0.5 rounded text-primary">
                        {node.data.title}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={handleClose} className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors">
                        <Minimize2 size={20} />
                    </button>
                    <button onClick={handleClose} className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors">
                        <X size={20} />
                    </button>
                </div>
            </div>

            {/* Lineage Summary */}
            <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-white dark:from-[#1a202a] dark:to-[#151a23]">
                <div className="flex items-start gap-4 p-4 rounded-xl border border-gray-200 dark:border-[#282e39] bg-white dark:bg-[#1c222e] shadow-sm">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary shrink-0">
                        <History size={20} />
                    </div>
                    <div className="flex flex-col gap-1 flex-1">
                        <div className="flex items-center justify-between">
                            <p className="text-[#111318] dark:text-white text-sm font-bold uppercase tracking-wide">Lineage Context</p>
                            <span className="text-xs text-slate-400 bg-gray-100 dark:bg-[#282e39] px-2 py-1 rounded">3 Parent Nodes</span>
                        </div>
                        <p className="text-[#5b6579] dark:text-[#9da6b9] text-sm font-normal leading-relaxed text-left">
                            This node inherits context from <span className="text-primary font-medium">System Architecture</span>. Key constraints: Low latency, modular plugins.
                        </p>
                    </div>
                </div>
            </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 bg-white dark:bg-[#151a23]">
             <div className="flex justify-center">
                <span className="text-xs font-medium text-slate-400 px-3 py-1 rounded-full border border-gray-200 dark:border-[#282e39] bg-gray-50 dark:bg-[#1c222e]">
                    Today, 10:23 AM
                </span>
            </div>

            {/* Mock User Message */}
            {nodeMessages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'flex-row-reverse' : 'items-start'} gap-3 group`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs shrink-0 ${msg.role === 'user' ? 'bg-primary' : 'bg-green-500'}`}>
                         {msg.role === 'user' ? 'U' : <Bot size={18} />}
                    </div>
                    <div className={`flex flex-col gap-1 max-w-[70%] ${msg.role === 'user' ? 'items-end' : ''}`}>
                         {msg.role !== 'user' && (
                             <div className="flex items-center gap-2">
                                <span className="text-sm font-bold text-[#111318] dark:text-white">Fractal AI</span>
                            </div>
                         )}
                        <div className={`p-4 rounded-2xl shadow-md text-left ${msg.role === 'user' ? 'rounded-tr-sm bg-primary text-white' : 'rounded-tl-none bg-gray-100 dark:bg-[#1c222e] text-[#111318] dark:text-[#e0e2e7]'}`}>
                            <p className="text-sm font-normal leading-relaxed font-body whitespace-pre-wrap">
                                {msg.content}
                            </p>
                        </div>
                    </div>
                </div>
            ))}
            
            {/* Typing Indicator */}
            {isTyping && (
                <div className="flex items-center gap-2 text-slate-500 text-sm italic ml-14">
                    <span className="animate-pulse">AI is thinking...</span>
                </div>
            )}
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white dark:bg-[#151a23] border-t border-gray-200 dark:border-[#282e39]">
            <div className="relative flex items-end gap-2 bg-gray-50 dark:bg-[#1c222e] border border-gray-200 dark:border-[#282e39] rounded-xl p-2 shadow-sm focus-within:ring-1 focus-within:ring-primary focus-within:border-primary transition-all">
                <button className="p-2 text-slate-400 hover:text-primary rounded-lg transition-colors self-end mb-0.5">
                    <CheckSquare size={20} />
                </button>
                <textarea 
                    className="flex-1 bg-transparent border-none focus:ring-0 text-[#111318] dark:text-white placeholder-slate-400 resize-none h-auto min-h-[44px] max-h-[120px] py-3 text-sm font-body"
                    placeholder="Ask follow up questions..."
                    rows={1}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSendMessage();
                        }
                    }}
                />
                 <div className="flex items-center gap-1 pb-1">
                    <button className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors">
                        <Mic size={20} />
                    </button>
                     <button 
                        onClick={handleSendMessage}
                        className="p-2 bg-primary hover:bg-blue-600 text-white rounded-lg shadow-sm transition-colors"
                     >
                        <Send size={20} />
                    </button>
                </div>
            </div>
        </div>

      </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ChatPanel;
