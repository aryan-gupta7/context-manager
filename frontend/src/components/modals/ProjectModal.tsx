import { useState } from 'react';
import { X, FolderPlus } from 'lucide-react';
import useStore from '../../store';

const ProjectModal = () => {
  const { createProjectModalOpen, setCreateProjectModalOpen, createProject, setCurrentProject } = useStore();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!createProjectModalOpen) return null;

  const handleClose = () => {
    setCreateProjectModalOpen(false);
    setName('');
    setDescription('');
  };

  const handleCreate = async () => {
    if (!name.trim()) return;
    
    setIsSubmitting(true);
    try {
      const project = await createProject(name.trim(), description.trim() || undefined);
      if (project) {
        // Switch to the new project
        await setCurrentProject(project.project_id);
        handleClose();
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-50">
      <div className="bg-white dark:bg-[#1a1d26] w-full max-w-md rounded-2xl shadow-2xl border border-gray-200 dark:border-[#282e39] overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-[#282e39]">
          <h3 className="text-lg font-bold text-[#111318] dark:text-white flex items-center gap-2">
            <FolderPlus className="text-primary" size={20} />
            Create New Project
          </h3>
          <button onClick={handleClose} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>
        
        <div className="p-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-400 mb-1">Project Name *</label>
            <input
              autoFocus
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Awesome Project"
              className="w-full bg-transparent border border-gray-200 dark:border-[#282e39] rounded-lg px-4 py-2 text-[#111318] dark:text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-400 mb-1">Description (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is this project about?"
              rows={3}
              className="w-full bg-transparent border border-gray-200 dark:border-[#282e39] rounded-lg px-4 py-2 text-[#111318] dark:text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all resize-none"
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
              disabled={!name.trim() || isSubmitting}
              className="px-4 py-2 rounded-lg text-sm font-bold bg-primary hover:bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isSubmitting ? 'Creating...' : <><FolderPlus size={16} /> Create Project</>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectModal;
