import { NavSidebar } from './components/NavSidebar';
import { FreestylePage } from './components/FreestylePage';
import { ImportPage } from './components/ImportPage';
import { SongsPage } from './components/SongsPage';
import { StudyPage } from './components/StudyPage';
import { useStore } from './store';

const PAGE_TITLES: Record<string, string> = {
  freestyle: 'Freestyle',
  import: 'Import',
  songs: 'Songs',
  study: 'Study',
};

function App() {
  const { currentPage } = useStore();

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-zinc-200 flex">
      <NavSidebar />
      <div className="flex-1 flex flex-col">
        <header className="border-b border-zinc-800 px-6 py-3">
          <h1 className="text-xl font-bold">
            <span className="text-amber-400">KSL</span>
            <span className="text-zinc-500 text-sm ml-2 font-normal">
              {PAGE_TITLES[currentPage] || 'Freestyle'}
            </span>
          </h1>
        </header>

        <div className="flex-1 overflow-y-auto">
          {currentPage === 'freestyle' && <FreestylePage />}
          {currentPage === 'import' && <ImportPage />}
          {currentPage === 'songs' && <SongsPage />}
          {currentPage === 'study' && <StudyPage />}
        </div>
      </div>
    </div>
  );
}

export default App;
