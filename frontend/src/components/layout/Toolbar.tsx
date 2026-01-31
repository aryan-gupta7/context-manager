import { Settings, Bell, UserCircle } from 'lucide-react';
import ProjectSelector from './ProjectSelector';

const Toolbar = () => {
  return (
    <header className="z-50 flex items-center justify-between border-b border-surface-border bg-background-dark/90 backdrop-blur-md px-6 py-3 h-16 shrink-0">
      <div className="flex items-center gap-6 text-white">
        <div className="flex items-center gap-4">
          <div className="size-8 text-primary flex items-center justify-center">
            {/* Logo Placeholder */}
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </div>
          <h2 className="text-white text-xl font-bold leading-tight tracking-tight">Fractal Workspace</h2>
        </div>
        
        {/* Project Selector */}
        <ProjectSelector />
      </div>
      
      <div className="flex gap-3">
        <button className="flex items-center gap-2 cursor-pointer overflow-hidden rounded-lg h-9 px-4 bg-primary hover:bg-blue-600 transition-colors text-white text-sm font-bold leading-normal tracking-wide">
          <UserCircle size={18} />
          <span className="truncate">Profile</span>
        </button>
        <button className="flex size-9 cursor-pointer items-center justify-center overflow-hidden rounded-lg bg-surface-border hover:bg-gray-700 transition-colors text-white">
          <Settings size={20} />
        </button>
        <button className="flex size-9 cursor-pointer items-center justify-center overflow-hidden rounded-lg bg-surface-border hover:bg-gray-700 transition-colors text-white relative">
          <Bell size={20} />
          <span className="absolute top-2 right-2 size-2 bg-red-500 rounded-full border border-[#111318]"></span>
        </button>
      </div>
    </header>
  );
};

export default Toolbar;

