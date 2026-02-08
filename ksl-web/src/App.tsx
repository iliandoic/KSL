import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { NavSidebar } from './components/NavSidebar';
import { FreestylePage } from './components/FreestylePage';
import { ImportPage } from './components/ImportPage';
import { SongsPage } from './components/SongsPage';
import { StudyPage } from './components/StudyPage';

const PAGE_TITLES: Record<string, string> = {
  freestyle: 'Freestyle',
  import: 'Import',
  songs: 'Songs',
  study: 'Study',
};

function AppLayout() {
  const location = useLocation();
  const path = location.pathname.slice(1) || 'freestyle';
  const pageKey = path in PAGE_TITLES ? path : 'freestyle';

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-zinc-200 flex">
      <NavSidebar />
      <div className="flex-1 flex flex-col">
        <header className="border-b border-zinc-800 px-6 py-3">
          <h1 className="text-xl font-bold">
            <span className="text-amber-400">KSL</span>
            <span className="text-zinc-500 text-sm ml-2 font-normal">
              {PAGE_TITLES[pageKey]}
            </span>
          </h1>
        </header>

        <div className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/freestyle" replace />} />
            <Route path="/freestyle" element={<FreestylePage />} />
            <Route path="/import" element={<ImportPage />} />
            <Route path="/songs" element={<SongsPage />} />
            <Route path="/study" element={<StudyPage />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}

export default App;
