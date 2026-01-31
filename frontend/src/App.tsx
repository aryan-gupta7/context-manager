import Sidebar from './components/layout/Sidebar';
import Toolbar from './components/layout/Toolbar';
import CanvasWrapper from './components/layout/Canvas';
import ChatPanel from './components/chat/ChatPanel';
import BranchModal from './components/modals/BranchModal';
import MergeModal from './components/modals/MergeModal';

function App() {
  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-background-dark text-white font-display relative">
      <Toolbar />
      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar />
        <main className="flex-1 relative bg-background-dark overflow-hidden">
          <CanvasWrapper />
          <ChatPanel />
          <BranchModal />
          <MergeModal />
        </main>
      </div>
    </div>
  );
}

export default App;
