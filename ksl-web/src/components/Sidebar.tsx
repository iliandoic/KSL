import { useState } from 'react';
import { api } from '../api';
import { useStore } from '../store';

export function Sidebar() {
  return (
    <div className="space-y-4">
      <RhymePanel />
      <QuickImportLink />
    </div>
  );
}

function RhymePanel() {
  const [word, setWord] = useState('');
  const [result, setResult] = useState<{
    perfect: string[];
    near: string[];
    slant: string[];
  } | null>(null);
  const { loading, setLoading } = useStore();

  const search = async () => {
    if (!word.trim()) return;
    setLoading('rhyme', true);
    try {
      const res = await api.rhymes(word.trim());
      setResult({ perfect: res.perfect, near: res.near, slant: res.slant });
    } finally {
      setLoading('rhyme', false);
    }
  };

  return (
    <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
      <h3 className="text-sm font-bold text-amber-400 mb-2">Rhymes</h3>
      <div className="flex gap-2 mb-3">
        <input
          value={word}
          onChange={(e) => setWord(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
          placeholder="Type a word..."
          className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm flex-1"
        />
        <button
          onClick={search}
          disabled={loading['rhyme']}
          className="bg-amber-500 text-black px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-amber-400 disabled:opacity-50"
        >
          {loading['rhyme'] ? '...' : 'Find'}
        </button>
      </div>

      {result && (
        <div className="space-y-2 text-sm">
          {result.perfect.length > 0 && (
            <div>
              <span className="text-green-400 text-xs font-bold">PERFECT</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {result.perfect.map((w, i) => (
                  <span key={i} className="px-2 py-0.5 bg-green-500/10 text-green-300 rounded">{w}</span>
                ))}
              </div>
            </div>
          )}
          {result.near.length > 0 && (
            <div>
              <span className="text-yellow-400 text-xs font-bold">NEAR</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {result.near.map((w, i) => (
                  <span key={i} className="px-2 py-0.5 bg-yellow-500/10 text-yellow-300 rounded">{w}</span>
                ))}
              </div>
            </div>
          )}
          {result.slant.length > 0 && (
            <div>
              <span className="text-orange-400 text-xs font-bold">SLANT</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {result.slant.map((w, i) => (
                  <span key={i} className="px-2 py-0.5 bg-orange-500/10 text-orange-300 rounded">{w}</span>
                ))}
              </div>
            </div>
          )}
          {!result.perfect.length && !result.near.length && !result.slant.length && (
            <p className="text-zinc-500">No rhymes found. Try importing lyrics first.</p>
          )}
        </div>
      )}
    </div>
  );
}

function QuickImportLink() {
  const { setPage } = useStore();

  return (
    <button
      onClick={() => setPage('import')}
      className="w-full bg-zinc-900 rounded-xl p-4 border border-zinc-800 hover:border-purple-500/50 transition-colors text-left group"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
          <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </div>
        <div>
          <h3 className="text-sm font-bold text-zinc-200 group-hover:text-purple-400 transition-colors">Import Lyrics</h3>
          <p className="text-xs text-zinc-500">Scrape from Genius or paste</p>
        </div>
      </div>
    </button>
  );
}
