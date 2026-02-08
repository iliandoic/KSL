import { SparkPanel } from './components/SparkPanel';
import { Editor } from './components/Editor';
import { Sidebar } from './components/Sidebar';

function App() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] text-zinc-200">
      <header className="border-b border-zinc-800 px-6 py-3">
        <h1 className="text-xl font-bold">
          <span className="text-amber-400">KSL</span>
          <span className="text-zinc-500 text-sm ml-2 font-normal">Lyrics Studio</span>
        </h1>
      </header>

      <main className="max-w-7xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          <SparkPanel />
          <Editor />
        </div>
        <Sidebar />
      </main>
    </div>
  );
}

export default App;
