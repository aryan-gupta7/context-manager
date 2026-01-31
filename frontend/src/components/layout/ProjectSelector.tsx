import { useEffect } from 'react';
import { FolderOpen, Plus, ChevronDown } from 'lucide-react';
import useStore from '../../store';

const ProjectSelector = () => {
  const { 
    projects, 
    currentProjectId, 
    fetchProjects, 
    setCurrentProject, 
    setCreateProjectModalOpen,
    loading 
  } = useStore();

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const currentProject = projects.find(p => p.project_id === currentProjectId);

  return (
    <div className="relative group">
      <button 
        className="flex items-center gap-2 px-3 py-1.5 bg-surface-dark/50 hover:bg-surface-dark border border-surface-border rounded-lg text-sm transition-colors"
      >
        <FolderOpen size={16} className="text-primary" />
        <span className="text-white font-medium max-w-[150px] truncate">
          {currentProject ? currentProject.name : 'Select Project'}
        </span>
        <ChevronDown size={14} className="text-slate-400" />
      </button>

      {/* Dropdown */}
      <div className="absolute top-full left-0 mt-1 w-64 bg-surface-dark border border-surface-border rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
        <div className="p-2 border-b border-surface-border">
          <button
            onClick={() => setCreateProjectModalOpen(true)}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-primary hover:bg-primary/10 rounded-lg transition-colors"
          >
            <Plus size={16} />
            Create New Project
          </button>
        </div>
        
        <div className="max-h-64 overflow-y-auto p-2">
          {loading.projects ? (
            <div className="text-center text-slate-400 text-sm py-4">Loading...</div>
          ) : projects.length === 0 ? (
            <div className="text-center text-slate-400 text-sm py-4">
              No projects yet. Create one to get started!
            </div>
          ) : (
            projects.map(project => (
              <button
                key={project.project_id}
                onClick={() => setCurrentProject(project.project_id)}
                className={`w-full flex items-center justify-between px-3 py-2 text-sm rounded-lg transition-colors ${
                  project.project_id === currentProjectId 
                    ? 'bg-primary/20 text-white' 
                    : 'text-slate-300 hover:bg-white/5'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <FolderOpen size={14} />
                  <span className="truncate">{project.name}</span>
                </div>
                <span className="text-xs text-slate-500">{project.node_count} nodes</span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectSelector;
