import { SparkPanel } from './components/SparkPanel';
import { Editor } from './components/Editor';
import { Sidebar } from './components/Sidebar';
import { NavSidebar } from './components/NavSidebar';
import { ImportPage } from './components/ImportPage';
import { useStore } from './store';

function StudioPage() {
  return (
    <main className="flex-1 max-w-7xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
      <div className="space-y-4">
        <SparkPanel />
        <Editor />
      </div>
      <Sidebar />
    </main>
  );
}

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
              {currentPage === 'studio' ? 'Lyrics Studio' : 'Import Lyrics'}
            </span>
          </h1>
        </header>

        <div className="flex-1 p-4">
          {currentPage === 'studio' && <StudioPage />}
          {currentPage === 'import' && <ImportPage />}
        </div>
      </div>
    </div>
  );
}

export default App;
